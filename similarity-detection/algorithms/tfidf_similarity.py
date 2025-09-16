#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TF-IDF Similarity Algorithm

Implements TF-IDF based similarity detection using cosine similarity.
Provides both individual article comparison and text processing utilities.
"""

import re
from typing import Dict, List, Tuple


class TFIDFSimilarity:
    """
    TF-IDF based similarity calculation algorithm.
    """

    def __init__(self, config: Dict):
        """
        Initialize TF-IDF similarity calculator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.title_weight = config.get('title_weight', 0.3)
        self.content_weight = config.get('content_weight', 0.7)
        self.check_title_similarity = config.get('check_title_similarity', True)
        self.check_content_similarity = config.get('check_content_similarity', True)

    def calculate_similarity(self, article1: Dict, article2: Dict) -> Dict[str, float]:
        """
        Calculate overall similarity between two articles.

        Args:
            article1: First article information
            article2: Second article information

        Returns:
            Dictionary with similarity scores
        """
        # Check for identical content
        if article1.get('content_hash') == article2.get('content_hash'):
            return {
                'title_similarity': 1.0,
                'content_similarity': 1.0,
                'overall_similarity': 1.0
            }

        # Calculate title similarity
        title_sim = 0.0
        if self.check_title_similarity:
            title_sim = self.calculate_title_similarity(
                article1.get('title', ''),
                article2.get('title', '')
            )

        # Calculate content similarity
        content_sim = 0.0
        if self.check_content_similarity:
            content_sim = self.calculate_content_similarity(
                article1.get('content', ''),
                article2.get('content', '')
            )

        # Calculate weighted overall similarity
        overall_sim = title_sim * self.title_weight + content_sim * self.content_weight

        return {
            'title_similarity': title_sim,
            'content_similarity': content_sim,
            'overall_similarity': min(1.0, overall_sim)
        }

    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using Jaccard similarity.

        Args:
            title1: First title
            title2: Second title

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not title1 or not title2:
            return 0.0

        # Normalize titles
        title1_clean = self.normalize_text(title1)
        title2_clean = self.normalize_text(title2)

        if title1_clean == title2_clean:
            return 1.0

        # Calculate word overlap (Jaccard similarity)
        words1 = set(title1_clean.split())
        words2 = set(title2_clean.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate content similarity using TF-IDF and cosine similarity.

        Args:
            content1: First article content
            content2: Second article content

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not content1 or not content2:
            return 0.0

        # Normalize content
        content1_clean = self.normalize_text(content1)
        content2_clean = self.normalize_text(content2)

        if content1_clean == content2_clean:
            return 1.0

        # Simple word frequency method (simplified TF-IDF)
        words1 = content1_clean.split()
        words2 = content2_clean.split()

        # Build vocabulary
        vocab = set(words1 + words2)

        if not vocab:
            return 0.0

        # Calculate word frequency vectors
        vec1 = [words1.count(word) for word in vocab]
        vec2 = [words2.count(word) for word in vocab]

        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()

        # Remove Markdown formatting
        text = re.sub(r'[#*`\[\]()]', '', text)
        text = re.sub(r'http[s]?://\S+', '', text)

        # Remove punctuation
        text = re.sub(r'[^\w\s-]', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def calculate_advanced_tfidf_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate advanced TF-IDF similarity using external libraries.

        This method uses sklearn for more accurate TF-IDF calculation.
        Falls back to simple method if sklearn is not available.

        Args:
            content1: First article content
            content2: Second article content

        Returns:
            Similarity score (0.0 to 1.0)
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            if not content1 or not content2:
                return 0.0

            # Normalize content
            content1_clean = self.normalize_text(content1)
            content2_clean = self.normalize_text(content2)

            # Create TF-IDF vectors
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_df=0.8,
                min_df=0.1,
                ngram_range=(1, 2)
            )

            # Fit and transform both documents
            corpus = [content1_clean, content2_clean]
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)

                # Calculate cosine similarity
                similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                return float(similarity_matrix[0][0])

            except ValueError:
                # If TF-IDF fails (e.g., no common terms), fall back to simple method
                return self.calculate_content_similarity(content1, content2)

        except ImportError:
            # If sklearn is not available, use simple method
            return self.calculate_content_similarity(content1, content2)

    def batch_similarity_calculation(self, articles: List[Dict]) -> List[List[float]]:
        """
        Calculate similarity matrix for multiple articles.

        Args:
            articles: List of article information dictionaries

        Returns:
            2D list representing similarity matrix
        """
        n = len(articles)
        similarity_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            # Diagonal is 1.0 (self-similarity)
            similarity_matrix[i][i] = 1.0

            for j in range(i + 1, n):
                # Calculate similarity between articles i and j
                sim_result = self.calculate_similarity(articles[i], articles[j])
                similarity = sim_result['overall_similarity']

                # Matrix is symmetric
                similarity_matrix[i][j] = similarity
                similarity_matrix[j][i] = similarity

        return similarity_matrix

    def get_similarity_statistics(self, similarity_matrix: List[List[float]]) -> Dict[str, float]:
        """
        Calculate statistics for a similarity matrix.

        Args:
            similarity_matrix: 2D similarity matrix

        Returns:
            Dictionary with statistical information
        """
        if not similarity_matrix or not similarity_matrix[0]:
            return {'max': 0.0, 'min': 0.0, 'mean': 0.0, 'median': 0.0}

        # Extract upper triangle (excluding diagonal)
        similarities = []
        n = len(similarity_matrix)
        for i in range(n):
            for j in range(i + 1, n):
                similarities.append(similarity_matrix[i][j])

        if not similarities:
            return {'max': 0.0, 'min': 0.0, 'mean': 0.0, 'median': 0.0}

        similarities.sort()
        n_sim = len(similarities)

        stats = {
            'max': max(similarities),
            'min': min(similarities),
            'mean': sum(similarities) / n_sim,
            'median': similarities[n_sim // 2] if n_sim % 2 == 1
                     else (similarities[n_sim // 2 - 1] + similarities[n_sim // 2]) / 2,
            'count': n_sim
        }

        return stats