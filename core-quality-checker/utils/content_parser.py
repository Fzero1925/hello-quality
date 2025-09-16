#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容解析工具

提供文章内容解析的通用工具函数，供各个检测器使用。
"""

import re
import yaml
from typing import Dict, List, Tuple, Any, Optional


class ContentParser:
    """内容解析器"""

    @staticmethod
    def extract_front_matter(content: str) -> Tuple[str, str, bool]:
        """
        提取Front Matter和正文

        Args:
            content: 完整文章内容

        Returns:
            Tuple[str, str, bool]: (front_matter_text, article_body, has_front_matter)
        """
        if not content.strip().startswith('---'):
            return "", content, False

        lines = content.split('\n')
        end_index = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_index = i
                break

        if end_index == -1:
            return "", content, False

        front_matter_text = '\n'.join(lines[1:end_index])
        article_body = '\n'.join(lines[end_index + 1:])

        return front_matter_text, article_body, True

    @staticmethod
    def parse_front_matter_data(front_matter_text: str) -> Dict[str, Any]:
        """
        解析Front Matter为字典

        Args:
            front_matter_text: Front Matter文本

        Returns:
            Dict[str, Any]: 解析后的数据
        """
        try:
            return yaml.safe_load(front_matter_text) or {}
        except yaml.YAMLError:
            return {}

    @staticmethod
    def count_words(content: str) -> int:
        """
        统计字数（中英文混合）

        Args:
            content: 文章内容

        Returns:
            int: 字数
        """
        # 中文字符数
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])

        # 英文单词数
        english_words = len([w for w in content.split() if any(c.isalpha() for c in w)])

        return chinese_chars + english_words

    @staticmethod
    def extract_images(content: str) -> List[Tuple[str, str]]:
        """
        提取图片信息

        Args:
            content: 文章内容

        Returns:
            List[Tuple[str, str]]: [(alt_text, image_url), ...]
        """
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return re.findall(image_pattern, content)

    @staticmethod
    def extract_links(content: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        提取链接信息

        Args:
            content: 文章内容

        Returns:
            Dict[str, List[Tuple[str, str]]]: {
                'internal': [(text, url), ...],
                'external': [(text, url), ...]
            }
        """
        # 所有链接
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        all_links = re.findall(link_pattern, content)

        internal_links = []
        external_links = []

        for text, url in all_links:
            if url.startswith(('http://', 'https://')):
                external_links.append((text, url))
            elif url.startswith('/') or not url.startswith(('mailto:', 'tel:')):
                internal_links.append((text, url))

        return {
            'internal': internal_links,
            'external': external_links
        }

    @staticmethod
    def extract_headings(content: str) -> Dict[str, List[str]]:
        """
        提取标题信息

        Args:
            content: 文章内容

        Returns:
            Dict[str, List[str]]: {
                'h1': [title1, title2, ...],
                'h2': [title1, title2, ...],
                ...
            }
        """
        headings = {
            'h1': re.findall(r'^#\s+(.+)$', content, re.MULTILINE),
            'h2': re.findall(r'^##\s+(.+)$', content, re.MULTILINE),
            'h3': re.findall(r'^###\s+(.+)$', content, re.MULTILINE),
            'h4': re.findall(r'^####\s+(.+)$', content, re.MULTILINE),
            'h5': re.findall(r'^#####\s+(.+)$', content, re.MULTILINE),
            'h6': re.findall(r'^######\s+(.+)$', content, re.MULTILINE)
        }
        return headings

    @staticmethod
    def extract_paragraphs(content: str) -> List[str]:
        """
        提取段落

        Args:
            content: 文章内容

        Returns:
            List[str]: 段落列表
        """
        # 按双换行分割段落，过滤空段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # 过滤掉标题、图片、链接等，只保留纯文本段落
        text_paragraphs = []
        for para in paragraphs:
            # 跳过标题
            if para.startswith('#'):
                continue
            # 跳过单独的图片或链接行
            if re.match(r'^\s*!\[.*\]\(.*\)\s*$', para) or re.match(r'^\s*\[.*\]\(.*\)\s*$', para):
                continue
            # 跳过表格
            if '|' in para and para.count('|') >= 2:
                continue

            text_paragraphs.append(para)

        return text_paragraphs

    @staticmethod
    def check_section_exists(content: str, section_patterns: List[str]) -> bool:
        """
        检查是否包含特定章节

        Args:
            content: 文章内容
            section_patterns: 章节模式列表

        Returns:
            bool: 是否存在
        """
        for pattern in section_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def find_keyword_density(content: str, keyword: str) -> float:
        """
        计算关键词密度

        Args:
            content: 文章内容
            keyword: 关键词

        Returns:
            float: 密度 (0-1)
        """
        if not keyword:
            return 0.0

        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        keyword_count = len(re.findall(re.escape(keyword.lower()), content.lower()))
        return keyword_count / total_words

    @staticmethod
    def extract_sentences(content: str) -> List[str]:
        """
        提取句子

        Args:
            content: 文章内容

        Returns:
            List[str]: 句子列表
        """
        # 使用多种句子结束符分割
        sentences = re.split(r'[.!?。！？]+', content)

        # 清理和过滤
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # 过滤太短的句子
                clean_sentences.append(sentence)

        return clean_sentences

    @staticmethod
    def check_table_exists(content: str) -> bool:
        """
        检查是否包含表格

        Args:
            content: 文章内容

        Returns:
            bool: 是否包含表格
        """
        # 检查Markdown表格格式
        table_rows = [line.strip() for line in content.split('\n') if line.strip().startswith('|')]
        return len(table_rows) >= 3  # 至少需要头部、分隔符、数据行

    @staticmethod
    def extract_list_items(content: str) -> Dict[str, List[str]]:
        """
        提取列表项

        Args:
            content: 文章内容

        Returns:
            Dict[str, List[str]]: {
                'ordered': [item1, item2, ...],
                'unordered': [item1, item2, ...]
            }
        """
        # 有序列表
        ordered_items = re.findall(r'^\d+\.\s+(.+)$', content, re.MULTILINE)

        # 无序列表
        unordered_items = re.findall(r'^[-*+]\s+(.+)$', content, re.MULTILINE)

        return {
            'ordered': ordered_items,
            'unordered': unordered_items
        }

    @staticmethod
    def calculate_readability_metrics(content: str) -> Dict[str, float]:
        """
        计算可读性指标

        Args:
            content: 文章内容

        Returns:
            Dict[str, float]: 可读性指标
        """
        sentences = ContentParser.extract_sentences(content)
        paragraphs = ContentParser.extract_paragraphs(content)
        words = content.split()

        if not sentences or not words:
            return {
                'avg_sentence_length': 0.0,
                'avg_paragraph_length': 0.0,
                'sentence_count': 0,
                'paragraph_count': 0
            }

        # 平均句子长度（单词数）
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # 平均段落长度（句子数）
        avg_paragraph_length = len(sentences) / len(paragraphs) if paragraphs else 0

        return {
            'avg_sentence_length': avg_sentence_length,
            'avg_paragraph_length': avg_paragraph_length,
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs)
        }