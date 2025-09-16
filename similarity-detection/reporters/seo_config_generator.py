#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO Config Generator

Generates SEO optimization configuration files based on similarity detection results.
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class SEOConfigGenerator:
    """
    Generates SEO optimization configuration files for handling duplicate content.
    """

    def __init__(self, config: Dict):
        """
        Initialize SEO config generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config

    def generate_seo_config_files(self, detection_result: Dict[str, Any],
                                 output_dir: str = ".") -> Dict[str, str]:
        """
        Generate comprehensive SEO optimization configuration files.

        Args:
            detection_result: Detection results
            output_dir: Output directory

        Returns:
            Dictionary mapping config types to file paths
        """
        print(f"📁 正在生成SEO优化配置文件...")

        duplicate_groups = detection_result.get('duplicate_groups', [])

        # 301 redirect configuration
        redirects_config = {'redirects': []}

        # Canonical tag mappings
        canonical_mappings = {}

        # Content differentiation suggestions
        differentiation_suggestions = []

        for group in duplicate_groups:
            base_article = group['base_article']
            articles = group['articles']

            # Process non-base articles
            non_base_articles = [a for a in articles if not a.get('is_base', False)]
            if not non_base_articles:
                continue

            for article in non_base_articles:
                similarity = article['similarity_to_base']
                source_path = f"/articles/{article['file_name'].replace('.md', '.html')}"
                target_path = f"/articles/{base_article['file_name'].replace('.md', '.html')}"

                if similarity >= 0.8:
                    # 301 redirect for high similarity
                    redirects_config['redirects'].append({
                        'from': source_path,
                        'to': target_path,
                        'status': 301,
                        'reason': f'重复内容合并 (相似度: {similarity:.3f})',
                        'similarity': similarity
                    })

                elif similarity >= 0.5:
                    # Canonical tag for medium similarity
                    canonical_mappings[article['file_name']] = {
                        'canonical_url': target_path,
                        'canonical_file': base_article['file_name'],
                        'similarity': similarity,
                        'html_tag': f'<link rel="canonical" href="{target_path}" />'
                    }

                else:
                    # Content differentiation for low similarity
                    differentiation_suggestions.append({
                        'file': article['file_name'],
                        'base_file': base_article['file_name'],
                        'similarity': similarity,
                        'suggestions': [
                            '为文章补充不同的案例、数据或观点',
                            '调整文章角度：技术实现 vs 用户指南 vs 产品比较',
                            '添加独特的应用场景或解决方案',
                            '确保文章有明确的目标受众'
                        ]
                    })

        # Generate configuration files
        config_files = {}

        # 1. Generate redirects.yaml
        if redirects_config['redirects']:
            redirects_file = os.path.join(output_dir, 'redirects.yaml')
            try:
                with open(redirects_file, 'w', encoding='utf-8') as f:
                    yaml.dump(redirects_config, f, default_flow_style=False,
                            allow_unicode=True, sort_keys=False)
                config_files['redirects'] = redirects_file
                print(f"✅ 301重定向配置已生成: {redirects_file}")
            except Exception as e:
                print(f"❌ 生成redirects.yaml失败: {e}")

        # 2. Generate canonical_mappings.json
        if canonical_mappings:
            canonical_file = os.path.join(output_dir, 'canonical_mappings.json')
            try:
                with open(canonical_file, 'w', encoding='utf-8') as f:
                    json.dump(canonical_mappings, f, indent=2, ensure_ascii=False)
                config_files['canonical'] = canonical_file
                print(f"✅ Canonical标签配置已生成: {canonical_file}")
            except Exception as e:
                print(f"❌ 生成canonical_mappings.json失败: {e}")

        # 3. Generate content_differentiation.json
        if differentiation_suggestions:
            diff_file = os.path.join(output_dir, 'content_differentiation.json')
            try:
                with open(diff_file, 'w', encoding='utf-8') as f:
                    json.dump(differentiation_suggestions, f, indent=2, ensure_ascii=False)
                config_files['differentiation'] = diff_file
                print(f"✅ 内容差异化建议已生成: {diff_file}")
            except Exception as e:
                print(f"❌ 生成content_differentiation.json失败: {e}")

        # 4. Generate implementation guide
        readme_content = self._generate_implementation_guide(
            len(redirects_config['redirects']),
            len(canonical_mappings),
            len(differentiation_suggestions)
        )

        readme_file = os.path.join(output_dir, 'SEO_CONFIG_README.md')
        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            config_files['readme'] = readme_file
            print(f"✅ 实施说明文档已生成: {readme_file}")
        except Exception as e:
            print(f"❌ 生成说明文档失败: {e}")

        print(f"📊 配置文件生成完成，共生成 {len(config_files)} 个文件")
        return config_files

    def _generate_implementation_guide(self, redirect_count: int,
                                     canonical_count: int,
                                     differentiation_count: int) -> str:
        """Generate implementation guide content."""
        return f"""# SEO优化配置文件使用说明

本目录包含自动生成的SEO优化配置文件，帮助您处理网站中的重复内容问题。

## 📁 文件说明

### 1. redirects.yaml
**用途**: 301永久重定向配置
**适用场景**: 高相似度文章(≥0.8)的合并处理

**Hugo实施方法**:
```yaml
# 在Hugo配置文件(config.yaml)中添加:
outputs:
  home: ["HTML", "RSS", "REDIRECTS"]

# 将redirects.yaml内容添加到static/_redirects文件
```

**文件数量**: {redirect_count} 个重定向规则

### 2. canonical_mappings.json
**用途**: Canonical标签配置映射
**适用场景**: 中等相似度文章(0.5-0.8)的SEO优化

**实施方法**:
1. 在文章的Front Matter中添加canonical字段
2. 或在模板文件的<head>部分使用配置生成canonical标签

**文件数量**: {canonical_count} 个canonical映射

### 3. content_differentiation.json
**用途**: 低相似度文章的差异化建议
**适用场景**: 相似度<0.5的文章优化指导

**文件数量**: {differentiation_count} 个差异化建议

## 🔧 实施步骤

1. **备份网站**: 在实施任何更改前，确保备份您的网站
2. **301重定向**: 根据redirects.yaml配置您的重定向规则
3. **Canonical标签**: 根据canonical_mappings.json为相关文章添加canonical标签
4. **内容优化**: 参考差异化建议改进文章内容
5. **测试验证**: 实施后使用工具验证重定向和canonical标签是否正确

## ⚠️ 注意事项

- 301重定向会永久改变URL访问，请谨慎操作
- 实施前请确认重定向目标文章确实是您想要保留的版本
- canonical标签不会影响用户访问，但会影响搜索引擎索引
- 建议分批实施，先测试少量文章的效果

---
*配置文件生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*质量检测工具版本: v2.3*
"""

    def generate_hugo_redirects(self, detection_result: Dict[str, Any],
                               output_file: str = "_redirects") -> str:
        """
        Generate Hugo-specific redirects file.

        Args:
            detection_result: Detection results
            output_file: Output file path

        Returns:
            Generated file path
        """
        duplicate_groups = detection_result.get('duplicate_groups', [])
        redirects_lines = []

        redirects_lines.append("# Auto-generated redirects for duplicate content")
        redirects_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        redirects_lines.append("")

        redirect_count = 0

        for group in duplicate_groups:
            base_article = group['base_article']
            articles = group['articles']

            base_url = f"/articles/{base_article['file_name'].replace('.md', '.html')}"

            for article in articles:
                if article.get('is_base', False):
                    continue

                similarity = article['similarity_to_base']
                if similarity >= 0.8:
                    source_url = f"/articles/{article['file_name'].replace('.md', '.html')}"
                    redirects_lines.append(f"{source_url} {base_url} 301")
                    redirect_count += 1

        if redirect_count > 0:
            redirects_lines.append("")
            redirects_lines.append(f"# Total redirects: {redirect_count}")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(redirects_lines))

            print(f"✅ Hugo重定向文件已生成: {output_file} ({redirect_count} 个重定向)")
            return output_file

        except Exception as e:
            print(f"❌ 生成Hugo重定向文件失败: {e}")
            return ""

    def generate_nginx_redirects(self, detection_result: Dict[str, Any],
                                output_file: str = "nginx_redirects.conf") -> str:
        """
        Generate Nginx redirects configuration.

        Args:
            detection_result: Detection results
            output_file: Output file path

        Returns:
            Generated file path
        """
        duplicate_groups = detection_result.get('duplicate_groups', [])
        config_lines = []

        config_lines.append("# Auto-generated Nginx redirects for duplicate content")
        config_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        config_lines.append("# Add these lines to your Nginx server configuration")
        config_lines.append("")

        redirect_count = 0

        for group in duplicate_groups:
            base_article = group['base_article']
            articles = group['articles']

            base_url = f"/articles/{base_article['file_name'].replace('.md', '.html')}"

            for article in articles:
                if article.get('is_base', False):
                    continue

                similarity = article['similarity_to_base']
                if similarity >= 0.8:
                    source_url = f"/articles/{article['file_name'].replace('.md', '.html')}"
                    config_lines.append(f'rewrite ^{source_url}$ {base_url} permanent;')
                    redirect_count += 1

        if redirect_count > 0:
            config_lines.append("")
            config_lines.append(f"# Total redirects: {redirect_count}")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(config_lines))

            print(f"✅ Nginx重定向配置已生成: {output_file} ({redirect_count} 个重定向)")
            return output_file

        except Exception as e:
            print(f"❌ 生成Nginx重定向配置失败: {e}")
            return ""

    def generate_htaccess_redirects(self, detection_result: Dict[str, Any],
                                   output_file: str = ".htaccess") -> str:
        """
        Generate Apache .htaccess redirects.

        Args:
            detection_result: Detection results
            output_file: Output file path

        Returns:
            Generated file path
        """
        duplicate_groups = detection_result.get('duplicate_groups', [])
        config_lines = []

        config_lines.append("# Auto-generated Apache redirects for duplicate content")
        config_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        config_lines.append("")

        redirect_count = 0

        for group in duplicate_groups:
            base_article = group['base_article']
            articles = group['articles']

            base_url = f"/articles/{base_article['file_name'].replace('.md', '.html')}"

            for article in articles:
                if article.get('is_base', False):
                    continue

                similarity = article['similarity_to_base']
                if similarity >= 0.8:
                    source_url = f"/articles/{article['file_name'].replace('.md', '.html')}"
                    config_lines.append(f'Redirect 301 {source_url} {base_url}')
                    redirect_count += 1

        if redirect_count > 0:
            config_lines.append("")
            config_lines.append(f"# Total redirects: {redirect_count}")

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(config_lines))

            print(f"✅ Apache .htaccess文件已生成: {output_file} ({redirect_count} 个重定向)")
            return output_file

        except Exception as e:
            print(f"❌ 生成.htaccess文件失败: {e}")
            return ""

    def generate_json_ld_schema(self, detection_result: Dict[str, Any],
                               output_file: str = "seo_schema.json") -> str:
        """
        Generate JSON-LD schema markup for SEO.

        Args:
            detection_result: Detection results
            output_file: Output file path

        Returns:
            Generated file path
        """
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])

        # Collect all canonical/primary articles
        primary_articles = []

        # Add base articles from duplicate groups
        for group in duplicate_groups:
            primary_articles.append(group['base_article'])

        # Add unique articles
        primary_articles.extend(unique_articles)

        # Generate schema
        schema_data = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Website Articles",
            "description": f"Collection of {len(primary_articles)} unique articles",
            "numberOfItems": len(primary_articles),
            "itemListElement": []
        }

        for i, article in enumerate(primary_articles, 1):
            article_item = {
                "@type": "Article",
                "position": i,
                "headline": article.get('title', 'Untitled'),
                "url": f"/articles/{article['file_name'].replace('.md', '.html')}",
                "wordCount": article.get('word_count', 0),
                "datePublished": article.get('created_time', datetime.now()).isoformat() if isinstance(article.get('created_time'), datetime) else datetime.now().isoformat(),
                "dateModified": article.get('modified_time', datetime.now()).isoformat() if isinstance(article.get('modified_time'), datetime) else datetime.now().isoformat()
            }
            schema_data["itemListElement"].append(article_item)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"✅ JSON-LD schema已生成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 生成JSON-LD schema失败: {e}")
            return ""