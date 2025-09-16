#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Similarity Algorithm

Implements AI-powered semantic similarity detection using sentence transformers
and embedding models for deep content understanding.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np


class SemanticSimilarity:
    """
    AI-powered semantic similarity detection using sentence transformers.

    Uses pre-trained language models to generate embeddings and calculate
    semantic similarity between articles based on meaning rather than just keywords.
    """

    def __init__(self, config: Dict):
        """
        Initialize semantic similarity calculator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.similarity_threshold = config.get('semantic_threshold', 0.86)
        self.comparison_window_days = config.get('comparison_window_days', 30)
        self.embedding_model_name = config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.min_content_length = config.get('min_content_length', 500)
        self.fingerprint_cache_path = config.get('fingerprint_db_path', 'data/content_fingerprints.json')

        # Initialize model (lazy loading)
        self.model = None
        self.fingerprint_db = self._load_fingerprint_database()

    def _load_embedding_model(self):
        """Load the sentence transformer model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"📥 加载语义模型: {self.embedding_model_name}")
                self.model = SentenceTransformer(self.embedding_model_name)
                print(f"✅ 语义模型加载完成")
            except ImportError:
                print("⚠️ sentence-transformers未安装，语义相似度功能不可用")
                print("   请运行: pip install sentence-transformers")
                raise ImportError("sentence-transformers package required for semantic similarity")

        return self.model

    def _load_fingerprint_database(self) -> Dict:
        """Load content fingerprint database."""
        if not Path(self.fingerprint_cache_path).exists():
            return {'version': '1.0', 'fingerprints': {}}

        try:
            with open(self.fingerprint_cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 指纹数据库加载失败: {e}")
            return {'version': '1.0', 'fingerprints': {}}

    def calculate_similarity(self, article1: Dict, article2: Dict) -> Dict[str, float]:
        """
        Calculate semantic similarity between two articles.

        Args:
            article1: First article information
            article2: Second article information

        Returns:
            Dictionary with similarity scores
        """
        model = self._load_embedding_model()

        # Extract and preprocess content
        content1 = self._preprocess_content(article1.get('content', ''))
        content2 = self._preprocess_content(article2.get('content', ''))

        if not content1 or not content2:
            return {
                'semantic_similarity': 0.0,
                'embedding_distance': 1.0,
                'is_semantically_similar': False
            }

        # Check content length
        if (len(content1) < self.min_content_length or
            len(content2) < self.min_content_length):
            return {
                'semantic_similarity': 0.0,
                'embedding_distance': 1.0,
                'is_semantically_similar': False,
                'reason': 'Content too short for semantic analysis'
            }

        # Generate embeddings
        embedding1 = self._get_content_embedding(content1, article1.get('file_path', ''))
        embedding2 = self._get_content_embedding(content2, article2.get('file_path', ''))

        if embedding1 is None or embedding2 is None:
            return {
                'semantic_similarity': 0.0,
                'embedding_distance': 1.0,
                'is_semantically_similar': False,
                'reason': 'Failed to generate embeddings'
            }

        # Calculate cosine similarity
        similarity = self._cosine_similarity(embedding1, embedding2)

        # Calculate distance
        distance = 1.0 - similarity

        # Check if semantically similar
        is_similar = similarity >= self.similarity_threshold

        return {
            'semantic_similarity': float(similarity),
            'embedding_distance': float(distance),
            'is_semantically_similar': is_similar,
            'threshold_used': self.similarity_threshold
        }

    def _get_content_embedding(self, content: str, file_path: str = '') -> Optional[np.ndarray]:
        """
        Get or generate content embedding with caching.

        Args:
            content: Content to embed
            file_path: File path for caching

        Returns:
            Content embedding or None if failed
        """
        # Generate content hash for caching
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        # Check cache
        if content_hash in self.fingerprint_db.get('fingerprints', {}):
            cached_data = self.fingerprint_db['fingerprints'][content_hash]
            if 'embedding' in cached_data:
                try:
                    return np.array(cached_data['embedding'])
                except Exception:
                    pass

        # Generate new embedding
        try:
            model = self._load_embedding_model()
            embedding = model.encode([content])[0]

            # Cache the embedding
            self._cache_embedding(content_hash, embedding, file_path)

            return embedding

        except Exception as e:
            print(f"❌ 生成语义嵌入失败: {e}")
            return None

    def _cache_embedding(self, content_hash: str, embedding: np.ndarray, file_path: str = ''):
        """Cache embedding to fingerprint database."""
        try:
            fingerprint_data = {
                'embedding': embedding.tolist(),
                'model': self.embedding_model_name,
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path
            }

            if 'fingerprints' not in self.fingerprint_db:
                self.fingerprint_db['fingerprints'] = {}

            self.fingerprint_db['fingerprints'][content_hash] = fingerprint_data

            # Save to file
            Path(self.fingerprint_cache_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.fingerprint_cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.fingerprint_db, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️ 缓存嵌入失败: {e}")

    def _preprocess_content(self, content: str) -> str:
        """
        Preprocess content for semantic analysis.

        Args:
            content: Raw content

        Returns:
            Preprocessed content
        """
        if not content:
            return ""

        # Remove excessive whitespace
        import re
        content = re.sub(r'\s+', ' ', content)

        # Truncate if too long (models have token limits)
        max_length = 8000  # Conservative limit for most models
        if len(content) > max_length:
            content = content[:max_length] + "..."

        return content.strip()

    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Calculate cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        similarity = dot_product / (norm1 * norm2)

        return similarity

    def find_semantically_similar_articles(self, target_article: Dict,
                                          candidate_articles: List[Dict],
                                          threshold: Optional[float] = None) -> List[Tuple[Dict, float]]:
        """
        Find articles semantically similar to target.

        Args:
            target_article: Target article to compare against
            candidate_articles: List of candidate articles
            threshold: Similarity threshold (uses default if None)

        Returns:
            List of (article, similarity_score) tuples sorted by similarity
        """
        if threshold is None:
            threshold = self.similarity_threshold

        target_content = self._preprocess_content(target_article.get('content', ''))
        if not target_content:
            return []

        target_embedding = self._get_content_embedding(
            target_content, target_article.get('file_path', ''))
        if target_embedding is None:
            return []

        similar_articles = []

        for candidate in candidate_articles:
            # Skip self
            if candidate.get('file_path') == target_article.get('file_path'):
                continue

            candidate_content = self._preprocess_content(candidate.get('content', ''))
            if not candidate_content:
                continue

            candidate_embedding = self._get_content_embedding(
                candidate_content, candidate.get('file_path', ''))
            if candidate_embedding is None:
                continue

            similarity = self._cosine_similarity(target_embedding, candidate_embedding)

            if similarity >= threshold:
                similar_articles.append((candidate, similarity))

        # Sort by similarity (descending)
        similar_articles.sort(key=lambda x: x[1], reverse=True)

        return similar_articles

    def batch_similarity_matrix(self, articles: List[Dict]) -> np.ndarray:
        """
        Generate similarity matrix for multiple articles.

        Args:
            articles: List of articles

        Returns:
            Similarity matrix as numpy array
        """
        n = len(articles)
        similarity_matrix = np.zeros((n, n))

        # Generate all embeddings
        embeddings = []
        for article in articles:
            content = self._preprocess_content(article.get('content', ''))
            embedding = self._get_content_embedding(content, article.get('file_path', ''))
            embeddings.append(embedding)

        # Calculate pairwise similarities
        for i in range(n):
            similarity_matrix[i][i] = 1.0  # Self-similarity

            for j in range(i + 1, n):
                if embeddings[i] is not None and embeddings[j] is not None:
                    similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarity_matrix[i][j] = similarity
                    similarity_matrix[j][i] = similarity

        return similarity_matrix

    def cleanup_cache(self, days_to_keep: int = 30):
        """
        Clean up old cached embeddings.

        Args:
            days_to_keep: Number of days to keep cached data
        """
        if 'fingerprints' not in self.fingerprint_db:
            return

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        fingerprints_to_remove = []

        for content_hash, data in self.fingerprint_db['fingerprints'].items():
            try:
                timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                if timestamp < cutoff_date:
                    fingerprints_to_remove.append(content_hash)
            except Exception:
                # Remove invalid timestamps
                fingerprints_to_remove.append(content_hash)

        # Remove old fingerprints
        for content_hash in fingerprints_to_remove:
            del self.fingerprint_db['fingerprints'][content_hash]

        # Save updated database
        if fingerprints_to_remove:
            try:
                with open(self.fingerprint_cache_path, 'w', encoding='utf-8') as f:
                    json.dump(self.fingerprint_db, f, indent=2, ensure_ascii=False)
                print(f"🧹 清理了 {len(fingerprints_to_remove)} 个过期缓存项")
            except Exception as e:
                print(f"⚠️ 缓存清理失败: {e}")

    def get_algorithm_info(self) -> Dict[str, any]:
        """Get information about this algorithm."""
        return {
            'name': 'Semantic Similarity',
            'description': 'AI-powered semantic understanding using sentence transformers',
            'complexity': 'O(1) with caching, O(n) for embedding generation',
            'suitable_for': 'Deep content understanding and semantic analysis',
            'features': [
                'Semantic understanding',
                'Pre-trained language models',
                'Embedding caching',
                'Configurable models'
            ],
            'parameters': {
                'similarity_threshold': self.similarity_threshold,
                'embedding_model': self.embedding_model_name,
                'min_content_length': self.min_content_length
            }
        }