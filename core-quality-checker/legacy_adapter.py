#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向后兼容适配器

提供与原有ComprehensiveQualityChecker兼容的接口，使得现有代码无需修改即可使用新的模块化系统
"""

import os
from typing import Dict, Any, Optional, List
from .main_checker import QualityChecker
from .utils.validation_result import CheckStatus


class ComprehensiveQualityChecker:
    """
    向后兼容的质量检测器

    保持与原有ComprehensiveQualityChecker相同的接口和返回格式
    """

    def __init__(self, config_path: Optional[str] = None, pqs_mode: bool = False):
        """
        初始化向后兼容的质量检测器

        Args:
            config_path: 配置文件路径
            pqs_mode: 是否启用PQS v3严格模式 (85+分数要求)
        """
        self.config_path = config_path
        self.pqs_mode = pqs_mode

        # 使用新的模块化系统
        config_dict = None
        if pqs_mode:
            # PQS模式下的特殊配置
            config_dict = {
                'quality_rules': {
                    'require_pqs_checks': True
                },
                'pqs_v3': {
                    'enabled': True,
                    'thresholds': {
                        'publish_score': 85
                    }
                }
            }

        self.quality_checker = QualityChecker(config_path, config_dict)

        # 确定评分模式
        self.scoring_mode = 'pqs' if pqs_mode else 'balanced'

        mode_desc = "PQS v3 Hard Gates + v2 Enhanced" if pqs_mode else "v2 Enhanced"
        config = self.quality_checker.get_config()
        rules_count = len(config.get('quality_rules', {}))
        print(f"✅ Quality checker initialized ({mode_desc}) with {rules_count} validation rules")

    def check_article_quality(self, filepath: str) -> Dict[str, Any]:
        """
        综合15项质量验证

        Args:
            filepath: 文件路径

        Returns:
            Dict: 与原有格式兼容的检测结果
        """
        # 使用新系统执行检测
        report = self.quality_checker.check_file(filepath, scoring_mode=self.scoring_mode)

        # 转换为兼容格式
        return self._convert_to_legacy_format(filepath, report)

    def _convert_to_legacy_format(self, filepath: str, report) -> Dict[str, Any]:
        """将新格式转换为旧格式"""
        # 收集所有问题和警告
        issues = []
        warnings = []
        metadata = {}

        for result in report.results:
            # 按严重性分类问题
            for issue in result.issues:
                if issue.get('severity') == 'error' or result.status == CheckStatus.ERROR:
                    issues.append(issue.get('description', str(issue)))
                elif issue.get('severity') == 'critical' or result.status == CheckStatus.CRITICAL:
                    issues.append(issue.get('description', str(issue)))
                else:
                    warnings.append(issue.get('description', str(issue)))

            # 合并元数据
            metadata.update(result.metadata)

        # 计算兼容的质量评分
        total_checks = len(report.results)
        passed_checks = sum(1 for result in report.results if result.status == CheckStatus.PASS)
        quality_score = passed_checks / total_checks if total_checks > 0 else 0

        # 确定状态
        if report.status == CheckStatus.CRITICAL:
            status = 'FAIL'
        elif report.status == CheckStatus.ERROR:
            status = 'FAIL'
        elif report.status == CheckStatus.WARNING:
            status = 'WARN'
        else:
            # 根据问题数量进一步确定状态
            if len(issues) == 0 and len(warnings) <= 2:
                status = 'PASS'
            elif len(issues) <= 2:
                status = 'WARN'
            else:
                status = 'FAIL'

        # PQS模式下的特殊处理
        if self.pqs_mode:
            pqs_score = metadata.get('pqs_total_score', 0)
            pqs_threshold = metadata.get('pqs_threshold', 85)
            pqs_hard_gates_passed = metadata.get('pqs_hard_gates_passed', False)

            if not pqs_hard_gates_passed:
                status = 'FAIL'
                if 'PQS HARD GATES BLOCK - Article cannot be published' not in issues:
                    issues.append('PQS HARD GATES BLOCK - Article cannot be published')

            elif pqs_score < pqs_threshold:
                status = 'FAIL'
                if f'PQS SCORE FAIL: {pqs_score}/100 (threshold: {pqs_threshold})' not in issues:
                    issues.append(f'PQS SCORE FAIL: {pqs_score}/100 (threshold: {pqs_threshold})')

        return {
            'file': os.path.basename(filepath),
            'status': status,
            'quality_score': quality_score,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'issues': issues,
            'warnings': warnings,
            'metadata': metadata,
            'word_count': metadata.get('word_count', 0),
            'sections': metadata.get('section_count', 0),
            # 保持与新系统的兼容性
            'overall_score': report.overall_score,
            'modular_report': report  # 可选：提供完整的新格式报告
        }


# 向后兼容的独立函数
def check_article_quality(filepath: str) -> Dict[str, Any]:
    """
    Legacy compatibility function
    保持与原有独立函数的兼容性
    """
    checker = ComprehensiveQualityChecker()
    result = checker.check_article_quality(filepath)

    # 转换为legacy格式以保持向后兼容
    return {
        'file': result['file'],
        'word_count': result['word_count'],
        'sections': result['sections'],
        'issues': result['issues'] + result['warnings'],
        'status': result['status']
    }


def validate_article_v2(filepath: str, rules: Optional[Dict] = None) -> Dict[str, Any]:
    """
    V2版本的文章验证函数
    保持与原有接口的兼容性

    Args:
        filepath: 文件路径
        rules: 质量规则配置（可选）

    Returns:
        Dict: 验证结果
    """
    # 如果提供了自定义规则，更新配置
    config_dict = None
    if rules:
        config_dict = {'quality_rules': rules}

    checker = QualityChecker(config_dict=config_dict)
    report = checker.check_file(filepath, scoring_mode='balanced')

    # 转换为V2兼容格式
    adapter = ComprehensiveQualityChecker()
    return adapter._convert_to_legacy_format(filepath, report)


# 额外的兼容性辅助函数
class LegacyConfigAdapter:
    """配置适配器，用于转换旧格式配置到新格式"""

    @staticmethod
    def convert_legacy_config(legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """将旧格式配置转换为新格式"""
        new_config = {
            'quality_rules': {},
            'seo': {},
            'adsense_compliance': {},
            'pqs_v3': {}
        }

        # 映射质量规则
        if 'quality_rules' in legacy_config:
            new_config['quality_rules'] = legacy_config['quality_rules']

        # 映射SEO配置
        if 'seo' in legacy_config:
            new_config['seo'] = legacy_config['seo']

        # 映射AdSense合规配置
        if 'adsense_compliance' in legacy_config:
            new_config['adsense_compliance'] = legacy_config['adsense_compliance']

        # 映射PQS配置
        if 'pqs_config' in legacy_config:
            new_config['pqs_v3'] = legacy_config['pqs_config']

        return new_config

    @staticmethod
    def get_legacy_default_config() -> Dict[str, Any]:
        """获取与原系统兼容的默认配置"""
        return {
            'quality_rules': {
                'min_images': 3,
                'require_featured': True,
                'min_word_count': 1500,
                'max_word_count': 4000,
                'ban_words_in_alt': True,
                'min_internal_links': 3,
                'min_external_links': 2,
                'require_disclosure': True,
                'require_schema': True,
                'require_author_date': True,
                'require_section_structure': True,
                'require_faq': True,
                'require_conclusion': True,
                'max_duplicate_usage': 3,
                'min_image_relevance_score': 0.6
            },
            'seo': {
                'banned_alt_words': [
                    'image', 'photo', 'picture', 'smart home', 'best',
                    'top', 'click', 'here', 'read more'
                ],
                'max_alt_length': 125,
                'min_alt_length': 15
            },
            'adsense_compliance': {
                'forbidden_phrases': {
                    'critical': [
                        'click here for discount', 'limited time offer',
                        'buy now or lose forever', 'secret formula',
                        'guaranteed results', 'miracle solution'
                    ],
                    'warning': [
                        'amazing deal', 'unbelievable price',
                        'don\'t miss out', 'act fast', 'urgent'
                    ],
                    'suggestion': [
                        'best deal ever', 'lowest price guaranteed',
                        'must have', 'life changing', 'perfect solution'
                    ]
                },
                'content_quality': {
                    'min_original_content': 0.85
                },
                'required_disclaimers': {
                    'affiliate_disclosure': True,
                    'commission_disclosure': False,
                    'research_methodology': True
                }
            },
            'pqs_v3': {
                'enabled': False,
                'thresholds': {
                    'publish_score': 85,
                    'keyword_density_max': 0.025,
                    'min_inline_images': 2
                },
                'entities_tokens': {
                    'generic': ["matter", "thread", "zigbee", "local control", "watt", "2.4g", "hub"],
                    'smart-plugs': ["smart plug", "energy", "monitor", "kwh", "standby"],
                    'smart-cameras': ["rtsp", "onvif", "privacy shutter", "fps"]
                }
            }
        }