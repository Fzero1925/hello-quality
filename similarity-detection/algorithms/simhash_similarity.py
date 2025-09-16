#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SimHash Similarity Algorithm

Implements SimHash-based similarity detection for efficient near-duplicate
content detection using Hamming distance calculations.
"""

import hashlib
import re
from typing import Dict, List, Tuple, Optional


class SimHashSimilarity:
    """
    SimHash-based similarity detection algorithm.

    Uses locality-sensitive hashing to efficiently detect near-duplicate content
    by computing Hamming distances between 64-bit SimHash fingerprints.
    """

    def __init__(self, config: Dict):
        """
        Initialize SimHash similarity calculator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.hamming_threshold = config.get('simhash_hamm_threshold', 16)
        self.ngram_size = config.get('simhash_ngram_size', 5)

    def calculate_similarity(self, article1: Dict, article2: Dict) -> Dict[str, float]:
        """
        Calculate SimHash-based similarity between two articles.

        Args:
            article1: First article information
            article2: Second article information

        Returns:
            Dictionary with similarity scores
        """
        # Extract and preprocess content
        content1 = self._preprocess_content(article1.get('content', ''))
        content2 = self._preprocess_content(article2.get('content', ''))

        if not content1 or not content2:
            return {
                'simhash_similarity': 0.0,
                'hamming_distance': 64,
                'is_near_duplicate': False
            }

        # Generate SimHash fingerprints
        hash1 = self.generate_simhash(content1)
        hash2 = self.generate_simhash(content2)

        # Calculate Hamming distance
        hamming_dist = self.hamming_distance(hash1, hash2)

        # Convert to similarity score (0.0 to 1.0)
        similarity = 1.0 - (hamming_dist / 64.0)

        # Check if near-duplicate based on threshold
        is_near_duplicate = hamming_dist <= self.hamming_threshold

        return {
            'simhash_similarity': similarity,
            'hamming_distance': hamming_dist,
            'is_near_duplicate': is_near_duplicate,
            'hash1': f"{hash1:016x}",
            'hash2': f"{hash2:016x}"
        }

    def generate_simhash(self, text: str) -> int:
        """
        Generate 64-bit SimHash fingerprint from text.

        Args:
            text: Input text content

        Returns:
            64-bit SimHash value
        """
        # Generate n-grams from text
        tokens = self._generate_ngrams(text, self.ngram_size)

        if not tokens:
            return 0

        # Initialize bit accumulator
        bits = [0] * 64

        # Process each token
        for token in tokens:
            # Generate hash for token
            token_hash = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
            token_hash &= ((1 << 64) - 1)  # Ensure 64-bit

            # Update bit accumulator
            for i in range(64):
                if (token_hash >> i) & 1:
                    bits[i] += 1
                else:
                    bits[i] -= 1

        # Generate final SimHash
        simhash = 0
        for i in range(64):
            if bits[i] > 0:
                simhash |= (1 << i)

        return simhash

    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """
        Calculate Hamming distance between two hashes.

        Args:
            hash1: First hash value
            hash2: Second hash value

        Returns:
            Hamming distance (number of differing bits)
        """
        xor_result = hash1 ^ hash2

        # Count set bits using Kernighan's algorithm
        count = 0
        while xor_result:
            xor_result &= xor_result - 1
            count += 1

        return count

    def _preprocess_content(self, content: str) -> str:
        """
        Preprocess content for SimHash generation.

        Args:
            content: Raw content

        Returns:
            Preprocessed content
        """
        if not content:
            return ""

        # Remove YAML front matter and code blocks
        content = re.sub(r"^---[\s\S]*?---\s+", "", content, flags=re.M)
        content = re.sub(r"```[\s\S]*?```", "", content)

        # Normalize whitespace
        content = re.sub(r"\s+", " ", content)

        return content.strip()

    def _generate_ngrams(self, text: str, n: int = 5) -> List[str]:
        """
        Generate word n-grams from text.

        Args:
            text: Input text
            n: N-gram size

        Returns:
            List of n-gram strings
        """
        # Extract words
        words = re.findall(r"[A-Za-z0-9']+", text.lower())

        if len(words) < n:
            return words

        # Generate n-grams
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i + n])
            ngrams.append(ngram)

        return ngrams

    def batch_simhash_calculation(self, articles: List[Dict]) -> List[int]:
        """
        Calculate SimHash fingerprints for multiple articles.

        Args:
            articles: List of article information dictionaries

        Returns:
            List of SimHash values
        """
        hashes = []
        for article in articles:
            content = self._preprocess_content(article.get('content', ''))
            simhash = self.generate_simhash(content)
            hashes.append(simhash)

        return hashes

    def find_similar_articles(self, target_hash: int, article_hashes: List[Tuple[int, Dict]],
                            threshold: Optional[int] = None) -> List[Tuple[Dict, int, float]]:
        """
        Find articles similar to target based on SimHash.

        Args:
            target_hash: Target SimHash value
            article_hashes: List of (hash, article_info) tuples
            threshold: Hamming distance threshold (uses default if None)

        Returns:
            List of (article_info, hamming_distance, similarity) tuples
        """
        if threshold is None:
            threshold = self.hamming_threshold

        similar_articles = []

        for article_hash, article_info in article_hashes:
            hamming_dist = self.hamming_distance(target_hash, article_hash)

            if hamming_dist <= threshold:
                similarity = 1.0 - (hamming_dist / 64.0)
                similar_articles.append((article_info, hamming_dist, similarity))

        # Sort by similarity (descending)
        similar_articles.sort(key=lambda x: x[2], reverse=True)

        return similar_articles

    def create_lsh_index(self, articles: List[Dict], band_size: int = 4) -> Dict[str, List[Dict]]:
        """
        Create Locality-Sensitive Hashing index for efficient similarity search.

        Args:
            articles: List of articles to index
            band_size: Size of each hash band

        Returns:
            LSH index mapping band hashes to articles
        """
        lsh_index = {}
        num_bands = 64 // band_size

        for article in articles:
            content = self._preprocess_content(article.get('content', ''))
            simhash = self.generate_simhash(content)

            # Create bands
            for band_idx in range(num_bands):
                start_bit = band_idx * band_size
                end_bit = start_bit + band_size

                # Extract band bits
                band_mask = ((1 << band_size) - 1) << start_bit
                band_hash = (simhash & band_mask) >> start_bit

                # Create band key
                band_key = f"band_{band_idx}_{band_hash:0{band_size}b}"

                # Add to index
                if band_key not in lsh_index:
                    lsh_index[band_key] = []
                lsh_index[band_key].append(article)

        return lsh_index

    def get_algorithm_info(self) -> Dict[str, any]:
        """Get information about this algorithm."""
        return {
            'name': 'SimHash Similarity',
            'description': 'Locality-sensitive hashing for near-duplicate detection',
            'complexity': 'O(1) for similarity check, O(n) for indexing',
            'suitable_for': 'Large-scale near-duplicate detection',
            'features': [
                'Fast fingerprint generation',
                'Efficient similarity search',
                'LSH indexing support',
                'Configurable similarity threshold'
            ],
            'parameters': {
                'hamming_threshold': self.hamming_threshold,
                'ngram_size': self.ngram_size
            }
        }