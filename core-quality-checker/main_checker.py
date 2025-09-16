#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主质量检测控制器

协调所有检测器模块，管理检测流程和评分系统
"""

import os
from typing import Dict, List, Any, Optional, Type, Union
from .config.config_manager import ConfigManager
from .utils.validation_result import ValidationResult, CheckStatus, QualityReport
from .utils.base_checker import BaseChecker
from .scoring.score_calculator import ScoreCalculator

# 导入所有检测器模块
from .checkers.content_checkers import (
    WordCountChecker, DuplicateContentChecker,
    ImageRelevanceChecker, ForbiddenPhrasesChecker
)
from .checkers.seo_checkers import (
    ImageChecker, AltTextChecker, InternalLinksChecker,
    ExternalLinksChecker, SchemaMarkupChecker
)
from .checkers.structure_checkers import (
    SectionStructureChecker, FaqSectionChecker, ConclusionChecker,
    FrontMatterChecker, AuthorDateChecker
)
from .checkers.compliance_checkers import (
    AffiliateDisclosureChecker, AdSenseComplianceChecker
)
from .checkers.pqs_checkers import (
    PQSHardGatesChecker, PQSScoreCalculator
)


class QualityChecker:
    """主质量检测器"""

    def __init__(self, config_path: Optional[str] = None, config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化质量检测器

        Args:
            config_path: 配置文件路径
            config_dict: 配置字典（可选，会覆盖文件配置）
        """
        # 初始化配置管理器
        self.config_manager = ConfigManager(config_path)
        if config_dict:
            self.config_manager.update_config(config_dict)

        self.config = self.config_manager.get_config()

        # 初始化评分计算器
        self.score_calculator = ScoreCalculator(self.config)

        # 注册所有检测器
        self.checkers = self._register_checkers()

    def _register_checkers(self) -> Dict[str, BaseChecker]:
        """注册所有检测器"""
        checkers = {}

        # 内容检测器
        content_checkers = [
            WordCountChecker,
            DuplicateContentChecker,
            ImageRelevanceChecker,
            ForbiddenPhrasesChecker
        ]

        # SEO检测器
        seo_checkers = [
            ImageChecker,
            AltTextChecker,
            InternalLinksChecker,
            ExternalLinksChecker,
            SchemaMarkupChecker
        ]

        # 结构检测器
        structure_checkers = [
            SectionStructureChecker,
            FaqSectionChecker,
            ConclusionChecker,
            FrontMatterChecker,
            AuthorDateChecker
        ]

        # 合规性检测器
        compliance_checkers = [
            AffiliateDisclosureChecker,
            AdSenseComplianceChecker
        ]

        # PQS检测器
        pqs_checkers = [
            PQSHardGatesChecker,
            PQSScoreCalculator
        ]

        # 实例化所有检测器
        all_checkers = (content_checkers + seo_checkers + structure_checkers +
                       compliance_checkers + pqs_checkers)

        for checker_class in all_checkers:
            try:
                checker_name = checker_class.__name__
                checker_instance = checker_class(config=self.config)
                checkers[checker_name] = checker_instance
            except Exception as e:
                print(f"Warning: Failed to initialize checker {checker_class.__name__}: {e}")

        return checkers

    def check_content(self,
                     content: str,
                     front_matter: str = "",
                     scoring_mode: str = 'balanced',
                     enabled_checkers: Optional[List[str]] = None,
                     disabled_checkers: Optional[List[str]] = None,
                     **kwargs) -> QualityReport:
        """
        执行内容质量检测

        Args:
            content: 文章内容（包含Front Matter）
            front_matter: 单独的Front Matter内容（可选）
            scoring_mode: 评分模式 ('strict', 'balanced', 'lenient', 'pqs')
            enabled_checkers: 启用的检测器列表（如果指定，只运行这些检测器）
            disabled_checkers: 禁用的检测器列表
            **kwargs: 传递给检测器的额外参数

        Returns:
            QualityReport: 质量检测报告
        """
        results = []

        # 确定要运行的检测器
        checkers_to_run = self._determine_checkers_to_run(
            enabled_checkers, disabled_checkers
        )

        # 执行检测
        hard_gates_result = None

        for checker_name, checker in checkers_to_run.items():
            try:
                # 特殊处理PQS评分计算器，需要硬性门槛结果
                if checker_name == 'PQSScoreCalculator' and hard_gates_result:
                    kwargs['hard_gates_result'] = hard_gates_result

                result = checker.check(content, front_matter, **kwargs)
                results.append(result)

                # 保存硬性门槛结果供PQS评分使用
                if checker_name == 'PQSHardGatesChecker':
                    hard_gates_result = {
                        'metadata': result.metadata,
                        'status': result.status
                    }

            except Exception as e:
                # 创建错误结果
                error_result = ValidationResult(
                    checker_name=checker_name,
                    status=CheckStatus.ERROR,
                    score=0.0,
                    message=f"Checker execution failed: {str(e)}"
                )
                error_result.add_issue(f"Internal error in {checker_name}: {str(e)}", "error")
                results.append(error_result)

        # 计算总体评分
        report = self.score_calculator.calculate_overall_score(results, scoring_mode)

        # 添加改进建议
        improvements = self.score_calculator.suggest_improvements(report)
        for suggestion in improvements:
            report.add_suggestion(suggestion)

        return report

    def _determine_checkers_to_run(self,
                                  enabled_checkers: Optional[List[str]] = None,
                                  disabled_checkers: Optional[List[str]] = None) -> Dict[str, BaseChecker]:
        """确定要运行的检测器"""
        checkers_to_run = {}

        for checker_name, checker in self.checkers.items():
            # 如果指定了启用列表，只运行列表中的检测器
            if enabled_checkers is not None:
                if checker_name in enabled_checkers:
                    checkers_to_run[checker_name] = checker
                continue

            # 如果检测器被禁用，跳过
            if disabled_checkers and checker_name in disabled_checkers:
                continue

            # 检查检测器是否在配置中启用
            if checker.is_enabled():
                checkers_to_run[checker_name] = checker

        return checkers_to_run

    def check_file(self, file_path: str, **kwargs) -> QualityReport:
        """
        检测文件内容

        Args:
            file_path: 文件路径
            **kwargs: 传递给check_content的额外参数

        Returns:
            QualityReport: 质量检测报告
        """
        if not os.path.exists(file_path):
            error_result = ValidationResult(
                checker_name="FileChecker",
                status=CheckStatus.ERROR,
                score=0.0,
                message=f"File not found: {file_path}"
            )
            return QualityReport(
                overall_score=0.0,
                status=CheckStatus.ERROR,
                total_issues=1,
                results=[error_result]
            )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.check_content(content, **kwargs)

        except Exception as e:
            error_result = ValidationResult(
                checker_name="FileChecker",
                status=CheckStatus.ERROR,
                score=0.0,
                message=f"Failed to read file: {str(e)}"
            )
            return QualityReport(
                overall_score=0.0,
                status=CheckStatus.ERROR,
                total_issues=1,
                results=[error_result]
            )

    def get_available_checkers(self) -> List[str]:
        """获取所有可用的检测器列表"""
        return list(self.checkers.keys())

    def get_checker_info(self, checker_name: str) -> Optional[Dict[str, Any]]:
        """获取检测器信息"""
        if checker_name not in self.checkers:
            return None

        checker = self.checkers[checker_name]
        return {
            'name': checker_name,
            'enabled': checker.is_enabled(),
            'category': checker.get_category(),
            'description': checker.__class__.__doc__ or "No description available",
            'config': checker.get_config()
        }

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy()

    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """更新配置"""
        self.config_manager.update_config(config_updates)
        self.config = self.config_manager.get_config()

        # 重新初始化评分计算器和检测器
        self.score_calculator = ScoreCalculator(self.config)

        # 更新现有检测器的配置
        for checker in self.checkers.values():
            checker.update_config(self.config)

    def get_score_breakdown(self, report: QualityReport) -> Dict[str, Any]:
        """获取详细的评分分解"""
        return self.score_calculator.get_score_breakdown(report)

    def validate_config(self) -> List[str]:
        """验证配置有效性，返回警告信息列表"""
        warnings = []

        # 检查必要的配置项
        required_sections = ['quality_rules', 'seo', 'adsense_compliance', 'pqs_v3']
        for section in required_sections:
            if section not in self.config:
                warnings.append(f"Missing required config section: {section}")

        # 检查检测器配置
        for checker_name, checker in self.checkers.items():
            try:
                checker.is_enabled()
            except Exception as e:
                warnings.append(f"Config error in {checker_name}: {str(e)}")

        return warnings

    def run_quick_check(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        快速检测（只运行关键检测器）

        Args:
            content: 文章内容
            **kwargs: 额外参数

        Returns:
            Dict: 简化的检测结果
        """
        # 定义快速检测的关键检测器
        quick_checkers = [
            'WordCountChecker',
            'ImageChecker',
            'AltTextChecker',
            'InternalLinksChecker',
            'AffiliateDisclosureChecker'
        ]

        report = self.check_content(
            content,
            enabled_checkers=quick_checkers,
            scoring_mode='balanced',
            **kwargs
        )

        return {
            'overall_score': report.overall_score,
            'status': report.status.value,
            'total_issues': report.total_issues,
            'key_issues': [issue for result in report.results for issue in result.issues[:2]],
            'top_suggestions': report.suggestions[:3]
        }