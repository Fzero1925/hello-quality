#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparison Algorithms - Unified interface for different similarity algorithms.

This module provides a common interface for various similarity detection algorithms
and coordinates their usage.
"""

from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from algorithms.tfidf_similarity import TFIDFSimilarity
    from algorithms.linear_comparison import LinearComparison
except ImportError:
    # Fallback for relative imports
    from ..algorithms.tfidf_similarity import TFIDFSimilarity
    from ..algorithms.linear_comparison import LinearComparison


class ComparisonAlgorithms:
    """
    Unified interface for similarity comparison algorithms.
    """

    def __init__(self, config: Dict):
        """
        Initialize comparison algorithms.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Initialize available algorithms
        self.tfidf_similarity = TFIDFSimilarity(config)
        self.linear_comparison = LinearComparison(config)

    def calculate_similarity(self, article1: Dict, article2: Dict,
                           algorithm: str = 'tfidf') -> Dict[str, float]:
        """
        Calculate similarity between two articles using specified algorithm.

        Args:
            article1: First article information
            article2: Second article information
            algorithm: Algorithm to use ('tfidf', 'simhash', 'semantic')

        Returns:
            Similarity scores dictionary
        """
        if algorithm == 'tfidf':
            return self.tfidf_similarity.calculate_similarity(article1, article2)
        elif algorithm == 'simhash':
            # Will be implemented when SimHash module is created
            raise NotImplementedError("SimHash algorithm not yet implemented")
        elif algorithm == 'semantic':
            # Will be implemented when Semantic module is created
            raise NotImplementedError("Semantic algorithm not yet implemented")
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def detect_similarities(self, articles: List[Dict],
                          algorithm: str = 'linear') -> Dict[str, Any]:
        """
        Detect similarities among multiple articles.

        Args:
            articles: List of articles to analyze
            algorithm: Detection algorithm ('linear', 'graph')

        Returns:
            Detection results
        """
        if algorithm == 'linear':
            return self.linear_comparison.detect_similarities(articles)
        elif algorithm == 'graph':
            # Will be implemented when Graph Clustering module is created
            raise NotImplementedError("Graph clustering algorithm not yet implemented")
        else:
            raise ValueError(f"Unknown detection algorithm: {algorithm}")

    def get_available_algorithms(self) -> List[str]:
        """Get list of available algorithms."""
        return ['tfidf', 'linear']

    def get_algorithm_info(self, algorithm: str) -> Dict[str, Any]:
        """Get information about a specific algorithm."""
        info_map = {
            'tfidf': {
                'name': 'TF-IDF Cosine Similarity',
                'description': 'Uses TF-IDF vectors and cosine similarity',
                'suitable_for': 'Content comparison',
                'performance': 'Fast'
            },
            'linear': {
                'name': 'Linear Comparison',
                'description': 'Sequential comparison with time-based optimization',
                'suitable_for': 'Large datasets with time constraints',
                'performance': 'Medium'
            }
        }
        return info_map.get(algorithm, {'name': 'Unknown', 'description': 'Unknown algorithm'})