#!/usr/bin/env python3
"""
Local Search Index Builder for AI Smart Home Hub

This script builds a JSON search index from all markdown content files,
enabling fast client-side search functionality using Lunr.js.

Usage:
    python scripts/seo/build_search_index.py

Generated files:
    - static/search_index.json: Search index for frontend consumption
    - data/search_stats.json: Search indexing statistics
"""

import os
import glob
import json
import re
from pathlib import Path
from datetime import datetime

def extract_frontmatter_and_content(file_content):
    """Extract YAML frontmatter and content from markdown file"""
    if not file_content.startswith('---'):
        return {}, file_content
    
    try:
        # Split frontmatter and content
        parts = file_content.split('---', 2)
        if len(parts) < 3:
            return {}, file_content
        
        frontmatter_text = parts[1].strip()
        content = parts[2].strip()
        
        # Parse basic YAML fields (simplified parser for common fields)
        metadata = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                # Handle array fields
                if value.startswith('[') and value.endswith(']'):
                    # Simple array parsing
                    value = [item.strip().strip('"').strip("'") 
                            for item in value[1:-1].split(',') if item.strip()]
                
                metadata[key] = value
        
        return metadata, content
        
    except Exception as e:
        print(f"⚠️ Error parsing frontmatter: {e}")
        return {}, file_content

def clean_content_for_search(content):
    """Clean markdown content for search indexing"""
    # Remove markdown syntax
    content = re.sub(r'#+\s*', '', content)  # Headers
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
    content = re.sub(r'\*(.*?)\*', r'\1', content)  # Italic
    content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)  # Links
    content = re.sub(r'`(.*?)`', r'\1', content)  # Inline code
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Code blocks
    content = re.sub(r'\n+', ' ', content)  # Multiple newlines
    content = re.sub(r'\s+', ' ', content)  # Multiple spaces
    
    return content.strip()

def extract_excerpt(content, max_length=200):
    """Extract a clean excerpt from content"""
    cleaned = clean_content_for_search(content)
    if len(cleaned) <= max_length:
        return cleaned
    
    # Find a good break point near max_length
    excerpt = cleaned[:max_length]
    last_sentence = excerpt.rfind('.')
    if last_sentence > max_length * 0.5:  # If we find a sentence end in the latter half
        return excerpt[:last_sentence + 1]
    else:
        return excerpt + "..."

def build_search_index(content_dir="content", output_path="static/search_index.json"):
    """Build search index from all markdown files"""
    
    print("🔍 Building local search index...")
    
    documents = []
    processed_files = 0
    error_files = 0
    
    # Ensure content directory exists
    content_path = Path(content_dir)
    if not content_path.exists():
        print(f"❌ Content directory not found: {content_dir}")
        return
    
    # Find all markdown files
    md_files = list(content_path.glob("**/*.md"))
    print(f"📄 Found {len(md_files)} markdown files")
    
    for file_path in md_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()
            
            # Extract metadata and content
            metadata, content = extract_frontmatter_and_content(file_content)
            
            # Skip empty or draft content
            if metadata.get('draft') == 'true' or not content.strip():
                continue
            
            # Generate URL path
            rel_path = file_path.relative_to(content_path)
            url_path = "/" + str(rel_path.with_suffix('').as_posix()) + "/"
            
            # Clean up URL for articles
            if url_path.startswith('/articles/'):
                url_path = url_path.replace('/articles/', '/articles/')
            
            # Extract search-friendly data
            title = metadata.get('title', file_path.stem)
            description = metadata.get('description', '')
            tags = metadata.get('tags', [])
            categories = metadata.get('categories', [])
            date = metadata.get('date', '')
            
            # Combine searchable text
            tags_text = ' '.join(tags) if isinstance(tags, list) else str(tags)
            categories_text = ' '.join(categories) if isinstance(categories, list) else str(categories)
            
            # Clean content for search
            clean_content = clean_content_for_search(content)
            excerpt = extract_excerpt(content)
            
            # Build search document
            document = {
                "id": str(processed_files),
                "title": title,
                "url": url_path,
                "excerpt": excerpt,
                "description": description,
                "date": str(date),
                "tags": tags_text,
                "categories": categories_text,
                "content": clean_content[:1000],  # Limit content length for performance
                "wordCount": len(clean_content.split())
            }
            
            documents.append(document)
            processed_files += 1
            
            if processed_files % 10 == 0:
                print(f"📄 Processed {processed_files} files...")
            
        except Exception as e:
            error_files += 1
            print(f"⚠️ Error processing {file_path}: {e}")
            continue
    
    # Create output directory
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write search index
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    # Save statistics
    stats = {
        "generated_at": datetime.now().isoformat(),
        "total_documents": len(documents),
        "processed_files": processed_files,
        "error_files": error_files,
        "index_size_kb": output_path.stat().st_size // 1024
    }
    
    stats_path = Path("data/search_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Search index generated successfully!")
    print(f"   📊 Documents indexed: {len(documents)}")
    print(f"   📁 Output file: {output_path}")
    print(f"   💾 Index size: {stats['index_size_kb']} KB")
    print(f"   ⚠️ Errors: {error_files}")
    
    return len(documents)

def build_search_config():
    """Generate search configuration for frontend"""
    config = {
        "lunr_version": "2.3.9",
        "search_fields": ["title", "description", "content", "tags", "categories"],
        "boost": {
            "title": 10,
            "description": 5,
            "tags": 3,
            "categories": 2,
            "content": 1
        },
        "search_options": {
            "fuzzy": 0.2,
            "prefix": True,
            "boost": True
        }
    }
    
    config_path = Path("static/search_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Search configuration saved to {config_path}")

def main():
    print("🚀 Local Search Index Builder")
    print("=" * 50)
    
    # Build search index
    document_count = build_search_index()
    
    if document_count > 0:
        # Generate search configuration
        build_search_config()
        
        print("\n🎉 Search index build completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Add search functionality to your Hugo templates")
        print("   2. Include Lunr.js library in your site")
        print("   3. Integrate the search interface")
    else:
        print("\n❌ No documents were indexed")

if __name__ == "__main__":
    main()