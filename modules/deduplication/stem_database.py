"""
30-day Stem Database for keyword deduplication.
Maintains a rolling window of keyword stems to prevent repetitive content generation.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dataclasses import dataclass
import nltk
from nltk.stem import PorterStemmer
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

@dataclass
class KeywordRecord:
    """Record for stored keywords with metadata"""
    keyword: str
    stems: List[str]
    angle: str
    timestamp: datetime
    category: str
    source: str

class StemDatabase:
    """
    Manages a 30-day rolling database of keyword stems for deduplication.
    Uses SQLite for persistence and Porter Stemmer for stem extraction.
    """
    
    def __init__(self, db_path: str = "data/keyword_stems.db"):
        self.db_path = db_path
        self.stemmer = PorterStemmer()
        self.logger = logging.getLogger(__name__)
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS keyword_stems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    stems_json TEXT NOT NULL,
                    angle TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON keyword_stems(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_stems 
                ON keyword_stems(stems_json)
            """)
            
    def extract_stems(self, text: str) -> List[str]:
        """
        Extract word stems from text using Porter Stemmer.
        
        Args:
            text: Input text to extract stems from
            
        Returns:
            List of unique stems
        """
        if not text:
            return []
            
        # Tokenize and clean
        tokens = nltk.word_tokenize(text.lower())
        
        # Filter out non-alphabetic tokens and short words
        words = [token for token in tokens if token.isalpha() and len(token) > 2]
        
        # Extract stems
        stems = [self.stemmer.stem(word) for word in words]
        
        # Return unique stems, maintaining order
        seen = set()
        unique_stems = []
        for stem in stems:
            if stem not in seen:
                seen.add(stem)
                unique_stems.append(stem)
                
        return unique_stems
    
    def add_keyword_record(self, keyword: str, angle: str = "general", 
                          category: str = "smart_home", source: str = "generated") -> bool:
        """
        Add a keyword record to the database.
        
        Args:
            keyword: The keyword to add
            angle: Content angle (e.g., "buyers_guide", "price_comparison")
            category: Product category
            source: Source of the keyword
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            stems = self.extract_stems(keyword)
            timestamp = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO keyword_stems 
                    (keyword, stems_json, angle, timestamp, category, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    keyword,
                    json.dumps(stems),
                    angle,
                    timestamp,
                    category,
                    source
                ))
                
            self.logger.info(f"Added keyword record: {keyword} with {len(stems)} stems")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add keyword record {keyword}: {e}")
            return False
    
    def get_recent_stems(self, days: int = 30) -> Set[str]:
        """
        Get all unique stems from the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Set of unique stems
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        all_stems = set()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT stems_json FROM keyword_stems 
                    WHERE timestamp >= ?
                """, (cutoff_date,))
                
                for (stems_json,) in cursor.fetchall():
                    stems = json.loads(stems_json)
                    all_stems.update(stems)
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent stems: {e}")
            
        return all_stems
    
    def check_stem_overlap(self, keyword: str, overlap_threshold: float = 0.7, 
                          days: int = 30) -> tuple[bool, float]:
        """
        Check if a keyword has significant stem overlap with recent keywords.
        
        Args:
            keyword: Keyword to check
            overlap_threshold: Threshold for considering overlap significant (0-1)
            days: Number of days to check against
            
        Returns:
            Tuple of (has_significant_overlap, overlap_ratio)
        """
        keyword_stems = set(self.extract_stems(keyword))
        if not keyword_stems:
            return False, 0.0
            
        recent_stems = self.get_recent_stems(days)
        
        if not recent_stems:
            return False, 0.0
            
        # Calculate overlap ratio
        overlap_stems = keyword_stems.intersection(recent_stems)
        overlap_ratio = len(overlap_stems) / len(keyword_stems)
        
        has_overlap = overlap_ratio >= overlap_threshold
        
        self.logger.debug(f"Keyword '{keyword}' stem overlap: {overlap_ratio:.2f} "
                         f"({'SIGNIFICANT' if has_overlap else 'acceptable'})")
        
        return has_overlap, overlap_ratio
    
    def get_recent_keywords(self, days: int = 7, category: str = None) -> List[KeywordRecord]:
        """
        Get recent keyword records.
        
        Args:
            days: Number of days to look back
            category: Optional category filter
            
        Returns:
            List of KeywordRecord objects
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        records = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if category:
                    cursor = conn.execute("""
                        SELECT keyword, stems_json, angle, timestamp, category, source
                        FROM keyword_stems 
                        WHERE timestamp >= ? AND category = ?
                        ORDER BY timestamp DESC
                    """, (cutoff_date, category))
                else:
                    cursor = conn.execute("""
                        SELECT keyword, stems_json, angle, timestamp, category, source
                        FROM keyword_stems 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (cutoff_date,))
                
                for row in cursor.fetchall():
                    keyword, stems_json, angle, timestamp, category, source = row
                    stems = json.loads(stems_json)
                    
                    records.append(KeywordRecord(
                        keyword=keyword,
                        stems=stems,
                        angle=angle,
                        timestamp=datetime.fromisoformat(timestamp),
                        category=category,
                        source=source
                    ))
                    
        except Exception as e:
            self.logger.error(f"Failed to get recent keywords: {e}")
            
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
                    DELETE FROM keyword_stems WHERE timestamp < ?
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old keyword records")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database stats
        """
        stats = {
            'total_records': 0,
            'last_7_days': 0,
            'last_30_days': 0,
            'unique_categories': 0,
            'unique_angles': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total records
                cursor = conn.execute("SELECT COUNT(*) FROM keyword_stems")
                stats['total_records'] = cursor.fetchone()[0]
                
                # Last 7 days
                cutoff_7d = (datetime.now() - timedelta(days=7)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM keyword_stems WHERE timestamp >= ?
                """, (cutoff_7d,))
                stats['last_7_days'] = cursor.fetchone()[0]
                
                # Last 30 days
                cutoff_30d = (datetime.now() - timedelta(days=30)).isoformat()
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM keyword_stems WHERE timestamp >= ?
                """, (cutoff_30d,))
                stats['last_30_days'] = cursor.fetchone()[0]
                
                # Unique categories
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT category) FROM keyword_stems
                """)
                stats['unique_categories'] = cursor.fetchone()[0]
                
                # Unique angles
                cursor = conn.execute("""
                    SELECT COUNT(DISTINCT angle) FROM keyword_stems
                """)
                stats['unique_angles'] = cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the stem database
    db = StemDatabase("test_stems.db")
    
    # Test stem extraction
    test_text = "smart plug alexa compatible wifi"
    stems = db.extract_stems(test_text)
    print(f"Stems for '{test_text}': {stems}")
    
    # Test adding records
    db.add_keyword_record("smart plug alexa", "buyers_guide", "smart_plugs", "reddit")
    db.add_keyword_record("robot vacuum pet hair", "reviews", "robot_vacuums", "youtube")
    
    # Test overlap checking
    has_overlap, ratio = db.check_stem_overlap("alexa smart plug wifi")
    print(f"Overlap check: {has_overlap}, ratio: {ratio:.2f}")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Database stats: {stats}")