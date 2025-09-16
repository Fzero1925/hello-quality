#!/usr/bin/env python3
"""
Content Quality Check Script v2 Enhanced
Comprehensive quality validation with 15-item validation system
Integrated with Smart Image Manager and YAML configuration
"""

import os
import sys
import argparse
import re
import codecs
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

# 导入自动修复器
try:
    from auto_quality_fixer import AutoQualityFixer
    AUTO_FIXER_AVAILABLE = True
except ImportError as e:
    AUTO_FIXER_AVAILABLE = False
    print(f"⚠️ AutoQualityFixer not available: {e}")

# 解决Windows编码问题
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ComprehensiveQualityChecker:
    """v3 Hybrid Quality Checker: v2 Enhanced + PQS v3 Hard Gates"""
    
    def __init__(self, config_path: Optional[str] = None, pqs_mode: bool = False):
        """Initialize with configuration
        Args:
            config_path: Path to configuration file
            pqs_mode: Enable PQS v3 strict mode (85+ score required)
        """
        self.config = self._load_config(config_path)
        self.quality_rules = self.config.get('quality_rules', {})
        self.seo_config = self.config.get('seo', {})
        self.pqs_mode = pqs_mode
        
        # Load PQS v3 config if available
        self.pqs_config = self._load_pqs_config()
        
        mode_desc = "PQS v3 Hard Gates + v2 Enhanced" if pqs_mode else "v2 Enhanced"
        print(f"✅ Quality checker initialized ({mode_desc}) with {len(self.quality_rules)} validation rules")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration file"""
        if not config_path:
            config_path = project_root / 'image_config.yml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            print(f"⚠️ Failed to load config, using defaults: {e}")
            return self._get_default_quality_rules()
    
    def _load_pqs_config(self) -> Dict:
        """Load PQS v3 configuration"""
        pqs_config_path = project_root / 'config' / 'pqs_config.yml'
        try:
            if pqs_config_path.exists():
                with open(pqs_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    print(f"📋 PQS v3 config loaded: {config.get('thresholds', {}).get('publish_score', 85)} score threshold")
                    return config
        except Exception as e:
            print(f"⚠️ Failed to load PQS v3 config: {e}")
        
        # Default PQS v3 config
        return {
            'thresholds': {
                'publish_score': 85,
                'keyword_density_max': 0.025,
                'min_inline_images': 2
            },
            'entities_tokens': {
                'generic': ["matter","thread","zigbee","local control","watt","2.4g","hub"],
                'smart-plugs': ["smart plug","energy","monitor","kwh","standby"],
                'smart-cameras': ["rtsp","onvif","privacy shutter","fps"]
            }
        }
    
    def _get_default_quality_rules(self) -> Dict:
        """Default quality rules - 15-item validation system"""
        return {
            'quality_rules': {
                'min_images': 3,
                'require_featured': True,
                'ban_words_in_alt': True,
                'min_internal_links': 3,
                'min_external_links': 2,
                'require_disclosure': True,
                'require_schema': True,
                'require_author_and_date': True,
                'max_duplicate_usage': 3,
                'min_image_relevance_score': 0.6,
                'min_word_count': 1500,
                'max_word_count': 4000,
                'min_sections': 5,
                'require_faq': True,
                'require_conclusion': True
            },
            'seo': {
                'banned_alt_words': ['best', '2025', 'cheap', 'lowest price', 'amazing', 'incredible'],
                'max_alt_length': 125,
                'min_alt_length': 15
            }
        }
    
    def check_article_quality(self, filepath: str) -> Dict[str, Any]:
        """Comprehensive 15-item quality validation"""
        issues = []
        warnings = []
        metadata = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract front matter and content
            front_matter, article_content = self._extract_front_matter(content)
            
            # Run all 16 validation checks (added enhanced forbidden phrases)
            validations = [
                self._check_word_count(article_content),
                self._check_images(article_content),
                self._check_featured_image(article_content),
                self._check_alt_text_compliance(article_content),
                self._check_internal_links(article_content),
                self._check_external_links(article_content),
                self._check_affiliate_disclosure(article_content),
                self._check_schema_markup(article_content),
                self._check_author_and_date(front_matter),
                self._check_section_structure(article_content),
                self._check_faq_section(article_content),
                self._check_conclusion(article_content),
                self._check_front_matter_completeness(front_matter),
                self._check_image_relevance(article_content, front_matter),
                self._check_duplicate_content(article_content),
                self._check_enhanced_forbidden_phrases(article_content)
            ]
            
            # PQS v3 Hard Gates (if enabled)
            if self.pqs_mode:
                # First check hard gates
                hard_gates_result = self._pqs_check_hard_gates(content, front_matter, article_content)
                validations.append(hard_gates_result)

                # Only calculate score if hard gates passed
                if hard_gates_result['status'] != 'error':
                    score_result = self._pqs_calculate_score(content, front_matter, article_content, validations, hard_gates_result)
                    validations.append(score_result)
                else:
                    # Hard gates failed - create a failing score result
                    validations.append({
                        'status': 'error',
                        'issues': ['PQS HARD GATES BLOCK - Article cannot be published'],
                        'metadata': {
                            'pqs_total_score': 0,
                            'pqs_threshold': self.pqs_config.get('thresholds', {}).get('publish_score', 85),
                            'pqs_hard_gates_passed': False,
                            'hard_gate_failures': len(hard_gates_result.get('issues', [])),
                            'pqs_subscores': {
                                'depth': 0, 'evidence': 0, 'images': 0,
                                'structure': 0, 'readability': 0, 'compliance': 0
                            }
                        }
                    })
            
            # Collect issues and warnings
            for validation in validations:
                if validation['status'] == 'error':
                    issues.extend(validation['issues'])
                elif validation['status'] == 'warning':
                    warnings.extend(validation['issues'])
                
                metadata.update(validation.get('metadata', {}))
            
            # Calculate overall score
            total_checks = 15
            passed_checks = sum(1 for v in validations if v['status'] == 'pass')
            quality_score = passed_checks / total_checks
            
            # Determine status
            if len(issues) == 0 and len(warnings) <= 2:
                status = 'PASS'
            elif len(issues) <= 2:
                status = 'WARN'
            else:
                status = 'FAIL'
            
            return {
                'file': os.path.basename(filepath),
                'status': status,
                'quality_score': quality_score,
                'passed_checks': passed_checks,
                'total_checks': total_checks,
                'issues': issues,
                'warnings': warnings,
                'metadata': metadata,
                'word_count': metadata.get('word_count', 0),
                'sections': metadata.get('section_count', 0),
                'images': metadata.get('image_count', 0)
            }
            
        except Exception as e:
            return {
                'file': os.path.basename(filepath),
                'status': 'ERROR',
                'quality_score': 0.0,
                'passed_checks': 0,
                'total_checks': 15,
                'issues': [f"Error reading file: {e}"],
                'warnings': [],
                'metadata': {},
                'word_count': 0,
                'sections': 0,
                'images': 0
            }
    
    def _extract_front_matter(self, content: str) -> Tuple[str, str]:
        """Extract front matter and article content"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[1].strip(), parts[2].strip()
        return "", content
    
    def _check_word_count(self, content: str) -> Dict:
        """Check 1: Word count validation"""
        word_count = len(content.split())
        min_words = self.quality_rules.get('min_word_count', 1500)
        max_words = self.quality_rules.get('max_word_count', 4000)
        
        issues = []
        if word_count < min_words:
            issues.append(f"Article too short: {word_count} words (minimum: {min_words})")
        elif word_count > max_words:
            issues.append(f"Article too long: {word_count} words (maximum: {max_words})")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'word_count': word_count}
        }
    
    def _check_images(self, content: str) -> Dict:
        """Check 2: Minimum images requirement"""
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, content)
        image_count = len(images)
        min_images = self.quality_rules.get('min_images', 3)
        
        issues = []
        if image_count < min_images:
            issues.append(f"Too few images: {image_count} (minimum: {min_images})")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'image_count': image_count, 'images': images}
        }
    
    def _check_featured_image(self, content: str) -> Dict:
        """Check 3: Featured image requirement"""
        if not self.quality_rules.get('require_featured', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        # Look for hero/featured image patterns
        hero_patterns = [
            r'!\[([^\]]*hero[^\]]*)\]',
            r'!\[([^\]]*featured[^\]]*)\]',
            r'!\[([^\]]*main[^\]]*)\]'
        ]
        
        has_hero = any(re.search(pattern, content, re.IGNORECASE) for pattern in hero_patterns)
        
        issues = []
        if not has_hero:
            issues.append("Missing featured/hero image")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'has_featured_image': has_hero}
        }
    
    def _check_alt_text_compliance(self, content: str) -> Dict:
        """Check 4: Alt text banned words validation"""
        if not self.quality_rules.get('ban_words_in_alt', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        banned_words = self.seo_config.get('banned_alt_words', [])
        image_pattern = r'!\[([^\]]*)\]'
        alt_texts = re.findall(image_pattern, content)
        
        issues = []
        violations = []
        
        for alt_text in alt_texts:
            for banned_word in banned_words:
                if banned_word.lower() in alt_text.lower():
                    violations.append(f"Alt text contains banned word '{banned_word}': {alt_text[:50]}...")
        
        if violations:
            issues.append(f"Alt text violations: {len(violations)} instances")
            issues.extend(violations[:3])  # Show first 3 violations
        
        return {
            'status': 'error' if violations else 'pass',
            'issues': issues,
            'metadata': {'alt_violations': len(violations)}
        }
    
    def _check_internal_links(self, content: str) -> Dict:
        """Check 5: Internal links requirement"""
        # Look for relative links (internal)
        internal_pattern = r'\[([^\]]+)\]\((/[^)]+|[^/][^)]*\.html?)\)'
        internal_links = re.findall(internal_pattern, content)
        min_internal = self.quality_rules.get('min_internal_links', 3)
        
        issues = []
        if len(internal_links) < min_internal:
            issues.append(f"Too few internal links: {len(internal_links)} (minimum: {min_internal})")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'internal_links': len(internal_links)}
        }
    
    def _check_external_links(self, content: str) -> Dict:
        """Check 6: External links requirement"""
        # Look for external links (http/https)
        external_pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        external_links = re.findall(external_pattern, content)
        min_external = self.quality_rules.get('min_external_links', 2)
        
        issues = []
        if len(external_links) < min_external:
            issues.append(f"Too few external links: {len(external_links)} (minimum: {min_external})")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'external_links': len(external_links)}
        }
    
    def _check_affiliate_disclosure(self, content: str) -> Dict:
        """Check 7: Affiliate disclosure requirement"""
        if not self.quality_rules.get('require_disclosure', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        disclosure_patterns = [
            r'affiliate',
            r'commission',
            r'earn.*from.*purchas',
            r'disclosure',
            r'as an amazon associate'
        ]
        
        has_disclosure = any(re.search(pattern, content, re.IGNORECASE) for pattern in disclosure_patterns)
        
        issues = []
        if not has_disclosure:
            issues.append("Missing affiliate disclosure statement")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'has_disclosure': has_disclosure}
        }
    
    def _check_schema_markup(self, content: str) -> Dict:
        """Check 8: Schema markup requirement"""
        if not self.quality_rules.get('require_schema', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        # Look for structured data patterns
        schema_patterns = [
            r'schema\.org',
            r'"@type".*"Article"',
            r'"@type".*"Review"',
            r'"@type".*"Product"'
        ]
        
        has_schema = any(re.search(pattern, content, re.IGNORECASE) for pattern in schema_patterns)
        
        # This is often handled by templates, so it's a warning rather than error
        issues = []
        if not has_schema:
            issues.append("No schema markup detected (may be handled by template)")
        
        return {
            'status': 'warning' if issues else 'pass',
            'issues': issues,
            'metadata': {'has_schema': has_schema}
        }
    
    def _check_author_and_date(self, front_matter: str) -> Dict:
        """Check 9: Author and date requirement"""
        if not self.quality_rules.get('require_author_and_date', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        has_author = 'author:' in front_matter
        has_date = 'date:' in front_matter
        
        issues = []
        if not has_author:
            issues.append("Missing author field in front matter")
        if not has_date:
            issues.append("Missing date field in front matter")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'has_author': has_author, 'has_date': has_date}
        }
    
    def _check_section_structure(self, content: str) -> Dict:
        """Check 10: Section structure requirement"""
        section_count = len(re.findall(r'^## ', content, re.MULTILINE))
        min_sections = self.quality_rules.get('min_sections', 5)
        
        issues = []
        if section_count < min_sections:
            issues.append(f"Too few sections: {section_count} (minimum: {min_sections})")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'section_count': section_count}
        }
    
    def _check_faq_section(self, content: str) -> Dict:
        """Check 11: FAQ section requirement"""
        if not self.quality_rules.get('require_faq', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        faq_patterns = [
            r'##.*FAQ',
            r'##.*Frequently.*Asked',
            r'##.*Questions.*Answers'
        ]
        
        has_faq = any(re.search(pattern, content, re.IGNORECASE) for pattern in faq_patterns)
        
        issues = []
        if not has_faq:
            issues.append("Missing FAQ section")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'has_faq': has_faq}
        }
    
    def _check_conclusion(self, content: str) -> Dict:
        """Check 12: Conclusion requirement"""
        if not self.quality_rules.get('require_conclusion', True):
            return {'status': 'pass', 'issues': [], 'metadata': {}}
        
        conclusion_patterns = [
            r'##.*Conclusion',
            r'##.*Summary',
            r'##.*Final.*Thoughts'
        ]
        
        has_conclusion = any(re.search(pattern, content, re.IGNORECASE) for pattern in conclusion_patterns)
        
        issues = []
        if not has_conclusion:
            issues.append("Missing conclusion section")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'has_conclusion': has_conclusion}
        }
    
    def _check_front_matter_completeness(self, front_matter: str) -> Dict:
        """Check 13: Complete front matter validation"""
        required_fields = ['title:', 'description:', 'date:', 'categories:', 'tags:', 'keywords:']
        missing_fields = []
        
        for field in required_fields:
            if field not in front_matter:
                missing_fields.append(field.replace(':', ''))
        
        issues = []
        if missing_fields:
            issues.append(f"Missing front matter fields: {', '.join(missing_fields)}")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {'missing_fields': missing_fields}
        }
    
    def _check_image_relevance(self, content: str, front_matter: str) -> Dict:
        """Check 14: Image relevance scoring"""
        min_relevance = self.quality_rules.get('min_image_relevance_score', 0.6)
        
        # Extract keywords from front matter
        keywords_match = re.search(r'keywords:\s*\[([^\]]+)\]', front_matter)
        if not keywords_match:
            return {
                'status': 'warning',
                'issues': ['Cannot assess image relevance - no keywords found'],
                'metadata': {'image_relevance_score': 0.0}
            }
        
        keywords = [k.strip(' "\'') for k in keywords_match.group(1).split(',')]
        primary_keyword = keywords[0] if keywords else ""
        
        # Simple relevance check - look for keyword matches in alt text
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, content)
        
        relevant_images = 0
        for alt_text, _ in images:
            if any(keyword.lower() in alt_text.lower() for keyword in keywords):
                relevant_images += 1
        
        relevance_score = relevant_images / len(images) if images else 0.0
        
        issues = []
        status = 'pass'
        if relevance_score < min_relevance:
            issues.append(f"Low image relevance: {relevance_score:.2f} (minimum: {min_relevance})")
            status = 'warning'  # Warning rather than error for relevance
        
        return {
            'status': status,
            'issues': issues,
            'metadata': {'image_relevance_score': relevance_score}
        }
    
    def _check_duplicate_content(self, content: str) -> Dict:
        """Check 15: Duplicate content detection"""
        max_usage = self.quality_rules.get('max_duplicate_usage', 3)
        
        # Simple duplicate detection - check for repeated paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        duplicate_count = 0
        
        for i, para in enumerate(paragraphs):
            for j, other_para in enumerate(paragraphs[i+1:], i+1):
                # Simple similarity check
                if len(set(para.split()) & set(other_para.split())) > len(para.split()) * 0.7:
                    duplicate_count += 1
        
        issues = []
        if duplicate_count > max_usage:
            issues.append(f"Excessive duplicate content detected: {duplicate_count} instances")
        
        return {
            'status': 'warning' if issues else 'pass',
            'issues': issues,
            'metadata': {'duplicate_content_score': duplicate_count}
        }

    def _check_enhanced_forbidden_phrases(self, content: str) -> Dict:
        """Check 16: Enhanced forbidden phrases detection (critical/warning/suggestion)"""
        # Get forbidden phrases from config
        forbidden_config = self.config.get('adsense_compliance', {}).get('forbidden_phrases', {})

        critical_phrases = forbidden_config.get('critical', [])
        warning_phrases = forbidden_config.get('warning', [])
        suggestion_phrases = forbidden_config.get('suggestion', [])

        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()

        violations = {
            'critical': [],
            'warning': [],
            'suggestion': []
        }

        # Check critical phrases (严重违规)
        for phrase in critical_phrases:
            if phrase.lower() in content_lower:
                violations['critical'].append(phrase)

        # Check warning phrases (警告)
        for phrase in warning_phrases:
            if phrase.lower() in content_lower:
                violations['warning'].append(phrase)

        # Check suggestion phrases (建议避免)
        for phrase in suggestion_phrases:
            if phrase.lower() in content_lower:
                violations['suggestion'].append(phrase)

        # Create issues based on violations
        issues = []
        status = 'pass'

        if violations['critical']:
            issues.extend([f"Critical forbidden phrase: '{phrase}'" for phrase in violations['critical']])
            status = 'error'

        if violations['warning']:
            issues.extend([f"Warning phrase detected: '{phrase}'" for phrase in violations['warning']])
            if status != 'error':
                status = 'warning'

        if violations['suggestion']:
            issues.extend([f"Suggested to avoid: '{phrase}'" for phrase in violations['suggestion']])
            if status not in ['error', 'warning']:
                status = 'warning'

        return {
            'status': status,
            'issues': issues,
            'metadata': {
                'critical_violations': len(violations['critical']),
                'warning_violations': len(violations['warning']),
                'suggestion_violations': len(violations['suggestion']),
                'total_violations': sum(len(v) for v in violations.values())
            }
        }
    
    def _pqs_check_hard_gates(self, content: str, front_matter: str, article_content: str) -> Dict:
        """PQS v3 Hard Gates - Any failure = immediate FAIL"""
        issues = []
        
        # Hard Gate 1: Featured image + >= 2 inline images with proper ALT
        fm_data, _ = self._extract_front_matter_data(content)
        featured_image = fm_data.get('featured_image')
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        images = re.findall(image_pattern, article_content)
        
        if not featured_image:
            issues.append("HARD GATE FAIL: Missing featured_image in front matter")
        else:
            # Validate file exists under static/ for site paths like /images/...
            try:
                if featured_image.startswith('/'):
                    fs_path = os.path.join('static', featured_image.lstrip('/'))
                else:
                    fs_path = os.path.join('static', featured_image)
                if not os.path.exists(fs_path):
                    issues.append(f"HARD GATE FAIL: featured_image not found: {featured_image}")
            except Exception:
                pass
        
        if len(images) < self.pqs_config.get('thresholds', {}).get('min_inline_images', 2):
            issues.append(f"HARD GATE FAIL: Insufficient inline images ({len(images)} < 2)")

        # Validate inline image files exist under static/ and check ALT quality
        for alt_text, img_path in images:
            try:
                # Check file existence
                if img_path.startswith('/'):
                    fs_path = os.path.join('static', img_path.lstrip('/'))
                else:
                    fs_path = os.path.join('static', img_path)
                if not os.path.exists(fs_path):
                    issues.append(f"HARD GATE FAIL: Inline image not found: {img_path}")

                # Enhanced ALT text validation
                if not alt_text or len(alt_text.strip()) < 8:
                    issues.append(f"HARD GATE FAIL: ALT text too short (<8 chars): '{alt_text}'")
                elif len(alt_text) > 120:
                    issues.append(f"HARD GATE FAIL: ALT text too long (>120 chars): '{alt_text[:50]}...'")

                # Check for entity tokens in ALT text
                category = fm_data.get('category', fm_data.get('categories', ['generic']))
                if isinstance(category, list):
                    category = category[0] if category else 'generic'

                entity_tokens = self.pqs_config.get('entities_tokens', {}).get(category, []) + \
                               self.pqs_config.get('entities_tokens', {}).get('generic', [])

                if entity_tokens and not any(token.lower() in alt_text.lower() for token in entity_tokens):
                    issues.append(f"HARD GATE FAIL: ALT text lacks entity tokens: '{alt_text[:50]}...'")

            except Exception:
                pass
        # Hard Gate 2: Evidence links >= 2
        external_pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
        external_links = re.findall(external_pattern, article_content)
        if len(external_links) < 2:
            issues.append(f"HARD GATE FAIL: Insufficient evidence links ({len(external_links)} < 2)")
        
        # Hard Gate 3: JSON-LD presence
        jsonld_patterns = [r'"@type"\s*:\s*"Article"', r'"@type"\s*:\s*"FAQPage"']
        has_jsonld = any(re.search(pattern, content, re.IGNORECASE) for pattern in jsonld_patterns)
        if not has_jsonld:
            issues.append("HARD GATE FAIL: Missing JSON-LD structured data")
        
        # Hard Gate 4: MANDATORY Comparison Table (Fix for "空心推荐" problem)
        table_rows = [ln.strip() for ln in article_content.splitlines() if ln.strip().startswith('|')]
        has_proper_table = len(table_rows) >= 6  # Header + separator + at least 4 data rows

        # Check if table has required columns (model/protocol/features)
        has_model_column = False
        has_protocol_column = False
        if table_rows:
            header_row = table_rows[0].lower()
            has_model_column = any(word in header_row for word in ['model', 'product', 'device', 'name'])
            has_protocol_column = any(word in header_row for word in ['protocol', 'connectivity', 'wifi', 'zigbee', 'matter'])

        if not has_proper_table:
            issues.append(f"HARD GATE FAIL: Missing proper comparison table (found {len(table_rows)} rows, need ≥6)")
        elif not (has_model_column and has_protocol_column):
            issues.append("HARD GATE FAIL: Comparison table must include Model and Protocol columns")

        # Alternative: Check for structured product recommendations with specific models
        has_specific_models = len(re.findall(r'(?i)(model|version)\s+[\w\d-]{3,}', article_content)) >= 3
        has_itemlist = 'ItemList' in content

        # Allow alternatives but prefer table
        if not has_proper_table and not has_itemlist and not has_specific_models:
            issues.append("HARD GATE FAIL: No structured comparison - need table OR ≥3 specific model names")
        
        # Hard Gate 5: Keyword density check
        primary_kw = fm_data.get('keyword', fm_data.get('title', '').split('|')[0])
        if primary_kw:
            word_count = len(article_content.split())
            kw_count = len(re.findall(re.escape(primary_kw.lower()), article_content.lower()))
            density = kw_count / max(1, word_count)
            max_density = self.pqs_config.get('thresholds', {}).get('keyword_density_max', 0.025)
            
            if density > max_density:
                issues.append(f"HARD GATE FAIL: Keyword density too high ({density:.1%} > {max_density:.1%})")
        
        # Hard Gate 6: Entity coverage >= 3
        text_lower = article_content.lower()
        category = fm_data.get('category', fm_data.get('categories', ['generic']))
        if isinstance(category, list):
            category = category[0] if category else 'generic'

        entity_tokens = self.pqs_config.get('entities_tokens', {}).get(category, []) + \
                       self.pqs_config.get('entities_tokens', {}).get('generic', [])

        entity_hits = [token for token in entity_tokens if token.lower() in text_lower]
        if len(set(entity_hits)) < 3:
            issues.append(f"HARD GATE FAIL: Insufficient entity coverage ({len(set(entity_hits))} < 3)")

        # Hard Gate 7: Compliance Disclosure Positioning (First 2 screens)
        disclosure_patterns = [
            r'(?i)(affiliate|commission|earn.*from.*purchas|as an amazon associate)',
            r'(?i)(disclosure|披露)',
            r'(?i)(no.*physical.*test|research.*based|specification.*analysis)'
        ]

        # Check if disclosure appears in first ~600 characters (roughly first screen)
        first_screen = article_content[:600]
        has_early_disclosure = any(re.search(pattern, first_screen) for pattern in disclosure_patterns)

        # Check if methodology/no-testing disclosure exists anywhere
        has_methodology_disclosure = any(re.search(pattern, article_content) for pattern in disclosure_patterns)

        if not has_methodology_disclosure:
            issues.append("HARD GATE FAIL: Missing methodology/no-testing disclosure statement")
        elif not has_early_disclosure:
            issues.append("HARD GATE FAIL: Disclosure must appear within first 600 characters")

        # Hard Gate 8: Basic Readability Requirements
        word_count = len(article_content.split())
        if word_count < 1500:
            issues.append(f"HARD GATE FAIL: Article too short ({word_count} words, minimum 1500)")

        # Check paragraph length (basic readability)
        paragraphs = [p.strip() for p in article_content.split('\n\n') if p.strip()]
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 120]
        if len(long_paragraphs) > len(paragraphs) * 0.3:  # More than 30% long paragraphs
            issues.append(f"HARD GATE FAIL: Too many long paragraphs ({len(long_paragraphs)}, max 30% of total)")

        # Check sentence structure (avoid AI-like patterns)
        sentences = re.split(r'[.!?]+', article_content)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        if valid_sentences:
            avg_sentence_len = sum(len(s.split()) for s in valid_sentences) / len(valid_sentences)
            if avg_sentence_len > 35:  # Very long average sentences = AI-like
                issues.append(f"HARD GATE FAIL: Sentences too long (avg {avg_sentence_len:.1f} words, max 35)")
        
        status = 'error' if issues else 'pass'
        return {
            'status': status,
            'issues': issues,
            'metadata': {
                'pqs_hard_gates_passed': status == 'pass',
                'hard_gate_failures': len(issues)
            }
        }
    
    def _pqs_calculate_score(self, content: str, front_matter: str, article_content: str, validations: List, hard_gates_result: Dict = None) -> Dict:
        """PQS v3 100-point scoring system - Only runs if Hard Gates passed"""
        if not self.pqs_mode:
            return {'status': 'pass', 'issues': [], 'metadata': {}}

        # Hard Gates must have passed for this method to be called
        # This method only calculates the detailed score
        # Content depth (30 points)
        depth_score = 0
        if re.search(r'(?i)(conclusion|summary)', article_content):
            depth_score += 6
        if '|' in article_content:  # has table
            depth_score += 8
        if re.search(r'(?i)(alternatives|who should buy|who should not buy)', article_content):
            depth_score += 8
        if re.search(r'(?i)(risks|watch out|considerations)', article_content):
            depth_score += 8
        depth_score = min(30, depth_score)
        
        # Evidence quality (20 points)  
        external_links = len(re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', article_content))
        evidence_score = min(20, external_links * 5)
        
        # Images and visualization (15 points)
        fm_data, _ = self._extract_front_matter_data(content)
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', article_content)
        featured_image = fm_data.get('featured_image')
        images_score = 0
        if featured_image:
            images_score += 7
        if len(images) >= 2:
            images_score += 8
        images_score = min(15, images_score)
        
        # Structure and SEO (15 points)
        structure_score = 0
        if re.search(r'^\s*#\s+.+', article_content, re.M):  # H1
            structure_score += 5
        if len(re.findall(r'^\s*##\s+.+', article_content, re.M)) >= 4:  # H2s
            structure_score += 5  
        if re.search(r'\[(.+)\]\((\/[^)]+)\)', article_content):  # internal links
            structure_score += 5
        structure_score = min(15, structure_score)
        
        # Readability (10 points)
        sentences = re.split(r'[。！？.!?]+', article_content)
        valid_sentences = [s for s in sentences if s.strip()]
        if valid_sentences:
            avg_len = sum(len(s) for s in valid_sentences) / len(valid_sentences)
            h2_count = len(re.findall(r'^\s*##\s+.+', article_content, re.M))
            readability_score = max(0, min(10, (100 - min(70, avg_len) + min(10, h2_count*2)) / 10))
        else:
            readability_score = 5
        
        # Compliance and E-E-A-T (10 points)
        compliance_score = 0
        if fm_data.get('author') and fm_data.get('date'):
            compliance_score += 4
        if re.search(r'(?i)(affiliate disclosure|as an amazon associate|披露)', article_content):
            compliance_score += 3
        if re.search(r'(?i)(about|review policy)', article_content):
            compliance_score += 3
        compliance_score = min(10, compliance_score)
        
        total_score = depth_score + evidence_score + images_score + structure_score + readability_score + compliance_score
        total_score = max(0, min(100, total_score))
        
        threshold = self.pqs_config.get('thresholds', {}).get('publish_score', 85)
        issues = []
        if total_score < threshold:
            issues.append(f"PQS SCORE FAIL: {total_score}/100 (threshold: {threshold})")
        
        return {
            'status': 'error' if issues else 'pass',
            'issues': issues,
            'metadata': {
                'pqs_total_score': total_score,
                'pqs_threshold': threshold,
                'pqs_subscores': {
                    'depth': depth_score,
                    'evidence': evidence_score,
                    'images': images_score,
                    'structure': structure_score,
                    'readability': readability_score,
                    'compliance': compliance_score
                }
            }
        }
    
    def _extract_front_matter_data(self, content: str) -> Tuple[Dict, str]:
        """Extract front matter as dictionary and return body"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    fm_data = yaml.safe_load(parts[1]) or {}
                    return fm_data, parts[2].strip()
                except:
                    pass
        return {}, content


def check_article_quality(filepath):
    """Legacy compatibility function"""
    checker = ComprehensiveQualityChecker()
    result = checker.check_article_quality(filepath)
    
    # Convert to legacy format for backwards compatibility
    return {
        'file': result['file'],
        'word_count': result['word_count'],
        'sections': result['sections'],
        'issues': result['issues'] + result['warnings'],
        'status': result['status']
    }

def main():
    """Main function with v2 enhanced quality checking"""
    parser = argparse.ArgumentParser(description='Content Quality Check v2 Enhanced')
    parser.add_argument('path', help='Directory containing articles to check or single file path')
    parser.add_argument('--recent-only', action='store_true', help='Only check recently generated files')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--detailed', action='store_true', help='Show detailed quality analysis')
    parser.add_argument('--export', help='Export results to JSON file')
    parser.add_argument('--mode', choices=['legacy', 'v2', 'v3', 'pqs'], default='v2',
                        help='Quality check mode (default: v2, v3=PQS hard gates, pqs=PQS strict)')
    parser.add_argument('--min-score', type=float, default=0.9, 
                        help='Minimum quality score threshold (0.0-1.0)')
    parser.add_argument('--fail-fast', action='store_true', help='Stop at first failure')
    parser.add_argument('--single-file', action='store_true', help='Check single file instead of directory')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically fix articles that fail quality checks')
    
    args = parser.parse_args()
    
    mode_name = {'legacy': 'Legacy', 'v2': 'v2 Enhanced', 'v3': 'v3 Hybrid (PQS+v2)', 'pqs': 'PQS v3 Strict'}
    print(f"🔍 Starting Content Quality Check {mode_name.get(args.mode, args.mode)}...")
    print("=" * 60)
    
    # Initialize quality checker
    pqs_mode = args.mode in ['v3', 'pqs']
    checker = ComprehensiveQualityChecker(config_path=args.config, pqs_mode=pqs_mode)
    
    # Get files to check
    if args.single_file:
        # Single file mode
        if not os.path.exists(args.path):
            print(f"❌ File not found: {args.path}")
            return False
        files_to_check = [args.path]
        print(f"📋 Checking single file: {os.path.basename(args.path)}")
    elif args.recent_only and os.path.exists('generated_files.txt'):
        with open('generated_files.txt', 'r') as f:
            files_to_check = [line.strip() for line in f if line.strip()]
        print(f"📋 Checking {len(files_to_check)} recently generated files")
    else:
        files_to_check = list(Path(args.path).glob('*.md'))
        print(f"📋 Checking all {len(files_to_check)} files in {args.path}")
    
    if not files_to_check:
        print("❌ No files found to check")
        return False
    
    # Check each file
    results = []
    total_issues = 0
    total_warnings = 0
    failed_files = []
    
    print(f"⚙️ Using {mode_name.get(args.mode, args.mode)} mode")
    if pqs_mode:
        threshold = checker.pqs_config.get('thresholds', {}).get('publish_score', 85)
        print(f"🎯 PQS Score threshold: {threshold}/100")
    else:
        print(f"🎯 Quality threshold: {args.min_score:.1%}")
    print("-" * 60)
    
    for i, filepath in enumerate(files_to_check, 1):
        print(f"📄 [{i}/{len(files_to_check)}] {os.path.basename(filepath)}")
        
        if args.mode == 'legacy':
            result = check_article_quality(filepath)
        else:  # v2, v3, pqs modes
            result = checker.check_article_quality(filepath)
        
        results.append(result)
        
        # Count issues
        if args.mode != 'legacy':
            total_issues += len(result.get('issues', []))
            total_warnings += len(result.get('warnings', []))
        else:
            total_issues += len(result.get('issues', []))
        
        # Print individual result
        status_emoji = {'PASS': '✅', 'WARN': '⚠️', 'FAIL': '❌', 'ERROR': '💥'}
        emoji = status_emoji.get(result['status'], '❓')
        
        if args.mode != 'legacy':
            quality_score = result.get('quality_score', 0.0)
            passed_checks = result.get('passed_checks', 0)
            total_checks = result.get('total_checks', 15 if args.mode == 'v2' else 17)
            
            print(f"  {emoji} Quality Score: {quality_score:.1%} ({passed_checks}/{total_checks} checks passed)")
            print(f"  📊 {result['word_count']} words, {result['sections']} sections, {result['images']} images")
            
            # Show PQS specific info if in PQS mode
            if pqs_mode and result.get('metadata', {}).get('pqs_total_score') is not None:
                pqs_score = result['metadata']['pqs_total_score']
                pqs_threshold = result['metadata']['pqs_threshold']
                hard_gates_passed = result['metadata'].get('pqs_hard_gates_passed', False)

                # 🔧 Auto-fix integration for failed articles
                if args.auto_fix and AUTO_FIXER_AVAILABLE and result['status'] == 'FAIL' and pqs_score == 0:
                    print(f"  🔧 Article failed quality check (PQS: {pqs_score}/100), attempting auto-fix...")
                    try:
                        fixer = AutoQualityFixer()
                        # Extract keyword from filename
                        keyword = os.path.splitext(os.path.basename(filepath))[0].replace('-', ' ')
                        fix_success, final_score = fixer.fix_quality_loop(filepath, keyword)
                        fix_result = {'success': fix_success, 'final_score': final_score}

                        if fix_result.get('success', False):
                            print(f"  ✅ Auto-fix successful! Re-checking quality...")
                            # Re-run quality check
                            fixed_result = checker.check_article_quality(filepath)

                            if fixed_result['status'] != 'FAIL':
                                print(f"  🎉 Fixed article now passes quality check!")
                                # Update the result to reflect the fix
                                results[-1] = fixed_result
                                result = fixed_result
                            else:
                                print(f"  ⚠️ Auto-fix applied but article still needs manual review")
                        else:
                            print(f"  ❌ Auto-fix failed: {fix_result.get('reason', 'Unknown error')}")

                    except Exception as fix_error:
                        print(f"  ❌ Auto-fix error: {fix_error}")

            elif args.auto_fix and AUTO_FIXER_AVAILABLE and result['status'] == 'FAIL':
                # Handle non-PQS mode failures
                print(f"  🔧 Article failed quality check (Score: {quality_score:.1%}), attempting auto-fix...")
                try:
                    fixer = AutoQualityFixer()
                    keyword = os.path.splitext(os.path.basename(filepath))[0].replace('-', ' ')
                    fix_success, final_score = fixer.fix_quality_loop(filepath, keyword)
                    fix_result = {'success': fix_success, 'final_score': final_score}

                    if fix_result.get('success', False):
                        print(f"  ✅ Auto-fix successful! Re-checking quality...")
                        fixed_result = checker.check_article_quality(filepath)

                        if fixed_result.get('quality_score', 0) >= args.min_score:
                            print(f"  🎉 Fixed article now passes quality check!")
                            results[-1] = fixed_result
                            result = fixed_result
                        else:
                            print(f"  ⚠️ Auto-fix applied but score still below threshold")
                    else:
                        print(f"  ❌ Auto-fix failed: {fix_result.get('reason', 'Unknown error')}")

                except Exception as fix_error:
                    print(f"  ❌ Auto-fix error: {fix_error}")
                
                gate_status = "✅ PASSED" if hard_gates_passed else "❌ FAILED"
                print(f"  🎯 PQS Score: {pqs_score}/100 (threshold: {pqs_threshold}) | Hard Gates: {gate_status}")
                
                if args.detailed and 'pqs_subscores' in result['metadata']:
                    subscores = result['metadata']['pqs_subscores']
                    print(f"    📈 Depth: {subscores['depth']}/30, Evidence: {subscores['evidence']}/20, " +
                          f"Images: {subscores['images']}/15, Structure: {subscores['structure']}/15")
            
            # Check failure conditions
            if pqs_mode:
                # PQS mode: hard gates + score threshold
                pqs_score = result.get('metadata', {}).get('pqs_total_score', 0)
                pqs_threshold = result.get('metadata', {}).get('pqs_threshold', 85)
                hard_gates_passed = result.get('metadata', {}).get('pqs_hard_gates_passed', False)
                
                if not hard_gates_passed or pqs_score < pqs_threshold:
                    failed_files.append(result['file'])
            else:
                # v2 mode: quality score threshold
                if quality_score < args.min_score:
                    failed_files.append(result['file'])
                
            if args.detailed:
                # Show detailed breakdown
                if result.get('issues'):
                    print(f"  ❌ Issues ({len(result['issues'])}):")
                    for issue in result['issues'][:5]:  # Show first 5 issues
                        print(f"    • {issue}")
                    if len(result['issues']) > 5:
                        print(f"    ... and {len(result['issues']) - 5} more issues")
                
                if result.get('warnings'):
                    print(f"  ⚠️ Warnings ({len(result['warnings'])}):")
                    for warning in result['warnings'][:3]:  # Show first 3 warnings
                        print(f"    • {warning}")
                    if len(result['warnings']) > 3:
                        print(f"    ... and {len(result['warnings']) - 3} more warnings")
        else:
            # Legacy mode display
            print(f"  {emoji} {result['word_count']} words, {result['sections']} sections")
            
            if result.get('issues'):
                for issue in result['issues']:
                    print(f"    • {issue}")
        
        print()  # Blank line between files
        
        # Fail fast option
        if args.fail_fast and result['status'] in ['FAIL', 'ERROR']:
            print(f"❌ Stopping at first failure: {result['file']}")
            break
    
    # Generate comprehensive summary
    print("=" * 60)
    print("📊 Quality Check Summary Report")
    print("=" * 60)
    
    # Basic statistics
    passed = sum(1 for r in results if r['status'] == 'PASS')
    warned = sum(1 for r in results if r['status'] == 'WARN')
    failed = sum(1 for r in results if r['status'] == 'FAIL')
    errors = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"📈 File Statistics:")
    print(f"  ✅ Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"  ⚠️ Warnings: {warned} ({warned/len(results)*100:.1f}%)")
    print(f"  ❌ Failed: {failed} ({failed/len(results)*100:.1f}%)")
    print(f"  💥 Errors: {errors} ({errors/len(results)*100:.1f}%)")
    print(f"  📋 Total Files: {len(results)}")
    
    if args.mode == 'v2':
        # Enhanced v2 statistics
        avg_quality_score = sum(r.get('quality_score', 0) for r in results) / len(results)
        avg_word_count = sum(r.get('word_count', 0) for r in results) / len(results)
        avg_sections = sum(r.get('sections', 0) for r in results) / len(results)
        avg_images = sum(r.get('images', 0) for r in results) / len(results)
        
        print(f"\n📊 Quality Metrics:")
        print(f"  🎯 Average Quality Score: {avg_quality_score:.1%}")
        print(f"  📝 Average Word Count: {avg_word_count:.0f}")
        print(f"  📑 Average Sections: {avg_sections:.1f}")
        print(f"  🖼️ Average Images: {avg_images:.1f}")
        print(f"  ❌ Total Issues: {total_issues}")
        print(f"  ⚠️ Total Warnings: {total_warnings}")
        
        if failed_files:
            print(f"\n🚨 Files Below Quality Threshold ({args.min_score:.1%}):")
            for failed_file in failed_files[:10]:  # Show first 10
                print(f"  • {failed_file}")
            if len(failed_files) > 10:
                print(f"  ... and {len(failed_files) - 10} more files")
    
    # Export results if requested
    if args.export:
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'mode': args.mode,
                'min_score_threshold': args.min_score,
                'summary': {
                    'total_files': len(results),
                    'passed': passed,
                    'warned': warned, 
                    'failed': failed,
                    'errors': errors,
                    'total_issues': total_issues,
                    'total_warnings': total_warnings if args.mode == 'v2' else 0
                },
                'results': results
            }
            
            with open(args.export, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Results exported to: {args.export}")
            
        except Exception as e:
            print(f"⚠️ Failed to export results: {e}")
    
    # Determine overall success
    print(f"\n" + "=" * 60)
    
    if args.mode == 'v2':
        below_threshold = len(failed_files)
        success_rate = (len(results) - below_threshold) / len(results)
        
        if errors > 0:
            print("❌ QUALITY CHECK FAILED - Files with critical errors detected")
            return False
        elif below_threshold > len(results) * 0.3:  # More than 30% below threshold
            print(f"❌ QUALITY CHECK FAILED - {below_threshold} files below quality threshold")
            return False
        elif success_rate >= 0.9:  # 90%+ success rate
            print(f"🎉 QUALITY CHECK PASSED - {success_rate:.1%} success rate")
            return True
        else:
            print(f"⚠️ QUALITY CHECK PASSED WITH WARNINGS - {success_rate:.1%} success rate")
            return True
    else:
        # Legacy success determination
        if errors > 0 or failed > 3:
            print("❌ QUALITY CHECK FAILED - Too many issues")
            return False
        elif total_issues == 0:
            print("🎉 ALL QUALITY CHECKS PASSED!")
            return True
        else:
            print("⚠️ QUALITY CHECK PASSED WITH MINOR ISSUES")
            return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


# === v2: Enhanced Quality Gate & External Rules Loading ===

def load_quality_rules(path: str = 'templates/quality_rules.json') -> Dict:
    """v2 Helper function - Load external quality rules configuration (backward compatibility)"""
    rules_path = Path(path)
    
    if not rules_path.exists():
        # Return default rules matching image_config.yml structure
        return {
            "min_images": 3,
            "require_featured": True,
            "ban_words_in_alt": ["best", "2025", "cheap", "lowest price", "amazing", "incredible"],
            "min_internal_links": 3,
            "min_external_links": 2,
            "require_disclosure": True,
            "require_schema": True,
            "require_author_and_date": True,
            "max_duplicate_usage": 3,
            "min_image_relevance_score": 0.6
        }
    
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load quality rules from {path}: {e}")
        return {}


def validate_article_v2(filepath: str, rules: Optional[Dict] = None) -> Dict[str, Any]:
    """v2 Enhanced validation function with external rules"""
    if rules:
        # Create temporary config with custom rules
        config = {'quality_rules': rules}
        checker = ComprehensiveQualityChecker()
        checker.quality_rules = rules
    else:
        checker = ComprehensiveQualityChecker()
    
    return checker.check_article_quality(filepath)


def batch_quality_check(directory: str, rules_file: Optional[str] = None, export_file: Optional[str] = None) -> Dict[str, Any]:
    """v2 Batch quality checking with results export"""
    rules = None
    if rules_file:
        rules = load_quality_rules(rules_file)
    
    files = list(Path(directory).glob('*.md'))
    results = []
    
    print(f"🔄 Processing {len(files)} files...")
    
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {file_path.name}", end=' ')
        
        result = validate_article_v2(str(file_path), rules)
        results.append(result)
        
        # Quick status indicator
        emoji = {'PASS': '✅', 'WARN': '⚠️', 'FAIL': '❌', 'ERROR': '💥'}
        print(emoji.get(result['status'], '❓'))
    
    # Generate summary
    summary = {
        'total_files': len(results),
        'passed': sum(1 for r in results if r['status'] == 'PASS'),
        'warnings': sum(1 for r in results if r['status'] == 'WARN'),
        'failed': sum(1 for r in results if r['status'] == 'FAIL'),
        'errors': sum(1 for r in results if r['status'] == 'ERROR'),
        'avg_quality_score': sum(r.get('quality_score', 0) for r in results) / len(results) if results else 0,
        'results': results
    }
    
    # Export if requested
    if export_file:
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'directory': directory,
            'rules_file': rules_file,
            'summary': summary
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Results exported to {export_file}")
    
    return summary


def create_quality_report(results_file: str, output_file: str = None) -> str:
    """v2 Generate HTML quality report from JSON results"""
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data.get('summary', {})
    results = summary.get('results', [])
    
    # Generate HTML report
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Content Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .pass {{ color: green; }}
        .warn {{ color: orange; }}
        .fail {{ color: red; }}
        .error {{ color: darkred; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .score {{ font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Content Quality Report</h1>
    <p>Generated: {data.get('timestamp', 'Unknown')}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Files:</strong> {summary.get('total_files', 0)}</p>
        <p><span class="pass">✅ Passed: {summary.get('passed', 0)}</span></p>
        <p><span class="warn">⚠️ Warnings: {summary.get('warnings', 0)}</span></p>
        <p><span class="fail">❌ Failed: {summary.get('failed', 0)}</span></p>
        <p><span class="error">💥 Errors: {summary.get('errors', 0)}</span></p>
        <p><strong>Average Quality Score:</strong> {summary.get('avg_quality_score', 0):.1%}</p>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>File</th>
            <th>Status</th>
            <th>Quality Score</th>
            <th>Word Count</th>
            <th>Sections</th>
            <th>Images</th>
            <th>Issues</th>
        </tr>
    """
    
    for result in results:
        status_class = result['status'].lower()
        issues_count = len(result.get('issues', [])) + len(result.get('warnings', []))
        
        html += f"""
        <tr>
            <td>{result['file']}</td>
            <td class="{status_class}">{result['status']}</td>
            <td class="score">{result.get('quality_score', 0):.1%}</td>
            <td>{result.get('word_count', 0)}</td>
            <td>{result.get('sections', 0)}</td>
            <td>{result.get('images', 0)}</td>
            <td>{issues_count}</td>
        </tr>
        """
    
    html += """
    </table>
</body>
</html>
    """
    
    if not output_file:
        output_file = results_file.replace('.json', '_report.html')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"📄 HTML report generated: {output_file}")
    return output_file


# Command-line utilities for v2 features
if __name__ == "__main__" and len(sys.argv) > 1:
    if sys.argv[1] == "batch":
        # Batch processing mode
        if len(sys.argv) < 3:
            print("Usage: python quality_check.py batch <directory> [rules_file] [export_file]")
            sys.exit(1)
        
        directory = sys.argv[2]
        rules_file = sys.argv[3] if len(sys.argv) > 3 else None
        export_file = sys.argv[4] if len(sys.argv) > 4 else None
        
        summary = batch_quality_check(directory, rules_file, export_file)
        
        print(f"\n📊 Batch Quality Check Complete:")
        print(f"  ✅ {summary['passed']}/{summary['total_files']} files passed")
        print(f"  📈 Average quality score: {summary['avg_quality_score']:.1%}")
        
        sys.exit(0 if summary['errors'] == 0 else 1)
    
    elif sys.argv[1] == "report":
        # Generate HTML report
        if len(sys.argv) < 3:
            print("Usage: python quality_check.py report <results.json> [output.html]")
            sys.exit(1)
        
        results_file = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        create_quality_report(results_file, output_file)
        sys.exit(0)
