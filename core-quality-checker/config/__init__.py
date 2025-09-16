#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

提供统一的配置加载和管理功能。
"""

from .config_manager import ConfigManager
from .default_rules import get_default_config

__all__ = [
    'ConfigManager',
    'get_default_config'
]