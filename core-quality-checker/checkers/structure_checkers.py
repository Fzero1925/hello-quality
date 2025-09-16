#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构检测器模块

包含文章结构相关的检测器，从原始quality_check.py重构而来。
"""

import re
from typing import Dict, Any, List
from ..utils.base_checker import StructureChecker
from ..utils.validation_result import ValidationResult, CheckStatus
from ..utils.content_parser import ContentParser


class SectionStructureChecker(StructureChecker):
    """章节结构检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查文章的章节结构

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Section structure check disabled")

        # 获取配置
        quality_rules = self.config.get('quality_rules', {})
        min_sections = quality_rules.get('min_sections', 5)

        # 提取标题结构
        headings = ContentParser.extract_headings(content)

        # 统计各级标题
        h1_count = len(headings['h1'])
        h2_count = len(headings['h2'])
        h3_count = len(headings['h3'])
        total_sections = h2_count  # 主要以H2作为章节计算

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('h1_count', h1_count)
        result.set_metadata('h2_count', h2_count)
        result.set_metadata('h3_count', h3_count)
        result.set_metadata('section_count', total_sections)
        result.set_metadata('headings_structure', headings)

        # 检查H1标题数量（应该只有一个）
        if h1_count > 1:
            result.status = CheckStatus.WARNING
            result.score = max(result.score - 10, 70)
            result.add_issue(f"Multiple H1 titles found: {h1_count} (should be 1)", "warning")
            result.add_suggestion("Use only one H1 title per article for better SEO")

        elif h1_count == 0:
            result.status = CheckStatus.WARNING
            result.score = max(result.score - 15, 65)
            result.add_issue("No H1 title found", "warning")
            result.add_suggestion("Add an H1 title to improve content structure")

        # 检查H2章节数量
        if h2_count < min_sections:
            result.status = CheckStatus.ERROR
            result.score = max(50, (h2_count / min_sections) * 100)
            result.add_issue(f"Too few sections: {h2_count} (minimum: {min_sections})", "error")
            result.add_suggestion(f"Add {min_sections - h2_count} more H2 sections to improve content structure")

        else:
            # 根据章节数量给出评分
            if h2_count >= min_sections * 1.5:
                result.score = 100.0
            else:
                result.score = 85 + ((h2_count - min_sections) / min_sections) * 15

        # 检查层次结构的合理性
        structure_issues = self._analyze_heading_hierarchy(headings)
        if structure_issues:
            result.score = max(result.score - len(structure_issues) * 5, 60)
            for issue in structure_issues:
                result.add_issue(issue, "warning")
            result.add_suggestion("Improve heading hierarchy for better readability")

        return result

    def _analyze_heading_hierarchy(self, headings: Dict[str, List[str]]) -> List[str]:
        """分析标题层次结构问题"""
        issues = []

        # 检查是否有过多的H3相对于H2
        h2_count = len(headings['h2'])
        h3_count = len(headings['h3'])

        if h2_count > 0 and h3_count > h2_count * 3:
            issues.append(f"Too many H3 subsections ({h3_count}) relative to H2 sections ({h2_count})")

        # 检查是否有深层嵌套
        h4_count = len(headings['h4'])
        h5_count = len(headings['h5'])
        h6_count = len(headings['h6'])

        if h5_count > 0 or h6_count > 0:
            issues.append("Avoid using H5/H6 headings - content may be too deeply nested")

        if h4_count > h3_count * 2:
            issues.append(f"Too many H4 subsections ({h4_count}) - consider flattening content structure")

        return issues


class FaqSectionChecker(StructureChecker):
    """FAQ章节检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查是否包含FAQ章节

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "FAQ section check disabled")

        quality_rules = self.config.get('quality_rules', {})

        if not quality_rules.get('require_faq', True):
            return self.create_result(CheckStatus.PASS, 100.0, "FAQ section not required")

        # FAQ章节模式
        faq_patterns = [
            r'##.*FAQ',
            r'##.*Frequently.*Asked',
            r'##.*Questions.*Answers',
            r'##.*常见问题',
            r'##.*问答',
            r'##.*Q&A'
        ]

        # 检查是否存在FAQ章节
        has_faq = ContentParser.check_section_exists(content, faq_patterns)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('has_faq', has_faq)

        if not has_faq:
            result.status = CheckStatus.ERROR
            result.score = 70.0
            result.add_issue("Missing FAQ section", "error")
            result.add_suggestion("Add a FAQ section to address common user questions")

        else:
            # 分析FAQ质量
            faq_quality_score = self._analyze_faq_quality(content)
            result.score = max(85, 85 + faq_quality_score * 15)
            result.set_metadata('faq_quality_score', faq_quality_score)

            if faq_quality_score < 0.5:
                result.add_issue("FAQ section exists but may lack sufficient content", "warning")
                result.add_suggestion("Expand FAQ section with more detailed Q&A pairs")

        return result

    def _analyze_faq_quality(self, content: str) -> float:
        """分析FAQ章节质量"""
        # 查找FAQ章节后的内容
        faq_match = re.search(r'##.*(?:FAQ|Frequently.*Asked|Questions.*Answers|常见问题|问答|Q&A)(.*?)(?=##|$)',
                             content, re.IGNORECASE | re.DOTALL)

        if not faq_match:
            return 0.0

        faq_content = faq_match.group(1)

        # 计算Q&A对数量
        question_patterns = [
            r'\*\*Q[:\s]',  # **Q: 格式
            r'Q\d+[:\s]',   # Q1: 格式
            r'问[：:]',      # 中文问:
            r'\d+\.\s*\w+.*\?',  # 1. What is...? 格式
        ]

        question_count = 0
        for pattern in question_patterns:
            question_count += len(re.findall(pattern, faq_content, re.IGNORECASE))

        # 根据问题数量和内容长度评分
        if question_count >= 5:
            return 1.0
        elif question_count >= 3:
            return 0.8
        elif question_count >= 1:
            return 0.6
        else:
            # 如果没有明确的Q&A格式，检查内容长度
            if len(faq_content.strip()) > 200:
                return 0.4
            else:
                return 0.2


class ConclusionChecker(StructureChecker):
    """结论部分检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查是否包含结论部分

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Conclusion check disabled")

        quality_rules = self.config.get('quality_rules', {})

        if not quality_rules.get('require_conclusion', True):
            return self.create_result(CheckStatus.PASS, 100.0, "Conclusion section not required")

        # 结论章节模式
        conclusion_patterns = [
            r'##.*Conclusion',
            r'##.*Summary',
            r'##.*Final.*Thoughts',
            r'##.*总结',
            r'##.*结论',
            r'##.*最后',
            r'##.*小结'
        ]

        # 检查是否存在结论章节
        has_conclusion = ContentParser.check_section_exists(content, conclusion_patterns)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('has_conclusion', has_conclusion)

        if not has_conclusion:
            result.status = CheckStatus.ERROR
            result.score = 75.0
            result.add_issue("Missing conclusion section", "error")
            result.add_suggestion("Add a conclusion section to summarize key points")

        else:
            # 分析结论质量
            conclusion_quality = self._analyze_conclusion_quality(content)
            result.score = max(85, 85 + conclusion_quality * 15)
            result.set_metadata('conclusion_quality', conclusion_quality)

            if conclusion_quality < 0.5:
                result.add_issue("Conclusion section exists but may be too brief", "warning")
                result.add_suggestion("Expand conclusion with more detailed summary and recommendations")

        return result

    def _analyze_conclusion_quality(self, content: str) -> float:
        """分析结论章节质量"""
        # 查找结论章节后的内容
        conclusion_match = re.search(r'##.*(?:Conclusion|Summary|Final.*Thoughts|总结|结论|最后|小结)(.*?)(?=##|$)',
                                   content, re.IGNORECASE | re.DOTALL)

        if not conclusion_match:
            return 0.0

        conclusion_content = conclusion_match.group(1).strip()

        # 根据内容长度和质量指标评分
        word_count = len(conclusion_content.split())

        if word_count >= 150:
            return 1.0
        elif word_count >= 100:
            return 0.8
        elif word_count >= 50:
            return 0.6
        elif word_count >= 20:
            return 0.4
        else:
            return 0.2


class FrontMatterChecker(StructureChecker):
    """Front Matter完整性检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查Front Matter的完整性

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Front matter check disabled")

        # 解析Front Matter
        try:
            fm_text, _, has_fm = ContentParser.extract_front_matter(content)
            if has_fm:
                fm_data = ContentParser.parse_front_matter_data(fm_text)
            else:
                fm_data = {}
        except:
            fm_data = {}

        # 必需字段
        required_fields = ['title', 'description', 'date', 'categories', 'tags', 'keywords']
        missing_fields = []

        for field in required_fields:
            if field not in fm_data or not fm_data[field]:
                missing_fields.append(field)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('has_front_matter', has_fm)
        result.set_metadata('missing_fields', missing_fields)
        result.set_metadata('total_fields', len(required_fields))
        result.set_metadata('present_fields', len(required_fields) - len(missing_fields))

        if not has_fm:
            result.status = CheckStatus.CRITICAL
            result.score = 30.0
            result.add_issue("No front matter found", "critical")
            result.add_suggestion("Add complete front matter with all required fields")

        elif missing_fields:
            result.status = CheckStatus.ERROR
            result.score = max(50, 100 - len(missing_fields) * 15)
            result.add_issue(f"Missing front matter fields: {', '.join(missing_fields)}", "error")
            result.add_suggestion(f"Add missing fields: {', '.join(missing_fields)}")

        else:
            # 检查字段质量
            quality_issues = self._analyze_front_matter_quality(fm_data)
            if quality_issues:
                result.score = max(80, 100 - len(quality_issues) * 5)
                for issue in quality_issues:
                    result.add_issue(issue, "warning")
                result.add_suggestion("Improve front matter field quality")

        return result

    def _analyze_front_matter_quality(self, fm_data: Dict[str, Any]) -> List[str]:
        """分析Front Matter质量问题"""
        issues = []

        # 检查标题长度
        title = fm_data.get('title', '')
        if title:
            if len(title) > 60:
                issues.append(f"Title too long: {len(title)} characters (recommended: ≤60)")
            elif len(title) < 30:
                issues.append(f"Title too short: {len(title)} characters (recommended: ≥30)")

        # 检查描述长度
        description = fm_data.get('description', '')
        if description:
            if len(description) > 160:
                issues.append(f"Description too long: {len(description)} characters (recommended: ≤160)")
            elif len(description) < 120:
                issues.append(f"Description too short: {len(description)} characters (recommended: ≥120)")

        # 检查分类格式
        categories = fm_data.get('categories', [])
        if isinstance(categories, str):
            issues.append("Categories should be a list, not a string")
        elif isinstance(categories, list) and len(categories) == 0:
            issues.append("At least one category is required")

        # 检查标签
        tags = fm_data.get('tags', [])
        if isinstance(tags, list) and len(tags) > 10:
            issues.append(f"Too many tags: {len(tags)} (recommended: ≤10)")

        return issues


class AuthorDateChecker(StructureChecker):
    """作者和日期检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查作者和日期字段

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Author and date check disabled")

        quality_rules = self.config.get('quality_rules', {})

        if not quality_rules.get('require_author_and_date', True):
            return self.create_result(CheckStatus.PASS, 100.0, "Author and date not required")

        # 解析Front Matter
        try:
            fm_text, _, has_fm = ContentParser.extract_front_matter(content)
            if has_fm:
                fm_data = ContentParser.parse_front_matter_data(fm_text)
            else:
                fm_data = {}
        except:
            fm_data = {}

        # 检查字段存在性
        has_author = 'author' in fm_data and fm_data['author']
        has_date = 'date' in fm_data and fm_data['date']

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('has_author', has_author)
        result.set_metadata('has_date', has_date)

        issues = []
        if not has_author:
            issues.append("Missing author field in front matter")

        if not has_date:
            issues.append("Missing date field in front matter")

        if issues:
            result.status = CheckStatus.ERROR
            result.score = 60.0 if len(issues) == 2 else 80.0
            for issue in issues:
                result.add_issue(issue, "error")
            result.add_suggestion("Add author and date fields to front matter for proper attribution")

        else:
            # 检查字段质量
            quality_score = self._analyze_author_date_quality(fm_data)
            result.score = max(85, 85 + quality_score * 15)
            result.set_metadata('quality_score', quality_score)

        return result

    def _analyze_author_date_quality(self, fm_data: Dict[str, Any]) -> float:
        """分析作者和日期字段质量"""
        quality_score = 0.0

        # 检查作者字段
        author = fm_data.get('author', '')
        if author:
            if len(author) > 3 and author != 'Author':  # 非默认值
                quality_score += 0.5
            else:
                quality_score += 0.2

        # 检查日期格式
        date = fm_data.get('date', '')
        if date:
            # 检查是否为标准ISO格式
            iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
            if re.match(iso_pattern, str(date)):
                quality_score += 0.5
            else:
                quality_score += 0.3

        return quality_score