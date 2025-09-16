#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规性检测器模块

包含合规性相关的检测器，从原始quality_check.py重构而来。
"""

import re
from typing import Dict, Any, List
from ..utils.base_checker import ComplianceChecker
from ..utils.validation_result import ValidationResult, CheckStatus
from ..utils.content_parser import ContentParser


class AffiliateDisclosureChecker(ComplianceChecker):
    """联盟声明检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查是否包含联盟声明

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "Affiliate disclosure check disabled")

        quality_rules = self.config.get('quality_rules', {})

        if not quality_rules.get('require_disclosure', True):
            return self.create_result(CheckStatus.PASS, 100.0, "Affiliate disclosure not required")

        # 联盟声明模式
        disclosure_patterns = [
            r'affiliate',
            r'commission',
            r'earn.*from.*purchas',
            r'disclosure',
            r'as an amazon associate',
            r'联盟',
            r'佣金',
            r'分成',
            r'披露',
            r'声明'
        ]

        # 检查是否存在联盟声明
        has_disclosure = False
        found_patterns = []

        for pattern in disclosure_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                has_disclosure = True
                found_patterns.extend(matches)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        result.set_metadata('has_disclosure', has_disclosure)
        result.set_metadata('found_patterns', found_patterns[:5])  # 只保留前5个

        if not has_disclosure:
            result.status = CheckStatus.ERROR
            result.score = 60.0
            result.add_issue("Missing affiliate disclosure statement", "error")
            result.add_suggestion("Add clear affiliate disclosure to comply with FTC guidelines")

        else:
            # 分析声明质量和位置
            disclosure_quality = self._analyze_disclosure_quality(content)
            result.score = max(85, 85 + disclosure_quality * 15)
            result.set_metadata('disclosure_quality', disclosure_quality)

            if disclosure_quality < 0.7:
                result.add_issue("Affiliate disclosure exists but may not be prominent enough", "warning")
                result.add_suggestion("Make affiliate disclosure more prominent and clear")

        return result

    def _analyze_disclosure_quality(self, content: str) -> float:
        """分析联盟声明质量"""
        quality_score = 0.0

        # 检查声明位置（在前面更好）
        first_third = len(content) // 3

        # 更详细的联盟声明模式
        detailed_patterns = [
            r'as an amazon associate.*earn',
            r'affiliate.*commission',
            r'may.*earn.*commission',
            r'earn.*qualifying.*purchase',
            r'affiliate.*relationship',
            r'disclosure.*affiliate'
        ]

        # 检查是否在前1/3内出现
        early_disclosure = False
        for pattern in detailed_patterns:
            if re.search(pattern, content[:first_third], re.IGNORECASE):
                early_disclosure = True
                quality_score += 0.4
                break

        # 检查声明的完整性
        complete_disclosure = False
        complete_patterns = [
            r'as an amazon associate.*earn.*qualifying.*purchase',
            r'affiliate.*commission.*no.*additional.*cost',
            r'earn.*commission.*recommend.*product'
        ]

        for pattern in complete_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                complete_disclosure = True
                quality_score += 0.4
                break

        # 检查是否有专门的披露部分
        dedicated_section = bool(re.search(r'##.*disclosure|披露|声明', content, re.IGNORECASE))
        if dedicated_section:
            quality_score += 0.2

        # 如果只是简单提及但没有完整声明
        if not early_disclosure and not complete_disclosure:
            quality_score = min(quality_score, 0.3)

        return min(quality_score, 1.0)


class AdSenseComplianceChecker(ComplianceChecker):
    """AdSense合规性检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        检查AdSense合规性

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "AdSense compliance check disabled")

        # 获取AdSense配置
        adsense_config = self.config.get('adsense_compliance', {})

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)

        # 1. 检查内容质量要求
        content_quality_score = self._check_content_quality(content, adsense_config)

        # 2. 检查必需的免责声明
        disclaimer_score = self._check_required_disclaimers(content, adsense_config)

        # 3. 检查是否有误导性声明
        misleading_score = self._check_misleading_content(content)

        # 计算总体评分
        overall_score = (content_quality_score + disclaimer_score + misleading_score) / 3
        result.score = overall_score * 100

        # 设置元数据
        result.set_metadata('content_quality_score', content_quality_score)
        result.set_metadata('disclaimer_score', disclaimer_score)
        result.set_metadata('misleading_score', misleading_score)

        # 根据评分设置状态
        if overall_score < 0.6:
            result.status = CheckStatus.ERROR
            result.add_issue("Multiple AdSense compliance issues detected", "error")
            result.add_suggestion("Review and improve content to meet AdSense guidelines")
        elif overall_score < 0.8:
            result.status = CheckStatus.WARNING
            result.add_issue("Some AdSense compliance concerns found", "warning")
            result.add_suggestion("Address compliance issues to improve ad eligibility")

        return result

    def _check_content_quality(self, content: str, adsense_config: Dict[str, Any]) -> float:
        """检查内容质量要求"""
        quality_score = 1.0

        # 检查最小原创内容比例
        min_original = adsense_config.get('content_quality', {}).get('min_original_content', 0.85)

        # 简单的原创性检查（基于内容多样性）
        sentences = ContentParser.extract_sentences(content)
        if len(sentences) > 0:
            unique_sentences = len(set(sentences))
            originality_ratio = unique_sentences / len(sentences)

            if originality_ratio < min_original:
                quality_score -= 0.3

        # 检查内容长度充足性
        word_count = ContentParser.count_words(content)
        if word_count < 1000:
            quality_score -= 0.2
        elif word_count < 1500:
            quality_score -= 0.1

        return max(0.0, quality_score)

    def _check_required_disclaimers(self, content: str, adsense_config: Dict[str, Any]) -> float:
        """检查必需的免责声明"""
        disclaimer_score = 1.0
        required_disclaimers = adsense_config.get('required_disclaimers', {})

        # 检查联盟关系披露
        if required_disclaimers.get('affiliate_disclosure', False):
            affiliate_patterns = [
                r'affiliate',
                r'commission',
                r'earn.*from.*purchas',
                r'as an amazon associate'
            ]
            has_affiliate_disclosure = any(re.search(pattern, content, re.IGNORECASE)
                                         for pattern in affiliate_patterns)
            if not has_affiliate_disclosure:
                disclaimer_score -= 0.4

        # 检查佣金收入披露
        if required_disclaimers.get('commission_disclosure', False):
            commission_patterns = [
                r'commission',
                r'earn.*money',
                r'paid.*partnership',
                r'sponsored'
            ]
            has_commission_disclosure = any(re.search(pattern, content, re.IGNORECASE)
                                          for pattern in commission_patterns)
            if not has_commission_disclosure:
                disclaimer_score -= 0.3

        # 检查研究方法说明
        if required_disclaimers.get('research_methodology', False):
            methodology_patterns = [
                r'research.*based',
                r'specification.*analysis',
                r'no.*physical.*test',
                r'based.*on.*review',
                r'methodology'
            ]
            has_methodology = any(re.search(pattern, content, re.IGNORECASE)
                                for pattern in methodology_patterns)
            if not has_methodology:
                disclaimer_score -= 0.3

        return max(0.0, disclaimer_score)

    def _check_misleading_content(self, content: str) -> float:
        """检查误导性内容"""
        misleading_score = 1.0

        # 检查过度承诺的语言
        excessive_claims = [
            r'guaranteed.*results',
            r'100%.*guaranteed',
            r'never.*fail',
            r'always.*work',
            r'miracle.*solution',
            r'secret.*method',
            r'instant.*results',
            r'effortless',
            r'magic.*formula'
        ]

        claim_violations = 0
        for pattern in excessive_claims:
            matches = re.findall(pattern, content, re.IGNORECASE)
            claim_violations += len(matches)

        if claim_violations > 0:
            misleading_score -= min(0.5, claim_violations * 0.1)

        # 检查虚假紧迫性
        false_urgency = [
            r'limited.*time.*only',
            r'act.*now.*or.*lose',
            r'offer.*expires.*soon',
            r'only.*\d+.*left',
            r'hurry.*before.*gone'
        ]

        urgency_violations = 0
        for pattern in false_urgency:
            matches = re.findall(pattern, content, re.IGNORECASE)
            urgency_violations += len(matches)

        if urgency_violations > 0:
            misleading_score -= min(0.3, urgency_violations * 0.1)

        # 检查健康声明（如果相关）
        health_claims = [
            r'cure.*disease',
            r'treat.*medical.*condition',
            r'heal.*instantly',
            r'medical.*breakthrough',
            r'doctor.*approved',
            r'clinically.*proven'
        ]

        health_violations = 0
        for pattern in health_claims:
            matches = re.findall(pattern, content, re.IGNORECASE)
            health_violations += len(matches)

        if health_violations > 0:
            misleading_score -= min(0.4, health_violations * 0.15)

        return max(0.0, misleading_score)