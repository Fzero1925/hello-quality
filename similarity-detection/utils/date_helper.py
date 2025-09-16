#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Date Helper Utilities

Provides date and time utilities for similarity detection system.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple


class DateHelper:
    """
    Handles date and time operations for similarity detection.
    """

    def __init__(self):
        """Initialize date helper."""
        # Common date formats for parsing
        self.date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%Y%m%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M',
            '%d %B %Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]

    def parse_date_from_string(self, date_string: str) -> Optional[datetime]:
        """
        Parse date from various string formats.

        Args:
            date_string: Date string to parse

        Returns:
            Parsed datetime or None if parsing fails
        """
        if not date_string:
            return None

        date_string = date_string.strip()

        # Try each format
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        # Try ISO format parsing
        try:
            return datetime.fromisoformat(date_string)
        except ValueError:
            pass

        return None

    def extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract date from filename using common patterns.

        Args:
            filename: Filename to parse

        Returns:
            Extracted datetime or None if not found
        """
        # Pattern 1: YYYYMMDD
        pattern1 = re.search(r'(\d{8})', filename)
        if pattern1:
            try:
                date_str = pattern1.group(1)
                return datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass

        # Pattern 2: YYYY-MM-DD
        pattern2 = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if pattern2:
            try:
                date_str = pattern2.group(1)
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass

        # Pattern 3: YYYY_MM_DD
        pattern3 = re.search(r'(\d{4}_\d{2}_\d{2})', filename)
        if pattern3:
            try:
                date_str = pattern3.group(1)
                return datetime.strptime(date_str, '%Y_%m_%d')
            except ValueError:
                pass

        # Pattern 4: DDMMYYYY
        pattern4 = re.search(r'(\d{2}\d{2}\d{4})', filename)
        if pattern4:
            try:
                date_str = pattern4.group(1)
                return datetime.strptime(date_str, '%d%m%Y')
            except ValueError:
                pass

        return None

    def get_effective_date(self, article_info: Dict) -> datetime:
        """
        Get the most appropriate date for an article.

        Priority: filename date > front_matter date > created_time > modified_time

        Args:
            article_info: Article information dictionary

        Returns:
            Effective date
        """
        # Try filename date
        if 'file_name' in article_info:
            filename_date = self.extract_date_from_filename(article_info['file_name'])
            if filename_date:
                return filename_date

        # Try front matter date
        if 'front_matter' in article_info and article_info['front_matter']:
            front_matter = article_info['front_matter']

            # Check common date fields in front matter
            date_fields = ['date', 'created', 'published', 'publish_date']
            for field in date_fields:
                if field in front_matter:
                    date_value = front_matter[field]
                    if isinstance(date_value, str):
                        parsed_date = self.parse_date_from_string(date_value)
                        if parsed_date:
                            return parsed_date
                    elif isinstance(date_value, datetime):
                        return date_value

        # Try created time
        if 'created_time' in article_info and article_info['created_time']:
            return article_info['created_time']

        # Fall back to modified time
        if 'modified_time' in article_info and article_info['modified_time']:
            return article_info['modified_time']

        # Ultimate fallback
        return datetime.now()

    def is_within_time_window(self, date1: datetime, date2: datetime,
                             window_days: int) -> bool:
        """
        Check if two dates are within a specified time window.

        Args:
            date1: First date
            date2: Second date
            window_days: Time window in days

        Returns:
            True if dates are within the window
        """
        time_diff = abs((date1 - date2).days)
        return time_diff <= window_days

    def get_time_diff_in_days(self, date1: datetime, date2: datetime) -> int:
        """
        Get time difference between two dates in days.

        Args:
            date1: First date
            date2: Second date

        Returns:
            Time difference in days (absolute value)
        """
        return abs((date1 - date2).days)

    def format_date_for_display(self, date: datetime, format_type: str = 'default') -> str:
        """
        Format date for display purposes.

        Args:
            date: Date to format
            format_type: Format type ('default', 'short', 'long', 'iso')

        Returns:
            Formatted date string
        """
        if format_type == 'short':
            return date.strftime('%Y-%m-%d')
        elif format_type == 'long':
            return date.strftime('%B %d, %Y')
        elif format_type == 'iso':
            return date.isoformat()
        else:  # default
            return date.strftime('%Y-%m-%d %H:%M')

    def get_date_range_stats(self, dates: List[datetime]) -> Dict[str, any]:
        """
        Calculate statistics for a list of dates.

        Args:
            dates: List of datetime objects

        Returns:
            Dictionary with date range statistics
        """
        if not dates:
            return {
                'earliest': None,
                'latest': None,
                'span_days': 0,
                'count': 0
            }

        sorted_dates = sorted(dates)
        earliest = sorted_dates[0]
        latest = sorted_dates[-1]
        span_days = (latest - earliest).days

        return {
            'earliest': earliest,
            'latest': latest,
            'span_days': span_days,
            'count': len(dates)
        }

    def group_articles_by_date_range(self, articles: List[Dict],
                                   range_days: int = 7) -> Dict[str, List[Dict]]:
        """
        Group articles by date ranges.

        Args:
            articles: List of article information dictionaries
            range_days: Size of each date range in days

        Returns:
            Dictionary mapping date range strings to article lists
        """
        groups = {}

        for article in articles:
            article_date = self.get_effective_date(article)

            # Calculate range start date
            days_since_epoch = (article_date - datetime(1970, 1, 1)).days
            range_start_days = (days_since_epoch // range_days) * range_days
            range_start = datetime(1970, 1, 1) + timedelta(days=range_start_days)
            range_end = range_start + timedelta(days=range_days - 1)

            # Create range key
            range_key = f"{range_start.strftime('%Y-%m-%d')}_to_{range_end.strftime('%Y-%m-%d')}"

            if range_key not in groups:
                groups[range_key] = []
            groups[range_key].append(article)

        return groups

    def calculate_publication_frequency(self, articles: List[Dict]) -> Dict[str, float]:
        """
        Calculate publication frequency statistics.

        Args:
            articles: List of article information dictionaries

        Returns:
            Dictionary with frequency statistics
        """
        if len(articles) < 2:
            return {
                'articles_per_day': 0.0,
                'articles_per_week': 0.0,
                'articles_per_month': 0.0,
                'avg_days_between_articles': 0.0
            }

        # Get all dates
        dates = [self.get_effective_date(article) for article in articles]
        dates.sort()

        # Calculate time span
        time_span = dates[-1] - dates[0]
        span_days = max(1, time_span.days)

        # Calculate frequencies
        articles_per_day = len(articles) / span_days
        articles_per_week = articles_per_day * 7
        articles_per_month = articles_per_day * 30

        # Calculate average time between articles
        time_diffs = []
        for i in range(1, len(dates)):
            diff_days = (dates[i] - dates[i-1]).days
            time_diffs.append(diff_days)

        avg_days_between = sum(time_diffs) / len(time_diffs) if time_diffs else 0

        return {
            'articles_per_day': articles_per_day,
            'articles_per_week': articles_per_week,
            'articles_per_month': articles_per_month,
            'avg_days_between_articles': avg_days_between
        }

    def is_recent(self, date: datetime, days_threshold: int = 30) -> bool:
        """
        Check if a date is considered recent.

        Args:
            date: Date to check
            days_threshold: Threshold in days for considering "recent"

        Returns:
            True if date is recent
        """
        now = datetime.now()
        time_diff = (now - date).days
        return time_diff <= days_threshold

    def get_age_category(self, date: datetime) -> str:
        """
        Categorize article age.

        Args:
            date: Article date

        Returns:
            Age category string
        """
        now = datetime.now()
        days_old = (now - date).days

        if days_old <= 7:
            return 'very_recent'
        elif days_old <= 30:
            return 'recent'
        elif days_old <= 90:
            return 'moderate'
        elif days_old <= 365:
            return 'old'
        else:
            return 'very_old'