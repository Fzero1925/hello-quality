#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Reporter

Generates detailed Markdown reports for similarity detection results.
"""

from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class MarkdownReporter:
    """
    Generates comprehensive Markdown reports for similarity detection analysis.
    """

    def __init__(self, config: Dict):
        """
        Initialize Markdown reporter.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.comparison_window_days = config.get('comparison_window_days', 90)

    def generate_duplicate_analysis_report(self, detection_result: Dict[str, Any],
                                         output_file: str = "duplicate_analysis_report.md") -> str:
        """
        Generate detailed analysis report for duplicate groups.

        Args:
            detection_result: Detection results from graph clustering
            output_file: Output file path

        Returns:
            Report file path
        """
        print(f"📄 正在生成重复文章分析报告...")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])
        total_comparisons = detection_result.get('total_comparisons', 0)
        algorithm = detection_result.get('algorithm', 'graph_clustering')

        # Statistics
        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        total_articles = total_duplicates + len(unique_articles)

        report_parts = []

        # Report header
        report_parts.append(self._generate_report_header(
            timestamp, algorithm, total_articles, total_comparisons,
            len(duplicate_groups), total_duplicates, len(unique_articles)
        ))

        # Executive summary
        if duplicate_groups:
            report_parts.append(self._generate_executive_summary(
                duplicate_groups, total_duplicates, len(unique_articles), total_articles
            ))

        # Duplicate groups details
        if duplicate_groups:
            report_parts.append(self._generate_duplicate_groups_section(duplicate_groups))

        # SEO optimization suggestions
        if duplicate_groups:
            report_parts.append(self._generate_seo_optimization_section(duplicate_groups))

        # Unique articles section
        if unique_articles:
            report_parts.append(self._generate_unique_articles_section(unique_articles))

        # Technical details
        report_parts.append(self._generate_technical_section())

        # Generate report file
        report_content = '\n'.join(report_parts)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ 重复文章分析报告已生成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            return ""

    def _generate_report_header(self, timestamp: str, algorithm: str, total_articles: int,
                               total_comparisons: int, duplicate_groups_count: int,
                               total_duplicates: int, unique_articles_count: int) -> str:
        """Generate report header section."""
        return f"""# 📊 重复文章群组分析报告

**生成时间**: {timestamp}
**检测算法**: {algorithm} (全连接图聚类)
**检测阈值**: {self.similarity_threshold}
**总文章数**: {total_articles}
**比较次数**: {total_comparisons}
**重复群组**: {duplicate_groups_count} 个
**重复文章**: {total_duplicates} 篇
**独立文章**: {unique_articles_count} 篇
**重复率**: {(total_duplicates/total_articles*100):.1f}%

---"""

    def _generate_executive_summary(self, duplicate_groups: List[Dict],
                                   total_duplicates: int, unique_count: int,
                                   total_articles: int) -> str:
        """Generate executive summary section."""
        avg_group_size = total_duplicates / len(duplicate_groups) if duplicate_groups else 0

        return f"""
## 🎯 执行摘要

本次检测使用全连接图聚类算法，确保数学完整性，无遗漏任何相似关系。

### 关键发现
- 📦 发现 **{len(duplicate_groups)}** 个重复文章群组
- 🔸 涉及 **{total_duplicates}** 篇重复文章
- ✅ **{unique_count}** 篇文章完全独立
- 📈 平均每群组 **{avg_group_size:.1f}** 篇文章

### 算法优势
- ✅ **数学完整性**: 所有文章对都进行了比较分析
- ✅ **传递性处理**: A→B→C关系被正确识别为一个群组
- ✅ **零遗漏**: 连通分量算法确保不遗漏任何相似关系
- ✅ **SEO友好**: 每个群组保留最早发布的文章（SEO价值最高）
"""

    def _generate_duplicate_groups_section(self, duplicate_groups: List[Dict]) -> str:
        """Generate duplicate groups details section."""
        sections = ["\n## 📦 重复文章群组详情\n"]

        for i, group in enumerate(duplicate_groups, 1):
            base_article = group['base_article']
            articles = group['articles']
            topic = group.get('topic', 'Unknown')

            # Group header
            base_date = self._get_article_date(base_article).strftime('%Y-%m-%d')
            min_sim = min((a['similarity_to_base'] for a in articles if not a.get('is_base', False)), default=1.0)
            max_sim = max((a['similarity_to_base'] for a in articles if not a.get('is_base', False)), default=1.0)

            sections.append(f"""### 群组 {i}: {topic} 主题 ({len(articles)}篇文章)

**基准文章**: `{base_article['file_name']}` (发布日期: {base_date})
**群组主题**: {topic}
**相似度范围**: {min_sim:.3f} - {max_sim:.3f}

#### 文章列表:""")

            # Article details
            for article in articles:
                if article.get('is_base', False):
                    marker = "🔹 **基准**"
                    sim_text = "1.000"
                else:
                    marker = "🔸"
                    sim_text = f"{article['similarity_to_base']:.3f}"

                article_date = self._get_article_date(article).strftime('%Y-%m-%d')
                sections.append(f"- {marker} `{article['file_name']}` (相似度: {sim_text}, 日期: {article_date})")

            sections.append("")  # Empty line separator

        return '\n'.join(sections)

    def _generate_seo_optimization_section(self, duplicate_groups: List[Dict]) -> str:
        """Generate SEO optimization suggestions section."""
        sections = [f"""
## 🔧 SEO优化处理建议

基于最佳实践，为发现的{len(duplicate_groups)}个重复群组提供具体的SEO优化方案：

### 📋 处理策略总览

1. **301重定向 (推荐)**: 合并内容相似度>0.8的文章，设置永久重定向保护SEO权重
2. **Canonical标签**: 保留相似度0.5-0.8之间的文章，使用canonical标签指向主要版本
3. **内容差异化**: 相似度<0.7的文章可通过内容补充实现差异化

---"""]

        # Generate specific SEO recommendations for each group
        for i, group in enumerate(duplicate_groups, 1):
            base_article = group['base_article']
            articles = group['articles']
            topic = group.get('topic', 'Unknown')

            # Calculate group similarity statistics
            non_base_articles = [a for a in articles if not a.get('is_base', False)]
            if non_base_articles:
                max_similarity = max(a['similarity_to_base'] for a in non_base_articles)
                avg_similarity = sum(a['similarity_to_base'] for a in non_base_articles) / len(non_base_articles)
            else:
                max_similarity = avg_similarity = 0.0

            sections.append(f"""
### 群组 {i} 处理建议: {topic}

**基准文章**: `{base_article['file_name']}`
**群组相似度**: 平均 {avg_similarity:.3f}, 最高 {max_similarity:.3f}

#### 🎯 推荐策略:""")

            # Generate strategy based on similarity level
            if max_similarity >= 0.8:
                sections.extend(self._generate_301_redirect_strategy(base_article, non_base_articles))
            elif max_similarity >= 0.5:
                sections.extend(self._generate_canonical_strategy(base_article, non_base_articles))
            else:
                sections.extend(self._generate_differentiation_strategy())

            sections.append("")

        return '\n'.join(sections)

    def _generate_301_redirect_strategy(self, base_article: Dict, articles: List[Dict]) -> List[str]:
        """Generate 301 redirect strategy text."""
        strategy = [f"""
**301重定向方案** (相似度 ≥ 0.8)
- ✅ **保留**: `{base_article['file_name']}` (基准文章)
- 🔄 **重定向到基准文章**:"""]

        for article in articles:
            if article['similarity_to_base'] >= 0.8:
                strategy.append(f"  - `{article['file_name']}` → `{base_article['file_name']}`")

        strategy.extend([f"""
**操作步骤**:
1. 将重复文章的优质内容合并到基准文章 `{base_article['file_name']}`
2. 在网站配置中添加301重定向规则
3. 删除重复文章文件
4. 更新内部链接指向基准文章"""])

        return strategy

    def _generate_canonical_strategy(self, base_article: Dict, articles: List[Dict]) -> List[str]:
        """Generate canonical tag strategy text."""
        strategy = [f"""
**Canonical标签方案** (相似度 0.5-0.8)
- ✅ **主要文章**: `{base_article['file_name']}`
- 🏷️ **设置Canonical标签**:"""]

        for article in articles:
            if 0.5 <= article['similarity_to_base'] < 0.8:
                strategy.append(f"  - `{article['file_name']}` → canonical指向 `{base_article['file_name']}`")

        strategy.extend([f"""
**HTML标签示例**:
```html
<link rel="canonical" href="/articles/{base_article['file_name'].replace('.md', '.html')}" />
```

**操作说明**:
1. 保留所有文章，不删除任何内容
2. 在次要文章的HTML头部添加canonical标签
3. 告诉搜索引擎以基准文章为准进行索引"""])

        return strategy

    def _generate_differentiation_strategy(self) -> List[str]:
        """Generate content differentiation strategy text."""
        return ["""
**内容差异化方案** (相似度 < 0.5)
- 📝 **差异化处理**: 各文章保持独立，增强内容差异性

**优化建议**:
1. 为每篇文章补充不同的案例、数据或观点
2. 调整文章角度：技术实现 vs 用户指南 vs 产品比较
3. 添加独特的应用场景或解决方案
4. 确保每篇文章都有明确的目标受众"""]

    def _generate_unique_articles_section(self, unique_articles: List[Dict]) -> str:
        """Generate unique articles section."""
        sections = [f"""
## ✅ 独立文章列表 ({len(unique_articles)}篇)

以下文章与其他文章不存在显著相似性，为独立原创内容：

"""]

        for article in unique_articles:
            article_date = self._get_article_date(article).strftime('%Y-%m-%d')
            word_count = article.get('word_count', 0)
            sections.append(f"- `{article['file_name']}` (日期: {article_date}, 字数: {word_count})")

        return '\n'.join(sections)

    def _generate_technical_section(self) -> str:
        """Generate technical details section."""
        cross_topic_threshold = getattr(self, 'cross_topic_threshold', 0.7)

        return f"""

---

## 🔬 技术说明

### 算法原理
1. **相似度矩阵构建**: 计算所有文章对的TF-IDF余弦相似度
2. **图构建**: 相似度≥{self.similarity_threshold}的文章对形成连接
3. **连通分量**: 使用DFS算法找出所有连通分量(重复群组)
4. **基准选择**: 每个群组选择最早发布的文章作为基准保留

### 相似度计算
- **标题权重**: 30%
- **内容权重**: 70%
- **同主题阈值**: {self.similarity_threshold}
- **跨主题阈值**: {cross_topic_threshold}

### 时间窗口
- **检测窗口**: {self.comparison_window_days} 天
- **字数门槛**: {self.config.get('min_content_length', 1000)} 字

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*算法版本: Graph Clustering v2.3*"""

    def _get_article_date(self, article: Dict) -> datetime:
        """Get article effective date."""
        # This is a simplified version - in practice, you'd use DateHelper
        if 'effective_date' in article:
            return article['effective_date']
        elif 'created_time' in article:
            return article['created_time']
        elif 'modified_time' in article:
            return article['modified_time']
        else:
            return datetime.now()

    def generate_comparison_report(self, article1: Dict, article2: Dict,
                                 similarity_result: Dict[str, Any],
                                 output_file: str = "comparison_report.md") -> str:
        """
        Generate report for two-article comparison.

        Args:
            article1: First article information
            article2: Second article information
            similarity_result: Similarity calculation results
            output_file: Output file path

        Returns:
            Report file path
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_content = f"""# 📊 文章相似度对比报告

**生成时间**: {timestamp}
**检测阈值**: {self.similarity_threshold}

## 📝 对比文章

### 文章 A
- **文件**: `{article1.get('file_name', 'Unknown')}`
- **标题**: {article1.get('title', 'Unknown')}
- **字数**: {article1.get('word_count', 0)}
- **日期**: {self._get_article_date(article1).strftime('%Y-%m-%d')}

### 文章 B
- **文件**: `{article2.get('file_name', 'Unknown')}`
- **标题**: {article2.get('title', 'Unknown')}
- **字数**: {article2.get('word_count', 0)}
- **日期**: {self._get_article_date(article2).strftime('%Y-%m-%d')}

## 📊 相似度分析

- **标题相似度**: {similarity_result.get('title_similarity', 0):.3f}
- **内容相似度**: {similarity_result.get('content_similarity', 0):.3f}
- **综合相似度**: {similarity_result.get('overall_similarity', 0):.3f}
- **检测阈值**: {self.similarity_threshold:.3f}

## 🎯 结论

相似度评分: **{similarity_result.get('overall_similarity', 0):.3f}**

{'✅ **相似**: 超过检测阈值，被判定为相似内容' if similarity_result.get('is_similar', False) else '❌ **不相似**: 低于检测阈值，被判定为独立内容'}

---

*报告生成时间: {timestamp}*
*检测工具版本: v2.3*
"""

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ 对比报告已生成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 对比报告生成失败: {e}")
            return ""