"""
SimHash-based similarity detection for content deduplication.
Implements LSH (Locality-Sensitive Hashing) for efficient similarity search.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re
import logging
from simhash import Simhash, SimhashIndex

@dataclass
class ContentRecord:
    """Record for stored content with SimHash fingerprint"""
    title: str
    simhash_value: int
    timestamp: datetime
    category: str
    angle: str
    source: str

class SimHashDetector:
    """
    SimHash-based content similarity detector.
    Uses Hamming distance to find similar content efficiently.
    """
    
    def __init__(self, db_path: str = "data/content_simhash.db", 
                 similarity_threshold: int = 3):
        """
        Initialize SimHash detector.
        
        Args:
            db_path: Path to SQLite database for storing SimHash records
            similarity_threshold: Maximum Hamming distance for similarity (0-64)
        """
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        
        # Create data directory
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Initialize SimHash index for fast similarity search
        self.simhash_index = None
        self._rebuild_index()
    
    def _init_database(self):
        """Initialize SQLite database for SimHash storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS content_simhash (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    simhash_value INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    angle TEXT NOT NULL,
                    source TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_simhash 
                ON content_simhash(simhash_value)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON content_simhash(timestamp)
            """)
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for SimHash calculation.
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def calculate_simhash(self, text: str) -> int:
        """
        Calculate SimHash fingerprint for text.
        
        Args:
            text: Input text
            
        Returns:
            64-bit SimHash value
        """
        preprocessed = self._preprocess_text(text)
        
        if not preprocessed:
            return 0
        
        # Use 64-bit SimHash with word-level features
        return Simhash(preprocessed).value
    
    def add_content_record(self, title: str, category: str = "smart_home", 
                          angle: str = "general", source: str = "generated") -> bool:
        """
        Add a content record with SimHash fingerprint.
        
        Args:
            title: Content title
            category: Product category  
            angle: Content angle
            source: Source of content
            
        Returns:
            True if successfully added
        """
        try:
            simhash_value = self.calculate_simhash(title)
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO content_simhash 
                    (title, simhash_value, timestamp, category, angle, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, simhash_value, timestamp, category, angle, source))
            
            # Rebuild index to include new record
            self._rebuild_index()
            
            self.logger.info(f"Added content record: {title[:50]}... "
                           f"(SimHash: {simhash_value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add content record '{title}': {e}")
            return False
    
    def find_similar_content(self, title: str, days: int = 7) -> List[Tuple[ContentRecord, int]]:
        """
        Find similar content based on SimHash similarity.
        
        Args:
            title: Title to check for similarity
            days: Number of days to search back
            
        Returns:
            List of (ContentRecord, hamming_distance) tuples for similar content
        """
        try:
            target_simhash = self.calculate_simhash(title)
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            similar_content = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT title, simhash_value, timestamp, category, angle, source
                    FROM content_simhash
                    WHERE timestamp >= ?
                """, (cutoff_date,))
                
                for row in cursor.fetchall():
                    title_db, simhash_db, timestamp, category, angle, source = row
                    
                    # Calculate Hamming distance
                    hamming_distance = bin(target_simhash ^ simhash_db).count('1')
                    
                    if hamming_distance <= self.similarity_threshold:
                        record = ContentRecord(
                            title=title_db,
                            simhash_value=simhash_db,
                            timestamp=datetime.fromisoformat(timestamp),
                            category=category,
                            angle=angle,
                            source=source
                        )
                        similar_content.append((record, hamming_distance))
            
            # Sort by similarity (lower hamming distance = more similar)
            similar_content.sort(key=lambda x: x[1])
            
            return similar_content
            
        except Exception as e:
            self.logger.error(f"Failed to find similar content for '{title}': {e}")
            return []
    
    def check_similarity(self, title: str, max_similarity: float = 0.85, 
                        days: int = 7) -> Tuple[bool, float, Optional[str]]:
        """
        Check if content is too similar to recent content.
        
        Args:
            title: Title to check
            max_similarity: Maximum allowed similarity ratio (0-1)
            days: Days to check against
            
        Returns:
            Tuple of (is_too_similar, max_similarity_found, most_similar_title)
        """
        similar_content = self.find_similar_content(title, days)
        
        if not similar_content:
            return False, 0.0, None
        
        # Get the most similar content (lowest Hamming distance)
        most_similar_record, hamming_distance = similar_content[0]
        
        # Convert Hamming distance to similarity ratio
        # SimHash is 64-bit, so max distance is 64
        similarity_ratio = 1.0 - (hamming_distance / 64.0)
        
        is_too_similar = similarity_ratio >= max_similarity
        
        self.logger.debug(f"Similarity check for '{title[:30]}...': "
                         f"{similarity_ratio:.3f} vs {max_similarity} threshold "
                         f"({'SIMILAR' if is_too_similar else 'OK'})")
        
        return is_too_similar, similarity_ratio, most_similar_record.title
    
    def _rebuild_index(self):
        """Rebuild SimHash index for fast similarity search"""
        try:
            # Get all current SimHash values
            simhash_data = []
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT id, simhash_value FROM content_simhash")
                simhash_data = [(row[0], row[1]) for row in cursor.fetchall()]
            
            if simhash_data:
                # Create new SimHash index
                objects = [(str(id_val), Simhash(simhash_val, hashfunc=lambda x: int(x))) 
                          for id_val, simhash_val in simhash_data]
                
                self.simhash_index = SimhashIndex(objects, k=self.similarity_threshold)
                
                self.logger.debug(f"Rebuilt SimHash index with {len(objects)} records")
            else:
                self.simhash_index = None
                
        except Exception as e:
            self.logger.warning(f"Failed to rebuild SimHash index: {e}")
            self.simhash_index = None
    
    def get_recent_records(self, days: int = 7, limit: int = 100) -> List[ContentRecord]:
        """
        Get recent content records.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of records to return
            
        Returns:
            List of ContentRecord objects
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        records = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT title, simhash_value, timestamp, category, angle, source
                    FROM content_simhash
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (cutoff_date, limit))
                
                for row in cursor.fetchall():
                    title, simhash_value, timestamp, category, angle, source = row
                    
                    records.append(ContentRecord(
                        title=title,
                        simhash_value=simhash_value,
                        timestamp=datetime.fromisoformat(timestamp),
                        category=category,
                        angle=angle,
                        source=source
                    ))
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent records: {e}")
            
        return records
    
    def cleanup_old_records(self, days: int = 30):
        """
        Remove records older than specified days.
        
        Args:
            days: Number of days to retain
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM content_simhash WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old SimHash records")
                # Rebuild index after cleanup
                self._rebuild_index()
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old SimHash records: {e}")
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {
            'total_records': 0,
            'last_7_days': 0,
            'last_30_days': 0,
            'avg_hamming_distance': 0.0,
            'index_size': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total records
                cursor = conn.execute("SELECT COUNT(*) FROM content_simhash")
                stats['total_records'] = cursor.fetchone()[0]
                
                # Recent records
                cutoff_7d = (datetime.now() - timedelta(days=7)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM content_simhash WHERE timestamp >= ?
                """, (cutoff_7d,))
                stats['last_7_days'] = cursor.fetchone()[0]
                
                cutoff_30d = (datetime.now() - timedelta(days=30)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM content_simhash WHERE timestamp >= ?
                """, (cutoff_30d,))
                stats['last_30_days'] = cursor.fetchone()[0]
                
                # Index information
                if self.simhash_index:
                    stats['index_size'] = len(self.simhash_index.bucket)
                    
        except Exception as e:
            self.logger.error(f"Failed to get SimHash statistics: {e}")
            
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test SimHash detector
    detector = SimHashDetector("test_simhash.db")
    
    # Test content addition
    detector.add_content_record(
        "Smart Plug Alexa Compatible WiFi Buyer's Guide", 
        "smart_plugs", "buyers_guide", "generated"
    )
    
    detector.add_content_record(
        "Best Robot Vacuum for Pet Hair 2025 Reviews",
        "robot_vacuums", "reviews", "generated"  
    )
    
    # Test similarity detection
    is_similar, similarity, similar_title = detector.check_similarity(
        "Smart Plug Alexa WiFi Setup Guide"
    )
    
    print(f"Similarity check: {is_similar}, ratio: {similarity:.3f}")
    if similar_title:
        print(f"Most similar: {similar_title}")
    
    # Get statistics
    stats = detector.get_statistics()
    print(f"SimHash stats: {stats}")