#!/usr/bin/env python3
"""
SEO Internal Linking Optimization for AI Smart Home Hub

This script automatically adds internal links and related article recommendations
to improve SEO performance and user engagement.

Features:
- Automatic internal linking for key terms
- Related article recommendations based on content similarity
- Strategic external link placement
- Link anchor text optimization

Usage:
    python scripts/seo/optimize_internal_links.py
"""

import os
import glob
import re
import random
from pathlib import Path
from collections import defaultdict
import json

def extract_frontmatter_and_content(file_content):
    """Extract YAML frontmatter and content from markdown file"""
    if not file_content.startswith('---'):
        return {}, file_content
    
    try:
        parts = file_content.split('---', 2)
        if len(parts) < 3:
            return {}, file_content
        
        frontmatter_text = parts[1].strip()
        content = parts[2].strip()
        
        metadata = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Handle array fields
                if value.startswith('[') and value.endswith(']'):
                    value = [item.strip().strip('"').strip("'") 
                            for item in value[1:-1].split(',') if item.strip()]
                
                metadata[key] = value
        
        return metadata, content
        
    except Exception as e:
        print(f"⚠️ Error parsing frontmatter: {e}")
        return {}, file_content

# Smart Home Internal Link Mapping
INTERNAL_LINK_ANCHORS = {
    # Product categories
    "smart plug": "/categories/smart-plugs/",
    "smart plugs": "/categories/smart-plugs/",
    "smart bulb": "/categories/smart-bulbs/", 
    "smart bulbs": "/categories/smart-bulbs/",
    "smart speaker": "/categories/smart-speakers/",
    "smart speakers": "/categories/smart-speakers/",
    "security camera": "/categories/security-cameras/",
    "security cameras": "/categories/security-cameras/",
    "robot vacuum": "/categories/robot-vacuums/",
    "robot vacuums": "/categories/robot-vacuums/",
    "smart thermostat": "/categories/smart-thermostats/",
    "smart thermostats": "/categories/smart-thermostats/",
    
    # Technology terms
    "home automation": "/tags/home-automation/",
    "voice control": "/tags/voice-control/", 
    "wifi setup": "/tags/wifi-setup/",
    "energy saving": "/tags/energy-saving/",
    "smart home": "/tags/smart-home/",
    "IoT devices": "/tags/iot-devices/",
    "home security": "/tags/home-security/",
    
    # Popular brands
    "Amazon Alexa": "/tags/alexa/",
    "Google Assistant": "/tags/google-assistant/",
    "Apple HomeKit": "/tags/homekit/",
    "Samsung SmartThings": "/tags/smartthings/"
}

# Strategic external links for authority and user value
EXTERNAL_LINK_SUGGESTIONS = [
    {
        "anchor": "Amazon Smart Home Store",
        "url": "https://www.amazon.com/smart-home-devices/b?ie=UTF8&node=9818047011",
        "context": ["amazon", "buying", "store", "purchase"]
    },
    {
        "anchor": "Google Home ecosystem", 
        "url": "https://store.google.com/category/connected_home",
        "context": ["google", "ecosystem", "integration"]
    },
    {
        "anchor": "Smart Home Security Guide",
        "url": "https://www.consumer.ftc.gov/articles/0382-using-ip-cameras-safely",
        "context": ["security", "privacy", "safety"]
    },
    {
        "anchor": "Energy Star Smart Home Guidelines",
        "url": "https://www.energystar.gov/products/smart_home",
        "context": ["energy", "efficiency", "saving"]
    }
]

def load_all_articles(content_dir="content/articles"):
    """Load all articles with metadata for relationship analysis"""
    articles = []
    content_path = Path(content_dir)
    
    if not content_path.exists():
        print(f"❌ Content directory not found: {content_dir}")
        return articles
    
    for file_path in content_path.glob("**/*.md"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, article_content = extract_frontmatter_and_content(content)
            
            # Skip drafts
            if metadata.get('draft') == 'true':
                continue
                
            # Generate URL path
            slug = file_path.stem
            url_path = f"/articles/{slug}/"
            
            articles.append({
                'title': metadata.get('title', slug),
                'url': url_path,
                'slug': slug,
                'path': str(file_path),
                'tags': metadata.get('tags', []),
                'categories': metadata.get('categories', []),
                'content': article_content,
                'word_count': len(article_content.split())
            })
            
        except Exception as e:
            print(f"⚠️ Error loading {file_path}: {e}")
            continue
    
    return articles

def find_related_articles(target_article, all_articles, max_related=5):
    """Find related articles based on tags, categories, and content similarity"""
    related_scores = []
    
    target_tags = set(target_article.get('tags', []))
    target_categories = set(target_article.get('categories', []))
    target_words = set(target_article.get('content', '').lower().split())
    
    for article in all_articles:
        if article['slug'] == target_article['slug']:
            continue
            
        score = 0
        
        # Tag similarity (high weight)
        article_tags = set(article.get('tags', []))
        tag_overlap = len(target_tags.intersection(article_tags))
        score += tag_overlap * 3
        
        # Category similarity (medium weight) 
        article_categories = set(article.get('categories', []))
        category_overlap = len(target_categories.intersection(article_categories))
        score += category_overlap * 2
        
        # Content keyword similarity (low weight)
        article_words = set(article.get('content', '').lower().split())
        # Use common smart home keywords for comparison
        smart_home_keywords = {
            'smart', 'home', 'automation', 'device', 'control', 'setup',
            'review', 'best', 'guide', 'features', 'price', 'compatible'
        }
        target_keywords = target_words.intersection(smart_home_keywords)
        article_keywords = article_words.intersection(smart_home_keywords)
        keyword_overlap = len(target_keywords.intersection(article_keywords))
        score += keyword_overlap * 0.5
        
        if score > 0:
            related_scores.append((article, score))
    
    # Sort by score and return top results
    related_scores.sort(key=lambda x: x[1], reverse=True)
    return [article for article, score in related_scores[:max_related]]

def add_internal_links(content, existing_links=None):
    """Add internal links for key terms"""
    if existing_links is None:
        existing_links = set()
    
    modified_content = content
    added_links = []
    
    for anchor_text, link_url in INTERNAL_LINK_ANCHORS.items():
        # Skip if we already have a link to this URL
        if link_url in existing_links:
            continue
            
        # Case-insensitive search for the term
        pattern = re.compile(rf'\b{re.escape(anchor_text)}\b', re.IGNORECASE)
        matches = pattern.finditer(modified_content)
        
        # Only link the first occurrence to avoid over-optimization
        for match in matches:
            matched_text = match.group()
            
            # Check if already linked
            start, end = match.span()
            before = modified_content[max(0, start-10):start]
            after = modified_content[end:end+10]
            
            if '[' in before or ']' in after or '(' in before or ')' in after:
                continue  # Already part of a link
            
            # Create the link
            link_markdown = f"[{matched_text}]({link_url})"
            modified_content = modified_content[:start] + link_markdown + modified_content[end:]
            
            added_links.append({
                'anchor': matched_text,
                'url': link_url
            })
            
            existing_links.add(link_url)
            break  # Only link first occurrence
    
    return modified_content, added_links

def suggest_external_links(content, max_suggestions=2):
    """Suggest relevant external links based on content"""
    content_lower = content.lower()
    relevant_links = []
    
    for link_info in EXTERNAL_LINK_SUGGESTIONS:
        # Check if any context keywords appear in content
        if any(keyword in content_lower for keyword in link_info['context']):
            relevant_links.append(link_info)
    
    # Return a random sample of relevant links
    if relevant_links:
        return random.sample(relevant_links, min(len(relevant_links), max_suggestions))
    
    return []

def add_related_articles_section(content, related_articles):
    """Add related articles section to content"""
    if not related_articles:
        return content
    
    related_section = "\n\n---\n\n## Related Articles\n\n"
    
    for article in related_articles:
        related_section += f"- **[{article['title']}]({article['url']})**\n"
    
    # Add external links if space allows
    external_suggestions = suggest_external_links(content, max_suggestions=1)
    if external_suggestions:
        related_section += "\n### Additional Resources\n\n"
        for link_info in external_suggestions:
            related_section += f"- [{link_info['anchor']}]({link_info['url']})\n"
    
    return content + related_section

def optimize_article_links(article_path, all_articles):
    """Optimize internal links for a single article"""
    
    try:
        with open(article_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        metadata, content = extract_frontmatter_and_content(original_content)
        
        # Skip if already optimized
        if 'Related Articles' in content or len(re.findall(r'\[.*?\]\(.*?\)', content)) > 10:
            print(f"⏭️ Already optimized: {Path(article_path).name}")
            return None
        
        # Find current article info
        current_article = None
        for article in all_articles:
            if article['path'] == str(article_path):
                current_article = article
                break
        
        if not current_article:
            print(f"❌ Article not found in index: {article_path}")
            return None
        
        # Extract existing links to avoid duplication
        existing_links = set()
        link_pattern = r'\[.*?\]\((.*?)\)'
        for match in re.finditer(link_pattern, content):
            existing_links.add(match.group(1))
        
        # Add internal links
        optimized_content, added_links = add_internal_links(content, existing_links)
        
        # Find and add related articles
        related_articles = find_related_articles(current_article, all_articles, max_related=4)
        
        if related_articles:
            optimized_content = add_related_articles_section(optimized_content, related_articles)
        
        # Reconstruct full content with frontmatter
        if metadata:
            frontmatter_text = "---\n"
            for key, value in metadata.items():
                if isinstance(value, list):
                    frontmatter_text += f"{key}: {value}\n"
                else:
                    frontmatter_text += f'{key}: "{value}"\n'
            frontmatter_text += "---\n\n"
            
            final_content = frontmatter_text + optimized_content
        else:
            final_content = optimized_content
        
        # Write optimized content
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        result = {
            'file': Path(article_path).name,
            'added_internal_links': len(added_links),
            'related_articles': len(related_articles),
            'internal_links': added_links
        }
        
        print(f"✅ Optimized: {result['file']} (+{result['added_internal_links']} links, +{result['related_articles']} related)")
        return result
        
    except Exception as e:
        print(f"❌ Error optimizing {article_path}: {e}")
        return None

def main():
    print("🔗 SEO Internal Linking Optimization")
    print("=" * 50)
    
    # Load all articles first
    print("📚 Loading all articles...")
    all_articles = load_all_articles()
    
    if not all_articles:
        print("❌ No articles found to optimize")
        return
    
    print(f"📄 Found {len(all_articles)} articles")
    
    # Find markdown files to optimize
    content_path = Path("content/articles")
    md_files = list(content_path.glob("**/*.md"))
    
    results = []
    processed = 0
    
    for md_file in md_files:
        result = optimize_article_links(str(md_file), all_articles)
        if result:
            results.append(result)
        processed += 1
        
        if processed % 5 == 0:
            print(f"📊 Progress: {processed}/{len(md_files)} files processed")
    
    # Generate report
    if results:
        total_internal_links = sum(r['added_internal_links'] for r in results)
        total_related = sum(r['related_articles'] for r in results)
        
        print(f"\n🎉 Optimization completed!")
        print(f"   📄 Processed articles: {len(results)}")
        print(f"   🔗 Added internal links: {total_internal_links}")
        print(f"   📋 Added related sections: {len([r for r in results if r['related_articles'] > 0])}")
        print(f"   🔄 Total related articles: {total_related}")
        
        # Save optimization report
        report = {
            'timestamp': str(Path(__file__).stat().st_mtime),
            'processed_files': len(results),
            'total_internal_links': total_internal_links,
            'total_related_articles': total_related,
            'results': results
        }
        
        report_path = Path("data/seo_optimization_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 Report saved: {report_path}")
    else:
        print("\n⚠️ No articles were optimized")

if __name__ == "__main__":
    main()