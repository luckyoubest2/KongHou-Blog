#!/usr/bin/env python3
"""文章册 regctl —— KongHou-Blog 文章登记库

架构（2026-09-21 定，老大拍板）：
  - registry 词注册表：数据库为准。词的用途/状态/归并关系直接在库里维护，
    taxonomy.md 只是 export-taxonomy 生成的只读快照。
  - posts + 三张关联表：跟 frontmatter 增量同步（update 逐篇 upsert，删文即清行），
    永不整库重建（build 命令已废除）。
  - verify：校验库与磁盘的一致性；有硬伤时退出码 1，可挂脚本。

词状态机: normal(在用) / 新词(新出现待定类) / 候选(治理建议待裁决) / 废弃(停用)

用法:
  python3 regctl.py update             # 增量同步磁盘 → 库（新词自动登记为「新词」）
  python3 regctl.py verify             # 校验一致性（硬伤退出码 1）
  python3 regctl.py words [--dim tags] [--status 候选]        # 注册表查询
  python3 regctl.py word --dim tags --name X [--status S] [--merged-into Y]
                      [--purpose "..."] [--aliases "a,b"]      # 维护注册表
  python3 regctl.py tags [--min N] / cats / colls             # 使用计数
  python3 regctl.py show --tag X | --cat X | --coll X         # 词 → 文章
  python3 regctl.py article 关键词                             # 单篇完整元数据
  python3 regctl.py fields             # frontmatter 字段使用率
  python3 regctl.py export-taxonomy [--out taxonomy.md]       # 注册表 → markdown 快照
"""
import argparse
import hashlib
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # 仓库根
REGDIR = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
DB = REGDIR / "articles.db"

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.S)
DIMS = (("tags", "tags"), ("categories", "categories"), ("collections", "collections"))
STATUSES = ("normal", "新词", "候选", "废弃")


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def fm_block(text: str) -> str:
    m = FM_RE.match(text)
    return m.group(1) if m else ""


def parse_fm(text: str) -> dict:
    raw = fm_block(text)
    if not raw:
        return {}
    try:
        import yaml  # 本机已装（scripts/metadata_manager.py 在用）
        d = yaml.safe_load(raw)
        return d if isinstance(d, dict) else {}
    except ImportError:
        pass
    d, cur = {}, None
    for line in raw.splitlines():
        if re.match(r"^[A-Za-z_][\w-]*:\s*$", line):
            cur = line.split(":")[0]
            d.setdefault(cur, None)
        elif re.match(r"^[A-Za-z_][\w-]*:", line):
            k, v = line.split(":", 1)
            d[k] = v.strip().strip("'\"") or None
            cur = None
        elif cur and re.match(r"^\s+-\s*", line):
            if not isinstance(d.get(cur), list):
                d[cur] = []
            d[cur].append(re.sub(r"^\s+-\s*", "", line).strip().strip("'\""))
    return d


def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [str(v).strip()]


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def ensure_schema(con):
    con.execute("""CREATE TABLE IF NOT EXISTS registry(
        word TEXT NOT NULL, dim TEXT NOT NULL,
        purpose TEXT DEFAULT '', status TEXT DEFAULT 'normal',
        merged_into TEXT DEFAULT '', aliases TEXT DEFAULT '',
        updated_at TEXT DEFAULT '',
        PRIMARY KEY(word, dim))""")
    cols = {r[1] for r in con.execute("PRAGMA table_info(posts)")}
    if cols and "fm_hash" not in cols:
        con.execute("ALTER TABLE posts ADD COLUMN fm_hash TEXT")
    con.commit()


def disk_files():
    return {f.relative_to(ROOT).as_posix(): f
            for f in sorted(CONTENT.rglob("*.md"))}


def text_hash(text: str) -> str:
    return hashlib.sha256(fm_block(text).encode("utf-8")).hexdigest()


def upsert_post(con, rel, text):
    """逐篇入库：posts 行 REPLACE + 该篇在三张关联表的行全换新。返回词列表。"""
    fm = parse_fm(text)
    con.execute("""INSERT OR REPLACE INTO posts
        (file,title,date,draft,subtitle,description,fm_json,fm_hash)
        VALUES(?,?,?,?,?,?,?,?)""",
        (rel, fm.get("title"), str(fm.get("date") or ""),
         1 if fm.get("draft") in (True, "true") else 0,
         fm.get("subtitle"), fm.get("description"),
         json.dumps(fm, ensure_ascii=False, default=str), text_hash(text)))
    words = []
    for dim, key in DIMS:
        con.execute(f"DELETE FROM post_{dim} WHERE file=?", (rel,))
        vals = as_list(fm.get(key))
        con.executemany(f"INSERT OR IGNORE INTO post_{dim} VALUES(?,?)",
                        [(rel, w) for w in vals])
        words += [(dim, w) for w in vals]
    return words


def cmd_update():
    con = connect()
    ensure_schema(con)
    seeded = con.execute("SELECT COUNT(*) FROM registry").fetchone()[0] == 0
    disk = disk_files()
    known = {r["file"]: r["fm_hash"] for r in
             con.execute("SELECT file, fm_hash FROM posts")}
    added = updated = unchanged = removed = 0
    new_words = []
    for rel, path in disk.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        h = text_hash(text)
        if rel in known and known[rel] == h:
            unchanged += 1
            continue
        words = upsert_post(con, rel, text)
        for dim, w in words:
            hit = con.execute("SELECT 1 FROM registry WHERE word=? AND dim=?",
                              (w, dim)).fetchone()
            if not hit:
                # 首次播种全记 normal；此后新出现的词标「新词」等人定类
                st = "normal" if seeded else "新词"
                con.execute("INSERT INTO registry VALUES(?,?,?,?,?,?,?)",
                            (w, dim, "", st, "", "", now()))
                new_words.append((dim, w))
        if rel in known:
            updated += 1
        else:
            added += 1
    for rel in sorted(set(known) - set(disk)):
        con.execute("DELETE FROM posts WHERE file=?", (rel,))
        for _, key in DIMS:
            con.execute(f"DELETE FROM post_{key} WHERE file=?", (rel,))
        removed += 1
    con.commit()
    print(f"同步完成：新增 {added} / 更新 {updated} / 未变 {unchanged} / 移除 {removed}")
    if new_words:
        print(f"新词登记 {len(new_words)} 个（status=新词，待定类）：")
        for dim, w in new_words:
            print(f"  [{dim}] {w}")


def cmd_verify():
    con = connect()
    ensure_schema(con)
    disk = disk_files()
    db = {r["file"]: r["fm_hash"] for r in
          con.execute("SELECT file, fm_hash FROM posts")}
    reg = {(r["word"], r["dim"]): r["status"] for r in
           con.execute("SELECT word, dim, status FROM registry")}

    missing = sorted(set(disk) - set(db))
    orphan = sorted(set(db) - set(disk))
    stale = sorted(rel for rel in set(disk) & set(db)
                   if text_hash(disk[rel].read_text(
                       encoding="utf-8", errors="replace")) != db[rel])
    unreg, banned = [], []
    for rel, path in disk.items():
        fm = parse_fm(path.read_text(encoding="utf-8", errors="replace"))
        for dim, key in DIMS:
            for w in as_list(fm.get(key)):
                st = reg.get((w, dim))
                if st is None:
                    unreg.append((dim, w, rel))
                elif st == "废弃":
                    banned.append((dim, w, rel))

    hard = 0
    if missing:
        hard += 1
        print(f"✗ 磁盘有、库没有 {len(missing)} 篇（跑 update）:")
        for r in missing:
            print(f"    {r}")
    if orphan:
        hard += 1
        print(f"✗ 库有、磁盘没了 {len(orphan)} 条（跑 update 清理）:")
        for r in orphan:
            print(f"    {r}")
    if stale:
        hard += 1
        print(f"✗ frontmatter 改了、库没跟上 {len(stale)} 篇（跑 update）:")
        for r in stale:
            print(f"    {r}")
    if unreg:
        hard += 1
        print(f"✗ 未登记词 {len(unreg)} 处:")
        for dim, w, rel in unreg:
            print(f"    [{dim}] {w} <- {rel}")
    if banned:
        hard += 1
        print(f"✗ 已废弃词仍挂在文章上 {len(banned)} 处:")
        for dim, w, rel in banned:
            print(f"    [{dim}] {w} <- {rel}")

    for st in ("新词", "候选"):
        rows = con.execute(
            "SELECT word, dim, purpose FROM registry WHERE status=? "
            "ORDER BY dim, word", (st,)).fetchall()
        if rows:
            print(f"● {st} {len(rows)} 个（待处理，不算错误）:")
            for r in rows:
                tail = f"  # {r['purpose']}" if r["purpose"] else ""
                print(f"    [{r['dim']}] {r['word']}{tail}")
    ban_cnt = con.execute(
        "SELECT COUNT(*) FROM registry WHERE status='废弃'").fetchone()[0]
    print(f"● 废弃词 {ban_cnt} 个"
          + ("（全部未挂用，干净）" if ban_cnt and not banned else ""))

    if hard:
        sys.exit(f"✗ verify 未通过：{hard} 类硬伤")
    print("✓ 库与磁盘一致，注册表无违规挂用")


def cmd_word(args):
    con = connect()
    ensure_schema(con)
    row = con.execute("SELECT * FROM registry WHERE word=? AND dim=?",
                      (args.name, args.dim)).fetchone()
    if row is None:
        if not args.status and not args.purpose:
            sys.exit(f"registry 里没有 [{args.dim}] {args.name}，"
                     f"新建请至少给 --status 或 --purpose")
        data = {"purpose": "", "status": "normal", "merged_into": "",
                "aliases": ""}
        print(f"新建注册项 [{args.dim}] {args.name}")
    else:
        data = dict(row)
    for k in ("status", "merged_into", "purpose", "aliases"):
        v = getattr(args, k)
        if v is not None:
            if k == "status" and v not in STATUSES:
                sys.exit(f"status 只能是 {'/'.join(STATUSES)}")
            data[k] = v
    con.execute("""INSERT OR REPLACE INTO registry
        (word,dim,purpose,status,merged_into,aliases,updated_at)
        VALUES(?,?,?,?,?,?,?)""",
        (args.name, args.dim, data["purpose"], data["status"],
         data["merged_into"], data["aliases"], now()))
    con.commit()
    msg = f"已登记：[{args.dim}] {args.name}  status={data['status']}"
    if data["merged_into"]:
        msg += f"  →并入 {data['merged_into']}"
    if data["purpose"]:
        msg += f"  # {data['purpose']}"
    print(msg)


def cmd_words(args):
    con = connect()
    ensure_schema(con)
    q = "SELECT * FROM registry WHERE 1=1"
    params = []
    if args.dim:
        q += " AND dim=?"
        params.append(args.dim)
    if args.status:
        q += " AND status=?"
        params.append(args.status)
    q += " ORDER BY dim, status, word"
    rows = con.execute(q, params).fetchall()
    print(f"registry 共 {len(rows)} 条")
    for r in rows:
        parts = [f"[{r['dim']}] {r['word']}", r["status"]]
        if r["merged_into"]:
            parts.append(f"→{r['merged_into']}")
        if r["aliases"]:
            parts.append(f"别名:{r['aliases']}")
        if r["purpose"]:
            parts.append(f"# {r['purpose']}")
        print("  " + "  ".join(parts))


def _dim_report(table, col, min_n):
    rows = connect().execute(
        f"SELECT {col} v, COUNT(*) n FROM {table} GROUP BY v "
        "ORDER BY n DESC, v").fetchall()
    for r in rows:
        if r["n"] < min_n:
            continue
        mark = "  <- 一次性" if r["n"] == 1 else ""
        print(f"  {r['n']:>2}x  {r['v']}{mark}")
    print(f"  ({len(rows)} 个不同值)")


def cmd_tags(min_n):
    print("=== tags 使用计数 ===")
    _dim_report("post_tags", "tag", min_n)


def cmd_cats():
    print("=== categories 使用计数 ===")
    _dim_report("post_categories", "category", 1)


def cmd_colls():
    print("=== collections 使用计数 ===")
    _dim_report("post_collections", "collection", 1)


def cmd_show(field, value):
    col, table = {"tag": ("tag", "post_tags"),
                  "cat": ("category", "post_categories"),
                  "coll": ("collection", "post_collections")}[field]
    con = connect()
    rows = con.execute(
        f"""SELECT p.date, p.title, p.file FROM posts p
            JOIN {table} j ON j.file = p.file
            WHERE j.{col} = ? ORDER BY p.date""", (value,)).fetchall()
    if not rows:
        sys.exit(f"没有文章挂着 {field}={value}")
    print(f"=== {field}={value}：{len(rows)} 篇 ===")
    for r in rows:
        print(f"  {r['date'][:10]}  {r['title']}\n      {r['file']}")


def cmd_article(kw):
    con = connect()
    rows = con.execute(
        "SELECT file, title FROM posts WHERE file LIKE ? OR title LIKE ?",
        (f"%{kw}%", f"%{kw}%")).fetchall()
    if not rows:
        sys.exit(f"没找到匹配「{kw}」的文章")
    if len(rows) > 1:
        print(f"匹配到 {len(rows)} 篇，缩小关键词：")
        for r in rows:
            print(f"  {r['file']}")
        return
    p = con.execute("SELECT * FROM posts WHERE file=?",
                    (rows[0]["file"],)).fetchone()
    fm = json.loads(p["fm_json"])
    print(f"=== {p['title']} ===")
    print(f"文件: {p['file']}")
    for k, v in fm.items():
        if isinstance(v, str) and len(v) > 60:
            v = v[:60] + "…"
        print(f"  {k}: {v}")
    print("  --- 关联 ---")
    for label, table, col in [("tags", "post_tags", "tag"),
                              ("categories", "post_categories", "category"),
                              ("collections", "post_collections", "collection")]:
        vals = [r[0] for r in con.execute(
            f"SELECT {col} FROM {table} WHERE file=? ORDER BY {col}",
            (p["file"],))]
        print(f"  {label}: {vals}")


def cmd_fields():
    con = connect()
    n = con.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    print(f"=== frontmatter 字段使用率（/ {n} 篇）===")
    counters = {}
    for (js,) in con.execute("SELECT fm_json FROM posts"):
        for k in json.loads(js):
            counters[k] = counters.get(k, 0) + 1
    for k, v in sorted(counters.items(), key=lambda x: -x[1]):
        print(f"  {v:>2}/{n}  {k}")


def cmd_export_taxonomy(out):
    con = connect()
    ensure_schema(con)
    lines = [
        "# 词注册表快照", "",
        f"> 真源：article-register/articles.db 的 registry 表（{now()} 导出）。"
        "本文件由 export-taxonomy 生成，勿手改；改词用 `regctl.py word`。", ""]
    for dim in ("tags", "categories", "collections"):
        rows = con.execute(
            "SELECT word,status,merged_into,purpose,aliases FROM registry "
            "WHERE dim=? ORDER BY status, word", (dim,)).fetchall()
        lines.append(f"## {dim}（{len(rows)} 词）")
        lines.append("")
        lines.append("| 词 | 状态 | 并入 | 用途 | 别名 |")
        lines.append("|---|---|---|---|---|")
        for r in rows:
            lines.append(f"| {r['word']} | {r['status']} | "
                         f"{r['merged_into']} | {r['purpose']} | {r['aliases']} |")
        lines.append("")
    text = "\n".join(lines)
    if out:
        p = Path(out)
        if not p.is_absolute():
            p = REGDIR / p
        p.write_text(text, encoding="utf-8")
        print(f"已写出 {p}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="文章册：文章登记库")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("update")
    sub.add_parser("verify")
    p = sub.add_parser("word")
    p.add_argument("--dim", required=True,
                   choices=["tags", "categories", "collections"])
    p.add_argument("--name", required=True)
    p.add_argument("--status", choices=list(STATUSES))
    p.add_argument("--merged-into", dest="merged_into")
    p.add_argument("--purpose")
    p.add_argument("--aliases")
    p = sub.add_parser("words")
    p.add_argument("--dim", choices=["tags", "categories", "collections"])
    p.add_argument("--status", choices=list(STATUSES))
    p = sub.add_parser("tags"); p.add_argument("--min", type=int, default=1)
    sub.add_parser("cats")
    sub.add_parser("colls")
    p = sub.add_parser("show")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--tag"); g.add_argument("--cat"); g.add_argument("--coll")
    p = sub.add_parser("article"); p.add_argument("keyword")
    sub.add_parser("fields")
    p = sub.add_parser("export-taxonomy"); p.add_argument("--out")

    args = ap.parse_args()
    if args.cmd == "update":
        cmd_update()
    elif args.cmd == "verify":
        cmd_verify()
    elif args.cmd == "word":
        cmd_word(args)
    elif args.cmd == "words":
        cmd_words(args)
    elif args.cmd == "tags":
        cmd_tags(args.min)
    elif args.cmd == "cats":
        cmd_cats()
    elif args.cmd == "colls":
        cmd_colls()
    elif args.cmd == "show":
        field, value = next((f, v) for f in ("tag", "cat", "coll")
                            for v in [getattr(args, f)] if v)
        cmd_show(field, value)
    elif args.cmd == "article":
        cmd_article(args.keyword)
    elif args.cmd == "fields":
        cmd_fields()
    elif args.cmd == "export-taxonomy":
        cmd_export_taxonomy(args.out)


if __name__ == "__main__":
    main()
