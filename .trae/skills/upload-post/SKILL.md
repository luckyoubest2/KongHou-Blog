---
name: "upload-post"
description: "Executes the KongHou-Blog article upload workflow end-to-end. Use when the user says '上传文章' / 'publish post' / '发布文章' or hands over a draft .md to add to the Hugo blog. Adds YAML frontmatter, places the file under content/posts/ with the YYYYMMDD_title-blog.md naming, syncs metadata, and (if asked) commits to git."
---

# 上传文章到 KongHou-Blog

将一篇 Markdown 文章发布到本仓库的 Hugo 站点，遵循仓库既定的命名、元数据与元数据同步流程。

## 适用场景

- 用户说"上传文章"、"publish post"、"发布文章"、"新增到博客"
- 用户提供一份草稿 .md（可能位于仓库根目录或任意位置），希望入库到 `content/posts/`
- 用户说"为上传文章创建 skill"（即当前 skill 本身）

## 仓库前置结构（必须遵守）

- 文章一律放到 [content/posts/](file:///Users/luckyoubest/GitHub/KongHou-Blog/content/posts/) 下
- 文件命名：**`YYYYMMDD_标题-blog.md`**，日期采用发布日期（同 YAML `date` 字段）
- 标题中允许中文，禁止空格，使用下划线分隔词
- 不再保留仓库根目录的同名 .md 草稿（上传前先删除根目录原文件，避免重复）

## YAML 头规范

每篇文章必须以如下 YAML 开头（紧接 `---\n` 之后）：

```yaml
---
title: 文章标题
date: YYYY-MM-DDT00:00:00+08:00
draft: false
tags:
  - 标签1
  - 标签2
categories:
  - 分类
collections:
  - 集合
---
```

字段含义：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `title` | string | 文章标题，纯文本 |
| `date` | ISO8601 | 发布日期，时间固定 `T00:00:00+08:00`（北京时间） |
| `draft` | bool | 上线版本统一填 `false` |
| `tags` | list | 至少 1 个；优先复用 `scripts/data/tags.json` 已存在标签；新词条需追加 |
| `categories` | list | 至少 1 个；优先复用 `scripts/data/categories.json` 已存在分类 |
| `collections` | list | 至少 1 个；优先复用 `scripts/data/collections.json` 已存在集合 |

**YAML 之后的正文直接来自用户提供的内容**，如原文件里包含旧标题/前言可直接整段保留，无需重写。

## 元数据同步流程

1. 写入新文章到 `content/posts/YYYYMMDD_标题-blog.md`
2. 进入 `scripts/` 目录执行：

```bash
cd scripts
python3 validate_and_update.py
```

脚本会扫描所有文章、合并标签/分类/集合，并写回 `scripts/data/{tags,categories,collections}.json`。

> ⚠️ 若本机 `python3` 缺 `yaml` 模块，先 `python3 -m pip install pyyaml --user`，再执行上述脚本。

3. 三个 JSON 文件如有变更，一并 `git add` 进同一次提交。

## Git 提交规范

根据用户项目规则：

- 提交信息前缀使用 `user:`（用户手动请求的提交）或 `auto:`（系统自动触发的提交）。
- 标题首行建议格式：`user: 新增文章《标题》` / `auto: 新增文章《标题》`
- 正文可加 `- 新增 content/posts/...md\n- 同步更新 scripts/data/*.json`
- 命令使用 HEREDOC 传参，避免中文编码问题。
- 仅 `git add` 对应文件，不要 `git add -A`，避免误带敏感/二进制文件。
- **绝不主动 push**，除非用户明确说"推送"/"push"。

## 完整工作流（端到端）

当用户说"上传这篇文章"并提供路径时，依次执行：

1. **读取原文**：用 `Read` 工具读取用户给出的 `.md` 路径。
2. **确定日期**：以原文里声明的"决策日期 / 发布日期"为准；若未声明，使用系统当天 `YYYY-MM-DD`。
3. **确定文件名**：`YYYYMMDD_<标题>-blog.md`，标题去除特殊符号、保留中文。
4. **确定元数据**：
   - `tags`：先查 `scripts/data/tags.json` 已存在的相关词；不足则按文章主题补充新词。
   - `categories`：在 `生活指南 / 测评 / 方法论 / 思考 / 游记 / 影评 / 书评 / 解决方案 / 旅行` 中择最贴近。
   - `collections`：在 `实用指南 / 笔记软件相关 / 选品记录 / 个人文章 / 游记 / 评论文章 / 建站笔记` 中择最贴近。
5. **写入新文件**：用 `Write` 落到 `content/posts/YYYYMMDD_<标题>-blog.md`，YAML + 原文正文。
6. **删除根目录原文件**：`rm` 用户提供的原始路径（如果仍在仓库根），避免重复。
7. **同步元数据**：进入 `scripts/` 跑 `python3 validate_and_update.py`。
8. **询问是否提交**：默认不要直接 commit，除非用户说"提交 git"或类似指令。用户同意后：
   - `git add content/posts/...md scripts/data/{tags,categories,collections}.json`
   - `git commit -m "$(cat <<'EOF'\nuser: 新增文章《标题》\n\n- 新增 content/posts/...md\n- 同步更新 scripts/data/*.json\nEOF\n)"`
9. **回复用户**：报告写入路径、文件名、元数据、commit hash。

## 反例（不要做的事）

- 不要在 `content/posts/` 之外新建文章文件。
- 不要用破折号、空格或英文混杂的中文文件名。
- 不要让 YAML 中的 `tags/categories/collections` 引用 `*` 或 `[]` 之类的占位符；必须填实际值。
- 不要忘记运行 `validate_and_update.py`，否则新标签不会被索引。
- 不要把 `validate_and_update.py` 之外的脏文件一起 `git add`。
- 不要在 commit 信息里用英文（用户明确要求中文提交信息）。

## 快速自检清单

提交前自查：

- [ ] 文件位于 `content/posts/YYYYMMDD_标题-blog.md`
- [ ] YAML 头存在且含 title/date/draft/tags/categories/collections 六个字段
- [ ] date 形如 `2026-07-28T00:00:00+08:00`
- [ ] tags/categories/collections 至少各 1 项
- [ ] 仓库根目录无残留原文件
- [ ] 已运行 `python3 validate_and_update.py`
- [ ] `scripts/data/*.json` 的更改（如有）已暂存
- [ ] commit message 前缀为 `user:` 或 `auto:`
