#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Article Analyzer - Handles article scanning, parsing and information extraction.

This module provides functionality to scan directories, extract article information,
and prepare data for similarity analysis.
"""

import os
import sys
import re
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ArticleAnalyzer:
    """
    Analyzes articles and extracts metadata for similarity detection.
    """

    def __init__(self, config: Dict):
        """
        Initialize article analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.debug_mode = False
        self.min_content_length = config.get('min_content_length', 1000)

    def scan_directory(self, directory: str) -> List[Dict]:
        """
        Scan directory for articles and extract information.

        Args:
            directory: Directory path to scan

        Returns:
            List of article information dictionaries
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            print(f"❌ 目录不存在: {directory}")
            return []

        # Find all Markdown files
        md_files = list(directory_path.glob("*.md"))
        if not md_files:
            print(f"❌ 目录中没有找到Markdown文件: {directory}")
            return []

        print(f"📁 找到 {len(md_files)} 个文章文件")

        articles = []
        for i, file_path in enumerate(md_files, 1):
            print(f"  [{i}/{len(md_files)}] 正在分析: {file_path.name}")

            try:
                article_info = self.extract_article_info(file_path)
                if article_info:
                    articles.append(article_info)
            except Exception as e:
                print(f"    ⚠️ 文件处理失败: {e}")

        print(f"✅ 成功分析 {len(articles)} 篇文章")
        return articles

    def extract_article_info(self, file_path: Path) -> Optional[Dict]:
        """
        Extract comprehensive information from an article file.

        Args:
            file_path: Path to the article file

        Returns:
            Article information dictionary or None if extraction fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract Front Matter and main content
            front_matter, article_content = self._extract_front_matter(content)

            # Get file statistics
            file_stat = file_path.stat()

            # Extract title
            title = self._extract_title(front_matter, article_content, file_path.stem)

            article_info = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_stem': file_path.stem,
                'title': title,
                'content': article_content,
                'full_content': content,
                'word_count': len(article_content.split()),
                'char_count': len(article_content),
                'created_time': datetime.fromtimestamp(file_stat.st_ctime),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
                'file_size': file_stat.st_size,
                'content_hash': hashlib.md5(article_content.encode('utf-8')).hexdigest(),
                'title_hash': hashlib.md5(title.encode('utf-8')).hexdigest() if title else "",
                'front_matter': front_matter
            }

            return article_info

        except Exception as e:
            print(f"    ❌ 无法读取文件 {file_path}: {e}")
            return None

    def _extract_front_matter(self, content: str) -> Tuple[str, str]:
        """
        Extract Front Matter and main content from article.

        Args:
            content: Full article content

        Returns:
            Tuple of (front_matter, article_content)
        """
        if not content.strip().startswith('---'):
            return "", content

        lines = content.split('\n')
        end_index = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_index = i
                break

        if end_index == -1:
            return "", content

        front_matter_text = '\n'.join(lines[1:end_index])
        article_body = '\n'.join(lines[end_index + 1:])

        return front_matter_text, article_body

    def _extract_title(self, front_matter: str, content: str, fallback: str) -> str:
        """
        Extract article title from various sources.

        Args:
            front_matter: YAML front matter content
            content: Article main content
            fallback: Fallback title (usually filename)

        Returns:
            Extracted title
        """
        # Try to extract from Front Matter
        try:
            fm_data = yaml.safe_load(front_matter) or {}
            if 'title' in fm_data and fm_data['title']:
                return str(fm_data['title']).strip()
        except:
            pass

        # Try to extract H1 title from content
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Use filename as fallback
        return fallback.replace('-', ' ').replace('_', ' ').title()

    def get_effective_date(self, article: Dict) -> datetime:
        """
        Get the effective date for an article (used for sorting).

        Priority: filename date > created_time > modified_time

        Args:
            article: Article information dictionary

        Returns:
            Effective date
        """
        # Try to extract date from filename
        filename_date = self._extract_date_from_filename(article['file_name'])
        if filename_date:
            return filename_date

        # Use created time
        if 'created_time' in article:
            return article['created_time']

        # Use modified time as fallback
        return article['modified_time']

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract date from filename.

        Supports formats: xxx-20250914.md, xxx-2025-09-14.md etc.

        Args:
            filename: Filename to parse

        Returns:
            Extracted datetime or None
        """
        # Match YYYYMMDD format
        date_pattern1 = re.search(r'(\d{8})', filename)
        if date_pattern1:
            try:
                date_str = date_pattern1.group(1)
                return datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass

        # Match YYYY-MM-DD format
        date_pattern2 = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_pattern2:
            try:
                date_str = date_pattern2.group(1)
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass

        return None

    def classify_article_topic(self, article: Dict) -> Optional[str]:
        """
        Classify article topic based on content.

        Args:
            article: Article information

        Returns:
            Topic category name or None if cannot classify
        """
        topic_config = self.config.get('topic_classification', {})
        if not topic_config.get('enabled', False):
            return None

        topics = topic_config.get('topics', {})
        if not topics:
            return None

        # Combine title and content for classification
        text_to_classify = (article['title'] + ' ' + article['content']).lower()

        # Calculate scores for each topic
        topic_scores = {}
        for topic_name, topic_config in topics.items():
            keywords = topic_config.get('keywords', [])
            if not keywords:
                continue

            score = 0
            for keyword in keywords:
                if keyword.lower() in text_to_classify:
                    score += 1

            if score > 0:
                # Normalize score (matched keywords / total keywords)
                topic_scores[topic_name] = score / len(keywords)

        if not topic_scores:
            return None

        # Return topic with highest score
        best_topic = max(topic_scores.items(), key=lambda x: x[1])
        return best_topic[0] if best_topic[1] > 0.1 else None  # At least 10% keyword match

    def are_cross_topic_articles(self, article1: Dict, article2: Dict) -> bool:
        """
        Check if two articles belong to different topics.

        Args:
            article1, article2: Article information dictionaries

        Returns:
            True if articles belong to different topics
        """
        topic_config = self.config.get('topic_classification', {})
        if not topic_config.get('enabled', False):
            return False

        topic1 = self.classify_article_topic(article1)
        topic2 = self.classify_article_topic(article2)

        # If either article cannot be classified, not considered cross-topic
        if topic1 is None or topic2 is None:
            return False

        return topic1 != topic2