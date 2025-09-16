#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO检测器模块

包含SEO相关的检测器，从原始quality_check.py重构而来。
"""

import re
from typing import Dict, Any, List, Tuple
from ..utils.base_checker import SEOChecker
from ..utils.validation_result import ValidationResult, CheckStatus
from ..utils.content_parser import ContentParser


class ImageChecker(SEOChecker):
    """图片数量检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查图片数量是否符合要求

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Image count check disabled")

        # 提取图片
        images = ContentParser.extract_images(content)
        image_count = len(images)

        # 获取配置
        quality_rules = self.config.get('quality_rules', {})
        min_images = quality_rules.get('min_images', 3)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('image_count', image_count)
        result.set_metadata('images', images)

        if image_count < min_images:
            result.status = CheckStatus.ERROR
            result.score = max(0, (image_count / min_images) * 100)
            result.add_issue(f"Too few images: {image_count} (minimum: {min_images})", "error")
            result.add_suggestion(f"Add {min_images - image_count} more images to improve content quality")

        elif image_count >= min_images:
            # 根据图片数量给出评分
            if image_count >= min_images * 2:
                result.score = 100.0
            else:
                result.score = 85 + ((image_count - min_images) / min_images) * 15

        return result


class AltTextChecker(SEOChecker):
    """Alt文本合规性检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查Alt文本的合规性

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Alt text check disabled")

        quality_rules = self.config.get('quality_rules', {})
        seo_config = self.config.get('seo', {})

        if not quality_rules.get('ban_words_in_alt', True):
            return self.create_result(CheckStatus.PASS, 100.0, "Alt text validation disabled")

        # 获取禁用词汇和长度限制
        banned_words = seo_config.get('banned_alt_words', [])
        max_alt_length = seo_config.get('max_alt_length', 125)
        min_alt_length = seo_config.get('min_alt_length', 15)

        # 提取图片和Alt文本
        images = ContentParser.extract_images(content)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('total_images', len(images))

        if not images:
            result.score = 85.0
            result.add_issue("No images found for alt text analysis", "warning")
            return result

        violations = []
        length_issues = []
        missing_alt = []
        good_alt_count = 0

        for i, (alt_text, image_url) in enumerate(images):
            image_issues = []

            # 检查Alt文本是否存在
            if not alt_text or not alt_text.strip():
                missing_alt.append(f"Image {i+1}: {image_url[:50]}...")
                continue

            alt_text = alt_text.strip()

            # 检查长度
            if len(alt_text) < min_alt_length:
                length_issues.append(f"Image {i+1}: Alt text too short ({len(alt_text)} chars)")
                image_issues.append('too_short')
            elif len(alt_text) > max_alt_length:
                length_issues.append(f"Image {i+1}: Alt text too long ({len(alt_text)} chars)")
                image_issues.append('too_long')

            # 检查禁用词汇
            alt_lower = alt_text.lower()
            for banned_word in banned_words:
                if banned_word.lower() in alt_lower:
                    violations.append(f"Image {i+1}: Contains banned word '{banned_word}' in '{alt_text[:50]}...'")
                    image_issues.append('banned_word')
                    break

            # 如果没有问题，计为良好
            if not image_issues:
                good_alt_count += 1

        # 设置元数据
        result.set_metadata('alt_violations', len(violations))
        result.set_metadata('length_issues', len(length_issues))
        result.set_metadata('missing_alt', len(missing_alt))
        result.set_metadata('good_alt_count', good_alt_count)

        # 计算评分和状态
        total_issues = len(violations) + len(length_issues) + len(missing_alt)

        if violations:
            result.status = CheckStatus.ERROR
            result.score = max(30, 100 - len(violations) * 20)
            for violation in violations[:3]:  # 只显示前3个
                result.add_issue(violation, "error")
            if len(violations) > 3:
                result.add_issue(f"... and {len(violations) - 3} more alt text violations", "error")
            result.add_suggestion("Remove banned words from alt text and make descriptions more natural")

        elif length_issues or missing_alt:
            result.status = CheckStatus.WARNING
            result.score = max(60, 100 - total_issues * 10)

            # 添加长度问题
            for issue in length_issues[:2]:  # 只显示前2个
                result.add_issue(issue, "warning")

            # 添加缺失Alt文本问题
            for issue in missing_alt[:2]:  # 只显示前2个
                result.add_issue(issue, "warning")

            if len(length_issues) + len(missing_alt) > 4:
                result.add_issue(f"... and {total_issues - 4} more alt text issues", "warning")

            result.add_suggestion(f"Improve alt text length ({min_alt_length}-{max_alt_length} characters) and add missing descriptions")

        else:
            # 所有Alt文本都良好
            quality_ratio = good_alt_count / len(images)
            result.score = 85 + quality_ratio * 15

        return result


class InternalLinksChecker(SEOChecker):
    """内部链接检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查内部链接数量

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Internal links check disabled")

        # 获取配置
        quality_rules = self.config.get('quality_rules', {})
        min_internal = quality_rules.get('min_internal_links', 3)

        # 提取链接
        links = ContentParser.extract_links(content)
        internal_links = links['internal']

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('internal_links_count', len(internal_links))
        result.set_metadata('internal_links', internal_links)

        if len(internal_links) < min_internal:
            result.status = CheckStatus.ERROR
            result.score = max(50, (len(internal_links) / min_internal) * 100)
            result.add_issue(f"Too few internal links: {len(internal_links)} (minimum: {min_internal})", "error")
            result.add_suggestion(f"Add {min_internal - len(internal_links)} more internal links to improve SEO")

        else:
            # 根据内部链接数量给出评分
            if len(internal_links) >= min_internal * 2:
                result.score = 100.0
            else:
                result.score = 85 + ((len(internal_links) - min_internal) / min_internal) * 15

            # 检查链接质量（描述性锚文本）
            non_descriptive = 0
            for text, url in internal_links:
                if text.lower() in ['here', 'click here', 'read more', 'more', 'link']:
                    non_descriptive += 1

            if non_descriptive > 0:
                result.score = max(result.score - non_descriptive * 5, 70)
                result.add_issue(f"{non_descriptive} internal links have non-descriptive anchor text", "warning")
                result.add_suggestion("Use descriptive anchor text for better SEO value")

        return result


class ExternalLinksChecker(SEOChecker):
    """外部链接检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查外部链接数量和质量

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "External links check disabled")

        # 获取配置
        quality_rules = self.config.get('quality_rules', {})
        min_external = quality_rules.get('min_external_links', 2)

        # 提取链接
        links = ContentParser.extract_links(content)
        external_links = links['external']

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('external_links_count', len(external_links))
        result.set_metadata('external_links', external_links)

        if len(external_links) < min_external:
            result.status = CheckStatus.ERROR
            result.score = max(60, (len(external_links) / min_external) * 100)
            result.add_issue(f"Too few external links: {len(external_links)} (minimum: {min_external})", "error")
            result.add_suggestion(f"Add {min_external - len(external_links)} more authoritative external links")

        else:
            # 根据外部链接数量给出评分
            if len(external_links) >= min_external * 2:
                result.score = 100.0
            else:
                result.score = 85 + ((len(external_links) - min_external) / min_external) * 15

            # 分析链接质量
            authority_domains = [
                'amazon.com', 'bestbuy.com', 'walmart.com', 'target.com',
                'cnet.com', 'pcmag.com', 'techradar.com', 'theverge.com',
                'consumerreports.org', 'wirecutter.com', 'rtings.com'
            ]

            authority_links = 0
            for text, url in external_links:
                for domain in authority_domains:
                    if domain in url.lower():
                        authority_links += 1
                        break

            authority_ratio = authority_links / len(external_links) if external_links else 0

            # 根据权威链接比例调整评分
            if authority_ratio >= 0.5:
                result.score = min(100.0, result.score + 10)
            elif authority_ratio < 0.2:
                result.score = max(result.score - 10, 70)
                result.add_issue(f"Few authoritative external links ({authority_links}/{len(external_links)})", "warning")
                result.add_suggestion("Include more links to authoritative sources for better credibility")

            result.set_metadata('authority_links', authority_links)
            result.set_metadata('authority_ratio', authority_ratio)

        return result


class SchemaMarkupChecker(SEOChecker):
    """Schema标记检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查结构化数据标记

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Schema markup check disabled")

        quality_rules = self.config.get('quality_rules', {})

        if not quality_rules.get('require_schema', True):
            return self.create_result(CheckStatus.PASS, 100.0, "Schema markup not required")

        # 检查结构化数据模式
        schema_patterns = [
            r'schema\.org',
            r'"@type".*"Article"',
            r'"@type".*"Review"',
            r'"@type".*"Product"',
            r'"@type".*"FAQPage"',
            r'"@type".*"HowTo"',
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>',
            r'itemscope',
            r'itemtype',
            r'itemprop'
        ]

        found_schemas = []
        for pattern in schema_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                found_schemas.extend(matches)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('schema_patterns_found', len(found_schemas))
        result.set_metadata('schema_types', found_schemas[:5])  # 只保留前5个

        if not found_schemas:
            # Schema标记通常由模板处理，所以这是警告而不是错误
            result.status = CheckStatus.WARNING
            result.score = 75.0
            result.add_issue("No schema markup detected (may be handled by template)", "warning")
            result.add_suggestion("Consider adding structured data markup for better search visibility")

        else:
            # 根据找到的schema类型给出评分
            if len(found_schemas) >= 3:
                result.score = 100.0
            elif len(found_schemas) >= 2:
                result.score = 90.0
            else:
                result.score = 85.0

            # 检查是否有特定的有价值schema
            high_value_schemas = ['Article', 'Review', 'Product', 'FAQPage', 'HowTo']
            found_high_value = []

            for schema in found_schemas:
                for high_value in high_value_schemas:
                    if high_value.lower() in schema.lower():
                        found_high_value.append(high_value)
                        break

            if found_high_value:
                result.score = min(100.0, result.score + len(found_high_value) * 5)
                result.set_metadata('high_value_schemas', found_high_value)

        return result