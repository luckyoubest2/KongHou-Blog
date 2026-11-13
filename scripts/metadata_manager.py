#!/usr/bin/env python3
import os
import yaml
import json
import re
from pathlib import Path

# 配置信息
CONTENT_DIR = Path("../content")
DATA_DIR = Path("./data")
TAGS_DB = DATA_DIR / "tags.json"
CATEGORIES_DB = DATA_DIR / "categories.json"
COLLECTIONS_DB = DATA_DIR / "collections.json"

# 确保数据目录存在
DATA_DIR.mkdir(exist_ok=True)

class MetadataManager:
    def __init__(self):
        # 初始化数据库
        self.tags = self._load_db(TAGS_DB)
        self.categories = self._load_db(CATEGORIES_DB)
        self.collections = self._load_db(COLLECTIONS_DB)
    
    def _load_db(self, db_path):
        """加载数据库文件"""
        if db_path.exists():
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_db(self, data, db_path):
        """保存数据库文件"""
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _extract_yaml(self, file_path):
        """从文件中提取YAML元数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配YAML头
        yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            try:
                return yaml.safe_load(yaml_content)
            except:
                return {}
        return {}
    
    def scan_all_posts(self):
        """扫描所有文章并提取元数据"""
        for root, dirs, files in os.walk(CONTENT_DIR):
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    metadata = self._extract_yaml(file_path)
                    self._process_metadata(metadata)
        
        # 保存更新后的数据库
        self._save_db(self.tags, TAGS_DB)
        self._save_db(self.categories, CATEGORIES_DB)
        self._save_db(self.collections, COLLECTIONS_DB)
    
    def _process_metadata(self, metadata):
        """处理提取的元数据"""
        # 处理tags
        if 'tags' in metadata:
            tags = metadata['tags']
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                if tag not in self.tags:
                    self.tags.append(tag)
        
        # 处理categories
        if 'categories' in metadata:
            categories = metadata['categories']
            if isinstance(categories, str):
                categories = [categories]
            for category in categories:
                if category not in self.categories:
                    self.categories.append(category)
        
        # 处理collections
        if 'collections' in metadata:
            collections = metadata['collections']
            if isinstance(collections, str):
                collections = [collections]
            for collection in collections:
                if collection not in self.collections:
                    self.collections.append(collection)
    
    def get_existing_tags(self):
        """获取所有已存在的标签"""
        return self.tags
    
    def get_existing_categories(self):
        """获取所有已存在的分类"""
        return self.categories
    
    def get_existing_collections(self):
        """获取所有已存在的集合"""
        return self.collections
    
    def validate_metadata(self, metadata):
        """验证元数据格式"""
        errors = []
        
        # 验证tags
        if 'tags' in metadata:
            tags = metadata['tags']
            if not isinstance(tags, (list, str)):
                errors.append("tags must be a list or string")
        
        # 验证categories
        if 'categories' in metadata:
            categories = metadata['categories']
            if not isinstance(categories, (list, str)):
                errors.append("categories must be a list or string")
        
        # 验证collections
        if 'collections' in metadata:
            collections = metadata['collections']
            if not isinstance(collections, (list, str)):
                errors.append("collections must be a list or string")
        
        return errors
    
    def update_with_new_post(self, metadata):
        """使用新文章的元数据更新数据库"""
        # 验证元数据
        errors = self.validate_metadata(metadata)
        if errors:
            return errors
        
        # 处理元数据
        self._process_metadata(metadata)
        
        # 保存更新后的数据库
        self._save_db(self.tags, TAGS_DB)
        self._save_db(self.categories, CATEGORIES_DB)
        self._save_db(self.collections, COLLECTIONS_DB)
        
        return []

if __name__ == "__main__":
    manager = MetadataManager()
    print("Scanning all posts...")
    manager.scan_all_posts()
    print(f"Tags: {manager.get_existing_tags()}")
    print(f"Categories: {manager.get_existing_categories()}")
    print(f"Collections: {manager.get_existing_collections()}")
    print("Metadata processing completed!")
