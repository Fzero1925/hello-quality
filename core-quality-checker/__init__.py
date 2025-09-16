#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心质量检测器 - 模块化版本
Core Quality Checker - Modular Version

从单体的quality_check.py重构而来，提供模块化的文章质量检测功能。
每个检测功能独立成模块，便于维护、扩展和问题定位。

主要模块：
- checkers: 各类检测器（内容、SEO、结构、合规性、PQS）
- config: 配置管理
- scoring: 评分系统
- utils: 工具类
- legacy_adapter: 向后兼容层
"""

__version__ = "3.0.0"
__author__ = "Smart Home Research Team"

# 新的模块化接口
from .main_checker import QualityChecker
from .utils.validation_result import ValidationResult, CheckStatus, QualityReport
from .scoring.score_calculator import ScoreCalculator
from .config.config_manager import ConfigManager

# 向后兼容接口
from .legacy_adapter import (
    ComprehensiveQualityChecker,
    check_article_quality,
    validate_article_v2,
    LegacyConfigAdapter
)

__all__ = [
    # 新接口
    'QualityChecker',
    'ValidationResult',
    'CheckStatus',
    'QualityReport',
    'ScoreCalculator',
    'ConfigManager',

    # 向后兼容接口
    'ComprehensiveQualityChecker',
    'check_article_quality',
    'validate_article_v2',
    'LegacyConfigAdapter'
]

# 模块级别的便捷函数
def quick_check(content: str, **kwargs) -> dict:
    """
    快速质量检测（简化接口）

    Args:
        content: 文章内容
        **kwargs: 额外参数

    Returns:
        dict: 简化的检测结果
    """
    checker = QualityChecker()
    return checker.run_quick_check(content, **kwargs)


def check_file_quality(filepath: str, scoring_mode: str = 'balanced', **kwargs) -> dict:
    """
    文件质量检测（便捷函数）

    Args:
        filepath: 文件路径
        scoring_mode: 评分模式
        **kwargs: 额外参数

    Returns:
        dict: 检测结果
    """
    checker = QualityChecker()
    report = checker.check_file(filepath, scoring_mode=scoring_mode, **kwargs)
    return checker.get_score_breakdown(report)