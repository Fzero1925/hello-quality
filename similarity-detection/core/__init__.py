#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Modules for Similarity Detection

Contains the main engine and core functionality for similarity detection.
"""

from .similarity_engine import SimilarityEngine
from .article_analyzer import ArticleAnalyzer
from .comparison_algorithms import ComparisonAlgorithms
from .result_processor import ResultProcessor

__all__ = [
    'SimilarityEngine',
    'ArticleAnalyzer', 
    'ComparisonAlgorithms',
    'ResultProcessor',
]