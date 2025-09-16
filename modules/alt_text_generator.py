#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alt文本生成器
检测图片Alt文本问题并生成修复建议，不直接修改文件
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.parse import unquote

class AltTextGenerator:
    """Alt文本检测和建议生成器"""

    def __init__(self, config_path: str = "hugo_quality_standards.yml"):
        """初始化"""
        self.config = self._load_config(config_path)
        self.image_config = self.config.get('image_optimization', {})
        self.alt_config = self.image_config.get('seo_requirements', {})

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def analyze_images(self, content: str, front_matter_data: Dict, file_path: str = "") -> Dict:
        """分析文章中的图片Alt文本问题

        Args:
            content: 文章完整内容
            front_matter_data: Front Matter数据
            file_path: 文章文件路径

        Returns:
            图片分析结果
        """
        # 提取文章正文（去除Front Matter）
        if content.startswith('---'):
            end_index = content.find('\n---', 3)
            if end_index != -1:
                article_body = content[end_index + 4:]
            else:
                article_body = content
        else:
            article_body = content

        # 提取所有图片
        images = self._extract_images(article_body)
        featured_image = front_matter_data.get('featured_image', '')

        # 分析各种图片问题
        results = {
            'total_images': len(images) + (1 if featured_image else 0),
            'inline_images': len(images),
            'featured_image': featured_image,
            'problems': [],
            'suggestions': [],
            'fix_code': []
        }

        # 检查featured_image
        if not featured_image:
            results['problems'].append({
                'type': 'missing_featured_image',
                'severity': 'critical',
                'description': '缺少featured_image字段'
            })

        # 检查inline图片
        for i, (alt_text, img_path, full_match) in enumerate(images, 1):
            problems = self._check_single_image(alt_text, img_path, i, front_matter_data)
            results['problems'].extend(problems)

            # 生成修复建议
            if any(p['type'] in ['missing_alt', 'short_alt', 'poor_alt'] for p in problems):
                suggestion = self._generate_alt_suggestion(
                    alt_text, img_path, i, front_matter_data, file_path
                )
                results['suggestions'].append(suggestion)

                # 生成修复代码
                fix_code = self._generate_fix_code(full_match, suggestion['suggested_alt'])
                results['fix_code'].append(fix_code)

        return results

    def _extract_images(self, content: str) -> List[Tuple[str, str, str]]:
        """提取文章中的所有图片

        Returns:
            List[(alt_text, img_path, full_match)]
        """
        # 匹配Markdown图片格式: ![alt](path)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.findall(image_pattern, content)

        # 同时保存完整匹配用于替换
        full_matches = re.finditer(image_pattern, content)

        results = []
        for match, full_match in zip(matches, re.finditer(image_pattern, content)):
            alt_text, img_path = match
            full_match_text = full_match.group(0)
            results.append((alt_text, img_path, full_match_text))

        return results

    def _check_single_image(self, alt_text: str, img_path: str, index: int, front_matter: Dict) -> List[Dict]:
        """检查单张图片的Alt文本问题"""
        problems = []

        # 检查Alt文本是否存在
        if not alt_text or alt_text.strip() == '':
            problems.append({
                'type': 'missing_alt',
                'severity': 'critical',
                'image_index': index,
                'image_path': img_path,
                'description': f'第{index}张图片缺失Alt文本'
            })
            return problems

        # 检查Alt文本长度
        alt_min_length = self.alt_config.get('alt_text_min_length', 50)
        alt_max_length = self.alt_config.get('alt_text_max_length', 125)

        if len(alt_text) < alt_min_length:
            problems.append({
                'type': 'short_alt',
                'severity': 'warning',
                'image_index': index,
                'image_path': img_path,
                'current_length': len(alt_text),
                'min_length': alt_min_length,
                'description': f'第{index}张图片Alt文本过短({len(alt_text)}字符，建议{alt_min_length}-{alt_max_length}字符)'
            })

        if len(alt_text) > alt_max_length:
            problems.append({
                'type': 'long_alt',
                'severity': 'warning',
                'image_index': index,
                'image_path': img_path,
                'current_length': len(alt_text),
                'max_length': alt_max_length,
                'description': f'第{index}张图片Alt文本过长({len(alt_text)}字符，建议{alt_min_length}-{alt_max_length}字符)'
            })

        # 检查是否包含关键词
        keywords = front_matter.get('keywords', [])
        title = front_matter.get('title', '')

        if keywords or title:
            # 提取主要关键词
            main_keywords = []
            if isinstance(keywords, list) and keywords:
                main_keywords.extend(keywords[:2])  # 取前2个关键词

            # 从标题提取关键词
            if title:
                title_words = [w.strip() for w in title.lower().split() if len(w) > 2]
                main_keywords.extend(title_words[:2])

            # 检查Alt文本是否包含任何关键词
            alt_lower = alt_text.lower()
            contains_keyword = any(kw.lower() in alt_lower for kw in main_keywords if kw)

            if not contains_keyword:
                problems.append({
                    'type': 'poor_alt',
                    'severity': 'suggestion',
                    'image_index': index,
                    'image_path': img_path,
                    'missing_keywords': main_keywords[:3],
                    'description': f'第{index}张图片Alt文本建议包含相关关键词'
                })

        return problems

    def _generate_alt_suggestion(self, current_alt: str, img_path: str, index: int,
                                front_matter: Dict, file_path: str) -> Dict:
        """生成Alt文本建议"""

        # 收集可用信息
        title = front_matter.get('title', '')
        keywords = front_matter.get('keywords', [])
        categories = front_matter.get('categories', [])

        # 从图片路径提取信息
        img_filename = Path(img_path).stem
        img_info = self._extract_info_from_path(img_path)

        # 生成建议策略
        suggestions = []

        # 策略1: 基于标题+序号
        if title:
            title_based = f"{title}第{index}张配图"
            if len(title_based) <= 125:
                suggestions.append({
                    'strategy': 'title_based',
                    'text': title_based,
                    'confidence': 0.7
                })

        # 策略2: 基于关键词+功能描述
        if keywords:
            main_kw = keywords[0] if isinstance(keywords, list) and keywords else str(keywords)
            function_desc = self._get_function_description(img_path, index)
            kw_based = f"{main_kw}{function_desc}"
            if len(kw_based) <= 125:
                suggestions.append({
                    'strategy': 'keyword_based',
                    'text': kw_based,
                    'confidence': 0.8
                })

        # 策略3: 基于图片文件名
        if img_filename and img_filename not in ['image', 'img', 'photo']:
            # 清理文件名
            clean_filename = re.sub(r'[_\-\d]', ' ', img_filename).strip()
            if clean_filename:
                filename_based = f"{clean_filename}产品图片"
                if len(filename_based) <= 125:
                    suggestions.append({
                        'strategy': 'filename_based',
                        'text': filename_based,
                        'confidence': 0.6
                    })

        # 策略4: 基于分类+通用描述
        if categories:
            category = categories[0] if isinstance(categories, list) else categories
            category_mapping = {
                'smart-plugs': '智能插座',
                'security-cameras': '安防摄像头',
                'robot-vacuums': '扫地机器人',
                'smart-home': '智能家居设备'
            }
            category_cn = category_mapping.get(category, category)
            generic_desc = f"{category_cn}产品展示图{index}"
            suggestions.append({
                'strategy': 'category_based',
                'text': generic_desc,
                'confidence': 0.5
            })

        # 选择最佳建议
        if suggestions:
            best_suggestion = max(suggestions, key=lambda x: x['confidence'])
            suggested_alt = best_suggestion['text']
        else:
            # 兜底方案
            suggested_alt = f"产品图片{index}"

        # 确保长度合适
        if len(suggested_alt) > 125:
            suggested_alt = suggested_alt[:122] + "..."
        elif len(suggested_alt) < 50:
            # 尝试补充描述
            year = "2025"
            if year not in suggested_alt:
                suggested_alt = f"{year}年{suggested_alt}"
            if len(suggested_alt) < 50:
                suggested_alt += "详细介绍"

        return {
            'image_index': index,
            'image_path': img_path,
            'current_alt': current_alt,
            'suggested_alt': suggested_alt,
            'strategy_used': best_suggestion['strategy'] if suggestions else 'fallback',
            'confidence': best_suggestion['confidence'] if suggestions else 0.3,
            'length': len(suggested_alt)
        }

    def _extract_info_from_path(self, img_path: str) -> Dict:
        """从图片路径中提取信息"""
        path_info = {
            'filename': Path(img_path).stem,
            'category': '',
            'type': ''
        }

        # 从路径中提取分类信息
        path_lower = img_path.lower()
        if 'smart-plug' in path_lower:
            path_info['category'] = 'smart-plugs'
        elif 'camera' in path_lower:
            path_info['category'] = 'cameras'
        elif 'vacuum' in path_lower:
            path_info['category'] = 'vacuum'

        # 从文件名判断图片类型
        filename_lower = path_info['filename'].lower()
        if 'hero' in filename_lower or 'banner' in filename_lower:
            path_info['type'] = 'hero'
        elif 'inline' in filename_lower:
            path_info['type'] = 'inline'
        elif 'comparison' in filename_lower or 'compare' in filename_lower:
            path_info['type'] = 'comparison'

        return path_info

    def _get_function_description(self, img_path: str, index: int) -> str:
        """根据图片路径和序号生成功能描述"""
        path_lower = img_path.lower()
        filename_lower = Path(img_path).stem.lower()

        # 根据文件名特征判断功能
        if 'comparison' in filename_lower or 'compare' in filename_lower:
            return "产品对比图"
        elif 'installation' in filename_lower or 'setup' in filename_lower:
            return "安装设置图"
        elif 'feature' in filename_lower:
            return "功能特点图"
        elif 'review' in filename_lower:
            return "评测图片"
        elif index == 1:
            return "产品主图"
        elif index == 2:
            return "功能展示图"
        elif index == 3:
            return "使用场景图"
        else:
            return f"产品图片{index}"

    def _generate_fix_code(self, original_markdown: str, suggested_alt: str) -> Dict:
        """生成修复代码"""
        # 提取原始路径
        path_match = re.search(r'!\[[^\]]*\]\(([^)]+)\)', original_markdown)
        img_path = path_match.group(1) if path_match else ""

        # 生成新的Markdown
        new_markdown = f"![{suggested_alt}]({img_path})"

        return {
            'original': original_markdown,
            'fixed': new_markdown,
            'change_type': 'alt_text_improvement'
        }

    def get_image_optimization_checklist(self) -> List[str]:
        """获取图片优化检查清单"""
        return [
            "✅ 每张图片都有描述性Alt文本（50-125字符）",
            "✅ Alt文本包含相关关键词，但避免关键词堆砌",
            "✅ Featured_image字段已设置",
            "✅ 图片文件名使用描述性命名（包含关键词，用连字符分隔）",
            "✅ 图片格式优先使用WebP，备选JPEG",
            "✅ 图片文件大小控制在500KB以内",
            "✅ 图片尺寸符合标准（Featured: 1200x630px, 内容: 800x600px）",
            "✅ 图片路径遵循标准格式：static/images/{分类}/{slug}/",
            "✅ 每张图片都配备合适的说明文字",
            "✅ 图片位置与对应文本内容匹配"
        ]

    def generate_hugo_render_hook_suggestion(self) -> str:
        """生成Hugo Render Hook建议代码"""
        return '''<!-- layouts/_default/_markup/render-image.html -->
<!-- Hugo图片渲染钩子，为缺失Alt的图片提供兜底 -->
{{- $alt := .Text -}}
{{- if not $alt -}}
  {{- $filename := path.BaseName .Destination -}}
  {{- $alt = printf "%s图片" (humanize $filename) -}}
{{- end -}}

<img src="{{ .Destination | safeURL }}"
     alt="{{ $alt }}"
     loading="lazy"
     {{- if .Title }} title="{{ .Title }}"{{ end -}}>'''