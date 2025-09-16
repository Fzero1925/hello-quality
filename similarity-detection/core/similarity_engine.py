#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Similarity Engine - Core functionality for similarity detection.

This module provides the main SimilarityEngine class that coordinates
different similarity algorithms and manages the detection process.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add current package to path
current_package = Path(__file__).parent.parent
sys.path.insert(0, str(current_package))

try:
    from .article_analyzer import ArticleAnalyzer
    from .result_processor import ResultProcessor
except ImportError:
    from article_analyzer import ArticleAnalyzer
    from result_processor import ResultProcessor

try:
    from ..algorithms.linear_comparison import LinearComparison
    from ..algorithms.tfidf_similarity import TFIDFSimilarity
    from ..utils.file_handler import FileHandler
except ImportError:
    from algorithms.linear_comparison import LinearComparison
    from algorithms.tfidf_similarity import TFIDFSimilarity
    from utils.file_handler import FileHandler


class SimilarityEngine:
    """
    Core similarity detection engine.

    Coordinates different algorithms and manages the detection workflow.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the similarity engine.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)

        # Initialize components
        self.article_analyzer = ArticleAnalyzer(self.config)
        self.result_processor = ResultProcessor(self.config)
        self.file_handler = FileHandler()

        # Algorithm instances
        self.linear_comparison = LinearComparison(self.config)
        self.tfidf_similarity = TFIDFSimilarity(self.config)

        # Core configuration
        self.similarity_threshold = self.config.get('similarity_threshold', 0.7)
        self.comparison_window_days = self.config.get('comparison_window_days', 90)
        self.new_articles_folder = self.config.get('new_articles_folder', 'new-articles')
        self.old_articles_folder = self.config.get('old_articles_folder', 'old-articles')
        self.keep_oldest = self.config.get('keep_oldest_article', True)

        # Topic classification configuration
        self.topic_classification = self.config.get('topic_classification', {})
        self.cross_topic_threshold = self.topic_classification.get('cross_topic_similarity_threshold', 0.85)

        # Debug mode
        self.debug_mode = False

        print(f"✅ 相似度检测引擎初始化完成")
        print(f"📊 检测阈值: {self.similarity_threshold}")
        print(f"⏰ 检测窗口: {self.comparison_window_days} 天")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file."""
        import yaml

        default_config = {
            'similarity_threshold': 0.7,
            'comparison_window_days': 90,
            'duplicate_folder': 'oldarticles',
            'min_content_length': 1000,
            'check_title_similarity': True,
            'check_content_similarity': True,
            'title_weight': 0.3,
            'content_weight': 0.7,
            'preserve_newest': True,
            'backup_before_move': True,
            'topic_classification': {'enabled': False}
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    similarity_config = user_config.get('similarity_detection', {})

                    # Update configuration
                    if 'tfidf_threshold' in similarity_config:
                        default_config['similarity_threshold'] = similarity_config['tfidf_threshold']
                    if 'old_articles_folder' in similarity_config:
                        default_config['duplicate_folder'] = similarity_config['old_articles_folder']

                    default_config.update(similarity_config)
                    print(f"✅ 从配置文件加载设置: {config_path}")
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}，使用默认配置")

        return default_config

    def scan_articles(self, directory: str) -> List[Dict]:
        """
        Scan directory for articles and analyze them.

        Args:
            directory: Directory path to scan

        Returns:
            List of article information dictionaries
        """
        return self.article_analyzer.scan_directory(directory)

    def detect_similarities_linear(self, articles: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Perform linear similarity detection.

        Args:
            articles: List of articles to analyze

        Returns:
            Detection results
        """
        if articles is None:
            articles = getattr(self, 'all_articles', [])

        return self.linear_comparison.detect_similarities(articles)

    def detect_duplicate_groups(self, articles: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Perform graph-based duplicate group detection.

        Args:
            articles: List of articles to analyze

        Returns:
            Detection results with duplicate groups
        """
        if articles is None:
            articles = getattr(self, 'all_articles', [])

        # This will be implemented when we create the graph algorithm module
        from ..algorithms.graph_clustering import GraphClustering
        graph_clustering = GraphClustering(self.config)
        return graph_clustering.detect_duplicate_groups(articles)

    def compare_two_articles(self, file1: str, file2: str) -> Dict[str, Any]:
        """
        Compare two specific articles.

        Args:
            file1: First article file path
            file2: Second article file path

        Returns:
            Comparison results
        """
        # Extract article information
        article1 = self.article_analyzer.extract_article_info(Path(file1))
        article2 = self.article_analyzer.extract_article_info(Path(file2))

        if not article1 or not article2:
            print(f"❌ 无法解析文章内容")
            return None

        # Calculate similarities using TF-IDF algorithm
        similarity_score = self.tfidf_similarity.calculate_similarity(article1, article2)

        # Build detailed result
        result = {
            'article1': {
                'file_path': file1,
                'title': article1['title'],
                'word_count': article1['word_count'],
                'effective_date': self.article_analyzer.get_effective_date(article1)
            },
            'article2': {
                'file_path': file2,
                'title': article2['title'],
                'word_count': article2['word_count'],
                'effective_date': self.article_analyzer.get_effective_date(article2)
            },
            'similarity_scores': similarity_score,
            'analysis': {
                'is_similar': similarity_score['overall_similarity'] >= self.similarity_threshold,
                'threshold_used': self.similarity_threshold
            }
        }

        # Output results
        print(f"\n📊 相似度分析结果:")
        print(f"  综合相似度: {similarity_score['overall_similarity']:.3f}")
        print(f"  检测阈值: {self.similarity_threshold:.3f}")
        print(f"  判断结果: {'相似' if result['analysis']['is_similar'] else '不相似'}")

        return result

    def process_articles_by_date(self, detection_result: Dict[str, Any],
                                move_files: bool = True) -> Dict[str, Any]:
        """
        Process articles based on detection results.

        Args:
            detection_result: Results from similarity detection
            move_files: Whether to actually move files

        Returns:
            Processing results
        """
        return self.result_processor.process_by_date(detection_result, move_files)

    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode."""
        self.debug_mode = enabled
        self.article_analyzer.debug_mode = enabled
        self.linear_comparison.debug_mode = enabled
        if enabled:
            print("🐛 调试模式已启用")
        else:
            print("📊 调试模式已关闭")