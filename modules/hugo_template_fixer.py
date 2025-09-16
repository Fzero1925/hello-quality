#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugo模板智能修改器
自动修复Hugo模板不合规问题，支持自动修改和人工确认分类
"""

import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

class HugoTemplateFixer:
    """Hugo模板自动修复器"""

    def __init__(self, config_path: str = "hugo_quality_standards.yml"):
        """初始化"""
        self.config = self._load_config(config_path)
        self.hugo_config = self.config.get('hugo_template_compliance', {})
        self.auto_fix_rules = self.hugo_config.get('auto_fix_rules', {})
        self.category_mapping = self.hugo_config.get('standard_categories', {})

        # 修复记录
        self.fix_results = {
            'auto_fixed': [],      # 自动修复的项目
            'needs_manual': [],    # 需要人工确认的项目
            'warnings': []         # 警告信息
        }

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        # 默认配置
        default_config = {
            'hugo_template_compliance': {
                'required_fields': ['title', 'description', 'date', 'categories', 'author'],
                'auto_fix_rules': {
                    'add_missing_author': 'Smart Home Team',
                    'auto_generate_slug': True,
                    'standardize_categories': True,
                    'fix_date_format': True
                },
                'standard_categories': {
                    '智能家居': 'smart-home',
                    '智能插座': 'smart-plugs',
                    '智能灯泡': 'smart-lighting',
                    '智能摄像头': 'smart-cameras',
                    '机器人吸尘器': 'robot-vacuums',
                    '智能门锁': 'smart-locks',
                    '智能恒温器': 'smart-thermostats',
                    '智能音箱': 'smart-speakers'
                }
            }
        }

        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    # 合并配置
                    if 'hugo_template_compliance' in user_config:
                        default_config['hugo_template_compliance'].update(user_config['hugo_template_compliance'])
                    return default_config
        except Exception as e:
            logging.warning(f"Failed to load config {config_path}: {e}")

        return default_config

    def fix_article(self, content: str, file_path: str = "") -> Tuple[str, Dict]:
        """修复文章的Hugo模板问题

        Args:
            content: 文章内容
            file_path: 文件路径（用于生成slug）

        Returns:
            (修复后的内容, 修复结果报告)
        """
        self.fix_results = {'auto_fixed': [], 'needs_manual': [], 'warnings': []}

        # 分离Front Matter和正文
        front_matter_text, article_body, has_front_matter = self._extract_front_matter(content)

        if not has_front_matter:
            # 如果没有Front Matter，创建一个基本的
            front_matter_data = self._create_basic_front_matter(content, file_path)
            self.fix_results['auto_fixed'].append("创建了缺失的Front Matter")
        else:
            try:
                front_matter_data = yaml.safe_load(front_matter_text) or {}
            except yaml.YAMLError as e:
                self.fix_results['warnings'].append(f"Front Matter YAML格式错误: {e}")
                front_matter_data = {}

        # 执行各种修复
        original_fm = front_matter_data.copy()
        front_matter_data = self._fix_required_fields(front_matter_data, content, file_path)
        front_matter_data = self._fix_categories(front_matter_data)
        front_matter_data = self._fix_tags(front_matter_data)
        front_matter_data = self._fix_date_format(front_matter_data)
        front_matter_data = self._fix_slug(front_matter_data, file_path)
        front_matter_data = self._fix_author(front_matter_data)
        front_matter_data = self._validate_and_suggest(front_matter_data, original_fm)

        # 重新组装内容
        fixed_content = self._reassemble_content(front_matter_data, article_body)

        return fixed_content, self.fix_results

    def _extract_front_matter(self, content: str) -> Tuple[str, str, bool]:
        """提取Front Matter和正文"""
        if not content.strip().startswith('---'):
            return "", content, False

        # 查找第二个---
        lines = content.split('\n')
        end_index = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_index = i
                break

        if end_index == -1:
            return "", content, False

        front_matter_text = '\n'.join(lines[1:end_index])
        article_body = '\n'.join(lines[end_index + 1:])

        return front_matter_text, article_body, True

    def _create_basic_front_matter(self, content: str, file_path: str) -> Dict:
        """创建基本的Front Matter"""
        # 尝试从内容中提取标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "未设置标题"

        # 从文件路径生成slug
        file_name = Path(file_path).stem if file_path else "article"
        slug = self._generate_slug(title, file_name)

        return {
            'title': title,
            'slug': slug,
            'date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'author': self.auto_fix_rules.get('add_missing_author', 'Smart Home Team'),
            'draft': False
        }

    def _fix_required_fields(self, fm_data: Dict, content: str, file_path: str) -> Dict:
        """修复必填字段"""
        required_fields = self.hugo_config.get('required_fields', [])

        for field in required_fields:
            if field not in fm_data or not fm_data[field]:
                if field == 'title':
                    # 尝试从内容提取标题
                    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if title_match:
                        fm_data['title'] = title_match.group(1).strip()
                        self.fix_results['auto_fixed'].append(f"从内容中提取标题: {fm_data['title']}")
                    else:
                        fm_data['title'] = "需要设置标题"
                        self.fix_results['needs_manual'].append("标题字段为空，已设置占位符，需要人工填写")

                elif field == 'description':
                    # 从内容提取第一段作为描述
                    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
                    if paragraphs:
                        desc = paragraphs[0][:150] + "..." if len(paragraphs[0]) > 150 else paragraphs[0]
                        # 移除Markdown标记
                        desc = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', desc)  # 链接
                        desc = re.sub(r'[*_`]', '', desc)  # 格式标记
                        fm_data['description'] = desc
                        self.fix_results['needs_manual'].append(f"自动生成描述，建议人工优化: {desc[:50]}...")
                    else:
                        fm_data['description'] = "需要填写SEO描述"
                        self.fix_results['needs_manual'].append("描述字段为空，需要人工填写150-160字符的SEO描述")

                elif field == 'date':
                    fm_data['date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                    self.fix_results['auto_fixed'].append("添加了发布日期")

                elif field == 'categories':
                    fm_data['categories'] = ["smart-home"]  # 默认分类
                    self.fix_results['needs_manual'].append("添加了默认分类，建议根据内容选择正确分类")

                elif field == 'author':
                    default_author = self.auto_fix_rules.get('add_missing_author', 'Smart Home Team')
                    fm_data['author'] = default_author
                    self.fix_results['auto_fixed'].append(f"添加了作者字段: {default_author}")

        return fm_data

    def _fix_categories(self, fm_data: Dict) -> Dict:
        """修复分类字段"""
        if 'categories' not in fm_data:
            return fm_data

        categories = fm_data['categories']
        if not isinstance(categories, list):
            categories = [categories] if categories else []

        # 转换中文分类为英文标准分类
        fixed_categories = []
        for cat in categories:
            if isinstance(cat, str):
                if cat in self.category_mapping:
                    fixed_categories.append(self.category_mapping[cat])
                    self.fix_results['auto_fixed'].append(f"分类标准化: '{cat}' → '{self.category_mapping[cat]}'")
                else:
                    # 检查是否已经是标准分类
                    standard_cats = list(self.category_mapping.values())
                    if cat in standard_cats:
                        fixed_categories.append(cat)
                    else:
                        fixed_categories.append(cat)
                        self.fix_results['needs_manual'].append(f"未识别的分类 '{cat}'，请确认是否正确")

        if fixed_categories:
            fm_data['categories'] = fixed_categories

        return fm_data

    def _fix_tags(self, fm_data: Dict) -> Dict:
        """修复标签字段"""
        if 'tags' not in fm_data or not fm_data['tags']:
            return fm_data

        tags = fm_data['tags']
        if not isinstance(tags, list):
            # 尝试分割字符串
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]

        # 清理和标准化标签
        cleaned_tags = []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                # 移除引号
                clean_tag = tag.strip().strip('"\'')
                if clean_tag not in cleaned_tags:  # 去重
                    cleaned_tags.append(clean_tag)

        if cleaned_tags != fm_data['tags']:
            fm_data['tags'] = cleaned_tags
            self.fix_results['auto_fixed'].append("标签格式化和去重")

        return fm_data

    def _fix_date_format(self, fm_data: Dict) -> Dict:
        """修复日期格式"""
        if 'date' not in fm_data:
            return fm_data

        date_value = fm_data['date']
        if not isinstance(date_value, str):
            return fm_data

        # 检查是否已经是ISO格式
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?'
        if re.match(iso_pattern, date_value):
            return fm_data

        # 尝试解析并转换为ISO格式
        try:
            # 尝试常见格式
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d/%m/%Y',
                '%m/%d/%Y'
            ]

            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    iso_date = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                    fm_data['date'] = iso_date
                    self.fix_results['auto_fixed'].append(f"日期格式标准化: {date_value} → {iso_date}")
                    return fm_data
                except ValueError:
                    continue
        except:
            pass

        # 如果无法解析，使用当前时间
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        fm_data['date'] = current_time
        self.fix_results['needs_manual'].append(f"无法解析日期格式 '{date_value}'，已设置为当前时间，请确认")

        return fm_data

    def _fix_slug(self, fm_data: Dict, file_path: str) -> Dict:
        """修复slug字段"""
        if 'slug' in fm_data and fm_data['slug']:
            # 验证现有slug是否符合规范
            slug = fm_data['slug']
            if self._is_valid_slug(slug):
                return fm_data

        # 生成新的slug
        title = fm_data.get('title', '')
        file_name = Path(file_path).stem if file_path else 'article'
        new_slug = self._generate_slug(title, file_name)

        if 'slug' not in fm_data or fm_data['slug'] != new_slug:
            fm_data['slug'] = new_slug
            self.fix_results['auto_fixed'].append(f"生成标准slug: {new_slug}")

        return fm_data

    def _fix_author(self, fm_data: Dict) -> Dict:
        """修复作者字段（如果在required_fields中已处理则跳过）"""
        # 检查是否已经在required_fields中处理过
        if 'author' in self.hugo_config.get('required_fields', []):
            return fm_data

        # 如果未在required_fields中，则在这里处理
        if 'author' not in fm_data or not fm_data['author']:
            default_author = self.auto_fix_rules.get('add_missing_author', 'Smart Home Team')
            fm_data['author'] = default_author
            self.fix_results['auto_fixed'].append(f"添加默认作者: {default_author}")

        return fm_data

    def _validate_and_suggest(self, fm_data: Dict, original_fm: Dict) -> Dict:
        """验证并给出具体的人工确认建议"""

        # 检查标题优化
        title = fm_data.get('title', '')
        if title and title != "需要设置标题":
            if len(title) > 60:
                self.fix_results['needs_manual'].append({
                    'type': 'title_length',
                    'issue': f"标题长度 {len(title)} 字符，超过建议长度",
                    'suggestion': "建议缩短到50-60字符，保持关键词但提高可读性",
                    'current_value': title,
                    'recommended_action': "重写标题，保留主要关键词"
                })
            elif len(title) < 30:
                self.fix_results['needs_manual'].append({
                    'type': 'title_length',
                    'issue': f"标题长度 {len(title)} 字符，可能过短",
                    'suggestion': "考虑添加年份、修饰词或更具体的描述",
                    'current_value': title,
                    'recommended_action': "扩展标题，增加SEO价值"
                })

        # 检查描述优化
        desc = fm_data.get('description', '')
        if desc and desc != "需要填写SEO描述":
            if len(desc) < 150:
                self.fix_results['needs_manual'].append({
                    'type': 'description_length',
                    'issue': f"描述长度 {len(desc)} 字符，过短",
                    'suggestion': "扩展到150-160字符，添加更多关键词和价值主张",
                    'current_value': desc,
                    'recommended_action': "重写描述，包含主要关键词和用户价值"
                })
            elif len(desc) > 160:
                self.fix_results['needs_manual'].append({
                    'type': 'description_length',
                    'issue': f"描述长度 {len(desc)} 字符，过长",
                    'suggestion': "精简到150-160字符，保留核心信息",
                    'current_value': desc[:100] + "...",
                    'recommended_action': "精简描述，突出最重要的卖点"
                })

        # 检查分类合理性
        categories = fm_data.get('categories', [])
        if categories == ["smart-home"]:
            self.fix_results['needs_manual'].append({
                'type': 'category_generic',
                'issue': "使用了通用分类，缺乏针对性",
                'suggestion': "根据文章内容选择更具体的分类，如smart-plugs、smart-lighting等",
                'current_value': categories,
                'recommended_action': "更换为更具体的产品分类"
            })

        # 检查关键字段完整性
        missing_optional = []
        optional_fields = ['tags', 'keywords', 'featured_image', 'slug']
        for field in optional_fields:
            if field not in fm_data or not fm_data[field]:
                missing_optional.append(field)

        if missing_optional:
            self.fix_results['needs_manual'].append({
                'type': 'missing_optional_fields',
                'issue': f"缺少推荐字段: {', '.join(missing_optional)}",
                'suggestion': "添加这些字段可以提高SEO效果和用户体验",
                'current_value': "缺失",
                'recommended_action': f"添加字段: {', '.join(missing_optional)}"
            })

        # 检查featured_image路径格式
        if 'featured_image' in fm_data and fm_data['featured_image']:
            img_path = fm_data['featured_image']
            if not img_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                self.fix_results['needs_manual'].append({
                    'type': 'image_format',
                    'issue': "featured_image格式可能不是最优",
                    'suggestion': "建议使用.webp格式以获得更好的性能",
                    'current_value': img_path,
                    'recommended_action': "转换图片格式为.webp"
                })

        # 检查slug质量
        slug = fm_data.get('slug', '')
        if slug and not self._is_valid_slug(slug):
            self.fix_results['needs_manual'].append({
                'type': 'slug_quality',
                'issue': "Slug格式需要优化",
                'suggestion': "使用3-6个关键词，用连字符连接，符合SEO最佳实践",
                'current_value': slug,
                'recommended_action': "优化slug格式和关键词选择"
            })

        return fm_data

    def _is_valid_slug(self, slug: str) -> bool:
        """检查slug是否有效"""
        if not slug:
            return False

        # 检查基本格式
        if not re.match(r'^[a-z0-9-]+$', slug):
            return False

        # 检查长度和单词数
        words = slug.split('-')
        if len(words) < 3 or len(words) > 6:
            return False

        if len(slug) > 60:
            return False

        return True

    def _generate_slug(self, title: str, file_name: str) -> str:
        """生成slug"""
        # 优先使用title
        source_text = title if title and title != "需要设置标题" else file_name

        # 转为小写，替换非字母数字字符为连字符
        slug = re.sub(r'[^\w\s-]', '', source_text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')

        # 移除常见停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in slug.split('-') if w not in stop_words]

        # 限制单词数量
        if len(words) > 6:
            words = words[:6]
        elif len(words) < 3:
            # 补充文件名中的词
            file_words = re.sub(r'[^\w\s-]', '', file_name.lower()).split('-')
            words.extend([w for w in file_words if w not in words and w not in stop_words])
            words = words[:6]

        slug = '-'.join(words)

        # 确保长度不超过60字符
        if len(slug) > 60:
            words = words[:-1]  # 移除最后一个词
            slug = '-'.join(words)

        return slug or 'article'

    def _reassemble_content(self, front_matter_data: Dict, article_body: str) -> str:
        """重新组装内容"""
        # 生成YAML格式的Front Matter
        yaml_str = yaml.dump(front_matter_data, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return f"---\n{yaml_str}---\n\n{article_body}"

    def get_fix_summary(self) -> str:
        """获取修复摘要"""
        auto_count = len(self.fix_results['auto_fixed'])
        manual_count = len(self.fix_results['needs_manual'])
        warning_count = len(self.fix_results['warnings'])

        summary = f"修复摘要: 自动修复 {auto_count} 项，需人工确认 {manual_count} 项"
        if warning_count > 0:
            summary += f"，警告 {warning_count} 项"

        return summary