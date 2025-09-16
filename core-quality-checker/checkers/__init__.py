#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测器模块

包含所有类型的质量检测器，按功能分组。
"""

# 内容检测器
from .content_checkers import (
    WordCountChecker,
    DuplicateContentChecker,
    ImageRelevanceChecker,
    ForbiddenPhrasesChecker
)

# SEO检测器
from .seo_checkers import (
    ImageChecker,
    AltTextChecker,
    InternalLinksChecker,
    ExternalLinksChecker,
    SchemaMarkupChecker
)

# 结构检测器
from .structure_checkers import (
    SectionStructureChecker,
    FaqSectionChecker,
    ConclusionChecker,
    FrontMatterChecker,
    AuthorDateChecker
)

# 合规性检测器
from .compliance_checkers import (
    AffiliateDisclosureChecker,
    AdSenseComplianceChecker
)

# PQS检测器
from .pqs_checkers import (
    PQSHardGatesChecker,
    PQSScoreCalculator
)

__all__ = [
    # 内容检测器
    'WordCountChecker',
    'DuplicateContentChecker',
    'ImageRelevanceChecker',
    'ForbiddenPhrasesChecker',

    # SEO检测器
    'ImageChecker',
    'AltTextChecker',
    'InternalLinksChecker',
    'ExternalLinksChecker',
    'SchemaMarkupChecker',

    # 结构检测器
    'SectionStructureChecker',
    'FaqSectionChecker',
    'ConclusionChecker',
    'FrontMatterChecker',
    'AuthorDateChecker',

    # 合规性检测器
    'AffiliateDisclosureChecker',
    'AdSenseComplianceChecker',

    # PQS检测器
    'PQSHardGatesChecker',
    'PQSScoreCalculator'
]