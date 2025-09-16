#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3 Hard Gate Quality Checker
Implements strict quality gates for content generation

Based on Growth Kit v3 specifications:
- Entity coverage validation
- Information source requirements  
- Content depth and structure checks
- AdSense compliance verification
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class V3HardGateChecker:
    """Strict quality gate checker for v3 content generation"""
    
    def __init__(self, config_path: str = "configs/quality_gates.yml"):
        """Initialize with quality gate configuration"""
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load quality gate configuration"""
        default_config = {
            'entity_coverage': {
                'required_fields': ['category', 'product_type', 'use_case'],
                'min_coverage': 0.85  # 85% entity coverage required
            },
            'content_depth': {
                'min_sections': 5,  # Introduction, Features, Comparison, FAQ, Conclusion
                'min_words': 2500,
                'required_sections': [
                    'introduction', 'key_features', 'comparison', 
                    'installation', 'faq', 'conclusion'
                ]
            },
            'information_sources': {
                'min_sources': 3,
                'trusted_domains': [
                    'amazon.com', 'bestbuy.com', 'walmart.com',
                    'cnet.com', 'pcmag.com', 'techradar.com',
                    'consumerreports.org', 'wirecutter.com'
                ]
            },
            'adsense_compliance': {
                'forbidden_phrases': [
                    'click here', 'best deal', 'limited time',
                    'guaranteed', 'amazing results', 'miracle',
                    'secret', 'exclusive offer', 'act now'
                ],
                'required_disclaimers': [
                    'affiliate', 'commission', 'research-based'
                ]
            }
        }
        
        try:
            import yaml
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                # Deep merge with defaults
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        except Exception as e:
            print(f"Config load warning: {e}, using defaults")
            
        return default_config
    
    def check_content(self, content: str, metadata: Dict) -> Tuple[bool, Dict[str, any]]:
        """
        Perform comprehensive v3 hard gate check
        
        Args:
            content: Article content
            metadata: Article metadata (entities, sources, etc.)
            
        Returns:
            Tuple of (passed, detailed_results)
        """
        results = {
            'overall_pass': False,
            'score': 0.0,
            'checks': {},
            'failures': [],
            'recommendations': []
        }
        
        # Gate 1: Entity Coverage Check
        entity_pass, entity_details = self._check_entity_coverage(metadata)
        results['checks']['entity_coverage'] = entity_details
        if not entity_pass:
            results['failures'].append("Insufficient entity coverage")
            
        # Gate 2: Content Depth Check  
        depth_pass, depth_details = self._check_content_depth(content)
        results['checks']['content_depth'] = depth_details
        if not depth_pass:
            results['failures'].append("Content lacks required depth/structure")
            
        # Gate 3: Information Sources Check
        sources_pass, sources_details = self._check_information_sources(metadata)
        results['checks']['information_sources'] = sources_details
        if not sources_pass:
            results['failures'].append("Insufficient or untrusted information sources")
            
        # Gate 4: AdSense Compliance Check
        adsense_pass, adsense_details = self._check_adsense_compliance(content)
        results['checks']['adsense_compliance'] = adsense_details
        if not adsense_pass:
            results['failures'].append("AdSense compliance violations detected")
            
        # Gate 5: Technical SEO Check
        seo_pass, seo_details = self._check_technical_seo(content, metadata)
        results['checks']['technical_seo'] = seo_details
        if not seo_pass:
            results['failures'].append("Technical SEO requirements not met")
        
        # Calculate overall score and pass/fail
        gate_scores = [
            entity_details.get('score', 0),
            depth_details.get('score', 0), 
            sources_details.get('score', 0),
            adsense_details.get('score', 0),
            seo_details.get('score', 0)
        ]
        
        results['score'] = sum(gate_scores) / len(gate_scores)
        results['overall_pass'] = (
            entity_pass and depth_pass and sources_pass and 
            adsense_pass and seo_pass and results['score'] >= 0.90
        )
        
        # Generate recommendations
        if not results['overall_pass']:
            results['recommendations'] = self._generate_recommendations(results)
            
        return results['overall_pass'], results
    
    def _check_entity_coverage(self, metadata: Dict) -> Tuple[bool, Dict]:
        """Check if entities are sufficiently covered"""
        entities = metadata.get('entities', {})
        required_fields = self.config['entity_coverage']['required_fields']
        min_coverage = self.config['entity_coverage']['min_coverage']
        
        filled_fields = 0
        total_fields = len(required_fields)
        missing_fields = []
        
        for field in required_fields:
            if field in entities and entities[field]:
                filled_fields += 1
            else:
                missing_fields.append(field)
                
        coverage_ratio = filled_fields / total_fields
        passed = coverage_ratio >= min_coverage
        
        return passed, {
            'score': coverage_ratio,
            'coverage_ratio': coverage_ratio,
            'filled_fields': filled_fields,
            'total_fields': total_fields,
            'missing_fields': missing_fields,
            'passed': passed
        }
    
    def _check_content_depth(self, content: str) -> Tuple[bool, Dict]:
        """Check content depth and structure requirements"""
        word_count = len(content.split())
        min_words = self.config['content_depth']['min_words']
        required_sections = self.config['content_depth']['required_sections']
        
        # Check word count
        word_pass = word_count >= min_words
        
        # Check section presence
        content_lower = content.lower()
        found_sections = []
        missing_sections = []
        
        for section in required_sections:
            # Look for section headers or keywords
            section_patterns = [
                f"## {section}", f"# {section}", 
                f"**{section}**", section.replace('_', ' ')
            ]
            
            found = any(pattern.lower() in content_lower for pattern in section_patterns)
            if found:
                found_sections.append(section)
            else:
                missing_sections.append(section)
                
        section_coverage = len(found_sections) / len(required_sections)
        section_pass = section_coverage >= 0.8  # 80% section coverage required
        
        overall_pass = word_pass and section_pass
        score = (word_count / min_words * 0.5 + section_coverage * 0.5)
        score = min(1.0, score)  # Cap at 1.0
        
        return overall_pass, {
            'score': score,
            'word_count': word_count,
            'min_words_required': min_words,
            'word_count_pass': word_pass,
            'section_coverage': section_coverage,
            'found_sections': found_sections,
            'missing_sections': missing_sections,
            'section_pass': section_pass,
            'passed': overall_pass
        }
    
    def _check_information_sources(self, metadata: Dict) -> Tuple[bool, Dict]:
        """Check information source quality and quantity"""
        sources = metadata.get('sources', [])
        min_sources = self.config['information_sources']['min_sources']
        trusted_domains = self.config['information_sources']['trusted_domains']
        
        source_count = len(sources)
        trusted_count = 0
        untrusted_sources = []
        
        for source in sources:
            source_url = source if isinstance(source, str) else source.get('url', '')
            is_trusted = any(domain in source_url for domain in trusted_domains)
            if is_trusted:
                trusted_count += 1
            else:
                untrusted_sources.append(source_url)
                
        quantity_pass = source_count >= min_sources
        quality_ratio = trusted_count / max(source_count, 1)
        quality_pass = quality_ratio >= 0.6  # 60% trusted sources required
        
        overall_pass = quantity_pass and quality_pass
        score = (min(source_count / min_sources, 1.0) * 0.5 + quality_ratio * 0.5)
        
        return overall_pass, {
            'score': score,
            'source_count': source_count,
            'min_sources_required': min_sources,
            'trusted_count': trusted_count,
            'quality_ratio': quality_ratio,
            'untrusted_sources': untrusted_sources,
            'quantity_pass': quantity_pass,
            'quality_pass': quality_pass,
            'passed': overall_pass
        }
    
    def _check_adsense_compliance(self, content: str) -> Tuple[bool, Dict]:
        """Check AdSense policy compliance"""
        forbidden_phrases = self.config['adsense_compliance']['forbidden_phrases']
        required_disclaimers = self.config['adsense_compliance']['required_disclaimers']
        
        content_lower = content.lower()
        
        # Check for forbidden phrases
        violations = []
        for phrase in forbidden_phrases:
            if phrase.lower() in content_lower:
                violations.append(phrase)
                
        # Check for required disclaimers
        missing_disclaimers = []
        for disclaimer in required_disclaimers:
            if disclaimer.lower() not in content_lower:
                missing_disclaimers.append(disclaimer)
                
        compliance_pass = len(violations) == 0 and len(missing_disclaimers) <= 1
        
        # Score based on violations and missing disclaimers
        violation_penalty = len(violations) * 0.2
        disclaimer_penalty = len(missing_disclaimers) * 0.1
        score = max(0.0, 1.0 - violation_penalty - disclaimer_penalty)
        
        return compliance_pass, {
            'score': score,
            'violations': violations,
            'missing_disclaimers': missing_disclaimers,
            'violation_count': len(violations),
            'passed': compliance_pass
        }
    
    def _check_technical_seo(self, content: str, metadata: Dict) -> Tuple[bool, Dict]:
        """Check technical SEO requirements"""
        # Check for proper heading structure
        h1_count = len(re.findall(r'^# ', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        
        # Check for meta description equivalent
        first_paragraph = content.split('\n\n')[0] if '\n\n' in content else content[:200]
        meta_desc_length = len(first_paragraph)
        
        # Check for internal structure
        has_toc = 'table of contents' in content.lower() or '## contents' in content.lower()
        has_faq = 'faq' in content.lower() or 'frequently asked' in content.lower()
        
        # Scoring
        heading_score = min(1.0, (h1_count + h2_count * 0.5) / 6)  # Target: 1 H1 + 5 H2s
        meta_score = 1.0 if 150 <= meta_desc_length <= 300 else 0.5
        structure_score = (has_toc + has_faq) / 2
        
        overall_score = (heading_score + meta_score + structure_score) / 3
        passed = overall_score >= 0.7
        
        return passed, {
            'score': overall_score,
            'h1_count': h1_count,
            'h2_count': h2_count,
            'meta_desc_length': meta_desc_length,
            'has_toc': has_toc,
            'has_faq': has_faq,
            'heading_score': heading_score,
            'meta_score': meta_score,
            'structure_score': structure_score,
            'passed': passed
        }
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        # Entity coverage recommendations
        entity_check = results['checks'].get('entity_coverage', {})
        if not entity_check.get('passed', True):
            missing = entity_check.get('missing_fields', [])
            recommendations.append(f"Add missing entity fields: {', '.join(missing)}")
            
        # Content depth recommendations  
        depth_check = results['checks'].get('content_depth', {})
        if not depth_check.get('word_count_pass', True):
            current = depth_check.get('word_count', 0)
            required = depth_check.get('min_words_required', 2500)
            recommendations.append(f"Increase content length from {current} to {required} words")
            
        if depth_check.get('missing_sections'):
            missing_sections = depth_check['missing_sections']
            recommendations.append(f"Add missing sections: {', '.join(missing_sections)}")
            
        # Sources recommendations
        sources_check = results['checks'].get('information_sources', {})
        if not sources_check.get('quantity_pass', True):
            current = sources_check.get('source_count', 0) 
            required = sources_check.get('min_sources_required', 3)
            recommendations.append(f"Add more sources: {current}/{required} found")
            
        if sources_check.get('untrusted_sources'):
            recommendations.append("Replace untrusted sources with reputable ones")
            
        # AdSense compliance recommendations
        adsense_check = results['checks'].get('adsense_compliance', {})
        if adsense_check.get('violations'):
            violations = adsense_check['violations']
            recommendations.append(f"Remove AdSense policy violations: {', '.join(violations)}")
            
        if adsense_check.get('missing_disclaimers'):
            missing = adsense_check['missing_disclaimers']
            recommendations.append(f"Add required disclaimers: {', '.join(missing)}")
            
        # SEO recommendations
        seo_check = results['checks'].get('technical_seo', {})
        if not seo_check.get('passed', True):
            if seo_check.get('h1_count', 0) != 1:
                recommendations.append("Use exactly 1 H1 heading")
            if seo_check.get('h2_count', 0) < 4:
                recommendations.append("Add more H2 subheadings for better structure")
            if not seo_check.get('has_faq', False):
                recommendations.append("Add FAQ section for better user engagement")
                
        return recommendations


# Factory function for easy import
def create_hardgate_checker(config_path: str = None) -> V3HardGateChecker:
    """Create configured hard gate checker instance"""
    return V3HardGateChecker(config_path) if config_path else V3HardGateChecker()


if __name__ == "__main__":
    # Test the hard gate checker
    checker = V3HardGateChecker()
    
    # Sample test content
    test_content = """
    # Smart Plug Guide 2025
    
    ## Introduction
    Smart plugs are essential for home automation...
    
    ## Key Features
    - WiFi connectivity
    - Energy monitoring
    - Voice control
    
    ## Comparison
    We compared top smart plugs...
    
    ## Installation Guide
    Setup is straightforward...
    
    ## FAQ
    Q: Are smart plugs safe?
    A: Yes, when used properly...
    
    ## Conclusion
    Smart plugs offer great value...
    
    This is a research-based analysis. We may earn affiliate commissions.
    """
    
    test_metadata = {
        'entities': {
            'category': 'smart_plugs',
            'product_type': 'WiFi smart plug', 
            'use_case': 'home automation'
        },
        'sources': [
            'https://amazon.com/smart-plugs',
            'https://cnet.com/smart-home-review',
            'https://consumerreports.org/smart-plugs'
        ]
    }
    
    passed, results = checker.check_content(test_content, test_metadata)
    print(f"Test passed: {passed}")
    print(f"Overall score: {results['score']:.2f}")
    
    if not passed:
        print("Failures:")
        for failure in results['failures']:
            print(f"  - {failure}")
            
        print("Recommendations:")
        for rec in results['recommendations']:
            print(f"  - {rec}")