#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PQS专项检测模块

Publisher Quality Score v3 专项检测器，从原始quality_check.py重构而来。
提供严格的质量门槛检测和高级评分计算。
"""

import os
import re
from typing import Dict, Any, List
from ..utils.base_checker import PQSChecker
from ..utils.validation_result import ValidationResult, CheckStatus
from ..utils.content_parser import ContentParser


class PQSHardGatesChecker(PQSChecker):
    """PQS v3硬性门槛检测器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        执行PQS v3硬性门槛检测

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "PQS hard gates check disabled")

        # 获取PQS配置
        pqs_config = self.config.get('pqs_v3', {})
        thresholds = pqs_config.get('thresholds', {})

        # 解析Front Matter
        try:
            fm_text, article_content, has_fm = ContentParser.extract_front_matter(content)
            fm_data = ContentParser.parse_front_matter_data(fm_text) if has_fm else {}
        except:
            fm_data = {}
            article_content = content

        # 创建结果
        result = self.create_result(CheckStatus.PASS, 100.0)
        hard_gate_failures = []

        # 硬性门槛1: Featured图片 + 至少2张内联图片
        image_gate_passed = self._check_image_hard_gate(fm_data, article_content, thresholds, hard_gate_failures)

        # 硬性门槛2: 证据链接 >= 2
        evidence_gate_passed = self._check_evidence_hard_gate(article_content, hard_gate_failures)

        # 硬性门槛3: JSON-LD结构化数据
        jsonld_gate_passed = self._check_jsonld_hard_gate(content, hard_gate_failures)

        # 硬性门槛4: 比较表格（解决"空心推荐"问题）
        comparison_gate_passed = self._check_comparison_hard_gate(article_content, hard_gate_failures)

        # 硬性门槛5: 关键词密度检查
        keyword_gate_passed = self._check_keyword_density_hard_gate(fm_data, article_content, thresholds, hard_gate_failures)

        # 硬性门槛6: 实体覆盖度 >= 3
        entity_gate_passed = self._check_entity_coverage_hard_gate(fm_data, article_content, pqs_config, hard_gate_failures)

        # 硬性门槛7: 合规披露定位
        disclosure_gate_passed = self._check_disclosure_positioning_hard_gate(article_content, hard_gate_failures)

        # 硬性门槛8: 基础可读性要求
        readability_gate_passed = self._check_readability_hard_gate(article_content, hard_gate_failures)

        # 设置结果
        all_gates_passed = all([
            image_gate_passed, evidence_gate_passed, jsonld_gate_passed,
            comparison_gate_passed, keyword_gate_passed, entity_gate_passed,
            disclosure_gate_passed, readability_gate_passed
        ])

        result.set_metadata('pqs_hard_gates_passed', all_gates_passed)
        result.set_metadata('hard_gate_failures', len(hard_gate_failures))
        result.set_metadata('total_hard_gates', 8)

        if not all_gates_passed:
            result.status = CheckStatus.CRITICAL
            result.score = max(0, 50 - len(hard_gate_failures) * 10)
            for failure in hard_gate_failures:
                result.add_issue(f"HARD GATE FAIL: {failure}", "critical")
            result.add_suggestion("Fix all hard gate failures before publication - these are mandatory requirements")
        else:
            result.score = 100.0
            result.add_suggestion("All PQS hard gates passed - article meets publication standards")

        return result

    def _check_image_hard_gate(self, fm_data: Dict, article_content: str, thresholds: Dict, failures: List[str]) -> bool:
        """检查图片硬性门槛"""
        # 检查featured_image
        featured_image = fm_data.get('featured_image')
        if not featured_image:
            failures.append("Missing featured_image in front matter")
            return False

        # 验证featured_image文件存在
        try:
            if featured_image.startswith('/'):
                fs_path = os.path.join('static', featured_image.lstrip('/'))
            else:
                fs_path = os.path.join('static', featured_image)
            if not os.path.exists(fs_path):
                failures.append(f"featured_image not found: {featured_image}")
        except Exception:
            pass

        # 检查内联图片数量
        images = ContentParser.extract_images(article_content)
        min_inline = thresholds.get('min_inline_images', 2)

        if len(images) < min_inline:
            failures.append(f"Insufficient inline images ({len(images)} < {min_inline})")

        # 验证内联图片Alt文本质量
        entity_tokens = self._get_entity_tokens(fm_data)
        for alt_text, img_path in images:
            # 检查文件存在
            try:
                if img_path.startswith('/'):
                    fs_path = os.path.join('static', img_path.lstrip('/'))
                else:
                    fs_path = os.path.join('static', img_path)
                if not os.path.exists(fs_path):
                    failures.append(f"Inline image not found: {img_path}")
            except Exception:
                pass

            # Alt文本质量检查
            if not alt_text or len(alt_text.strip()) < 8:
                failures.append(f"ALT text too short (<8 chars): '{alt_text}'")
            elif len(alt_text) > 120:
                failures.append(f"ALT text too long (>120 chars): '{alt_text[:50]}...'")
            elif entity_tokens and not any(token.lower() in alt_text.lower() for token in entity_tokens):
                failures.append(f"ALT text lacks entity tokens: '{alt_text[:50]}...'")

        return len(failures) == 0 or not any("image" in f.lower() or "alt" in f.lower() for f in failures[-10:])

    def _check_evidence_hard_gate(self, article_content: str, failures: List[str]) -> bool:
        """检查证据链接硬性门槛"""
        external_links = ContentParser.extract_links(article_content)['external']
        if len(external_links) < 2:
            failures.append(f"Insufficient evidence links ({len(external_links)} < 2)")
            return False
        return True

    def _check_jsonld_hard_gate(self, content: str, failures: List[str]) -> bool:
        """检查JSON-LD硬性门槛"""
        jsonld_patterns = [r'"@type"\s*:\s*"Article"', r'"@type"\s*:\s*"FAQPage"']
        has_jsonld = any(re.search(pattern, content, re.IGNORECASE) for pattern in jsonld_patterns)
        if not has_jsonld:
            failures.append("Missing JSON-LD structured data")
            return False
        return True

    def _check_comparison_hard_gate(self, article_content: str, failures: List[str]) -> bool:
        """检查比较表格硬性门槛"""
        # 检查表格行数
        table_rows = [ln.strip() for ln in article_content.splitlines() if ln.strip().startswith('|')]
        has_proper_table = len(table_rows) >= 6  # 头部 + 分隔符 + 至少4行数据

        # 检查表格列
        has_model_column = False
        has_protocol_column = False
        if table_rows:
            header_row = table_rows[0].lower()
            has_model_column = any(word in header_row for word in ['model', 'product', 'device', 'name'])
            has_protocol_column = any(word in header_row for word in ['protocol', 'connectivity', 'wifi', 'zigbee', 'matter'])

        if not has_proper_table:
            failures.append(f"Missing proper comparison table (found {len(table_rows)} rows, need ≥6)")
        elif not (has_model_column and has_protocol_column):
            failures.append("Comparison table must include Model and Protocol columns")

        # 检查备选方案：具体型号提及
        has_specific_models = len(re.findall(r'(?i)(model|version)\s+[\w\d-]{3,}', article_content)) >= 3
        has_itemlist = 'ItemList' in content

        if not has_proper_table and not has_itemlist and not has_specific_models:
            failures.append("No structured comparison - need table OR ≥3 specific model names")
            return False

        return True

    def _check_keyword_density_hard_gate(self, fm_data: Dict, article_content: str, thresholds: Dict, failures: List[str]) -> bool:
        """检查关键词密度硬性门槛"""
        primary_kw = fm_data.get('keyword', fm_data.get('title', '').split('|')[0])
        if primary_kw:
            word_count = len(article_content.split())
            kw_count = len(re.findall(re.escape(primary_kw.lower()), article_content.lower()))
            density = kw_count / max(1, word_count)
            max_density = thresholds.get('keyword_density_max', 0.025)

            if density > max_density:
                failures.append(f"Keyword density too high ({density:.1%} > {max_density:.1%})")
                return False
        return True

    def _check_entity_coverage_hard_gate(self, fm_data: Dict, article_content: str, pqs_config: Dict, failures: List[str]) -> bool:
        """检查实体覆盖度硬性门槛"""
        text_lower = article_content.lower()
        entity_tokens = self._get_entity_tokens(fm_data, pqs_config)

        entity_hits = [token for token in entity_tokens if token.lower() in text_lower]
        if len(set(entity_hits)) < 3:
            failures.append(f"Insufficient entity coverage ({len(set(entity_hits))} < 3)")
            return False
        return True

    def _check_disclosure_positioning_hard_gate(self, article_content: str, failures: List[str]) -> bool:
        """检查披露定位硬性门槛"""
        disclosure_patterns = [
            r'(?i)(affiliate|commission|earn.*from.*purchas|as an amazon associate)',
            r'(?i)(disclosure|披露)',
            r'(?i)(no.*physical.*test|research.*based|specification.*analysis)'
        ]

        # 检查前600字符内是否有披露
        first_screen = article_content[:600]
        has_early_disclosure = any(re.search(pattern, first_screen) for pattern in disclosure_patterns)

        # 检查全文是否有方法论披露
        has_methodology_disclosure = any(re.search(pattern, article_content) for pattern in disclosure_patterns)

        if not has_methodology_disclosure:
            failures.append("Missing methodology/no-testing disclosure statement")
            return False
        elif not has_early_disclosure:
            failures.append("Disclosure must appear within first 600 characters")
            return False

        return True

    def _check_readability_hard_gate(self, article_content: str, failures: List[str]) -> bool:
        """检查可读性硬性门槛"""
        word_count = len(article_content.split())
        if word_count < 1500:
            failures.append(f"Article too short ({word_count} words, minimum 1500)")

        # 检查段落长度
        paragraphs = ContentParser.extract_paragraphs(article_content)
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 120]
        if len(long_paragraphs) > len(paragraphs) * 0.3:
            failures.append(f"Too many long paragraphs ({len(long_paragraphs)}, max 30% of total)")

        # 检查句子结构
        sentences = ContentParser.extract_sentences(article_content)
        if sentences:
            avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_len > 35:
                failures.append(f"Sentences too long (avg {avg_sentence_len:.1f} words, max 35)")

        return len([f for f in failures if any(word in f.lower() for word in ['short', 'paragraph', 'sentence'])]) == 0

    def _get_entity_tokens(self, fm_data: Dict, pqs_config: Dict = None) -> List[str]:
        """获取实体标记"""
        if not pqs_config:
            pqs_config = self.config.get('pqs_v3', {})

        entities_tokens = pqs_config.get('entities_tokens', {})
        category = fm_data.get('category', fm_data.get('categories', ['generic']))
        if isinstance(category, list):
            category = category[0] if category else 'generic'

        tokens = entities_tokens.get(category, []) + entities_tokens.get('generic', [])
        return tokens


class PQSScoreCalculator(PQSChecker):
    """PQS评分计算器"""

    def check(self, content: str, front_matter: str = "", **kwargs) -> ValidationResult:
        """
        计算PQS v3评分

        Args:
            content: 文章内容
            front_matter: Front Matter内容
            **kwargs: 其他参数（应包含hard_gates_result）

        Returns:
            ValidationResult: 检测结果
        """
        if not self.is_enabled():
            return self.create_result(CheckStatus.PASS, 100.0, "PQS score calculation disabled")

        # 获取硬性门槛结果
        hard_gates_result = kwargs.get('hard_gates_result')
        if hard_gates_result and not hard_gates_result.get('metadata', {}).get('pqs_hard_gates_passed', False):
            # 硬性门槛未通过，评分为0
            result = self.create_result(CheckStatus.CRITICAL, 0.0)
            result.add_issue("PQS SCORE FAIL: Hard gates not passed", "critical")
            result.set_metadata('pqs_total_score', 0)
            result.set_metadata('pqs_threshold', self.config.get('pqs_v3', {}).get('thresholds', {}).get('publish_score', 85))
            result.set_metadata('pqs_hard_gates_passed', False)
            return result

        # 解析内容
        try:
            fm_text, article_content, has_fm = ContentParser.extract_front_matter(content)
            fm_data = ContentParser.parse_front_matter_data(fm_text) if has_fm else {}
        except:
            fm_data = {}
            article_content = content

        # 计算各项得分
        depth_score = self._calculate_depth_score(article_content)  # 30分
        evidence_score = self._calculate_evidence_score(article_content)  # 20分
        images_score = self._calculate_images_score(content, fm_data, article_content)  # 15分
        structure_score = self._calculate_structure_score(article_content)  # 15分
        readability_score = self._calculate_readability_score(article_content)  # 10分
        compliance_score = self._calculate_compliance_score(fm_data, article_content)  # 10分

        total_score = depth_score + evidence_score + images_score + structure_score + readability_score + compliance_score
        total_score = max(0, min(100, total_score))

        # 获取阈值
        pqs_config = self.config.get('pqs_v3', {})
        threshold = pqs_config.get('thresholds', {}).get('publish_score', 85)

        # 创建结果
        result = self.create_result(CheckStatus.PASS, total_score)
        result.set_metadata('pqs_total_score', total_score)
        result.set_metadata('pqs_threshold', threshold)
        result.set_metadata('pqs_hard_gates_passed', True)
        result.set_metadata('pqs_subscores', {
            'depth': depth_score,
            'evidence': evidence_score,
            'images': images_score,
            'structure': structure_score,
            'readability': readability_score,
            'compliance': compliance_score
        })

        if total_score < threshold:
            result.status = CheckStatus.ERROR
            result.add_issue(f"PQS SCORE FAIL: {total_score}/100 (threshold: {threshold})", "error")
            result.add_suggestion("Improve content depth, evidence quality, and structure to meet PQS standards")

        return result

    def _calculate_depth_score(self, article_content: str) -> float:
        """计算内容深度得分 (30分)"""
        depth_score = 0

        if re.search(r'(?i)(conclusion|summary)', article_content):
            depth_score += 6
        if '|' in article_content:  # 包含表格
            depth_score += 8
        if re.search(r'(?i)(alternatives|who should buy|who should not buy)', article_content):
            depth_score += 8
        if re.search(r'(?i)(risks|watch out|considerations)', article_content):
            depth_score += 8

        return min(30, depth_score)

    def _calculate_evidence_score(self, article_content: str) -> float:
        """计算证据质量得分 (20分)"""
        external_links = ContentParser.extract_links(article_content)['external']
        evidence_score = min(20, len(external_links) * 5)
        return evidence_score

    def _calculate_images_score(self, content: str, fm_data: Dict, article_content: str) -> float:
        """计算图片和可视化得分 (15分)"""
        images = ContentParser.extract_images(article_content)
        featured_image = fm_data.get('featured_image')
        images_score = 0

        if featured_image:
            images_score += 7
        if len(images) >= 2:
            images_score += 8

        return min(15, images_score)

    def _calculate_structure_score(self, article_content: str) -> float:
        """计算结构和SEO得分 (15分)"""
        structure_score = 0

        if re.search(r'^\s*#\s+.+', article_content, re.M):  # H1
            structure_score += 5
        if len(re.findall(r'^\s*##\s+.+', article_content, re.M)) >= 4:  # H2s
            structure_score += 5
        if re.search(r'\[(.+)\]\((\/[^)]+)\)', article_content):  # 内部链接
            structure_score += 5

        return min(15, structure_score)

    def _calculate_readability_score(self, article_content: str) -> float:
        """计算可读性得分 (10分)"""
        sentences = ContentParser.extract_sentences(article_content)
        if sentences:
            avg_len = sum(len(s) for s in sentences) / len(sentences)
            h2_count = len(re.findall(r'^\s*##\s+.+', article_content, re.M))
            readability_score = max(0, min(10, (100 - min(70, avg_len) + min(10, h2_count*2)) / 10))
        else:
            readability_score = 5

        return readability_score

    def _calculate_compliance_score(self, fm_data: Dict, article_content: str) -> float:
        """计算合规性和E-E-A-T得分 (10分)"""
        compliance_score = 0

        if fm_data.get('author') and fm_data.get('date'):
            compliance_score += 4
        if re.search(r'(?i)(affiliate disclosure|as an amazon associate|披露)', article_content):
            compliance_score += 3
        if re.search(r'(?i)(about|review policy)', article_content):
            compliance_score += 3

        return min(10, compliance_score)