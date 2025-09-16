#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器

负责加载、合并和管理所有配置文件，提供统一的配置接口。
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from .default_rules import get_default_config, get_checker_config


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_paths: Optional[List[str]] = None, project_root: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_paths: 配置文件路径列表
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.config_paths = config_paths or self._get_default_config_paths()
        self.config_cache: Dict[str, Any] = {}
        self.loaded = False

        # 设置日志
        self.logger = logging.getLogger(__name__)

    def _get_default_config_paths(self) -> List[str]:
        """获取默认配置文件路径"""
        return [
            str(self.project_root / 'hugo_quality_standards.yml'),
            str(self.project_root / 'image_config.yml'),
            str(self.project_root / 'config' / 'pqs_config.yml')
        ]

    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载并合并所有配置

        Args:
            force_reload: 强制重新加载

        Returns:
            Dict[str, Any]: 合并后的配置
        """
        if self.loaded and not force_reload:
            return self.config_cache

        # 从默认配置开始
        merged_config = get_default_config()

        # 依次加载配置文件
        for config_path in self.config_paths:
            file_config = self._load_single_config(config_path)
            if file_config:
                merged_config = self._merge_config(merged_config, file_config)

        self.config_cache = merged_config
        self.loaded = True

        self.logger.info(f"Configuration loaded from {len(self.config_paths)} sources")
        return merged_config

    def _load_single_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """
        加载单个配置文件

        Args:
            config_path: 配置文件路径

        Returns:
            Optional[Dict[str, Any]]: 配置数据，失败返回None
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                self.logger.warning(f"Config file not found: {config_path}")
                return None

            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                self.logger.debug(f"Loaded config from: {config_path}")
                return config_data

        except Exception as e:
            self.logger.error(f"Failed to load config {config_path}: {e}")
            return None

    def _merge_config(self, base_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并配置

        Args:
            base_config: 基础配置
            new_config: 新配置

        Returns:
            Dict[str, Any]: 合并后的配置
        """
        if not new_config:
            return base_config

        merged = base_config.copy()

        for key, value in new_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # 递归合并字典
                merged[key] = self._merge_config(merged[key], value)
            else:
                # 直接覆盖
                merged[key] = value

        return merged

    def get_checker_config(self, checker_category: str, checker_name: str) -> Dict[str, Any]:
        """
        获取特定检测器的配置

        Args:
            checker_category: 检测器类别
            checker_name: 检测器名称

        Returns:
            Dict[str, Any]: 检测器配置
        """
        config = self.load_config()

        # 检查动态配置
        checkers_config = config.get('checkers', {})
        category_config = checkers_config.get(checker_category, {})
        checker_config = category_config.get(checker_name, {})

        # 合并相关的全局配置
        result = {
            'enabled': True,
            'weight': 1.0
        }
        result.update(checker_config)

        # 添加相关的全局配置
        if checker_category == 'content':
            result.update({
                'quality_rules': config.get('quality_rules', {}),
                'adsense_compliance': config.get('adsense_compliance', {})
            })
        elif checker_category == 'seo':
            result.update({
                'seo': config.get('seo', {}),
                'quality_rules': config.get('quality_rules', {})
            })
        elif checker_category == 'structure':
            result.update({
                'quality_rules': config.get('quality_rules', {}),
                'tldr_requirements': config.get('tldr_requirements', {})
            })
        elif checker_category == 'compliance':
            result.update({
                'adsense_compliance': config.get('adsense_compliance', {}),
                'quality_rules': config.get('quality_rules', {})
            })
        elif checker_category == 'pqs':
            result.update({
                'pqs_v3': config.get('pqs_v3', {})
            })

        return result

    def get_weight_config(self) -> Dict[str, float]:
        """获取权重配置"""
        config = self.load_config()
        weights = config.get('quality_scoring', {}).get('weights', {})

        # 确保有完整的权重配置
        default_weights = {
            'content_depth': 0.40,
            'seo_technical': 0.20,
            'content_structure': 0.15,
            'readability': 0.10,
            'adsense_compliance': 0.10,
            'reserved': 0.05
        }

        for key, default_value in default_weights.items():
            if key not in weights:
                weights[key] = default_value

        return weights

    def get_scoring_thresholds(self) -> Dict[str, float]:
        """获取评分阈值"""
        config = self.load_config()
        scoring_config = config.get('quality_scoring', {})

        return {
            'min_passing_score': scoring_config.get('min_passing_score', 75),
            'min_good_score': scoring_config.get('min_good_score', 85),
            'min_excellent_score': scoring_config.get('min_excellent_score', 95)
        }

    def is_pqs_mode_enabled(self) -> bool:
        """检查是否启用PQS模式"""
        config = self.load_config()
        pqs_config = config.get('checkers', {}).get('pqs', {})
        return (pqs_config.get('hard_gates', {}).get('enabled', False) or
                pqs_config.get('score_calculation', {}).get('enabled', False))

    def get_pqs_config(self) -> Dict[str, Any]:
        """获取PQS配置"""
        config = self.load_config()
        return config.get('pqs_v3', {
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
        })

    def get_enabled_checkers(self) -> Dict[str, List[str]]:
        """
        获取启用的检测器列表

        Returns:
            Dict[str, List[str]]: {category: [checker_names]}
        """
        config = self.load_config()
        checkers_config = config.get('checkers', {})

        enabled_checkers = {}
        for category, category_checkers in checkers_config.items():
            enabled_checkers[category] = []
            for checker_name, checker_config in category_checkers.items():
                if checker_config.get('enabled', True):
                    enabled_checkers[category].append(checker_name)

        return enabled_checkers

    def update_config(self, updates: Dict[str, Any]):
        """
        动态更新配置

        Args:
            updates: 配置更新
        """
        if not self.loaded:
            self.load_config()

        self.config_cache = self._merge_config(self.config_cache, updates)
        self.logger.info("Configuration updated dynamically")

    def reload_config(self):
        """重新加载配置"""
        self.loaded = False
        self.config_cache.clear()
        self.load_config()

    def save_config_to_file(self, output_path: str):
        """
        保存当前配置到文件

        Args:
            output_path: 输出文件路径
        """
        config = self.load_config()

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            self.logger.info(f"Configuration saved to: {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config to {output_path}: {e}")
            raise

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要信息"""
        config = self.load_config()
        enabled_checkers = self.get_enabled_checkers()

        return {
            'total_checkers': sum(len(checkers) for checkers in enabled_checkers.values()),
            'enabled_checkers': enabled_checkers,
            'pqs_mode': self.is_pqs_mode_enabled(),
            'config_sources': [str(Path(p).name) for p in self.config_paths if Path(p).exists()],
            'scoring_weights': self.get_weight_config(),
            'thresholds': self.get_scoring_thresholds()
        }