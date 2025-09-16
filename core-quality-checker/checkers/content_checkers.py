#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容检测器模块

包含内容质量相关的检测器，从原始quality_check.py重构而来。
"""

import re
from typing import Dict, Any
from ..utils.base_checker import ContentChecker
from ..utils.validation_result import ValidationResult, CheckStatus
from ..utils.content_parser import ContentParser


class WordCountChecker(ContentChecker):
    """字数统计检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查文章字数是否符合要求

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Word count check disabled")

        # 使用内容解析器统计字数（支持中英文混合）
        word_count = ContentParser.count_words(content)

        # 获取配置
        quality_rules = self.config.get('quality_rules', {})
        min_words = quality_rules.get('min_word_count', 1500)
        max_words = quality_rules.get('max_word_count', 4000)

        # 创建结果对象
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('word_count', word_count)

        # 检查字数范围
        if word_count < min_words:
            result.status = CheckStatus.ERROR
            result.score = max(0, (word_count / min_words) * 100)
            result.add_issue(f"Article too short: {word_count} words (minimum: {min_words})", "error")
            result.add_suggestion(f"Add approximately {min_words - word_count} more words")

        elif word_count > max_words:
            result.status = CheckStatus.WARNING
            result.score = max(60, 100 - ((word_count - max_words) / max_words * 40))
            result.add_issue(f"Article too long: {word_count} words (maximum: {max_words})", "warning")
            result.add_suggestion(f"Consider reducing content by {word_count - max_words} words")

        else:
            # 在合理范围内，给出评分
            optimal_range = (min_words + max_words) / 2
            distance_from_optimal = abs(word_count - optimal_range)
            max_distance = (max_words - min_words) / 2
            result.score = max(85, 100 - (distance_from_optimal / max_distance * 15))

        return result


class DuplicateContentChecker(ContentChecker):
    """重复内容检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查文章中的重复内容

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Duplicate content check disabled")

        quality_rules = self.config.get('quality_rules', {})
        max_duplicate_usage = quality_rules.get('max_duplicate_usage', 3)

        # 提取段落
        paragraphs = ContentParser.extract_paragraphs(content)

        # 检测重复段落
        duplicate_count = 0
        duplicate_pairs = []

        for i, para1 in enumerate(paragraphs):
            for j, para2 in enumerate(paragraphs[i+1:], i+1):
                # 简单相似度检测（基于单词交集）
                words1 = set(para1.lower().split())
                words2 = set(para2.lower().split())

                if len(words1) > 10 and len(words2) > 10:  # 只检测较长的段落
                    similarity = len(words1 & words2) / len(words1 | words2)
                    if similarity > 0.7:  # 70%相似度视为重复
                        duplicate_count += 1
                        duplicate_pairs.append((i, j, similarity))

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('duplicate_content_score', duplicate_count)
        result.set_metadata('total_paragraphs', len(paragraphs))

        if duplicate_count > max_duplicate_usage:
            result.status = CheckStatus.WARNING
            result.score = max(60, 100 - (duplicate_count - max_duplicate_usage) * 10)
            result.add_issue(f"Excessive duplicate content detected: {duplicate_count} instances", "warning")
            result.add_suggestion("Review and rewrite similar paragraphs to improve uniqueness")

            # 添加具体的重复段落信息
            for i, (para1_idx, para2_idx, similarity) in enumerate(duplicate_pairs[:3]):  # 只显示前3个
                result.set_metadata(f'duplicate_pair_{i}', {
                    'paragraph_1': para1_idx,
                    'paragraph_2': para2_idx,
                    'similarity': similarity
                })

        elif duplicate_count > 0:
            result.score = max(80, 100 - duplicate_count * 5)
            result.add_issue(f"Minor duplicate content detected: {duplicate_count} instances", "warning")

        return result


class ImageRelevanceChecker(ContentChecker):
    """图片相关性检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查图片与内容的相关性

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Image relevance check disabled")

        quality_rules = self.config.get('quality_rules', {})
        min_relevance = quality_rules.get('min_image_relevance_score', 0.6)

        # 解析Front Matter获取关键词
        try:
            from ..utils.content_parser import ContentParser
            fm_text, _, _ = ContentParser.extract_front_matter(f"---\n{front_matter}\n---\n{content}")
            fm_data = ContentParser.parse_front_matter_data(fm_text)
        except:
            fm_data = {}

        # 提取关键词
        keywords = []
        if 'keywords' in fm_data:
            if isinstance(fm_data['keywords'], list):
                keywords = fm_data['keywords']
            elif isinstance(fm_data['keywords'], str):
                keywords = [kw.strip() for kw in fm_data['keywords'].split(',')]

        # 如果没有关键词，尝试从标题提取
        if not keywords and 'title' in fm_data:
            title_words = fm_data['title'].split()
            keywords = [word.lower() for word in title_words if len(word) > 3]

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)

        if not keywords:
            result.status = CheckStatus.WARNING
            result.score = 70.0
            result.add_issue("Cannot assess image relevance - no keywords found", "warning")
            result.add_suggestion("Add keywords to front matter for better image relevance analysis")
            result.set_metadata('image_relevance_score', 0.0)
            return result

        # 提取图片和Alt文本
        images = ContentParser.extract_images(content)

        if not images:
            result.score = 85.0
            result.set_metadata('image_relevance_score', 0.0)
            result.set_metadata('total_images', 0)
            return result

        # 计算相关性
        relevant_images = 0
        relevance_scores = []

        for alt_text, image_url in images:
            if not alt_text:
                continue

            alt_words = set(alt_text.lower().split())
            keyword_matches = sum(1 for keyword in keywords if keyword.lower() in alt_words)
            relevance_score = keyword_matches / len(keywords) if keywords else 0.0
            relevance_scores.append(relevance_score)

            if relevance_score >= 0.3:  # 至少包含30%的关键词
                relevant_images += 1

        # 计算总体相关性
        if relevance_scores:
            avg_relevance = sum(relevance_scores) / len(relevance_scores)
            overall_relevance = relevant_images / len(images)
        else:
            avg_relevance = 0.0
            overall_relevance = 0.0

        # 设置元数据
        result.set_metadata('image_relevance_score', overall_relevance)
        result.set_metadata('average_relevance', avg_relevance)
        result.set_metadata('relevant_images', relevant_images)
        result.set_metadata('total_images', len(images))

        # 评分和状态
        if overall_relevance < min_relevance:
            result.status = CheckStatus.WARNING
            result.score = max(60, overall_relevance * 100)
            result.add_issue(f"Low image relevance: {overall_relevance:.2f} (minimum: {min_relevance})", "warning")
            result.add_suggestion("Improve alt text to include more relevant keywords")
        else:
            result.score = min(100, 70 + overall_relevance * 30)

        return result


class ForbiddenPhrasesChecker(ContentChecker):
    """增强型禁词检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查文章中的禁用短语

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Forbidden phrases check disabled")

        # 获取禁词配置
        adsense_config = self.config.get('adsense_compliance', {})
        forbidden_phrases = adsense_config.get('forbidden_phrases', {})

        critical_phrases = forbidden_phrases.get('critical', [])
        warning_phrases = forbidden_phrases.get('warning', [])
        suggestion_phrases = forbidden_phrases.get('suggestion', [])

        # 转换为小写进行匹配
        content_lower = content.lower()

        violations = {
            'critical': [],
            'warning': [],
            'suggestion': []
        }

        # 检查严重违规短语
        for phrase in critical_phrases:
            if phrase.lower() in content_lower:
                violations['critical'].append(phrase)

        # 检查警告短语
        for phrase in warning_phrases:
            if phrase.lower() in content_lower:
                violations['warning'].append(phrase)

        # 检查建议避免的短语
        for phrase in suggestion_phrases:
            if phrase.lower() in content_lower:
                violations['suggestion'].append(phrase)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)

        # 设置元数据
        result.set_metadata('critical_violations', len(violations['critical']))
        result.set_metadata('warning_violations', len(violations['warning']))
        result.set_metadata('suggestion_violations', len(violations['suggestion']))
        result.set_metadata('total_violations', sum(len(v) for v in violations.values()))

        # 根据违规情况设置状态和评分
        if violations['critical']:
            result.status = CheckStatus.CRITICAL
            result.score = max(0, 50 - len(violations['critical']) * 10)
            for phrase in violations['critical']:
                result.add_issue(f"Critical forbidden phrase: '{phrase}'", "critical")
            result.add_suggestion("Remove all critical forbidden phrases to ensure AdSense compliance")

        elif violations['warning']:
            result.status = CheckStatus.WARNING
            result.score = max(60, 90 - len(violations['warning']) * 5)
            for phrase in violations['warning'][:3]:  # 只显示前3个
                result.add_issue(f"Warning phrase detected: '{phrase}'", "warning")
            if len(violations['warning']) > 3:
                result.add_issue(f"... and {len(violations['warning']) - 3} more warning phrases", "warning")
            result.add_suggestion("Consider replacing warning phrases with more neutral language")

        elif violations['suggestion']:
            result.score = max(80, 95 - len(violations['suggestion']) * 2)
            for phrase in violations['suggestion'][:3]:  # 只显示前3个
                result.add_issue(f"Suggested to avoid: '{phrase}'", "warning")
            if len(violations['suggestion']) > 3:
                result.add_issue(f"... and {len(violations['suggestion']) - 3} more suggestion phrases", "warning")
            result.add_suggestion("Consider using less promotional language for better user experience")

        return result