#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证结果数据结构

定义检测结果的标准数据结构，确保所有检测器返回一致的格式。
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class CheckStatus(Enum):
    """检测状态枚举"""
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationResult:
    """检测结果数据结构"""

    def __init__(self,
                 checker_name: str,
                 status: CheckStatus = CheckStatus.PASS,
                 score: float = 100.0,
                 weight: float = 1.0,
                 issues: Optional[List[str]] = None,
                 warnings: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 suggestions: Optional[List[str]] = None):
        """
        初始化检测结果

        Args:
            checker_name: 检测器名称
            status: 检测状态
            score: 检测得分 (0-100)
            weight: 权重
            issues: 问题列表
            warnings: 警告列表
            metadata: 元数据信息
            suggestions: 修复建议
        """
        self.checker_name = checker_name
        self.status = status
        self.score = max(0.0, min(100.0, score))  # 限制在0-100范围
        self.weight = weight
        self.issues = issues or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.suggestions = suggestions or []

    def add_issue(self, issue: str, severity: str = "error"):
        """添加问题"""
        if severity == "critical":
            self.status = CheckStatus.CRITICAL
        elif severity == "error" and self.status != CheckStatus.CRITICAL:
            self.status = CheckStatus.ERROR
        elif severity == "warning" and self.status not in [CheckStatus.CRITICAL, CheckStatus.ERROR]:
            self.status = CheckStatus.WARNING

        if severity in ["critical", "error"]:
            self.issues.append(issue)
        else:
            self.warnings.append(issue)

    def add_suggestion(self, suggestion: str):
        """添加修复建议"""
        self.suggestions.append(suggestion)

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self.metadata[key] = value

    def is_passing(self) -> bool:
        """是否通过检测"""
        return self.status == CheckStatus.PASS

    def has_critical_issues(self) -> bool:
        """是否有严重问题"""
        return self.status == CheckStatus.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于兼容旧接口）"""
        return {
            'checker': self.checker_name,
            'status': self.status.value,
            'score': self.score,
            'weight': self.weight,
            'issues': self.issues,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'suggestions': self.suggestions
        }

    def __str__(self) -> str:
        """字符串表示"""
        status_emoji = {
            CheckStatus.PASS: "✅",
            CheckStatus.WARNING: "⚠️",
            CheckStatus.ERROR: "❌",
            CheckStatus.CRITICAL: "🚨"
        }

        emoji = status_emoji.get(self.status, "❓")
        return f"{emoji} {self.checker_name}: {self.score:.1f}/100 ({self.status.value})"


class QualityReport:
    """质量检测总报告"""

    def __init__(self, file_path: str):
        """
        初始化质量报告

        Args:
            file_path: 被检测文件路径
        """
        self.file_path = file_path
        self.results: List[ValidationResult] = []
        self.total_score: float = 0.0
        self.weighted_score: float = 0.0
        self.summary_metadata: Dict[str, Any] = {}

    def add_result(self, result: ValidationResult):
        """添加检测结果"""
        self.results.append(result)
        self._calculate_scores()

    def _calculate_scores(self):
        """计算总分"""
        if not self.results:
            self.total_score = 0.0
            self.weighted_score = 0.0
            return

        # 简单平均分
        self.total_score = sum(r.score for r in self.results) / len(self.results)

        # 加权平均分
        total_weight = sum(r.weight for r in self.results)
        if total_weight > 0:
            self.weighted_score = sum(r.score * r.weight for r in self.results) / total_weight
        else:
            self.weighted_score = self.total_score

    def get_critical_issues(self) -> List[str]:
        """获取所有严重问题"""
        critical_issues = []
        for result in self.results:
            if result.has_critical_issues():
                critical_issues.extend(result.issues)
        return critical_issues

    def get_all_issues(self) -> List[str]:
        """获取所有问题"""
        all_issues = []
        for result in self.results:
            all_issues.extend(result.issues)
        return all_issues

    def get_all_warnings(self) -> List[str]:
        """获取所有警告"""
        all_warnings = []
        for result in self.results:
            all_warnings.extend(result.warnings)
        return all_warnings

    def is_passing(self) -> bool:
        """是否通过检测"""
        return all(r.is_passing() or r.status == CheckStatus.WARNING for r in self.results)

    def get_status(self) -> CheckStatus:
        """获取总体状态"""
        if any(r.has_critical_issues() for r in self.results):
            return CheckStatus.CRITICAL
        elif any(r.status == CheckStatus.ERROR for r in self.results):
            return CheckStatus.ERROR
        elif any(r.status == CheckStatus.WARNING for r in self.results):
            return CheckStatus.WARNING
        else:
            return CheckStatus.PASS

    def to_legacy_format(self) -> Dict[str, Any]:
        """转换为旧版API格式（向后兼容）"""
        return {
            'file': self.file_path,
            'status': self.get_status().value.upper(),
            'quality_score': self.weighted_score / 100.0,  # 转换为0-1范围
            'passed_checks': len([r for r in self.results if r.is_passing()]),
            'total_checks': len(self.results),
            'issues': self.get_all_issues(),
            'warnings': self.get_all_warnings(),
            'metadata': self.summary_metadata,
            'word_count': self.summary_metadata.get('word_count', 0),
            'sections': self.summary_metadata.get('section_count', 0),
            'images': self.summary_metadata.get('image_count', 0)
        }

    def __str__(self) -> str:
        """字符串表示"""
        status = self.get_status()
        status_emoji = {
            CheckStatus.PASS: "✅",
            CheckStatus.WARNING: "⚠️",
            CheckStatus.ERROR: "❌",
            CheckStatus.CRITICAL: "🚨"
        }

        emoji = status_emoji.get(status, "❓")
        return f"{emoji} Quality Report: {self.weighted_score:.1f}/100 ({len(self.results)} checks)"