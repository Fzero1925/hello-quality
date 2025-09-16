#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Similarity Detection Package

Modularized similarity detection system for content deduplication.
Provides comprehensive algorithms for detecting similar content.
"""

__version__ = "2.0.0"
__author__ = "Quality Detection Tool"
__description__ = "Modular similarity detection system"

from .core.similarity_engine import SimilarityEngine
from .core.article_analyzer import ArticleAnalyzer

__all__ = [
    'SimilarityEngine',
    'ArticleAnalyzer',
]