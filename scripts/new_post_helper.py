#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 添加脚本目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metadata_manager import MetadataManager

def create_new_post():
    """创建新文章并帮助用户选择元数据"""
    manager = MetadataManager()
    
    print("=== 新文章创建助手 ===")
    print()
    
    # 获取用户输入
    title = input("请输入文章标题: ")
    date = input("请输入发布日期 (格式: YYYY-MM-DD): ")
    draft = input("是否为草稿? (y/n): ").lower() == 'y'
    
    print()
    print("=== 选择标签 ===")
    print("现有标签:")
    existing_tags = manager.get_existing_tags()
    for i, tag in enumerate(existing_tags, 1):
        print(f"{i}. {tag}")
    print("0. 手动输入新标签")
    
    tags = []
    while True:
        choice = input("请选择标签 (输入编号，0结束): ")
        if choice == '0':
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(existing_tags):
                tag = existing_tags[index]
                if tag not in tags:
                    tags.append(tag)
                    print(f"已添加标签: {tag}")
                else:
                    print("该标签已添加")
            else:
                print("无效的选择")
        except:
            print("请输入有效的数字")
    
    # 手动输入新标签
    while True:
        new_tag = input("请输入新标签 (留空结束): ").strip()
        if not new_tag:
            break
        if new_tag not in tags:
            tags.append(new_tag)
            print(f"已添加新标签: {new_tag}")
        else:
            print("该标签已添加")
    
    print()
    print("=== 选择分类 ===")
    print("现有分类:")
    existing_categories = manager.get_existing_categories()
    for i, category in enumerate(existing_categories, 1):
        print(f"{i}. {category}")
    print("0. 手动输入新分类")
    
    categories = []
    while True:
        choice = input("请选择分类 (输入编号，0结束): ")
        if choice == '0':
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(existing_categories):
                category = existing_categories[index]
                if category not in categories:
                    categories.append(category)
                    print(f"已添加分类: {category}")
                else:
                    print("该分类已添加")
            else:
                print("无效的选择")
        except:
            print("请输入有效的数字")
    
    # 手动输入新分类
    while True:
        new_category = input("请输入新分类 (留空结束): ").strip()
        if not new_category:
            break
        if new_category not in categories:
            categories.append(new_category)
            print(f"已添加新分类: {new_category}")
        else:
            print("该分类已添加")
    
    print()
    print("=== 选择集合 ===")
    print("现有集合:")
    existing_collections = manager.get_existing_collections()
    for i, collection in enumerate(existing_collections, 1):
        print(f"{i}. {collection}")
    print("0. 手动输入新集合")
    
    collections = []
    while True:
        choice = input("请选择集合 (输入编号，0结束): ")
        if choice == '0':
            break
        try:
            index = int(choice) - 1
            if 0 <= index < len(existing_collections):
                collection = existing_collections[index]
                if collection not in collections:
                    collections.append(collection)
                    print(f"已添加集合: {collection}")
                else:
                    print("该集合已添加")
            else:
                print("无效的选择")
        except:
            print("请输入有效的数字")
    
    # 手动输入新集合
    while True:
        new_collection = input("请输入新集合 (留空结束): ").strip()
        if not new_collection:
            break
        if new_collection not in collections:
            collections.append(new_collection)
            print(f"已添加新集合: {new_collection}")
        else:
            print("该集合已添加")
    
    # 生成YAML头
    yaml_header = f"---\ntitle: {title}\ndate: {date}T00:00:00+08:00\ndraft: {draft}\n"
    
    if tags:
        yaml_header += "tags:\n"
        for tag in tags:
            yaml_header += f"  - {tag}\n"
    
    if categories:
        yaml_header += "categories:\n"
        for category in categories:
            yaml_header += f"  - {category}\n"
    
    if collections:
        yaml_header += "collections:\n"
        for collection in collections:
            yaml_header += f"  - {collection}\n"
    
    yaml_header += "---\n\n"
    
    print()
    print("=== 生成的YAML头 ===")
    print(yaml_header)
    
    # 保存到文件
    filename = input("请输入文件名 (例如: 20260330_my-post-blog.md): ")
    if not filename:
        print("操作取消")
        return
    
    file_path = Path("../content") / filename
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(yaml_header)
        print(f"文件已创建: {file_path}")
        
        # 更新数据库
        metadata = {
            'title': title,
            'date': f"{date}T00:00:00+08:00",
            'draft': draft
        }
        if tags:
            metadata['tags'] = tags
        if categories:
            metadata['categories'] = categories
        if collections:
            metadata['collections'] = collections
        
        errors = manager.update_with_new_post(metadata)
        if errors:
            print("更新数据库时出现错误:")
            for error in errors:
                print(f"- {error}")
        else:
            print("数据库已更新")
            
    except Exception as e:
        print(f"创建文件时出现错误: {e}")

if __name__ == "__main__":
    create_new_post()
