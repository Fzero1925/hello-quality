"""
Comprehensive Keyword Deduplicator combining stem database, SimHash detection, and angle changing.
Prevents repetitive content generation through multi-layer deduplication strategy.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

from .stem_database import StemDatabase
from .simhash_detector import SimHashDetector  
from .angle_changer import AngleChanger, AngleType

@dataclass  
class DeduplicationResult:
    """Result of keyword deduplication analysis"""
    original_keyword: str
    processed_keyword: str
    is_duplicate: bool
    similarity_score: float
    angle_changed: bool
    angle_type: Optional[str]
    reason: str
    sources: List[str]
    freshness_score: float
    monetization_score: float
    novelty_penalty: float
    action_taken: str

class KeywordDeduplicator:
    """
    Comprehensive keyword deduplication system.
    
    Combines multiple detection methods:
    1. Stem-based overlap detection (30-day window)
    2. SimHash similarity detection (7-day window)  
    3. Automatic angle changing for similar content
    4. Novelty scoring and penalty system
    """
    
    def __init__(self, 
                 stem_db_path: str = "data/keyword_stems.db",
                 simhash_db_path: str = "data/content_simhash.db",
                 output_csv: str = "data/deduplication_log.csv"):
        """
        Initialize the keyword deduplicator.
        
        Args:
            stem_db_path: Path to stem database
            simhash_db_path: Path to SimHash database  
            output_csv: Path to CSV output file
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.stem_db = StemDatabase(stem_db_path)
        self.simhash_detector = SimHashDetector(simhash_db_path)
        self.angle_changer = AngleChanger()
        
        # Configuration
        self.output_csv = output_csv
        self.stem_overlap_threshold = 0.7  # 70% stem overlap = duplicate
        self.simhash_similarity_threshold = 0.85  # 85% similarity = duplicate
        self.stem_check_days = 30  # Check stems for last 30 days
        self.simhash_check_days = 7   # Check SimHash for last 7 days
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(output_csv):
            self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers"""
        headers = [
            'timestamp', 'original_keyword', 'processed_keyword', 'is_duplicate',
            'similarity_score', 'angle_changed', 'angle_type', 'reason', 
            'sources', 'freshness_score', 'monetization_score', 'novelty_penalty',
            'action_taken'
        ]
        
        try:
            with open(self.output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
            self.logger.info(f"Initialized CSV log: {self.output_csv}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize CSV file: {e}")
    
    def process_keyword(self, keyword: str, category: str = "smart_home",
                       source: str = "generated", 
                       monetization_score: float = 0.5) -> DeduplicationResult:
        """
        Process a keyword through the complete deduplication pipeline.
        
        Args:
            keyword: Keyword to process
            category: Product category
            source: Source of the keyword
            monetization_score: Commercial value score (0-1)
            
        Returns:
            DeduplicationResult object
        """
        original_keyword = keyword.strip()
        processed_keyword = original_keyword
        
        # Initialize result
        result = DeduplicationResult(
            original_keyword=original_keyword,
            processed_keyword=processed_keyword,
            is_duplicate=False,
            similarity_score=0.0,
            angle_changed=False,
            angle_type=None,
            reason="Initial processing",
            sources=[source],
            freshness_score=1.0,  # Start with max freshness
            monetization_score=monetization_score,
            novelty_penalty=0.0,
            action_taken="none"
        )
        
        try:
            # Step 1: Check stem overlap (30-day window)
            stem_duplicate, stem_overlap = self.stem_db.check_stem_overlap(
                original_keyword, 
                self.stem_overlap_threshold, 
                self.stem_check_days
            )
            
            # Step 2: Check SimHash similarity (7-day window)  
            simhash_duplicate, simhash_similarity, similar_title = self.simhash_detector.check_similarity(
                original_keyword,
                self.simhash_similarity_threshold,
                self.simhash_check_days
            )
            
            # Determine if duplicate
            is_duplicate = stem_duplicate or simhash_duplicate
            max_similarity = max(stem_overlap, simhash_similarity)
            
            # Update result
            result.is_duplicate = is_duplicate
            result.similarity_score = max_similarity
            
            # Calculate freshness score (inverse of similarity)
            result.freshness_score = max(0.0, 1.0 - max_similarity)
            
            if is_duplicate:
                # Step 3: Force angle change
                angle_result = self._apply_angle_change(original_keyword, category)
                
                if angle_result:
                    result.processed_keyword = angle_result['new_keyword']
                    result.angle_changed = True  
                    result.angle_type = angle_result['angle_type']
                    result.novelty_penalty = angle_result.get('novelty_penalty', 0.2)
                    result.action_taken = "angle_changed"
                    
                    # Build comprehensive reason
                    reasons = []
                    if stem_duplicate:
                        reasons.append(f"stem overlap {stem_overlap:.2f}")
                    if simhash_duplicate:
                        reasons.append(f"SimHash similarity {simhash_similarity:.2f}")
                    
                    result.reason = f"Duplicate detected ({', '.join(reasons)}). " + \
                                   f"Applied {angle_result['angle_type']} angle: {angle_result['modifier']}"
                else:
                    result.action_taken = "duplicate_rejected"
                    result.reason = f"Duplicate detected but angle change failed. " + \
                                   f"Stem overlap: {stem_overlap:.2f}, SimHash: {simhash_similarity:.2f}"
            else:
                result.action_taken = "accepted_original"
                result.reason = f"No duplicate detected. Stem overlap: {stem_overlap:.2f}, " + \
                               f"SimHash similarity: {simhash_similarity:.2f}"
            
            # Step 4: Record the processed keyword
            if result.processed_keyword != original_keyword or not is_duplicate:
                self._record_keyword(result, category, source)
            
            # Step 5: Log to CSV
            self._log_to_csv(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing keyword '{keyword}': {e}")
            result.reason = f"Processing error: {str(e)}"
            result.action_taken = "error"
            return result
    
    def _apply_angle_change(self, keyword: str, category: str) -> Optional[Dict]:
        """Apply angle change to avoid duplication"""
        try:
            # Get recent angles used for this category
            recent_records = self.stem_db.get_recent_keywords(7, category)
            recent_angles = [record.angle for record in recent_records]
            
            # Force angle change
            angle_result = self.angle_changer.force_angle_change(
                keyword, 
                recent_angles
            )
            
            return angle_result
            
        except Exception as e:
            self.logger.error(f"Failed to apply angle change for '{keyword}': {e}")
            return None
    
    def _record_keyword(self, result: DeduplicationResult, category: str, source: str):
        """Record the processed keyword in databases"""
        try:
            # Determine angle for recording
            angle = result.angle_type if result.angle_changed else "general"
            
            # Record in stem database
            self.stem_db.add_keyword_record(
                result.processed_keyword, 
                angle, 
                category, 
                source
            )
            
            # Record in SimHash database (for title similarity)  
            title = f"{result.processed_keyword} buyer's guide"  # Simulate title
            self.simhash_detector.add_content_record(
                title,
                category,
                angle,
                source
            )
            
        except Exception as e:
            self.logger.error(f"Failed to record keyword '{result.processed_keyword}': {e}")
    
    def _log_to_csv(self, result: DeduplicationResult):
        """Log result to CSV file"""
        try:
            row = [
                datetime.now().isoformat(),
                result.original_keyword,
                result.processed_keyword,
                result.is_duplicate,
                f"{result.similarity_score:.3f}",
                result.angle_changed,
                result.angle_type or "",
                result.reason,
                "|".join(result.sources),
                f"{result.freshness_score:.3f}",
                f"{result.monetization_score:.3f}",
                f"{result.novelty_penalty:.3f}",
                result.action_taken
            ]
            
            with open(self.output_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
                
        except Exception as e:
            self.logger.error(f"Failed to log to CSV: {e}")
    
    def batch_process_keywords(self, keywords: List[Dict]) -> List[DeduplicationResult]:
        """
        Process multiple keywords in batch.
        
        Args:
            keywords: List of keyword dictionaries with keys: 'keyword', 'category', 'source', 'score'
            
        Returns:
            List of DeduplicationResult objects
        """
        results = []
        
        for kw_data in keywords:
            keyword = kw_data.get('keyword', '')
            category = kw_data.get('category', 'smart_home')
            source = kw_data.get('source', 'generated')
            score = kw_data.get('monetization_score', 0.5)
            
            if keyword.strip():
                result = self.process_keyword(keyword, category, source, score)
                results.append(result)
        
        return results
    
    def get_recent_activity(self, days: int = 7) -> Dict:
        """
        Get recent deduplication activity summary.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Activity summary dictionary
        """
        try:
            # Get stem database stats
            stem_stats = self.stem_db.get_statistics()
            
            # Get SimHash stats
            simhash_stats = self.simhash_detector.get_statistics()
            
            # Get angle changer stats
            angle_stats = self.angle_changer.get_angle_statistics()
            
            # Analyze CSV log for recent activity
            csv_stats = self._analyze_csv_activity(days)
            
            activity = {
                'timeframe_days': days,
                'stem_database': {
                    'total_records': stem_stats['total_records'],
                    'last_7_days': stem_stats['last_7_days'],
                    'last_30_days': stem_stats['last_30_days']
                },
                'simhash_database': {
                    'total_records': simhash_stats['total_records'],
                    'last_7_days': simhash_stats['last_7_days'],
                    'index_size': simhash_stats['index_size']
                },
                'angle_changer': {
                    'available_angle_types': angle_stats['total_angle_types'],
                    'total_variations': angle_stats['total_variations']
                },
                'recent_processing': csv_stats
            }
            
            return activity
            
        except Exception as e:
            self.logger.error(f"Failed to get recent activity: {e}")
            return {'error': str(e)}
    
    def _analyze_csv_activity(self, days: int) -> Dict:
        """Analyze recent CSV activity"""
        stats = {
            'total_processed': 0,
            'duplicates_found': 0,
            'angles_changed': 0,
            'avg_similarity': 0.0,
            'avg_freshness': 0.0
        }
        
        if not os.path.exists(self.output_csv):
            return stats
        
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
            
            similarities = []
            freshness_scores = []
            
            with open(self.output_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        timestamp = datetime.fromisoformat(row['timestamp']).timestamp()
                        
                        if timestamp >= cutoff_date:
                            stats['total_processed'] += 1
                            
                            if row['is_duplicate'].lower() == 'true':
                                stats['duplicates_found'] += 1
                                
                            if row['angle_changed'].lower() == 'true':
                                stats['angles_changed'] += 1
                                
                            similarities.append(float(row['similarity_score']))
                            freshness_scores.append(float(row['freshness_score']))
                            
                    except (ValueError, KeyError):
                        continue
            
            if similarities:
                stats['avg_similarity'] = sum(similarities) / len(similarities)
                
            if freshness_scores:
                stats['avg_freshness'] = sum(freshness_scores) / len(freshness_scores)
                
        except Exception as e:
            self.logger.error(f"Failed to analyze CSV activity: {e}")
            
        return stats
    
    def cleanup_databases(self, days: int = 30):
        """Clean up old records from both databases"""
        try:
            self.stem_db.cleanup_old_records(days)
            self.simhash_detector.cleanup_old_records(days)
            self.logger.info(f"Cleaned up records older than {days} days")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup databases: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test keyword deduplicator
    deduplicator = KeywordDeduplicator("test_stems.db", "test_simhash.db", "test_dedup.csv")
    
    # Test single keyword processing
    result = deduplicator.process_keyword(
        "smart plug alexa compatible", 
        "smart_plugs", 
        "reddit",
        0.85
    )
    
    print(f"Processing result:")
    print(f"Original: {result.original_keyword}")
    print(f"Processed: {result.processed_keyword}")
    print(f"Is duplicate: {result.is_duplicate}")
    print(f"Similarity: {result.similarity_score:.3f}")
    print(f"Angle changed: {result.angle_changed}")
    print(f"Reason: {result.reason}")
    
    # Test batch processing
    test_keywords = [
        {'keyword': 'smart plug wifi energy monitoring', 'category': 'smart_plugs', 'source': 'youtube', 'monetization_score': 0.9},
        {'keyword': 'robot vacuum pet hair removal', 'category': 'robot_vacuums', 'source': 'amazon', 'monetization_score': 0.8},
        {'keyword': 'alexa smart plug setup guide', 'category': 'smart_plugs', 'source': 'google', 'monetization_score': 0.7}
    ]
    
    batch_results = deduplicator.batch_process_keywords(test_keywords)
    
    print(f"\\nBatch processing results: {len(batch_results)} keywords processed")
    
    # Get activity summary
    activity = deduplicator.get_recent_activity(7)
    print(f"\\nRecent activity: {activity}")