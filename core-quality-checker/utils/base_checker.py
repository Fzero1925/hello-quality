#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础检测器接口

定义所有检测器必须实现的基础接口，确保一致性和可扩展性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .validation_result import ValidationResult, CheckStatus


class BaseChecker(ABC):
    """基础检测器抽象类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化检测器

        Args:
            config: 检测器配置
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.weight = self.config.get('weight', 1.0)

    @abstractmethod
    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        执行检测

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        pass

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'enabled': True,
            'weight': 1.0
        }

    def is_enabled(self) -> bool:
        """检查是否启用"""
        return self.config.get('enabled', True)

    def create_result(self,
                     status: CheckStatus = CheckStatus.PASS,
                     score: float = 100.0,
                     message: str = "") -> ValidationResult:
        """
        创建检测结果

        Args:
            status: 检测状态
            score: 得分
            message: 消息

        Returns:
            ValidationResult: 检测结果对象
        """
        result = ValidationResult(
            checker_name=self.name,
            status=status,
            score=score,
            weight=self.weight
        )

        if message:
            if status in [CheckStatus.ERROR, CheckStatus.CRITICAL]:
                result.add_issue(message, status.value)
            elif status == CheckStatus.WARNING:
                result.add_issue(message, "warning")

        return result

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}(enabled={self.is_enabled()}, weight={self.weight})"


class ContentChecker(BaseChecker):
    """内容检测器基类"""

    def get_default_config(self) -> Dict[str, Any]:
        """内容检测器默认配置"""
        config = super().get_default_config()
        config.update({
            'category': 'content',
            'weight': 2.0  # 内容检测器权重较高
        })
        return config


class SEOChecker(BaseChecker):
    """SEO检测器基类"""

    def get_default_config(self) -> Dict[str, Any]:
        """SEO检测器默认配置"""
        config = super().get_default_config()
        config.update({
            'category': 'seo',
            'weight': 1.5
        })
        return config


class StructureChecker(BaseChecker):
    """结构检测器基类"""

    def get_default_config(self) -> Dict[str, Any]:
        """结构检测器默认配置"""
        config = super().get_default_config()
        config.update({
            'category': 'structure',
            'weight': 1.0
        })
        return config


class ComplianceChecker(BaseChecker):
    """合规性检测器基类"""

    def get_default_config(self) -> Dict[str, Any]:
        """合规性检测器默认配置"""
        config = super().get_default_config()
        config.update({
            'category': 'compliance',
            'weight': 1.5
        })
        return config


class PQSChecker(BaseChecker):
    """PQS检测器基类"""

    def get_default_config(self) -> Dict[str, Any]:
        """PQS检测器默认配置"""
        config = super().get_default_config()
        config.update({
            'category': 'pqs',
            'weight': 2.0,
            'strict_mode': True
        })
        return config