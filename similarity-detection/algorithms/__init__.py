#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Similarity Detection Algorithms

Collection of algorithms for detecting content similarity.
"""

from .tfidf_similarity import TFIDFSimilarity
from .simhash_similarity import SimHashSimilarity
from .semantic_similarity import SemanticSimilarity
from .linear_comparison import LinearComparison

__all__ = [
    'TFIDFSimilarity',
    'SimHashSimilarity',
    'SemanticSimilarity',
    'LinearComparison',
]