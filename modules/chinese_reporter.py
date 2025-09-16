#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文报告生成器
生成详细的中文质量检测报告，包含修复建议和固定的图片优化说明
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

class ChineseReporter:
    """中文质量检测报告生成器"""

    def __init__(self, config_path: str = "hugo_quality_standards.yml"):
        """初始化"""
        self.config = self._load_config(config_path)
        self.report_config = self.config.get('report_settings', {})

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def generate_report(self,
                       file_path: str,
                       quality_scores: Dict,
                       hugo_fix_results: Dict,
                       issues: List[Dict],
                       article_stats: Dict,
                       similarity_results: Optional[Dict] = None,
                       alt_analysis_results: Optional[Dict] = None) -> str:
        """生成完整的中文质量检测报告

        Args:
            file_path: 文章文件路径
            quality_scores: 质量评分结果
            hugo_fix_results: Hugo模板修复结果
            issues: 发现的问题列表
            article_stats: 文章统计信息
            similarity_results: 相似度检测结果
            alt_analysis_results: Alt文本分析结果

        Returns:
            完整的Markdown格式报告
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_name = Path(file_path).name if file_path else "未知文章"

        report_parts = []

        # 1. 报告标题
        report_parts.append(self._generate_header(file_name, timestamp, file_path))

        # 2. 检查总结
        report_parts.append(self._generate_summary(quality_scores, hugo_fix_results, issues, article_stats))

        # 3. Hugo模板自动修复结果
        report_parts.append(self._generate_hugo_fix_section(hugo_fix_results))

        # 4. 图片优化说明（引用独立文档）
        report_parts.append(self._generate_image_reference_section())

        # 5. 具体问题分析
        report_parts.append(self._generate_issues_analysis(issues, quality_scores))

        # 6. 自动修复代码
        report_parts.append(self._generate_auto_fix_code(hugo_fix_results))

        # 7. 相似度检测结果（如果有）
        if similarity_results:
            report_parts.append(self._generate_similarity_section(similarity_results))

        # 8. 检测统计
        report_parts.append(self._generate_statistics(article_stats, hugo_fix_results))

        return '\n\n'.join(report_parts)

    def _generate_header(self, file_name: str, timestamp: str, file_path: str) -> str:
        """生成报告头部"""
        return f"""# 📊 文章质量检测报告

**检测时间**: {timestamp}
**文章文件**: {file_name}
**文章路径**: {file_path}
**检测标准**: Hugo质量标准 + SEO优化检测

---"""

    def _generate_summary(self, quality_scores: Dict, hugo_fix_results: Dict, issues: List[Dict], article_stats: Dict) -> str:
        """生成检查总结"""
        total_score = quality_scores.get('total_score', 0)

        # 根据分数确定评级
        if total_score >= 95:
            grade_emoji = "🌟"
            grade_text = "优秀"
            grade_color = "green"
        elif total_score >= 85:
            grade_emoji = "✅"
            grade_text = "良好"
            grade_color = "blue"
        elif total_score >= 75:
            grade_emoji = "⚠️"
            grade_text = "需要优化"
            grade_color = "orange"
        else:
            grade_emoji = "❌"
            grade_text = "需要大幅改进"
            grade_color = "red"

        # 统计问题
        critical_issues = len([i for i in issues if i.get('severity') == 'critical'])
        warning_issues = len([i for i in issues if i.get('severity') == 'warning'])
        passed_checks = len([i for i in issues if i.get('status') == 'pass'])

        summary = f"""## 🎯 本次检查总结

**总体评分**: {total_score}/100 {grade_emoji} {grade_text}
**权重分配**: 内容深度40% + SEO技术20% + 内容结构15% + 可读性10% + 合规性10% + 预留5%

### 📈 分项得分"""

        # 生成各项得分
        dimensions = [
            ('content_depth', '内容深度质量', 40),
            ('seo_technical', 'SEO技术指标', 20),
            ('content_structure', '内容结构完整', 15),
            ('readability', '可读性指标', 10),
            ('adsense_compliance', 'AdSense合规性', 10)
        ]

        for dim_key, dim_name, weight in dimensions:
            score = quality_scores.get(dim_key, 0)
            if score >= 90:
                status_emoji = "✅"
                status_text = "优秀"
            elif score >= 80:
                status_emoji = "✅"
                status_text = "良好"
            elif score >= 70:
                status_emoji = "⚠️"
                status_text = "一般"
            else:
                status_emoji = "❌"
                status_text = "需要优化"

            summary += f"\n- {status_emoji} **{dim_name}**: {score}/100 ({status_text}) - 权重{weight}%"

        summary += f"""

### 📋 问题统计
- **通过项目**: {passed_checks}项
- **严重问题**: {critical_issues}项 (必须修改)
- **警告问题**: {warning_issues}项 (建议优化)
- **Hugo模板**: {len(hugo_fix_results.get('auto_fixed', []))}项自动修复，{len(hugo_fix_results.get('needs_manual', []))}项需确认"""

        return summary

    def _generate_hugo_fix_section(self, hugo_fix_results: Dict) -> str:
        """生成Hugo模板修复部分"""
        auto_fixed = hugo_fix_results.get('auto_fixed', [])
        needs_manual = hugo_fix_results.get('needs_manual', [])
        warnings = hugo_fix_results.get('warnings', [])

        section = """## 🔧 Hugo模板自动修复结果

> **说明**: Hugo模板合规性不计入质量评分，系统已自动修复以下问题："""

        if auto_fixed:
            section += "\n\n### ✅ 已自动修复"
            for i, fix in enumerate(auto_fixed, 1):
                section += f"\n{i}. {fix}"

        if needs_manual:
            section += "\n\n### ⚠️ 需要人工确认"
            for i, item in enumerate(needs_manual, 1):
                section += f"\n{i}. {item}"

        if warnings:
            section += "\n\n### 🚨 修复警告"
            for i, warning in enumerate(warnings, 1):
                section += f"\n{i}. {warning}"

        if not auto_fixed and not needs_manual and not warnings:
            section += "\n\n✅ Hugo模板格式完全符合标准，无需修复。"

        return section

    def _generate_image_reference_section(self) -> str:
        """生成图片优化指南引用部分"""
        return """## 📷 图片优化说明

> **⚠️ 检测系统局限性说明**
> 当前质量检测工具无法直接分析图片文件质量、大小、格式等技术指标。图片相关检测结果可能不完整，需要人工验证。

### 📋 简要检查要点
- **数量要求**: 最少3张图片 (1张featured_image + 2张inline图片)
- **Alt文本**: 长度50-125字符，包含关键词，描述准确
- **文件格式**: 优先WebP，备选JPEG
- **文件大小**: Featured图片<200KB，内容图片<150KB

### 📖 详细指南文档

**完整的图片优化标准和检查清单，请参考:**
📄 **[图片分析与优化指南](docs/image_analysis_guide.md)**

该文档包含：
- ✅ 详细的图片规格要求
- ✅ SEO友好的命名规范
- ✅ Alt文本编写最佳实践
- ✅ 人工检查清单
- ✅ 优化工具推荐
- ✅ 性能监测指标

> **建议**: 在发布文章前，请对照独立的图片指南文档进行完整检查"""

    def _generate_issues_analysis(self, issues: List[Dict], quality_scores: Dict) -> str:
        """生成具体问题分析"""
        section = "## 🔧 具体文章改动建议"

        # 分类问题
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        warning_issues = [i for i in issues if i.get('severity') == 'warning']
        suggestions = [i for i in issues if i.get('severity') == 'suggestion']

        if critical_issues:
            section += "\n\n### 🚨 严重问题 (必须修改)"
            for i, issue in enumerate(critical_issues, 1):
                section += f"\n{i}. **{issue.get('title', '未知问题')}**"
                section += f"\n   ```yaml"
                section += f"\n   问题: {issue.get('description', '无描述')}"
                if 'impact' in issue:
                    section += f"\n   影响: {issue['impact']}"
                if 'suggestion' in issue:
                    section += f"\n   修改建议: {issue['suggestion']}"
                section += f"\n   ```"

        if warning_issues:
            section += "\n\n### ⚠️ 中优先级问题"
            for i, issue in enumerate(warning_issues, 1):
                section += f"\n{i}. **{issue.get('title', '未知问题')}**"
                section += f"\n   ```yaml"
                section += f"\n   当前: {issue.get('current_value', '未知')}"
                section += f"\n   建议: {issue.get('suggestion', '无建议')}"
                section += f"\n   ```"

        if suggestions:
            section += "\n\n### 💡 优化建议"
            for i, issue in enumerate(suggestions, 1):
                section += f"\n{i}. **{issue.get('title', '未知建议')}**"
                if 'details' in issue:
                    section += f"\n   - {issue['details']}"

        if not critical_issues and not warning_issues and not suggestions:
            section += "\n\n✅ 文章质量良好，暂无需要修改的重要问题。"

        return section



    def _generate_auto_fix_code(self, hugo_fix_results: Dict) -> str:
        """生成自动修复代码"""
        if not hugo_fix_results.get('auto_fixed'):
            return ""

        return """## 📝 自动修复代码

**可直接复制的修改内容:**

> **注意**: 以下代码基于检测结果自动生成，使用前请确认内容正确性。

```yaml
# Front Matter修复建议
# (请根据实际情况调整内容)
---
title: "[已自动优化，请确认标题内容]"
slug: "[已自动生成URL友好格式]"
description: "[已自动生成，建议人工优化为150-160字符]"
date: "[已设置为ISO格式]"
categories: ["[已标准化为英文分类]"]
tags: ["[已格式化和去重]"]
author: "Smart Home Team"
draft: false
---
```

**修复说明:**
""" + '\n'.join(f"- {fix}" for fix in hugo_fix_results.get('auto_fixed', []))

    def _generate_similarity_section(self, similarity_results: Dict) -> str:
        """生成相似度检测部分"""
        similar_articles = similarity_results.get('similar_articles', [])
        max_similarity = similarity_results.get('max_similarity', 0)

        section = "## 🔍 相似度检测结果"

        if similar_articles:
            section += f"\n\n⚠️ 发现 {len(similar_articles)} 篇相似文章："
            for i, article in enumerate(similar_articles, 1):
                similarity = article.get('similarity', 0)
                file_name = article.get('file', '未知文章')
                section += f"\n{i}. **{file_name}** - 相似度: {similarity:.2%}"

            section += f"\n\n**最高相似度**: {max_similarity:.2%}"
            section += "\n\n**处理建议**:"
            section += "\n- 检查内容重复度，考虑增加差异化内容"
            section += "\n- 如确认为重复内容，建议删除或合并"
        else:
            section += "\n\n✅ 未发现高度相似的文章。"

        section += f"""

### 🛠️ 独立相似度检测工具

**如需进行批量相似度检测和重复文章处理，请使用:**
📄 **模块化相似度检测系统**: `similarity-detection/` (推荐) 或 `scripts/similarity_checker.py` (兼容性)

**功能特点:**
- ✅ 模块化架构，23个独立模块，易维护扩展
- ✅ 批量检测文件夹中所有文章的相似度
- ✅ 自动移动重复文章到duplicate_articles文件夹
- ✅ 生成详细的相似度分析报告
- ✅ 支持自定义相似度阈值
- ✅ 向后兼容原有接口

**使用方法:**
```bash
# 使用代理脚本 (推荐，保持兼容性)
python scripts/similarity_checker.py /path/to/articles

# 直接使用模块化系统 (高级用户)
cd similarity-detection && python main.py /path/to/articles

# 自动处理重复文章
python scripts/similarity_checker.py /path/to/articles --auto-process
```"""

        return section

    def _generate_statistics(self, article_stats: Dict, hugo_fix_results: Dict) -> str:
        """生成检测统计"""
        word_count = article_stats.get('word_count', 0)
        check_duration = article_stats.get('check_duration', 0)
        total_rules = article_stats.get('total_rules', 12)

        # 预计修改时间
        auto_fixes = len(hugo_fix_results.get('auto_fixed', []))
        manual_items = len(hugo_fix_results.get('needs_manual', []))
        estimated_time = manual_items * 5 + max(10, auto_fixes * 2)  # 估算分钟

        return f"""## 📊 检测统计

- **文章字数**: {word_count:,} 字
- **检测时长**: {check_duration:.1f} 秒
- **检测规则**: {total_rules} 项
- **自动修复**: {auto_fixes} 项
- **需要确认**: {manual_items} 项
- **预计修改时间**: {estimated_time} 分钟

**下次检测建议**: 修改完成后重新运行检测以验证改进效果

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**工具版本**: Hugo文章质量检测工具 v2.0"""

    def save_report(self, report_content: str, file_path: str, output_dir: str = "reports") -> str:
        """保存报告到文件

        Args:
            report_content: 报告内容
            file_path: 原文章文件路径
            output_dir: 输出目录

        Returns:
            保存的报告文件路径
        """
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_name = Path(file_path).stem if file_path else 'article'
        report_filename = f"quality_report_{timestamp}_{original_name}.md"

        # 保存文件
        report_file_path = output_path / report_filename
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return str(report_file_path)