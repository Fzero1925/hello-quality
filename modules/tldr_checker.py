#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TL;DR检测器
检测文章中的要点总结部分，提升用户体验和可读性
"""

import re
import yaml
from typing import Dict, List, Tuple, Optional

class TLDRChecker:
    """TL;DR要点总结检测器"""

    def __init__(self, config_path: str = "hugo_quality_standards.yml"):
        """初始化"""
        self.config = self._load_config(config_path)
        self.tldr_config = self.config.get('content_structure_requirements', {}).get('tldr_requirements', {})

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def check_tldr(self, content: str) -> Dict:
        """检测文章的TL;DR部分

        Args:
            content: 文章内容

        Returns:
            TL;DR检测结果
        """
        if not self.tldr_config.get('enabled', True):
            return {'enabled': False}

        # 提取文章正文（去除Front Matter）
        article_body = self._extract_article_body(content)

        # 查找TL;DR部分
        tldr_sections = self._find_tldr_sections(article_body)

        # 分析结果
        results = {
            'enabled': True,
            'required': self.tldr_config.get('required', True),
            'found_sections': len(tldr_sections),
            'sections': tldr_sections,
            'problems': [],
            'suggestions': [],
            'score': 0
        }

        # 检查是否满足要求
        if self.tldr_config.get('required', True):
            if not tldr_sections:
                results['problems'].append({
                    'type': 'missing_tldr',
                    'severity': 'warning',
                    'description': '缺少TL;DR要点总结部分',
                    'impact': '影响用户快速获取文章要点，降低用户体验'
                })
                results['suggestions'].append(self._generate_tldr_suggestion(article_body))
            else:
                # 检查TL;DR质量
                for i, section in enumerate(tldr_sections):
                    quality_issues = self._analyze_tldr_quality(section, i + 1)
                    results['problems'].extend(quality_issues)

        # 计算得分
        results['score'] = self._calculate_tldr_score(results)

        return results

    def _extract_article_body(self, content: str) -> str:
        """提取文章正文，去除Front Matter"""
        if content.startswith('---'):
            end_index = content.find('\n---', 3)
            if end_index != -1:
                return content[end_index + 4:]
        return content

    def _find_tldr_sections(self, content: str) -> List[Dict]:
        """查找TL;DR部分"""
        keywords = self.tldr_config.get('keywords', ['TL;DR', 'TLDR', '要点总结'])
        sections = []

        # 为每个关键词构建正则表达式
        for keyword in keywords:
            # 匹配标题格式: ## TL;DR 或 **TL;DR**
            patterns = [
                rf'^#+\s*{re.escape(keyword)}.*?$',  # Markdown标题
                rf'\*\*{re.escape(keyword)}\*\*',    # 粗体
                rf'_{re.escape(keyword)}_',          # 斜体
                rf'{re.escape(keyword)}[:：]',       # 冒号分隔
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    section = self._extract_tldr_content(content, match)
                    if section:
                        sections.append(section)

        # 去重并按位置排序
        unique_sections = []
        seen_positions = set()
        for section in sections:
            pos = section['start_pos']
            if pos not in seen_positions:
                unique_sections.append(section)
                seen_positions.add(pos)

        return sorted(unique_sections, key=lambda x: x['start_pos'])

    def _extract_tldr_content(self, content: str, match) -> Optional[Dict]:
        """提取TL;DR内容"""
        start_pos = match.start()
        match_text = match.group()

        # 查找TL;DR内容的结束位置
        lines = content[start_pos:].split('\n')
        tldr_lines = [lines[0]]  # 包含标题行

        # 收集后续的列表项或段落
        for i, line in enumerate(lines[1:], 1):
            line = line.strip()
            if not line:
                continue
            # 如果是列表项或继续的内容
            if (line.startswith(('- ', '* ', '+ ', '1. ', '2. ')) or
                line.startswith(('•', '▪', '◦')) or
                not re.match(r'^#+\s', line)):  # 不是新的标题
                tldr_lines.append(lines[i])
            else:
                break  # 遇到新的标题，停止

        # 分析内容
        full_content = '\n'.join(tldr_lines)
        points = self._extract_points(full_content)

        return {
            'keyword_matched': match_text.strip(),
            'start_pos': start_pos,
            'content': full_content,
            'points': points,
            'point_count': len(points),
            'position_in_article': self._determine_position(content, start_pos)
        }

    def _extract_points(self, content: str) -> List[str]:
        """提取要点列表"""
        points = []

        # 匹配各种列表格式
        list_patterns = [
            r'^[-*+]\s+(.+)',          # - 项目符号
            r'^\d+\.\s+(.+)',          # 1. 编号列表
            r'^[•▪◦]\s+(.+)',          # Unicode项目符号
        ]

        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            for pattern in list_patterns:
                match = re.match(pattern, line)
                if match:
                    point = match.group(1).strip()
                    if len(point) > 10:  # 要点应该有一定长度
                        points.append(point)
                    break

        return points

    def _determine_position(self, content: str, start_pos: int) -> str:
        """判断TL;DR在文章中的位置"""
        article_length = len(content)
        relative_position = start_pos / article_length

        if relative_position < 0.3:
            return "beginning"
        elif relative_position < 0.7:
            return "middle"
        else:
            return "end"

    def _analyze_tldr_quality(self, section: Dict, section_index: int) -> List[Dict]:
        """分析TL;DR质量"""
        problems = []
        min_points = self.tldr_config.get('min_points', 3)
        max_points = self.tldr_config.get('max_points', 8)
        preferred_position = self.tldr_config.get('position', 'beginning')

        point_count = section['point_count']
        position = section['position_in_article']

        # 检查要点数量
        if point_count < min_points:
            problems.append({
                'type': 'insufficient_points',
                'severity': 'warning',
                'section_index': section_index,
                'description': f'TL;DR要点过少({point_count}个，建议{min_points}-{max_points}个)',
                'current_count': point_count,
                'recommended_range': f"{min_points}-{max_points}"
            })

        if point_count > max_points:
            problems.append({
                'type': 'excessive_points',
                'severity': 'suggestion',
                'section_index': section_index,
                'description': f'TL;DR要点过多({point_count}个，建议{min_points}-{max_points}个)',
                'current_count': point_count,
                'recommended_range': f"{min_points}-{max_points}"
            })

        # 检查位置
        if preferred_position != 'anywhere' and position != preferred_position:
            problems.append({
                'type': 'suboptimal_position',
                'severity': 'suggestion',
                'section_index': section_index,
                'description': f'TL;DR位置建议优化(当前在{position}部分，建议在{preferred_position})',
                'current_position': position,
                'recommended_position': preferred_position
            })

        # 检查要点质量
        points = section['points']
        for i, point in enumerate(points):
            if len(point) < 20:
                problems.append({
                    'type': 'short_point',
                    'severity': 'suggestion',
                    'section_index': section_index,
                    'point_index': i + 1,
                    'description': f'第{i+1}个要点过于简短({len(point)}字符)',
                    'point_content': point[:50]
                })

        return problems

    def _calculate_tldr_score(self, results: Dict) -> int:
        """计算TL;DR得分"""
        if not results['enabled']:
            return 100  # 如果禁用，给满分

        if not results['required']:
            return 100  # 如果不要求，给满分

        base_score = 100
        sections = results['sections']

        # 如果完全没有TL;DR
        if not sections:
            return 30

        # 根据问题扣分
        problems = results['problems']
        for problem in problems:
            if problem['severity'] == 'critical':
                base_score -= 30
            elif problem['severity'] == 'warning':
                base_score -= 15
            elif problem['severity'] == 'suggestion':
                base_score -= 5

        # 根据最佳实践加分
        best_section = max(sections, key=lambda x: x['point_count']) if sections else None
        if best_section:
            min_points = self.tldr_config.get('min_points', 3)
            max_points = self.tldr_config.get('max_points', 8)

            if min_points <= best_section['point_count'] <= max_points:
                base_score += 10  # 要点数量合理

            if best_section['position_in_article'] == self.tldr_config.get('position', 'beginning'):
                base_score += 5   # 位置正确

        return max(0, min(100, base_score))

    def _generate_tldr_suggestion(self, content: str) -> Dict:
        """生成TL;DR建议"""
        # 分析文章结构，提取可能的要点
        sections = self._extract_article_sections(content)
        suggested_points = []

        # 从各个部分提取要点
        for section in sections[:5]:  # 取前5个部分
            title = section.get('title', '').strip()
            if title and len(title) > 10:
                # 生成基于标题的要点
                point = self._title_to_point(title)
                if point:
                    suggested_points.append(point)

        # 如果没有足够的要点，生成通用建议
        if len(suggested_points) < 3:
            suggested_points = [
                "本文介绍了[主题]的核心特点和优势",
                "详细对比了市面上主流[产品]的性能差异",
                "提供了实用的购买建议和选择要点",
                "总结了使用过程中需要注意的关键问题"
            ]

        return {
            'type': 'tldr_suggestion',
            'recommended_format': '## TL;DR 文章要点',
            'suggested_points': suggested_points[:6],  # 最多6个要点
            'placement_suggestion': 'beginning',
            'example_markdown': self._generate_tldr_markdown(suggested_points[:5])
        }

    def _extract_article_sections(self, content: str) -> List[Dict]:
        """提取文章章节"""
        sections = []
        lines = content.split('\n')

        current_section = None
        for line in lines:
            # 匹配标题
            heading_match = re.match(r'^(#+)\s+(.+)$', line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                if current_section:
                    sections.append(current_section)

                current_section = {
                    'level': level,
                    'title': title,
                    'content': []
                }
            elif current_section:
                current_section['content'].append(line)

        if current_section:
            sections.append(current_section)

        return sections

    def _title_to_point(self, title: str) -> str:
        """将标题转换为要点"""
        # 移除常见的标题词汇
        title = re.sub(r'^(什么是|如何|怎么|为什么|介绍)', '', title)
        title = title.strip()

        if len(title) < 5:
            return ""

        # 转换为要点格式
        if not title.endswith(('。', '!', '?', '：', ':')):
            title += "的关键信息"

        return title

    def _generate_tldr_markdown(self, points: List[str]) -> str:
        """生成TL;DR的Markdown示例"""
        markdown = "## TL;DR 文章要点\n\n"
        for i, point in enumerate(points, 1):
            markdown += f"{i}. {point}\n"
        markdown += "\n---\n"
        return markdown