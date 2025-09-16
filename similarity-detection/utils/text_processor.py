#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text Processor Utilities

Provides text processing utilities for content analysis and similarity detection.
"""

import re
import yaml
from typing import Dict, List, Tuple, Optional, Set


class TextProcessor:
    """
    Handles text processing operations for similarity detection.
    """

    def __init__(self):
        """Initialize text processor."""
        # Common stop words for better text processing
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
            'have', 'had', 'what', 'said', 'each', 'which', 'their', 'time',
            'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some',
            'her', 'would', 'make', 'like', 'into', 'him', 'two', 'more',
            'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call',
            'who', 'its', 'now', 'find', 'long', 'down', 'day', 'did', 'get',
            'come', 'made', 'may', 'part'
        }

    def normalize_text(self, text: str, remove_stop_words: bool = False) -> str:
        """
        Normalize text for analysis.

        Args:
            text: Input text
            remove_stop_words: Whether to remove stop words

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove Markdown formatting
        text = self.remove_markdown_formatting(text)

        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove punctuation (except hyphens in words)
        text = re.sub(r'[^\w\s-]', ' ', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove stop words if requested
        if remove_stop_words:
            text = self.remove_stop_words(text)

        return text.strip()

    def remove_markdown_formatting(self, text: str) -> str:
        """
        Remove Markdown formatting from text.

        Args:
            text: Text with Markdown formatting

        Returns:
            Plain text
        """
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Remove emphasis (bold, italic)
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
        text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)

        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)

        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove blockquotes
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # Remove list markers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # Remove horizontal rules
        text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)

        # Remove table formatting
        text = re.sub(r'\|', ' ', text)

        return text

    def remove_stop_words(self, text: str) -> str:
        """
        Remove stop words from text.

        Args:
            text: Input text

        Returns:
            Text with stop words removed
        """
        words = text.split()
        filtered_words = [word for word in words if word.lower() not in self.stop_words]
        return ' '.join(filtered_words)

    def extract_front_matter(self, content: str) -> Tuple[Dict, str]:
        """
        Extract YAML front matter from content.

        Args:
            content: Full content with potential front matter

        Returns:
            Tuple of (front_matter_dict, main_content)
        """
        if not content.strip().startswith('---'):
            return {}, content

        lines = content.split('\n')
        end_index = -1

        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_index = i
                break

        if end_index == -1:
            return {}, content

        front_matter_text = '\n'.join(lines[1:end_index])
        main_content = '\n'.join(lines[end_index + 1:])

        try:
            front_matter_dict = yaml.safe_load(front_matter_text) or {}
        except yaml.YAMLError:
            front_matter_dict = {}

        return front_matter_dict, main_content

    def extract_keywords(self, text: str, min_length: int = 3,
                        max_keywords: int = 50) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text
            min_length: Minimum keyword length
            max_keywords: Maximum number of keywords to return

        Returns:
            List of keywords sorted by frequency
        """
        # Normalize text
        normalized = self.normalize_text(text, remove_stop_words=True)

        # Extract words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', normalized)

        # Count word frequencies
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, freq in sorted_keywords[:max_keywords]]

    def calculate_readability_score(self, text: str) -> Dict[str, float]:
        """
        Calculate readability scores for text.

        Args:
            text: Input text

        Returns:
            Dictionary with readability metrics
        """
        # Basic text statistics
        sentences = self._count_sentences(text)
        words = len(text.split())
        syllables = self._count_syllables(text)

        if sentences == 0 or words == 0:
            return {
                'flesch_reading_ease': 0.0,
                'flesch_kincaid_grade': 0.0,
                'avg_sentence_length': 0.0,
                'avg_syllables_per_word': 0.0
            }

        # Calculate averages
        avg_sentence_length = words / sentences
        avg_syllables_per_word = syllables / words

        # Flesch Reading Ease Score
        flesch_reading_ease = (206.835 -
                              (1.015 * avg_sentence_length) -
                              (84.6 * avg_syllables_per_word))

        # Flesch-Kincaid Grade Level
        flesch_kincaid_grade = (0.39 * avg_sentence_length +
                               11.8 * avg_syllables_per_word - 15.59)

        return {
            'flesch_reading_ease': max(0.0, min(100.0, flesch_reading_ease)),
            'flesch_kincaid_grade': max(0.0, flesch_kincaid_grade),
            'avg_sentence_length': avg_sentence_length,
            'avg_syllables_per_word': avg_syllables_per_word
        }

    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Simple sentence counting based on punctuation
        sentence_endings = re.findall(r'[.!?]+', text)
        return len(sentence_endings)

    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count in text."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        total_syllables = 0

        for word in words:
            syllables = self._syllables_in_word(word)
            total_syllables += syllables

        return total_syllables

    def _syllables_in_word(self, word: str) -> int:
        """Estimate syllables in a single word."""
        if len(word) <= 1:
            return 1

        # Count vowel groups
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel

        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1

        # Ensure at least 1 syllable
        return max(1, syllable_count)

    def generate_text_fingerprint(self, text: str) -> str:
        """
        Generate a fingerprint for text content.

        Args:
            text: Input text

        Returns:
            Text fingerprint string
        """
        import hashlib

        # Normalize text heavily for fingerprinting
        normalized = self.normalize_text(text, remove_stop_words=True)

        # Remove excessive whitespace and sort words
        words = sorted(set(normalized.split()))
        fingerprint_text = ' '.join(words)

        # Generate hash
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def calculate_text_similarity_simple(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using Jaccard index.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize texts
        norm1 = self.normalize_text(text1, remove_stop_words=True)
        norm2 = self.normalize_text(text2, remove_stop_words=True)

        # Create word sets
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def extract_headings(self, text: str) -> List[Dict[str, any]]:
        """
        Extract headings from Markdown text.

        Args:
            text: Markdown text

        Returns:
            List of heading dictionaries with level and content
        """
        headings = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Match Markdown headings
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                content = heading_match.group(2).strip()
                headings.append({
                    'level': level,
                    'content': content,
                    'line_number': line_num
                })

        return headings