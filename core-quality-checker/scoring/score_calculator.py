#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评分计算器

负责权重管理和整体评分计算逻辑
"""

from typing import Dict, List, Any, Optional, Tuple
from ..utils.validation_result import ValidationResult, CheckStatus, QualityReport


class ScoreCalculator:
    """评分计算器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化评分计算器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.scoring_config = self.config.get('scoring', {})

    def calculate_overall_score(self, results: List[ValidationResult],
                               scoring_mode: str = 'balanced') -> QualityReport:
        """
        计算总体评分

        Args:
            results: 检测结果列表
            scoring_mode: 评分模式 ('strict', 'balanced', 'lenient', 'pqs')

        Returns:
            QualityReport: 质量报告
        """
        if not results:
            return QualityReport(
                overall_score=0.0,
                status=CheckStatus.ERROR,
                total_issues=0,
                results=[]
            )

        # 获取权重配置
        weights = self._get_weights(scoring_mode)

        # 按类别组织结果
        categorized_results = self._categorize_results(results)

        # 计算分类得分
        category_scores = {}
        total_weight = 0
        weighted_score = 0

        for category, category_results in categorized_results.items():
            if category_results and category in weights:
                category_score = self._calculate_category_score(category_results, scoring_mode)
                category_weight = weights[category]

                category_scores[category] = {
                    'score': category_score,
                    'weight': category_weight,
                    'weighted_score': category_score * category_weight,
                    'results_count': len(category_results)
                }

                total_weight += category_weight
                weighted_score += category_score * category_weight

        # 计算总分
        overall_score = weighted_score / total_weight if total_weight > 0 else 0

        # 确定整体状态
        overall_status = self._determine_overall_status(results, overall_score, scoring_mode)

        # 统计问题
        total_issues = sum(len(result.issues) for result in results)

        # 创建质量报告
        report = QualityReport(
            overall_score=overall_score,
            status=overall_status,
            total_issues=total_issues,
            results=results
        )

        # 设置评分元数据
        report.set_metadata('scoring_mode', scoring_mode)
        report.set_metadata('category_scores', category_scores)
        report.set_metadata('total_weight', total_weight)
        report.set_metadata('thresholds', self._get_thresholds(scoring_mode))

        return report

    def _get_weights(self, scoring_mode: str) -> Dict[str, float]:
        """获取权重配置"""
        weight_configs = {
            'strict': {
                'content': 0.20,    # 内容质量
                'seo': 0.25,        # SEO优化
                'structure': 0.20,  # 结构检查
                'compliance': 0.25, # 合规性
                'pqs': 0.10         # PQS专项
            },
            'balanced': {
                'content': 0.25,    # 内容质量
                'seo': 0.20,        # SEO优化
                'structure': 0.20,  # 结构检查
                'compliance': 0.20, # 合规性
                'pqs': 0.15         # PQS专项
            },
            'lenient': {
                'content': 0.30,    # 内容质量
                'seo': 0.15,        # SEO优化
                'structure': 0.25,  # 结构检查
                'compliance': 0.15, # 合规性
                'pqs': 0.15         # PQS专项
            },
            'pqs': {
                'content': 0.15,    # 内容质量
                'seo': 0.15,        # SEO优化
                'structure': 0.15,  # 结构检查
                'compliance': 0.15, # 合规性
                'pqs': 0.40         # PQS专项（重点）
            }
        }

        # 使用配置文件中的权重，或使用默认权重
        configured_weights = self.scoring_config.get('weights', {}).get(scoring_mode, {})
        default_weights = weight_configs.get(scoring_mode, weight_configs['balanced'])

        return {**default_weights, **configured_weights}

    def _get_thresholds(self, scoring_mode: str) -> Dict[str, float]:
        """获取评分阈值"""
        threshold_configs = {
            'strict': {
                'excellent': 95.0,
                'good': 85.0,
                'warning': 70.0,
                'error': 50.0
            },
            'balanced': {
                'excellent': 90.0,
                'good': 80.0,
                'warning': 65.0,
                'error': 45.0
            },
            'lenient': {
                'excellent': 85.0,
                'good': 75.0,
                'warning': 60.0,
                'error': 40.0
            },
            'pqs': {
                'excellent': 95.0,
                'good': 85.0,
                'warning': 75.0,
                'error': 60.0
            }
        }

        # 使用配置文件中的阈值，或使用默认阈值
        configured_thresholds = self.scoring_config.get('thresholds', {}).get(scoring_mode, {})
        default_thresholds = threshold_configs.get(scoring_mode, threshold_configs['balanced'])

        return {**default_thresholds, **configured_thresholds}

    def _categorize_results(self, results: List[ValidationResult]) -> Dict[str, List[ValidationResult]]:
        """按类别组织检测结果"""
        categories = {
            'content': [],
            'seo': [],
            'structure': [],
            'compliance': [],
            'pqs': []
        }

        for result in results:
            checker_name = result.checker_name.lower()

            # 根据检测器名称分类
            if any(keyword in checker_name for keyword in ['word', 'duplicate', 'relevance', 'phrase']):
                categories['content'].append(result)
            elif any(keyword in checker_name for keyword in ['image', 'alt', 'link', 'schema']):
                categories['seo'].append(result)
            elif any(keyword in checker_name for keyword in ['section', 'faq', 'conclusion', 'front', 'author']):
                categories['structure'].append(result)
            elif any(keyword in checker_name for keyword in ['affiliate', 'adsense', 'compliance']):
                categories['compliance'].append(result)
            elif any(keyword in checker_name for keyword in ['pqs', 'hard', 'gate']):
                categories['pqs'].append(result)
            else:
                # 默认归为内容类别
                categories['content'].append(result)

        return categories

    def _calculate_category_score(self, category_results: List[ValidationResult],
                                 scoring_mode: str) -> float:
        """计算分类得分"""
        if not category_results:
            return 100.0

        # 处理关键性失败
        critical_failures = [r for r in category_results if r.status == CheckStatus.CRITICAL]
        if critical_failures:
            # 严格模式下关键性失败导致该分类得分为0
            if scoring_mode == 'strict':
                return 0.0
            # 其他模式下大幅降分
            else:
                return max(0, 50 - len(critical_failures) * 15)

        # 计算权重平均分
        total_weight = sum(result.weight for result in category_results)
        if total_weight == 0:
            return sum(result.score for result in category_results) / len(category_results)

        weighted_score = sum(result.score * result.weight for result in category_results)
        return weighted_score / total_weight

    def _determine_overall_status(self, results: List[ValidationResult],
                                 overall_score: float, scoring_mode: str) -> CheckStatus:
        """确定整体状态"""
        # 检查是否有关键性失败
        if any(result.status == CheckStatus.CRITICAL for result in results):
            return CheckStatus.CRITICAL

        # 获取阈值
        thresholds = self._get_thresholds(scoring_mode)

        # 检查PQS硬性门槛（如果有PQS检测器）
        pqs_hard_gates_failed = False
        for result in results:
            if 'pqs' in result.checker_name.lower() and 'hard' in result.checker_name.lower():
                if not result.metadata.get('pqs_hard_gates_passed', True):
                    pqs_hard_gates_failed = True
                    break

        if pqs_hard_gates_failed:
            return CheckStatus.CRITICAL

        # 根据评分确定状态
        if overall_score >= thresholds['good']:
            return CheckStatus.PASS
        elif overall_score >= thresholds['warning']:
            return CheckStatus.WARNING
        else:
            return CheckStatus.ERROR

    def get_score_breakdown(self, report: QualityReport) -> Dict[str, Any]:
        """获取详细的评分分解"""
        breakdown = {
            'overall_score': report.overall_score,
            'status': report.status.value,
            'total_issues': report.total_issues,
            'scoring_mode': report.metadata.get('scoring_mode', 'unknown'),
            'categories': report.metadata.get('category_scores', {}),
            'thresholds': report.metadata.get('thresholds', {}),
            'checker_details': []
        }

        # 添加各检测器详情
        for result in report.results:
            checker_detail = {
                'name': result.checker_name,
                'score': result.score,
                'weight': result.weight,
                'status': result.status.value,
                'issues_count': len(result.issues),
                'suggestions_count': len(result.suggestions),
                'metadata': result.metadata
            }
            breakdown['checker_details'].append(checker_detail)

        return breakdown

    def suggest_improvements(self, report: QualityReport) -> List[str]:
        """基于评分结果提出改进建议"""
        suggestions = []

        # 分析分类得分
        category_scores = report.metadata.get('category_scores', {})
        scoring_mode = report.metadata.get('scoring_mode', 'balanced')
        thresholds = self._get_thresholds(scoring_mode)

        # 找出得分较低的分类
        low_categories = []
        for category, data in category_scores.items():
            if data['score'] < thresholds['warning']:
                low_categories.append((category, data['score']))

        # 按得分排序，优先处理得分最低的
        low_categories.sort(key=lambda x: x[1])

        for category, score in low_categories[:3]:  # 只处理前3个最需要改进的
            if category == 'content':
                suggestions.append(f"内容质量需要改进 (当前得分: {score:.1f}) - 增加字数、提高原创性、优化图片相关性")
            elif category == 'seo':
                suggestions.append(f"SEO优化需要改进 (当前得分: {score:.1f}) - 优化图片ALT文本、增加内外部链接、添加结构化数据")
            elif category == 'structure':
                suggestions.append(f"文章结构需要改进 (当前得分: {score:.1f}) - 完善标题层级、添加FAQ和结论、补充作者信息")
            elif category == 'compliance':
                suggestions.append(f"合规性需要改进 (当前得分: {score:.1f}) - 添加联盟声明、确保AdSense合规")
            elif category == 'pqs':
                suggestions.append(f"PQS标准需要改进 (当前得分: {score:.1f}) - 检查硬性门槛、提高内容深度和证据质量")

        # 检查整体得分情况
        if report.overall_score < thresholds['error']:
            suggestions.insert(0, "文章质量严重不达标，建议重新撰写或大幅修改")
        elif report.overall_score < thresholds['warning']:
            suggestions.insert(0, "文章质量偏低，需要重点改进多个方面")
        elif report.overall_score < thresholds['good']:
            suggestions.insert(0, "文章基本达标，但仍有提升空间")

        return suggestions[:5]  # 限制建议数量