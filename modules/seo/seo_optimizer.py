#!/usr/bin/env python3
"""
Advanced SEO Optimization Module for Hugo Website
针对Google AdSense和搜索引擎优化的完整SEO模块
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import yaml
from pathlib import Path

class SEOOptimizer:
    """
    Comprehensive SEO optimization system for smart home content
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._get_default_config()
        self.site_url = self.config.get('site_url', 'https://ai-smarthomehub.com')
        self.site_name = self.config.get('site_name', 'AI Smart Home Hub')
        
    def _get_default_config(self) -> Dict:
        """Get default SEO configuration"""
        return {
            'site_url': 'https://ai-smarthomehub.com',
            'site_name': 'AI Smart Home Hub',
            'organization_name': 'AI Smart Home Hub',
            'author': 'Smart Home Team',
            'default_image': '/images/smart-home-hero.jpg',
            'facebook_app_id': '',
            'twitter_username': '@aismarthomehub',
            'google_site_verification': '',
            'bing_site_verification': '',
            'pinterest_site_verification': ''
        }
    
    def generate_structured_data(self, content_type: str, data: Dict) -> Dict:
        """
        Generate Schema.org structured data for different content types
        
        Args:
            content_type: Type of content (article, product, review, etc.)
            data: Content data dictionary
            
        Returns:
            Schema.org JSON-LD structured data
        """
        
        if content_type == 'article':
            return self._generate_article_schema(data)
        elif content_type == 'product_review':
            return self._generate_product_review_schema(data)
        elif content_type == 'how_to':
            return self._generate_how_to_schema(data)
        elif content_type == 'faq':
            return self._generate_faq_schema(data)
        else:
            return self._generate_basic_webpage_schema(data)
    
    def _generate_article_schema(self, data: Dict) -> Dict:
        """Generate Article schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": data.get('title', ''),
            "description": data.get('description', ''),
            "url": urljoin(self.site_url, data.get('url', '')),
            "datePublished": data.get('date_published', datetime.now(timezone.utc).isoformat()),
            "dateModified": data.get('date_modified', datetime.now(timezone.utc).isoformat()),
            "author": {
                "@type": "Organization",
                "name": self.config['organization_name'],
                "url": self.site_url
            },
            "publisher": {
                "@type": "Organization",
                "name": self.site_name,
                "url": self.site_url,
                "logo": {
                    "@type": "ImageObject",
                    "url": urljoin(self.site_url, "/images/logo.png"),
                    "width": 200,
                    "height": 60
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": urljoin(self.site_url, data.get('url', ''))
            }
        }
        
        # Add image if available
        if data.get('image'):
            schema["image"] = {
                "@type": "ImageObject",
                "url": urljoin(self.site_url, data['image']),
                "width": 1200,
                "height": 630
            }
        
        # Add article section
        if data.get('category'):
            schema["articleSection"] = data['category']
            
        # Add keywords
        if data.get('keywords'):
            schema["keywords"] = data['keywords'] if isinstance(data['keywords'], list) else [data['keywords']]
            
        return schema
    
    def _generate_product_review_schema(self, data: Dict) -> Dict:
        """Generate Product Review schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "Review",
            "name": data.get('title', ''),
            "reviewBody": data.get('review_body', ''),
            "url": urljoin(self.site_url, data.get('url', '')),
            "datePublished": data.get('date_published', datetime.now(timezone.utc).isoformat()),
            "author": {
                "@type": "Organization",
                "name": self.config['organization_name']
            },
            "itemReviewed": {
                "@type": "Product",
                "name": data.get('product_name', ''),
                "description": data.get('product_description', ''),
                "brand": {
                    "@type": "Brand",
                    "name": data.get('brand', 'Unknown')
                },
                "category": data.get('category', ''),
                "offers": {
                    "@type": "Offer",
                    "price": data.get('price', ''),
                    "priceCurrency": data.get('currency', 'USD'),
                    "availability": "https://schema.org/InStock",
                    "url": data.get('product_url', '')
                }
            }
        }
        
        # Add rating if available
        if data.get('rating'):
            schema["reviewRating"] = {
                "@type": "Rating",
                "ratingValue": data['rating'],
                "bestRating": "5",
                "worstRating": "1"
            }
            
            # Add aggregate rating to product if available
            if data.get('review_count'):
                schema["itemReviewed"]["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": data['rating'],
                    "reviewCount": data['review_count'],
                    "bestRating": "5",
                    "worstRating": "1"
                }
        
        # Add product image
        if data.get('product_image'):
            schema["itemReviewed"]["image"] = urljoin(self.site_url, data['product_image'])
        
        return schema
    
    def _generate_how_to_schema(self, data: Dict) -> Dict:
        """Generate HowTo schema for installation guides"""
        schema = {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": data.get('title', ''),
            "description": data.get('description', ''),
            "url": urljoin(self.site_url, data.get('url', '')),
            "datePublished": data.get('date_published', datetime.now(timezone.utc).isoformat()),
            "author": {
                "@type": "Organization",
                "name": self.config['organization_name']
            },
            "totalTime": data.get('total_time', 'PT30M'),  # ISO 8601 duration
            "estimatedCost": {
                "@type": "MonetaryAmount",
                "currency": "USD",
                "value": data.get('estimated_cost', '0')
            }
        }
        
        # Add steps if provided
        if data.get('steps'):
            schema["step"] = []
            for i, step in enumerate(data['steps'], 1):
                step_schema = {
                    "@type": "HowToStep",
                    "name": step.get('name', f'Step {i}'),
                    "text": step.get('text', ''),
                    "position": i
                }
                
                if step.get('image'):
                    step_schema["image"] = urljoin(self.site_url, step['image'])
                    
                schema["step"].append(step_schema)
        
        # Add supply/tools if provided
        if data.get('supplies'):
            schema["supply"] = [
                {
                    "@type": "HowToSupply",
                    "name": supply
                } for supply in data['supplies']
            ]
        
        if data.get('tools'):
            schema["tool"] = [
                {
                    "@type": "HowToTool",
                    "name": tool
                } for tool in data['tools']
            ]
        
        return schema
    
    def _generate_faq_schema(self, data: Dict) -> Dict:
        """Generate FAQ schema"""
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "url": urljoin(self.site_url, data.get('url', '')),
            "mainEntity": []
        }
        
        for faq in data.get('faqs', []):
            faq_item = {
                "@type": "Question",
                "name": faq.get('question', ''),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq.get('answer', '')
                }
            }
            schema["mainEntity"].append(faq_item)
        
        return schema
    
    def _generate_basic_webpage_schema(self, data: Dict) -> Dict:
        """Generate basic WebPage schema"""
        return {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": data.get('title', ''),
            "description": data.get('description', ''),
            "url": urljoin(self.site_url, data.get('url', '')),
            "datePublished": data.get('date_published', datetime.now(timezone.utc).isoformat()),
            "author": {
                "@type": "Organization",
                "name": self.config['organization_name']
            },
            "publisher": {
                "@type": "Organization",
                "name": self.site_name,
                "url": self.site_url
            }
        }
    
    def generate_meta_tags(self, data: Dict) -> Dict[str, str]:
        """
        Generate comprehensive meta tags for SEO
        
        Args:
            data: Page data dictionary
            
        Returns:
            Dictionary of meta tags
        """
        
        tags = {}
        
        # Basic meta tags
        tags['title'] = data.get('title', self.site_name)
        tags['description'] = self._truncate_description(data.get('description', ''))
        tags['keywords'] = self._format_keywords(data.get('keywords', []))
        
        # Canonical URL
        tags['canonical'] = urljoin(self.site_url, data.get('url', ''))
        
        # Open Graph tags
        tags.update(self._generate_og_tags(data))
        
        # Twitter Card tags
        tags.update(self._generate_twitter_tags(data))
        
        # Additional SEO tags
        tags.update(self._generate_additional_tags(data))
        
        return tags
    
    def _generate_og_tags(self, data: Dict) -> Dict[str, str]:
        """Generate Open Graph tags"""
        og_tags = {
            'og:title': data.get('title', self.site_name),
            'og:description': self._truncate_description(data.get('description', ''), max_length=300),
            'og:url': urljoin(self.site_url, data.get('url', '')),
            'og:site_name': self.site_name,
            'og:type': data.get('og_type', 'article'),
            'og:locale': 'en_US'
        }
        
        # Add image
        image_url = data.get('image', self.config['default_image'])
        og_tags['og:image'] = urljoin(self.site_url, image_url)
        og_tags['og:image:width'] = '1200'
        og_tags['og:image:height'] = '630'
        og_tags['og:image:alt'] = data.get('image_alt', data.get('title', ''))
        
        # Add article specific tags
        if data.get('og_type') == 'article':
            if data.get('date_published'):
                og_tags['article:published_time'] = data['date_published']
            if data.get('date_modified'):
                og_tags['article:modified_time'] = data['date_modified']
            if data.get('author'):
                og_tags['article:author'] = data['author']
            if data.get('category'):
                og_tags['article:section'] = data['category']
            if data.get('tags'):
                for tag in data['tags'][:5]:  # Limit to 5 tags
                    og_tags[f'article:tag'] = tag
        
        return og_tags
    
    def _generate_twitter_tags(self, data: Dict) -> Dict[str, str]:
        """Generate Twitter Card tags"""
        twitter_tags = {
            'twitter:card': 'summary_large_image',
            'twitter:site': self.config['twitter_username'],
            'twitter:creator': self.config['twitter_username'],
            'twitter:title': data.get('title', self.site_name),
            'twitter:description': self._truncate_description(data.get('description', ''), max_length=200)
        }
        
        # Add image
        image_url = data.get('image', self.config['default_image'])
        twitter_tags['twitter:image'] = urljoin(self.site_url, image_url)
        twitter_tags['twitter:image:alt'] = data.get('image_alt', data.get('title', ''))
        
        return twitter_tags
    
    def _generate_additional_tags(self, data: Dict) -> Dict[str, str]:
        """Generate additional SEO tags"""
        additional_tags = {}
        
        # Robots meta
        additional_tags['robots'] = data.get('robots', 'index,follow')
        
        # Language and locale
        additional_tags['language'] = 'en-US'
        additional_tags['locale'] = 'en_US'
        
        # Author
        if data.get('author'):
            additional_tags['author'] = data['author']
        
        # Copyright
        current_year = datetime.now().year
        additional_tags['copyright'] = f'© {current_year} {self.site_name}'
        
        # Theme color
        additional_tags['theme-color'] = '#1e40af'
        
        # Verification tags
        if self.config.get('google_site_verification'):
            additional_tags['google-site-verification'] = self.config['google_site_verification']
        if self.config.get('bing_site_verification'):
            additional_tags['msvalidate.01'] = self.config['bing_site_verification']
        
        return additional_tags
    
    def optimize_content_for_seo(self, content: str, target_keyword: str) -> Dict[str, Any]:
        """
        Analyze and optimize content for SEO
        
        Args:
            content: Raw content text
            target_keyword: Primary target keyword
            
        Returns:
            SEO optimization analysis and suggestions
        """
        
        analysis = {
            'keyword_density': self._analyze_keyword_density(content, target_keyword),
            'readability': self._analyze_readability(content),
            'content_structure': self._analyze_content_structure(content),
            'internal_links': self._analyze_internal_links(content),
            'image_optimization': self._analyze_image_optimization(content),
            'meta_optimization': self._analyze_meta_optimization(content),
            'suggestions': []
        }
        
        # Generate optimization suggestions
        analysis['suggestions'] = self._generate_seo_suggestions(analysis, target_keyword)
        
        return analysis
    
    def _analyze_keyword_density(self, content: str, keyword: str) -> Dict:
        """Analyze keyword density"""
        words = content.lower().split()
        total_words = len(words)
        keyword_count = content.lower().count(keyword.lower())
        
        density = (keyword_count / total_words) * 100 if total_words > 0 else 0
        
        return {
            'target_keyword': keyword,
            'occurrences': keyword_count,
            'total_words': total_words,
            'density_percent': round(density, 2),
            'optimal_range': (1.0, 2.5),
            'status': 'good' if 1.0 <= density <= 2.5 else 'needs_improvement'
        }
    
    def _analyze_readability(self, content: str) -> Dict:
        """Analyze content readability"""
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        
        if sentences == 0 or words == 0:
            return {'status': 'error', 'score': 0}
        
        # Simplified readability calculation
        avg_sentence_length = words / sentences
        
        # Determine readability level
        if avg_sentence_length <= 15:
            level = 'very_easy'
            score = 90
        elif avg_sentence_length <= 20:
            level = 'easy'
            score = 80
        elif avg_sentence_length <= 25:
            level = 'moderate'
            score = 70
        else:
            level = 'difficult'
            score = 60
        
        return {
            'avg_sentence_length': round(avg_sentence_length, 1),
            'total_sentences': sentences,
            'total_words': words,
            'level': level,
            'score': score,
            'status': 'good' if score >= 70 else 'needs_improvement'
        }
    
    def _analyze_content_structure(self, content: str) -> Dict:
        """Analyze content structure for SEO"""
        # Count headings
        h1_count = len(re.findall(r'^# ', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))
        
        # Check for lists
        lists = len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE))
        
        # Check for emphasis
        bold_count = len(re.findall(r'\*\*(.+?)\*\*', content))
        italic_count = len(re.findall(r'\*(.+?)\*', content))
        
        return {
            'headings': {
                'h1': h1_count,
                'h2': h2_count,
                'h3': h3_count,
                'total': h1_count + h2_count + h3_count
            },
            'lists': lists,
            'emphasis': {
                'bold': bold_count,
                'italic': italic_count
            },
            'status': 'good' if h2_count >= 3 and lists > 0 else 'needs_improvement'
        }
    
    def _analyze_internal_links(self, content: str) -> Dict:
        """Analyze internal link structure"""
        # Find markdown links
        internal_links = re.findall(r'\[([^\]]+)\]\((/[^)]+)\)', content)
        external_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', content)
        
        return {
            'internal_count': len(internal_links),
            'external_count': len(external_links),
            'internal_links': internal_links[:5],  # First 5 for analysis
            'status': 'good' if len(internal_links) >= 3 else 'needs_improvement'
        }
    
    def _analyze_image_optimization(self, content: str) -> Dict:
        """Analyze image optimization"""
        # Find image references
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        
        images_with_alt = sum(1 for alt, src in images if alt.strip())
        total_images = len(images)
        
        return {
            'total_images': total_images,
            'images_with_alt': images_with_alt,
            'alt_text_coverage': (images_with_alt / total_images * 100) if total_images > 0 else 0,
            'status': 'good' if images_with_alt == total_images else 'needs_improvement'
        }
    
    def _analyze_meta_optimization(self, content: str) -> Dict:
        """Analyze meta tag optimization"""
        # This would typically check frontmatter, but we'll simulate
        return {
            'title_length': 0,  # Would check actual title
            'description_length': 0,  # Would check actual description
            'status': 'needs_check'
        }
    
    def _generate_seo_suggestions(self, analysis: Dict, target_keyword: str) -> List[str]:
        """Generate SEO improvement suggestions"""
        suggestions = []
        
        # Keyword density suggestions
        kw_density = analysis['keyword_density']
        if kw_density['density_percent'] < 1.0:
            suggestions.append(f"Increase keyword '{target_keyword}' density to 1-2.5% (currently {kw_density['density_percent']}%)")
        elif kw_density['density_percent'] > 2.5:
            suggestions.append(f"Reduce keyword '{target_keyword}' density to avoid over-optimization (currently {kw_density['density_percent']}%)")
        
        # Readability suggestions
        readability = analysis['readability']
        if readability['avg_sentence_length'] > 25:
            suggestions.append("Break down long sentences to improve readability")
        
        # Structure suggestions
        structure = analysis['content_structure']
        if structure['headings']['h2'] < 3:
            suggestions.append("Add more H2 headings to improve content structure")
        if structure['lists'] == 0:
            suggestions.append("Add bullet points or numbered lists to improve scannability")
        
        # Internal linking suggestions
        links = analysis['internal_links']
        if links['internal_count'] < 3:
            suggestions.append("Add more internal links to related content")
        
        # Image optimization suggestions
        images = analysis['image_optimization']
        if images['total_images'] > 0 and images['alt_text_coverage'] < 100:
            suggestions.append("Add descriptive alt text to all images")
        
        return suggestions
    
    def _truncate_description(self, description: str, max_length: int = 160) -> str:
        """Truncate description to SEO-friendly length"""
        if len(description) <= max_length:
            return description
        
        # Find the last complete word before the limit
        truncated = description[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + '...'
    
    def _format_keywords(self, keywords: List[str]) -> str:
        """Format keywords for meta tag"""
        if isinstance(keywords, list):
            return ', '.join(keywords[:10])  # Limit to 10 keywords
        return str(keywords)
    
    def generate_sitemap_data(self, pages: List[Dict]) -> str:
        """Generate sitemap.xml data"""
        sitemap_entries = []
        
        for page in pages:
            url = urljoin(self.site_url, page.get('url', ''))
            lastmod = page.get('date_modified', page.get('date_published', datetime.now().isoformat()))
            changefreq = page.get('changefreq', 'weekly')
            priority = page.get('priority', 0.8)
            
            entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
            sitemap_entries.append(entry)
        
        sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemap_entries)}
</urlset>"""
        
        return sitemap_xml

    def generate_organization_schema(self, data: Optional[Dict] = None) -> str:
        """Generate Organization structured data schema"""
        org_data = {
            'name': self.site_name,
            'url': self.site_url,
            'logo': f"{self.site_url}/images/logo.png",
            'description': 'Expert reviews and buying guides for smart home devices'
        }
        
        if data:
            org_data.update(data)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            **org_data
        }
        
        return json.dumps(schema, indent=2)

    def generate_article_schema(self, data: Dict) -> str:
        """Generate Article structured data schema"""
        schema = self._generate_article_schema(data)
        return json.dumps(schema, indent=2)

    def generate_review_schema(self, data: Dict) -> str:
        """Generate Review structured data schema"""
        schema = self._generate_product_review_schema(data)
        return json.dumps(schema, indent=2)

    def calculate_seo_score(self, data: Dict) -> float:
        """Calculate overall SEO score for content"""
        title = data.get('title', '')
        description = data.get('description', '')
        content = data.get('content', '')
        
        score = 0.0
        max_score = 100.0
        
        # Title optimization (20 points)
        if 30 <= len(title) <= 60:
            score += 20
        elif len(title) > 0:
            score += 10
        
        # Description optimization (20 points)
        if 120 <= len(description) <= 160:
            score += 20
        elif len(description) > 0:
            score += 10
        
        # Content length (20 points)
        word_count = len(content.split()) if content else 0
        if word_count >= 2000:
            score += 20
        elif word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        
        # URL structure (10 points)
        url = data.get('url', '')
        if url and len(url.split('/')) >= 4:
            score += 10
        
        # Category and tags (10 points)
        if data.get('category') or data.get('tags'):
            score += 10
        
        # Images (10 points)
        if data.get('featured_image') or 'img' in content.lower():
            score += 10
        
        # Review rating (10 points)
        if data.get('review_rating') or data.get('rating'):
            score += 10
        
        return score / max_score

# Usage example and testing
if __name__ == "__main__":
    seo = SEOOptimizer()
    
    # Test structured data generation
    article_data = {
        'title': 'Best Smart Plugs 2025: Complete Buying Guide',
        'description': 'Expert reviews of the top smart plugs for home automation',
        'url': '/reviews/best-smart-plugs-2025/',
        'keywords': ['smart plugs', 'home automation', 'alexa', 'google home'],
        'image': '/images/smart-plugs-hero.jpg',
        'category': 'Smart Home',
        'rating': 4.5,
        'review_count': 150
    }
    
    # Generate article schema
    schema = seo.generate_structured_data('article', article_data)
    print("Generated Schema.org JSON-LD:")
    print(json.dumps(schema, indent=2))
    
    # Generate meta tags
    meta_tags = seo.generate_meta_tags(article_data)
    print("\nGenerated Meta Tags:")
    for key, value in meta_tags.items():
        print(f"{key}: {value}")
    
    # Test SEO analysis
    sample_content = """
    # Best Smart Plugs 2025
    
    Smart plugs are essential for modern home automation. These devices allow you to control any plugged-in device remotely.
    
    ## Top Features to Consider
    
    When choosing smart plugs, consider these important factors:
    - Voice control compatibility
    - Energy monitoring capabilities
    - App functionality
    
    ## Best Smart Plug Reviews
    
    Our testing shows that smart plugs with energy monitoring provide the best value.
    """
    
    seo_analysis = seo.optimize_content_for_seo(sample_content, 'smart plugs')
    print("\nSEO Analysis:")
    print(json.dumps(seo_analysis, indent=2, default=str))