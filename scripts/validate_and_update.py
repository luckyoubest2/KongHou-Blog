#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 添加脚本目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metadata_manager import MetadataManager

def validate_and_update():
    """验证所有文章的元数据并更新数据库"""
    manager = MetadataManager()
    
    print("=== 验证和更新元数据 ===")
    print()
    
    # 扫描所有文章
    print("扫描所有文章...")
    manager.scan_all_posts()
    
    # 显示结果
    print()
    print("=== 数据库状态 ===")
    print(f"标签数量: {len(manager.get_existing_tags())}")
    print(f"分类数量: {len(manager.get_existing_categories())}")
    print(f"集合数量: {len(manager.get_existing_collections())}")
    print()
    
    print("标签列表:")
    for tag in manager.get_existing_tags():
        print(f"- {tag}")
    print()
    
    print("分类列表:")
    for category in manager.get_existing_categories():
        print(f"- {category}")
    print()
    
    print("集合列表:")
    for collection in manager.get_existing_collections():
        print(f"- {collection}")
    print()
    
    print("=== 验证完成 ===")
    print("数据库已更新，所有文章的元数据已验证")

if __name__ == "__main__":
    validate_and_update()
