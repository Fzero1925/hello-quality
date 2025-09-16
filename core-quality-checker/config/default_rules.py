#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
默认检测规则配置

定义各个检测器的默认配置规则，当配置文件不存在时使用。
"""

from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """获取默认的完整配置"""
    return {
        # 质量检测规则
        'quality_rules': {
            'min_images': 3,
            'require_featured': True,
            'ban_words_in_alt': True,
            'min_internal_links': 3,
            'min_external_links': 2,
            'require_disclosure': True,
            'require_schema': True,
            'require_author_and_date': True,
            'max_duplicate_usage': 3,
            'min_image_relevance_score': 0.6,
            'min_word_count': 1500,
            'max_word_count': 4000,
            'min_sections': 5,
            'require_faq': True,
            'require_conclusion': True
        },

        # SEO配置
        'seo': {
            'banned_alt_words': ['best', '2025', 'cheap', 'lowest price', 'amazing', 'incredible'],
            'max_alt_length': 125,
            'min_alt_length': 15
        },

        # 权重配置
        'quality_scoring': {
            'weights': {
                'content_depth': 0.40,
                'seo_technical': 0.20,
                'content_structure': 0.15,
                'readability': 0.10,
                'adsense_compliance': 0.10,
                'reserved': 0.05
            },
            'min_passing_score': 75,
            'min_good_score': 85,
            'min_excellent_score': 95
        },

        # AdSense合规性
        'adsense_compliance': {
            'forbidden_phrases': {
                'critical': [
                    'click here', 'buy now', 'act now', 'limited time only',
                    'best deal ever', 'guaranteed results', '100% guaranteed',
                    'get rich quick', 'make money fast', 'exclusive offer',
                    'miracle solution', 'secret method', 'amazing discovery',
                    'special discount'
                ],
                'warning': [
                    'must buy', "don't miss", 'hurry up', 'while supplies last',
                    'act fast', 'limited quantity', 'today only', 'flash sale',
                    'super sale', 'mega deal'
                ],
                'suggestion': [
                    'revolutionary', 'breakthrough', 'life-changing', 'game-changer',
                    'incredible', 'unbelievable', 'phenomenal', 'outstanding'
                ]
            },
            'source_verification': {
                'enabled': False,  # 手写文章保持禁用来源验证
                'min_sources': 2,
                'min_trusted_ratio': 0.50,
                'min_content_length_for_sources': 2000
            }
        },

        # PQS v3配置
        'pqs_v3': {
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
        },

        # TL;DR检测配置
        'tldr_requirements': {
            'enabled': True,
            'required': True,
            'position': 'beginning',
            'min_points': 3,
            'max_points': 8,
            'keywords': [
                'TL;DR', 'TLDR', '要点总结', '核心要点',
                '文章要点', '快速总结', '关键信息', '重点摘要'
            ]
        },

        # 检测器启用配置
        'checkers': {
            'content': {
                'word_count': {'enabled': True, 'weight': 2.0},
                'duplicate_content': {'enabled': True, 'weight': 1.5},
                'image_relevance': {'enabled': True, 'weight': 1.0},
                'forbidden_phrases': {'enabled': True, 'weight': 2.0}
            },
            'seo': {
                'images': {'enabled': True, 'weight': 1.5},
                'alt_text': {'enabled': True, 'weight': 1.5},
                'internal_links': {'enabled': True, 'weight': 1.0},
                'external_links': {'enabled': True, 'weight': 1.0},
                'schema_markup': {'enabled': True, 'weight': 0.5}
            },
            'structure': {
                'sections': {'enabled': True, 'weight': 1.0},
                'faq': {'enabled': True, 'weight': 1.0},
                'conclusion': {'enabled': True, 'weight': 1.0},
                'front_matter': {'enabled': True, 'weight': 1.5},
                'author_date': {'enabled': True, 'weight': 1.0}
            },
            'compliance': {
                'affiliate_disclosure': {'enabled': True, 'weight': 1.5},
                'adsense': {'enabled': True, 'weight': 2.0}
            },
            'pqs': {
                'hard_gates': {'enabled': False, 'weight': 3.0},  # 默认禁用PQS
                'score_calculation': {'enabled': False, 'weight': 3.0}
            }
        }
    }


def get_checker_config(checker_category: str, checker_name: str) -> Dict[str, Any]:
    """
    获取特定检测器的配置

    Args:
        checker_category: 检测器类别 (content, seo, structure, compliance, pqs)
        checker_name: 检测器名称

    Returns:
        Dict[str, Any]: 检测器配置
    """
    default_config = get_default_config()
    checkers_config = default_config.get('checkers', {})
    category_config = checkers_config.get(checker_category, {})
    checker_config = category_config.get(checker_name, {})

    # 合并全局规则
    result = {
        'enabled': True,
        'weight': 1.0
    }
    result.update(checker_config)

    # 添加相关的全局配置
    if checker_category == 'content':
        result.update({'quality_rules': default_config.get('quality_rules', {})})
    elif checker_category == 'seo':
        result.update({'seo': default_config.get('seo', {})})
    elif checker_category == 'compliance':
        result.update({'adsense_compliance': default_config.get('adsense_compliance', {})})
    elif checker_category == 'pqs':
        result.update({'pqs_v3': default_config.get('pqs_v3', {})})

    return result


def get_weight_config() -> Dict[str, float]:
    """获取权重配置"""
    default_config = get_default_config()
    return default_config.get('quality_scoring', {}).get('weights', {
        'content_depth': 0.40,
        'seo_technical': 0.20,
        'content_structure': 0.15,
        'readability': 0.10,
        'adsense_compliance': 0.10,
        'reserved': 0.05
    })


def get_scoring_thresholds() -> Dict[str, float]:
    """获取评分阈值配置"""
    default_config = get_default_config()
    scoring_config = default_config.get('quality_scoring', {})
    return {
        'min_passing_score': scoring_config.get('min_passing_score', 75),
        'min_good_score': scoring_config.get('min_good_score', 85),
        'min_excellent_score': scoring_config.get('min_excellent_score', 95)
    }