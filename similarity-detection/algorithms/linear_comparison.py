#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linear Comparison Algorithm

Implements linear similarity detection algorithm that compares articles
sequentially in chronological order for efficient duplicate detection.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class LinearComparison:
    """
    Linear comparison algorithm for similarity detection.

    Uses chronological ordering and sequential comparison to efficiently
    detect and organize similar articles.
    """

    def __init__(self, config: Dict):
        """
        Initialize linear comparison algorithm.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.comparison_window_days = config.get('comparison_window_days', 90)
        self.min_content_length = config.get('min_content_length', 1000)
        self.debug_mode = False

        # Import TF-IDF algorithm for similarity calculation
        try:
            from .tfidf_similarity import TFIDFSimilarity
        except ImportError:
            from tfidf_similarity import TFIDFSimilarity
        self.tfidf_calculator = TFIDFSimilarity(config)

    def detect_similarities(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        Perform linear similarity detection.

        Logic: Sort articles by time, earliest article vs others comparison.
        Similar articles are moved to old-articles, unique ones are kept.

        Args:
            articles: List of articles to analyze

        Returns:
            Detection results dictionary
        """
        if len(articles) < 2:
            print("📊 文章数量不足，无法进行相似度比较")
            return {
                'kept_articles': articles,
                'moved_articles': [],
                'total_comparisons': 0
            }

        print(f"🔍 开始线性相似度检测 {len(articles)} 篇文章...")

        # Sort articles by effective date (earliest to newest)
        articles_sorted = sorted(articles, key=lambda x: self._get_article_effective_date(x))

        # Add effective date to articles
        for article in articles_sorted:
            article['effective_date'] = self._get_article_effective_date(article)

        print(f"📅 文章按日期排序完成，时间范围: "
              f"{articles_sorted[0]['effective_date'].strftime('%Y-%m-%d')} 到 "
              f"{articles_sorted[-1]['effective_date'].strftime('%Y-%m-%d')}")

        # Perform linear comparison
        kept_articles = []
        moved_articles = []
        total_comparisons = 0
        processing_date = datetime.now().strftime('%Y-%m-%d')

        remaining_articles = articles_sorted[:]  # Create copy

        while remaining_articles:
            # Take earliest article as base
            base_article = remaining_articles.pop(0)
            kept_articles.append(base_article)

            print(f"\n📝 处理基准文章: {base_article['file_name']} "
                  f"(日期: {base_article['effective_date'].strftime('%Y-%m-%d')})")

            # Compare with remaining articles
            to_remove = []
            for i, other_article in enumerate(remaining_articles):
                # Check time window
                time_diff = abs((base_article['effective_date'] -
                               other_article['effective_date']).days)
                if time_diff > self.comparison_window_days:
                    if self.debug_mode:
                        print(f"    🕐 跳过 {other_article['file_name']} - "
                              f"时间差 {time_diff} 天 > {self.comparison_window_days} 天窗口")
                    continue

                # Skip articles with insufficient content
                if (base_article['word_count'] < self.min_content_length or
                    other_article['word_count'] < self.min_content_length):
                    if self.debug_mode:
                        print(f"    📝 跳过 {other_article['file_name']} - 字数不足 "
                              f"(base: {base_article['word_count']}, "
                              f"other: {other_article['word_count']})")
                    continue

                total_comparisons += 1

                # Calculate similarity
                similarity_result = self.tfidf_calculator.calculate_similarity(
                    base_article, other_article)
                similarity_score = similarity_result['overall_similarity']

                # Check if cross-topic comparison (if enabled)
                is_cross_topic = self._are_cross_topic_articles(base_article, other_article)
                effective_threshold = (self.config.get('cross_topic_threshold', 0.85)
                                     if is_cross_topic else self.similarity_threshold)

                if self.debug_mode:
                    title_sim = similarity_result['title_similarity']
                    content_sim = similarity_result['content_similarity']

                    print(f"    🔍 比较 {other_article['file_name']}:")
                    print(f"      标题相似度: {title_sim:.3f}")
                    print(f"      内容相似度: {content_sim:.3f}")
                    print(f"      综合相似度: {similarity_score:.3f}")
                    print(f"      跨主题: {is_cross_topic}, 阈值: {effective_threshold:.3f}")

                if similarity_score >= effective_threshold:
                    print(f"  📦 相似文章 (相似度: {similarity_score:.3f}): "
                          f"{other_article['file_name']}")

                    # Record move information
                    moved_info = {
                        **other_article,
                        'similarity_to_base': similarity_score,
                        'base_article': base_article['file_name'],
                        'is_cross_topic': is_cross_topic,
                        'effective_threshold': effective_threshold,
                        'similarity_details': similarity_result
                    }
                    moved_articles.append(moved_info)
                    to_remove.append(i)
                elif self.debug_mode:
                    print(f"    ❌ 不相似 {similarity_score:.3f} < {effective_threshold:.3f}")

            # Remove marked articles
            for index in reversed(to_remove):
                remaining_articles.pop(index)

        result = {
            'kept_articles': kept_articles,
            'moved_articles': moved_articles,
            'total_comparisons': total_comparisons,
            'processing_date': processing_date,
            'algorithm': 'linear'
        }

        print(f"\n✅ 线性检测完成:")
        print(f"  📊 总比较次数: {total_comparisons}")
        print(f"  ✅ 保留文章: {len(kept_articles)} 篇")
        print(f"  📦 移动文章: {len(moved_articles)} 篇")

        return result

    def _get_article_effective_date(self, article: Dict) -> datetime:
        """
        Get effective date for article (used for sorting).

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
        import re

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

    def _are_cross_topic_articles(self, article1: Dict, article2: Dict) -> bool:
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

        topic1 = self._classify_article_topic(article1)
        topic2 = self._classify_article_topic(article2)

        # If either article cannot be classified, not considered cross-topic
        if topic1 is None or topic2 is None:
            return False

        return topic1 != topic2

    def _classify_article_topic(self, article: Dict) -> Optional[str]:
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
        for topic_name, topic_settings in topics.items():
            keywords = topic_settings.get('keywords', [])
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

    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode."""
        self.debug_mode = enabled

    def get_algorithm_info(self) -> Dict[str, Any]:
        """Get information about this algorithm."""
        return {
            'name': 'Linear Comparison',
            'description': 'Sequential chronological comparison algorithm',
            'complexity': 'O(n²) worst case, O(n) optimized with time windows',
            'suitable_for': 'Large datasets with chronological data',
            'features': [
                'Time-based optimization',
                'Preserves earliest articles',
                'Cross-topic awareness',
                'Memory efficient'
            ]
        }