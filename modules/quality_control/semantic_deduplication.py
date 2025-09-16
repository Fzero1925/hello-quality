#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Semantic Deduplication System
Prevents generation of similar content using AI embeddings

Uses sentence-transformers to detect semantic similarity between articles
and prevent content duplication across the website.

Based on Growth Kit v3 specifications:
- 0.86 similarity threshold for content blocking
- 30-day comparison window for recent content
- Intelligent content fingerprinting and caching
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np


class SemanticDeduplicator:
    """AI-powered semantic deduplication system"""
    
    def __init__(self, config_path: str = "configs/quality_gates.yml"):
        """Initialize with configuration"""
        self.config = self._load_config(config_path)
        self.model = self._load_embedding_model()
        self.fingerprint_db = self._load_fingerprint_database()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load deduplication configuration"""
        default_config = {
            'similarity_threshold': 0.86,
            'comparison_window_days': 30,
            'embedding_model': 'all-MiniLM-L6-v2',
            'fingerprint_db_path': 'data/content_fingerprints.json',
            'min_content_length': 500,  # Minimum content length to check
            'cache_embeddings': True
        }
        
        try:
            import yaml
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    dedup_config = user_config.get('semantic_deduplication', {})
                    default_config.update(dedup_config)
        except Exception as e:
            print(f"Config load warning: {e}, using defaults")
            
        return default_config
    
    def _load_embedding_model(self):
        """Load sentence-transformers model for embeddings"""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
            return SentenceTransformer(model_name)
        except ImportError:
            print("Warning: sentence-transformers not available, using fallback")
            return None
        except Exception as e:
            print(f"Model loading error: {e}, using fallback")
            return None
    
    def _load_fingerprint_database(self) -> Dict:
        """Load existing content fingerprint database"""
        db_path = Path(self.config.get('fingerprint_db_path', 'data/content_fingerprints.json'))
        
        if db_path.exists():
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Database load error: {e}, starting fresh")
                
        return {
            'fingerprints': {},
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def _save_fingerprint_database(self):
        """Save content fingerprint database"""
        db_path = Path(self.config.get('fingerprint_db_path', 'data/content_fingerprints.json'))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.fingerprint_db['last_updated'] = datetime.now().isoformat()
        
        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(self.fingerprint_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Database save error: {e}")
    
    def create_content_fingerprint(self, content: str, metadata: Dict) -> Dict:
        """
        Create comprehensive content fingerprint
        
        Args:
            content: Article content text
            metadata: Article metadata (title, category, etc.)
            
        Returns:
            Content fingerprint with embeddings and metadata
        """
        # Generate content hash for exact duplicate detection
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Extract key phrases for semantic analysis
        key_phrases = self._extract_key_phrases(content)
        
        # Generate semantic embedding
        embedding = self._generate_embedding(content) if self.model else None
        
        # Create fingerprint
        fingerprint = {
            'content_hash': content_hash,
            'key_phrases': key_phrases,
            'embedding': embedding.tolist() if embedding is not None else None,
            'metadata': {
                'title': metadata.get('title', ''),
                'category': metadata.get('category', ''),
                'keyword': metadata.get('keyword', ''),
                'word_count': len(content.split()),
                'created_date': datetime.now().isoformat()
            },
            'similarity_scores': {},  # Will store similarity scores with other content
            'dedup_status': 'unique'  # unique, similar, duplicate
        }
        
        return fingerprint
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases for semantic comparison"""
        # Simple key phrase extraction
        # In production, could use more sophisticated NLP
        import re
        
        # Remove markdown and HTML
        clean_content = re.sub(r'[#*`\[\]()]', '', content)
        clean_content = re.sub(r'http[s]?://\S+', '', clean_content)
        
        # Extract potential key phrases (2-4 words)
        words = clean_content.lower().split()
        phrases = []
        
        for i in range(len(words) - 1):
            if len(words[i]) > 3 and len(words[i+1]) > 3:
                phrases.append(f"{words[i]} {words[i+1]}")
                
        for i in range(len(words) - 2):
            if all(len(word) > 3 for word in words[i:i+3]):
                phrases.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        
        # Return top 20 most relevant phrases
        phrase_counts = {}
        for phrase in phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
            
        sorted_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, count in sorted_phrases[:20]]
    
    def _generate_embedding(self, content: str) -> Optional[np.ndarray]:
        """Generate semantic embedding for content"""
        if not self.model:
            return None
            
        try:
            # Use first 1000 words for embedding to manage memory
            content_sample = ' '.join(content.split()[:1000])
            embedding = self.model.encode(content_sample)
            return embedding
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return None
    
    def check_content_similarity(self, content: str, metadata: Dict) -> Tuple[bool, Dict]:
        """
        Check if content is too similar to existing content
        
        Args:
            content: New article content
            metadata: New article metadata
            
        Returns:
            Tuple of (is_unique, similarity_report)
        """
        if len(content.split()) < self.config.get('min_content_length', 500):
            return True, {'status': 'too_short_to_check', 'similarities': []}
        
        # Create fingerprint for new content
        new_fingerprint = self.create_content_fingerprint(content, metadata)
        
        # Get comparison window
        comparison_window = timedelta(days=self.config.get('comparison_window_days', 30))
        cutoff_date = datetime.now() - comparison_window
        
        # Find similar content
        similarities = []
        max_similarity = 0.0
        
        for content_id, existing_fingerprint in self.fingerprint_db.get('fingerprints', {}).items():
            # Skip old content outside comparison window
            created_date_str = existing_fingerprint.get('metadata', {}).get('created_date')
            if created_date_str:
                try:
                    created_date = datetime.fromisoformat(created_date_str)
                    if created_date < cutoff_date:
                        continue
                except:
                    pass  # Skip if date parsing fails
            
            # Check exact duplicate (content hash)
            if new_fingerprint['content_hash'] == existing_fingerprint.get('content_hash'):
                return False, {
                    'status': 'exact_duplicate',
                    'duplicate_id': content_id,
                    'similarities': [{'id': content_id, 'similarity': 1.0, 'type': 'exact'}]
                }
            
            # Check semantic similarity
            similarity_score = self._calculate_similarity(new_fingerprint, existing_fingerprint)
            
            if similarity_score > max_similarity:
                max_similarity = similarity_score
            
            if similarity_score >= self.config.get('similarity_threshold', 0.86):
                similarities.append({
                    'id': content_id,
                    'similarity': similarity_score,
                    'type': 'semantic',
                    'title': existing_fingerprint.get('metadata', {}).get('title', ''),
                    'category': existing_fingerprint.get('metadata', {}).get('category', ''),
                    'created_date': existing_fingerprint.get('metadata', {}).get('created_date', '')
                })
        
        # Determine if content is unique
        threshold = self.config.get('similarity_threshold', 0.86)
        is_unique = max_similarity < threshold
        
        status = 'unique' if is_unique else 'too_similar'
        if similarities and similarities[0]['type'] == 'exact':
            status = 'exact_duplicate'
        
        return is_unique, {
            'status': status,
            'max_similarity': max_similarity,
            'threshold': threshold,
            'similarities': similarities,
            'comparison_count': len(self.fingerprint_db.get('fingerprints', {}))
        }
    
    def _calculate_similarity(self, fp1: Dict, fp2: Dict) -> float:
        """Calculate similarity between two content fingerprints"""
        # Method 1: Embedding-based similarity (most accurate)
        if fp1.get('embedding') and fp2.get('embedding'):
            try:
                emb1 = np.array(fp1['embedding'])
                emb2 = np.array(fp2['embedding'])
                
                # Cosine similarity
                dot_product = np.dot(emb1, emb2)
                norm1 = np.linalg.norm(emb1)
                norm2 = np.linalg.norm(emb2)
                
                if norm1 > 0 and norm2 > 0:
                    return dot_product / (norm1 * norm2)
            except Exception as e:
                print(f"Embedding similarity error: {e}")
        
        # Method 2: Key phrase similarity (fallback)
        phrases1 = set(fp1.get('key_phrases', []))
        phrases2 = set(fp2.get('key_phrases', []))
        
        if phrases1 and phrases2:
            intersection = len(phrases1 & phrases2)
            union = len(phrases1 | phrases2)
            return intersection / union if union > 0 else 0.0
        
        # Method 3: Metadata similarity (last resort)
        meta1 = fp1.get('metadata', {})
        meta2 = fp2.get('metadata', {})
        
        category_match = 0.5 if meta1.get('category') == meta2.get('category') else 0.0
        keyword_similarity = 0.3 if meta1.get('keyword', '').lower() in meta2.get('keyword', '').lower() else 0.0
        
        return category_match + keyword_similarity
    
    def register_content(self, content: str, metadata: Dict, content_id: Optional[str] = None) -> str:
        """
        Register new content in the deduplication database
        
        Args:
            content: Article content
            metadata: Article metadata  
            content_id: Optional custom content ID
            
        Returns:
            Content ID for the registered content
        """
        # Generate content ID if not provided
        if not content_id:
            title = metadata.get('title', 'untitled')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            content_id = f"{title.lower().replace(' ', '_')}_{timestamp}"
        
        # Create and store fingerprint
        fingerprint = self.create_content_fingerprint(content, metadata)
        
        if 'fingerprints' not in self.fingerprint_db:
            self.fingerprint_db['fingerprints'] = {}
            
        self.fingerprint_db['fingerprints'][content_id] = fingerprint
        
        # Save database
        self._save_fingerprint_database()
        
        return content_id
    
    def cleanup_old_fingerprints(self):
        """Remove fingerprints older than comparison window"""
        comparison_window = timedelta(days=self.config.get('comparison_window_days', 30) * 2)  # Keep 2x window
        cutoff_date = datetime.now() - comparison_window
        
        if 'fingerprints' not in self.fingerprint_db:
            return
        
        old_ids = []
        for content_id, fingerprint in self.fingerprint_db['fingerprints'].items():
            created_date_str = fingerprint.get('metadata', {}).get('created_date')
            if created_date_str:
                try:
                    created_date = datetime.fromisoformat(created_date_str)
                    if created_date < cutoff_date:
                        old_ids.append(content_id)
                except:
                    pass
        
        # Remove old fingerprints
        for content_id in old_ids:
            del self.fingerprint_db['fingerprints'][content_id]
            
        if old_ids:
            print(f"Cleaned up {len(old_ids)} old content fingerprints")
            self._save_fingerprint_database()
    
    def get_database_stats(self) -> Dict:
        """Get deduplication database statistics"""
        fingerprints = self.fingerprint_db.get('fingerprints', {})
        
        if not fingerprints:
            return {
                'total_content': 0,
                'recent_content': 0,
                'database_size': '0 KB'
            }
        
        # Count recent content
        comparison_window = timedelta(days=self.config.get('comparison_window_days', 30))
        cutoff_date = datetime.now() - comparison_window
        recent_count = 0
        
        for fingerprint in fingerprints.values():
            created_date_str = fingerprint.get('metadata', {}).get('created_date')
            if created_date_str:
                try:
                    created_date = datetime.fromisoformat(created_date_str)
                    if created_date >= cutoff_date:
                        recent_count += 1
                except:
                    pass
        
        # Calculate database size
        db_path = Path(self.config.get('fingerprint_db_path', 'data/content_fingerprints.json'))
        db_size = db_path.stat().st_size if db_path.exists() else 0
        
        return {
            'total_content': len(fingerprints),
            'recent_content': recent_count,
            'comparison_window_days': self.config.get('comparison_window_days', 30),
            'similarity_threshold': self.config.get('similarity_threshold', 0.86),
            'database_size': f"{db_size / 1024:.1f} KB",
            'last_updated': self.fingerprint_db.get('last_updated', 'Unknown')
        }


# Factory function for easy import
def create_deduplicator(config_path: str = None) -> SemanticDeduplicator:
    """Create configured semantic deduplicator instance"""
    return SemanticDeduplicator(config_path) if config_path else SemanticDeduplicator()


if __name__ == "__main__":
    # Test the semantic deduplication system
    deduplicator = SemanticDeduplicator()
    
    print("=== Semantic Deduplication Test ===")
    print(f"Database stats: {deduplicator.get_database_stats()}")
    
    # Test content 1
    test_content_1 = """
    # Smart Plug Guide 2025
    
    Smart plugs are revolutionary devices that transform ordinary outlets into intelligent control points
    for your home automation system. These compact devices offer unprecedented control over your
    electrical appliances and provide valuable insights into energy consumption patterns.
    
    ## Key Features
    The most important features to consider when choosing a smart plug include WiFi connectivity,
    energy monitoring capabilities, voice control integration, and smartphone app functionality.
    These features work together to provide comprehensive control over your home's electrical devices.
    
    ## Top Recommendations  
    Based on extensive research and analysis, the top smart plugs for 2025 include the TP-Link Kasa
    smart plug for reliability, the Amazon Smart Plug for Alexa integration, and the Wyze Plug
    for budget-conscious consumers seeking quality features.
    """
    
    test_metadata_1 = {
        'title': 'Best Smart Plugs 2025: Complete Guide',
        'category': 'smart_plugs', 
        'keyword': 'smart plug guide'
    }
    
    # Check first content
    is_unique_1, report_1 = deduplicator.check_content_similarity(test_content_1, test_metadata_1)
    print(f"\\nContent 1 - Unique: {is_unique_1}")
    print(f"Status: {report_1['status']}")
    print(f"Max similarity: {report_1.get('max_similarity', 0):.3f}")
    
    # Register first content
    content_id_1 = deduplicator.register_content(test_content_1, test_metadata_1)
    print(f"Registered as: {content_id_1}")
    
    # Test similar content
    test_content_2 = """
    # Smart Plug Buying Guide 2025
    
    Smart plugs represent innovative devices that convert standard electrical outlets into intelligent
    control hubs for home automation systems. These small gadgets provide unmatched control over
    household appliances and deliver important data about power usage patterns.
    
    ## Essential Features
    The key features to evaluate when selecting a smart plug are WiFi connectivity, energy monitoring
    functions, voice command support, and mobile app integration. These capabilities combine to offer
    complete control over your home's electrical equipment.
    
    ## Best Options
    After thorough research and evaluation, the leading smart plugs for 2025 are the TP-Link Kasa
    smart plug for dependability, the Amazon Smart Plug for Alexa compatibility, and the Wyze Plug
    for cost-effective consumers wanting premium features.
    """
    
    test_metadata_2 = {
        'title': 'Smart Plug Buying Guide 2025',
        'category': 'smart_plugs',
        'keyword': 'smart plug buying guide'
    }
    
    # Check similar content
    is_unique_2, report_2 = deduplicator.check_content_similarity(test_content_2, test_metadata_2)
    print(f"\\nContent 2 - Unique: {is_unique_2}")
    print(f"Status: {report_2['status']}")
    print(f"Max similarity: {report_2.get('max_similarity', 0):.3f}")
    
    if report_2.get('similarities'):
        print("Similar content found:")
        for sim in report_2['similarities']:
            print(f"  - {sim['title']}: {sim['similarity']:.3f}")
    
    # Database stats after test
    print(f"\\nFinal database stats: {deduplicator.get_database_stats()}")