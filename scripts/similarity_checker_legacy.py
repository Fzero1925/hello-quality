#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立相似度检测工具
专门用于检测文章相似度，处理重复内容，生成详细分析报告

功能特点：
- 批量检测文件夹中所有文章的相似度
- 自动处理重复文章（保留最新，移动其他到duplicate_articles文件夹）
- 生成详细的相似度分析报告
- 支持配置相似度阈值和检测参数
"""

import os
import sys
import argparse
import yaml
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import re
import hashlib
import codecs

# 解决Windows编码问题
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SimilarityChecker:
    """独立相似度检测器"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化相似度检测器

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.similarity_threshold = self.config.get('tfidf_threshold', 0.5)
        self.comparison_window_days = self.config.get('comparison_window_days', 7)
        self.new_articles_folder = self.config.get('new_articles_folder', 'new-articles')
        self.old_articles_folder = self.config.get('old_articles_folder', 'old-articles')
        self.keep_oldest = self.config.get('keep_oldest_article', True)

        # 检测结果存储
        self.all_articles = []

        # 主题分类配置 (从配置文件读取)
        self.topic_classification = self.config.get('topic_classification', {})
        self.cross_topic_threshold = self.topic_classification.get('cross_topic_similarity_threshold', 0.85)

        # 调试模式
        self.debug_mode = False

        print(f"✅ 相似度检测器初始化完成")
        print(f"📊 检测阈值: {self.similarity_threshold}")
        print(f"⏰ 检测窗口: {self.comparison_window_days} 天")

    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """加载配置文件"""
        default_config = {
            'similarity_threshold': 0.7,
            'comparison_window_days': 90,
            'duplicate_folder': 'oldarticles',
            'min_content_length': 1000,
            'check_title_similarity': True,
            'check_content_similarity': True,
            'title_weight': 0.3,
            'content_weight': 0.7,
            'preserve_newest': True,
            'backup_before_move': True,
            'topic_classification': {'enabled': False}
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    similarity_config = user_config.get('similarity_detection', {})

                    # 更新基础配置
                    if 'tfidf_threshold' in similarity_config:
                        default_config['similarity_threshold'] = similarity_config['tfidf_threshold']
                    if 'old_articles_folder' in similarity_config:
                        default_config['duplicate_folder'] = similarity_config['old_articles_folder']

                    # 更新所有配置
                    default_config.update(similarity_config)

                    print(f"✅ 从配置文件加载设置: {config_path}")
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}，使用默认配置")

        return default_config

    def scan_articles(self, directory: str) -> List[Dict]:
        """扫描目录中的所有文章

        Args:
            directory: 要扫描的目录路径

        Returns:
            文章信息列表
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            print(f"❌ 目录不存在: {directory}")
            return []

        # 查找所有Markdown文件
        md_files = list(directory_path.glob("*.md"))
        if not md_files:
            print(f"❌ 目录中没有找到Markdown文件: {directory}")
            return []

        print(f"📁 找到 {len(md_files)} 个文章文件")

        articles = []
        for i, file_path in enumerate(md_files, 1):
            print(f"  [{i}/{len(md_files)}] 正在分析: {file_path.name}")

            try:
                article_info = self._extract_article_info(file_path)
                if article_info:
                    articles.append(article_info)
            except Exception as e:
                print(f"    ⚠️ 文件处理失败: {e}")

        self.all_articles = articles
        print(f"✅ 成功分析 {len(articles)} 篇文章")
        return articles

    def _extract_article_info(self, file_path: Path) -> Optional[Dict]:
        """提取文章信息

        Args:
            file_path: 文章文件路径

        Returns:
            文章信息字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取Front Matter和正文
            front_matter, article_content = self._extract_front_matter(content)

            # 获取文件统计信息
            file_stat = file_path.stat()

            # 提取基本信息
            title = self._extract_title(front_matter, article_content, file_path.stem)

            article_info = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_stem': file_path.stem,
                'title': title,
                'content': article_content,
                'full_content': content,
                'word_count': len(article_content.split()),
                'char_count': len(article_content),
                'created_time': datetime.fromtimestamp(file_stat.st_ctime),
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
                'file_size': file_stat.st_size,
                'content_hash': hashlib.md5(article_content.encode('utf-8')).hexdigest(),
                'title_hash': hashlib.md5(title.encode('utf-8')).hexdigest() if title else "",
                'front_matter': front_matter
            }

            return article_info

        except Exception as e:
            print(f"    ❌ 无法读取文件 {file_path}: {e}")
            return None

    def _extract_front_matter(self, content: str) -> Tuple[str, str]:
        """提取Front Matter和正文"""
        if not content.strip().startswith('---'):
            return "", content

        lines = content.split('\n')
        end_index = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                end_index = i
                break

        if end_index == -1:
            return "", content

        front_matter_text = '\n'.join(lines[1:end_index])
        article_body = '\n'.join(lines[end_index + 1:])

        return front_matter_text, article_body

    def _extract_title(self, front_matter: str, content: str, fallback: str) -> str:
        """提取文章标题"""
        # 尝试从Front Matter提取
        try:
            fm_data = yaml.safe_load(front_matter) or {}
            if 'title' in fm_data and fm_data['title']:
                return str(fm_data['title']).strip()
        except:
            pass

        # 尝试从内容中提取H1标题
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # 使用文件名作为后备
        return fallback.replace('-', ' ').replace('_', ' ').title()

    def detect_similarities(self, articles: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """线性相似度检测算法

        逻辑：按时间排序，最早文章vs其他文章比较
        相似的移动到old-articles，不相似的保留

        Args:
            articles: 文章列表，如果为None则使用self.all_articles

        Returns:
            处理结果字典
        """
        if articles is None:
            articles = self.all_articles

        if len(articles) < 2:
            print("📊 文章数量不足，无法进行相似度比较")
            return {'kept_articles': articles, 'moved_articles': [], 'total_comparisons': 0}

        print(f"🔍 开始线性相似度检测 {len(articles)} 篇文章...")

        # 1. 按有效日期排序（最早到最新）
        articles_sorted = sorted(articles, key=lambda x: self._get_article_effective_date(x))

        # 为文章添加有效日期
        for article in articles_sorted:
            article['effective_date'] = self._get_article_effective_date(article)

        print(f"📅 文章按日期排序完成，时间范围: {articles_sorted[0]['effective_date'].strftime('%Y-%m-%d')} 到 {articles_sorted[-1]['effective_date'].strftime('%Y-%m-%d')}")

        # 2. 线性比较处理
        kept_articles = []
        moved_articles = []
        total_comparisons = 0
        processing_date = datetime.now().strftime('%Y-%m-%d')

        remaining_articles = articles_sorted[:]  # 创建副本

        while remaining_articles:
            # 取最早的文章作为基准
            base_article = remaining_articles.pop(0)
            kept_articles.append(base_article)

            print(f"\n📝 处理基准文章: {base_article['file_name']} (日期: {base_article['effective_date'].strftime('%Y-%m-%d')})")

            # 与剩余文章比较
            to_remove = []
            for i, other_article in enumerate(remaining_articles):
                # 检查时间窗口
                time_diff = abs((base_article['effective_date'] - other_article['effective_date']).days)
                if time_diff > self.comparison_window_days:
                    if self.debug_mode:
                        print(f"    🕐 跳过 {other_article['file_name']} - 时间差 {time_diff} 天 > {self.comparison_window_days} 天窗口")
                    continue

                # 跳过内容太短的文章
                if (base_article['word_count'] < self.config.get('min_content_length', 1000) or
                    other_article['word_count'] < self.config.get('min_content_length', 1000)):
                    if self.debug_mode:
                        print(f"    📝 跳过 {other_article['file_name']} - 字数不足 (base: {base_article['word_count']}, other: {other_article['word_count']})")
                    continue

                total_comparisons += 1

                # 计算相似度
                similarity_score = self._calculate_article_similarity(base_article, other_article)

                # 检查是否为跨主题比较
                is_cross_topic = self._are_cross_topic_articles(base_article, other_article)
                effective_threshold = self.cross_topic_threshold if is_cross_topic else self.similarity_threshold

                if self.debug_mode:
                    title_sim = self._calculate_title_similarity(base_article['title'], other_article['title'])
                    content_sim = self._calculate_content_similarity(base_article['content'], other_article['content'])
                    topic1 = self._classify_article_topic(base_article)
                    topic2 = self._classify_article_topic(other_article)

                    print(f"    🔍 比较 {other_article['file_name']}:")
                    print(f"      标题相似度: {title_sim:.3f}")
                    print(f"      内容相似度: {content_sim:.3f}")
                    print(f"      综合相似度: {similarity_score:.3f}")
                    print(f"      主题分类: {topic1} vs {topic2}")
                    print(f"      跨主题: {is_cross_topic}, 阈值: {effective_threshold:.3f}")

                if similarity_score >= effective_threshold:
                    print(f"  📦 相似文章 (相似度: {similarity_score:.3f}): {other_article['file_name']}")

                    # 记录移动信息
                    moved_info = {
                        **other_article,
                        'similarity_to_base': similarity_score,
                        'base_article': base_article['file_name'],
                        'is_cross_topic': is_cross_topic,
                        'effective_threshold': effective_threshold
                    }
                    moved_articles.append(moved_info)
                    to_remove.append(i)
                elif self.debug_mode:
                    print(f"    ❌ 不相似 {similarity_score:.3f} < {effective_threshold:.3f}")

            # 移除已标记的文章
            for index in reversed(to_remove):
                remaining_articles.pop(index)

        result = {
            'kept_articles': kept_articles,
            'moved_articles': moved_articles,
            'total_comparisons': total_comparisons,
            'processing_date': processing_date
        }

        print(f"\n✅ 线性检测完成:")
        print(f"  📊 总比较次数: {total_comparisons}")
        print(f"  ✅ 保留文章: {len(kept_articles)} 篇")
        print(f"  📦 移动文章: {len(moved_articles)} 篇")

        return result

    def detect_duplicate_groups(self, articles: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """全连接图相似度检测算法 - 检测所有重复文章群组

        使用全连接图和连通分量算法，确保数学上的完整性，不遗漏任何相似关系
        只分析不移动文件，生成详细的重复文章分析报告

        Args:
            articles: 文章列表，如果为None则使用self.all_articles

        Returns:
            包含重复群组分析的详细结果字典
        """
        if articles is None:
            articles = self.all_articles

        if len(articles) < 2:
            print("📊 文章数量不足，无法进行相似度比较")
            return {'duplicate_groups': [], 'unique_articles': articles, 'similarity_matrix': [], 'total_comparisons': 0}

        print(f"🔍 开始全连接图相似度检测 {len(articles)} 篇文章...")
        print("📊 算法说明: 计算所有文章对相似度，使用连通分量算法识别重复群组")

        # 过滤掉字数不足的文章
        valid_articles = []
        min_length = self.config.get('min_content_length', 1000)

        for article in articles:
            if article['word_count'] >= min_length:
                valid_articles.append(article)
            elif self.debug_mode:
                print(f"📝 跳过字数不足的文章: {article['file_name']} ({article['word_count']} < {min_length})")

        if len(valid_articles) < 2:
            print("📊 有效文章数量不足，无法进行相似度比较")
            return {'duplicate_groups': [], 'unique_articles': articles, 'similarity_matrix': [], 'total_comparisons': 0}

        print(f"✅ 有效文章: {len(valid_articles)} 篇")

        # 第一阶段：构建相似度矩阵
        print("\n🔧 第一阶段: 构建相似度矩阵...")
        similarity_matrix, total_comparisons = self._build_similarity_matrix(valid_articles)

        if self.debug_mode:
            print("\n📈 相似度矩阵 (仅显示 >= 0.3 的相似度):")
            self._print_similarity_matrix(valid_articles, similarity_matrix, threshold=0.3)

        # 第二阶段：构建相似度图
        print("\n🔧 第二阶段: 构建相似度图...")
        similarity_graph = self._build_similarity_graph(valid_articles, similarity_matrix)

        # 第三阶段：找连通分量
        print("\n🔧 第三阶段: 查找重复文章群组...")
        duplicate_groups = self._find_duplicate_groups(valid_articles, similarity_graph, similarity_matrix)

        # 第四阶段：生成分析报告
        print("\n🔧 第四阶段: 生成分析报告...")
        unique_articles = self._identify_unique_articles(valid_articles, duplicate_groups)

        result = {
            'duplicate_groups': duplicate_groups,
            'unique_articles': unique_articles,
            'similarity_matrix': similarity_matrix,
            'total_comparisons': total_comparisons,
            'algorithm': 'graph_clustering'
        }

        # 输出统计信息
        print(f"\n✅ 全连接图检测完成:")
        print(f"  📊 总比较次数: {total_comparisons}")
        print(f"  📦 发现重复群组: {len(duplicate_groups)} 个")
        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        print(f"  🔸 重复文章总数: {total_duplicates} 篇")
        print(f"  ✅ 独立文章: {len(unique_articles)} 篇")

        return result

    def _build_similarity_matrix(self, articles: List[Dict]) -> Tuple[List[List[float]], int]:
        """构建完整的相似度矩阵

        Args:
            articles: 有效文章列表

        Returns:
            (相似度矩阵, 比较次数)
        """
        n = len(articles)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        total_comparisons = 0

        print(f"  🔄 计算 {n}×{n} 相似度矩阵...")

        for i in range(n):
            # 对角线为1.0 (自己与自己完全相似)
            matrix[i][i] = 1.0

            for j in range(i + 1, n):
                # 检查时间窗口限制
                date_i = self._get_article_effective_date(articles[i])
                date_j = self._get_article_effective_date(articles[j])
                time_diff = abs((date_i - date_j).days)

                if time_diff > self.comparison_window_days:
                    matrix[i][j] = matrix[j][i] = 0.0
                    if self.debug_mode:
                        print(f"    🕐 跳过时间窗口外: {articles[i]['file_name']} vs {articles[j]['file_name']} (时间差{time_diff}天)")
                    continue

                # 计算相似度
                similarity = self._calculate_article_similarity(articles[i], articles[j])
                matrix[i][j] = matrix[j][i] = similarity
                total_comparisons += 1

                if self.debug_mode and similarity >= 0.5:
                    print(f"    🔍 高相似度: {articles[i]['file_name']} vs {articles[j]['file_name']} = {similarity:.3f}")

        print(f"  ✅ 矩阵构建完成，共计算 {total_comparisons} 对文章")
        return matrix, total_comparisons

    def _build_similarity_graph(self, articles: List[Dict], similarity_matrix: List[List[float]]) -> Dict[int, List[int]]:
        """基于相似度矩阵构建图

        Args:
            articles: 文章列表
            similarity_matrix: 相似度矩阵

        Returns:
            邻接表表示的图
        """
        n = len(articles)
        graph = {i: [] for i in range(n)}
        edge_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                # 检查是否跨主题
                is_cross_topic = self._are_cross_topic_articles(articles[i], articles[j])
                effective_threshold = self.cross_topic_threshold if is_cross_topic else self.similarity_threshold

                if similarity_matrix[i][j] >= effective_threshold:
                    graph[i].append(j)
                    graph[j].append(i)
                    edge_count += 1

                    if self.debug_mode:
                        print(f"    🔗 连接: {articles[i]['file_name']} ↔ {articles[j]['file_name']} (相似度: {similarity_matrix[i][j]:.3f}, 阈值: {effective_threshold:.3f})")

        print(f"  ✅ 相似度图构建完成，包含 {edge_count} 条边")
        return graph

    def _find_duplicate_groups(self, articles: List[Dict], graph: Dict[int, List[int]], similarity_matrix: List[List[float]]) -> List[Dict]:
        """使用DFS查找连通分量，识别重复文章群组

        Args:
            articles: 文章列表
            graph: 相似度图
            similarity_matrix: 相似度矩阵

        Returns:
            重复群组列表
        """
        n = len(articles)
        visited = [False] * n
        duplicate_groups = []

        def dfs(node: int, component: List[int]):
            """深度优先搜索收集连通分量"""
            visited[node] = True
            component.append(node)

            for neighbor in graph[node]:
                if not visited[neighbor]:
                    dfs(neighbor, component)

        # 找所有连通分量
        for i in range(n):
            if not visited[i]:
                component = []
                dfs(i, component)

                # 只关心包含2篇以上文章的群组(重复群组)
                if len(component) > 1:
                    # 按日期排序，最早的作为基准文章
                    component_articles = [articles[idx] for idx in component]
                    component_sorted = sorted(component, key=lambda idx: self._get_article_effective_date(articles[idx]))
                    base_article_idx = component_sorted[0]

                    # 构建群组信息
                    group_info = {
                        'base_article': articles[base_article_idx],
                        'articles': [],
                        'group_id': len(duplicate_groups) + 1,
                        'topic': self._classify_article_topic(articles[base_article_idx]) or 'Unknown'
                    }

                    for idx in component_sorted:
                        article_info = {
                            **articles[idx],
                            'similarity_to_base': similarity_matrix[base_article_idx][idx] if idx != base_article_idx else 1.0,
                            'is_base': idx == base_article_idx
                        }
                        group_info['articles'].append(article_info)

                    duplicate_groups.append(group_info)

                    if self.debug_mode:
                        print(f"    📦 发现群组 {len(duplicate_groups)}: {len(component)} 篇文章")
                        for idx in component_sorted:
                            marker = "🔹" if idx == base_article_idx else "🔸"
                            sim = similarity_matrix[base_article_idx][idx] if idx != base_article_idx else 1.0
                            print(f"      {marker} {articles[idx]['file_name']} (相似度: {sim:.3f})")

        print(f"  ✅ 连通分量分析完成，发现 {len(duplicate_groups)} 个重复群组")
        return duplicate_groups

    def _identify_unique_articles(self, articles: List[Dict], duplicate_groups: List[Dict]) -> List[Dict]:
        """识别不属于任何重复群组的独立文章

        Args:
            articles: 所有文章列表
            duplicate_groups: 重复群组列表

        Returns:
            独立文章列表
        """
        # 收集所有属于重复群组的文章
        grouped_filenames = set()
        for group in duplicate_groups:
            for article in group['articles']:
                grouped_filenames.add(article['file_name'])

        # 找出不属于任何群组的文章
        unique_articles = [article for article in articles if article['file_name'] not in grouped_filenames]

        print(f"  ✅ 识别出 {len(unique_articles)} 篇独立文章")
        return unique_articles

    def _print_similarity_matrix(self, articles: List[Dict], matrix: List[List[float]], threshold: float = 0.5):
        """打印相似度矩阵的可视化版本

        Args:
            articles: 文章列表
            matrix: 相似度矩阵
            threshold: 显示阈值，低于此值的不显示
        """
        n = len(articles)
        if n > 10:
            print(f"    矩阵过大({n}×{n})，仅显示前10×10部分")
            display_n = 10
        else:
            display_n = n

        # 打印表头
        print("    " + "".join(f"{i:>8}" for i in range(display_n)))

        # 打印矩阵内容
        for i in range(display_n):
            row_values = []
            for j in range(display_n):
                value = matrix[i][j]
                if value >= threshold:
                    row_values.append(f"{value:.3f}")
                else:
                    row_values.append("  -  ")
            print(f"{i:>2}: " + "".join(f"{val:>8}" for val in row_values))

    def compare_two_articles(self, file1: str, file2: str) -> Dict[str, Any]:
        """对比两篇指定文章的相似度

        Args:
            file1: 第一篇文章文件路径
            file2: 第二篇文章文件路径

        Returns:
            详细的对比结果
        """
        print(f"🔍 对比两篇文章:")
        print(f"  文章A: {file1}")
        print(f"  文章B: {file2}")

        # 检查文件是否存在
        if not Path(file1).exists():
            print(f"❌ 文件不存在: {file1}")
            return None

        if not Path(file2).exists():
            print(f"❌ 文件不存在: {file2}")
            return None

        # 提取文章信息
        article1 = self._extract_article_info(Path(file1))
        article2 = self._extract_article_info(Path(file2))

        if not article1 or not article2:
            print(f"❌ 无法解析文章内容")
            return None

        # 计算各种相似度
        title_similarity = self._calculate_title_similarity(article1['title'], article2['title'])
        content_similarity = self._calculate_content_similarity(article1['content'], article2['content'])
        overall_similarity = self._calculate_article_similarity(article1, article2)

        # 判断是否跨主题
        is_cross_topic = self._are_cross_topic_articles(article1, article2)
        effective_threshold = self.cross_topic_threshold if is_cross_topic else self.similarity_threshold

        # 构建结果
        result = {
            'article1': {
                'file_path': file1,
                'title': article1['title'],
                'word_count': article1['word_count'],
                'effective_date': self._get_article_effective_date(article1)
            },
            'article2': {
                'file_path': file2,
                'title': article2['title'],
                'word_count': article2['word_count'],
                'effective_date': self._get_article_effective_date(article2)
            },
            'similarity_scores': {
                'title_similarity': title_similarity,
                'content_similarity': content_similarity,
                'overall_similarity': overall_similarity
            },
            'analysis': {
                'is_cross_topic': is_cross_topic,
                'effective_threshold': effective_threshold,
                'is_similar': overall_similarity >= effective_threshold,
                'topic1': self._classify_article_topic(article1),
                'topic2': self._classify_article_topic(article2)
            },
            'details': {
                'word_count_diff': abs(article1['word_count'] - article2['word_count']),
                'char_count_diff': abs(article1['char_count'] - article2['char_count']),
            }
        }

        # 输出结果
        print(f"\n📊 相似度分析结果:")
        print(f"  标题相似度: {title_similarity:.3f}")
        print(f"  内容相似度: {content_similarity:.3f}")
        print(f"  综合相似度: {overall_similarity:.3f}")
        print(f"  有效阈值: {effective_threshold:.3f} ({'跨主题' if is_cross_topic else '同主题'})")
        print(f"  判断结果: {'相似' if result['analysis']['is_similar'] else '不相似'}")

        if result['analysis']['is_similar']:
            print(f"  ✅ 相似度 {overall_similarity:.3f} ≥ 阈值 {effective_threshold:.3f}")
        else:
            print(f"  ❌ 相似度 {overall_similarity:.3f} < 阈值 {effective_threshold:.3f}")

        return result

    def _calculate_article_similarity(self, article1: Dict, article2: Dict) -> float:
        """计算两篇文章的整体相似度"""
        # 检查是否完全相同
        if article1['content_hash'] == article2['content_hash']:
            return 1.0

        # 计算标题相似度
        title_sim = 0.0
        if self.config.get('check_title_similarity', True):
            title_sim = self._calculate_title_similarity(article1['title'], article2['title'])

        # 计算内容相似度
        content_sim = 0.0
        if self.config.get('check_content_similarity', True):
            content_sim = self._calculate_content_similarity(article1['content'], article2['content'])

        # 加权计算总相似度
        title_weight = self.config.get('title_weight', 0.3)
        content_weight = self.config.get('content_weight', 0.7)

        total_similarity = title_sim * title_weight + content_sim * content_weight
        return min(1.0, total_similarity)

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0

        # 标准化标题
        title1_clean = self._normalize_text(title1)
        title2_clean = self._normalize_text(title2)

        if title1_clean == title2_clean:
            return 1.0

        # 计算词汇重叠度
        words1 = set(title1_clean.split())
        words2 = set(title2_clean.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度（使用TF-IDF和余弦相似度）"""
        if not content1 or not content2:
            return 0.0

        # 标准化内容
        content1_clean = self._normalize_text(content1)
        content2_clean = self._normalize_text(content2)

        if content1_clean == content2_clean:
            return 1.0

        # 简单的词频统计方法
        words1 = content1_clean.split()
        words2 = content2_clean.split()

        # 构建词汇表
        vocab = set(words1 + words2)

        if not vocab:
            return 0.0

        # 计算词频向量
        vec1 = [words1.count(word) for word in vocab]
        vec2 = [words2.count(word) for word in vocab]

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _normalize_text(self, text: str) -> str:
        """标准化文本"""
        # 转为小写
        text = text.lower()

        # 移除Markdown标记
        text = re.sub(r'[#*`\[\]()]', '', text)
        text = re.sub(r'http[s]?://\S+', '', text)

        # 移除标点符号
        text = re.sub(r'[^\w\s-]', ' ', text)

        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """从文件名中提取日期

        支持格式：xxx-20250914.md, xxx-2025-09-14.md 等
        """
        import re

        # 匹配YYYYMMDD格式
        date_pattern1 = re.search(r'(\d{8})', filename)
        if date_pattern1:
            try:
                date_str = date_pattern1.group(1)
                return datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass

        # 匹配YYYY-MM-DD格式
        date_pattern2 = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_pattern2:
            try:
                date_str = date_pattern2.group(1)
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass

        return None

    def _get_article_effective_date(self, article: Dict) -> datetime:
        """获取文章的有效日期（用于排序）

        优先级：文件名日期 > 创建时间 > 修改时间
        """
        # 1. 尝试从文件名提取日期
        filename_date = self._extract_date_from_filename(article['file_name'])
        if filename_date:
            return filename_date

        # 2. 使用创建时间
        if 'created_time' in article:
            return article['created_time']

        # 3. 使用修改时间作为后备
        return article['modified_time']

    def _classify_article_topic(self, article: Dict) -> Optional[str]:
        """对文章进行主题分类

        Args:
            article: 文章信息

        Returns:
            主题类别名称，如果无法分类则返回None
        """
        if not self.topic_classification.get('enabled', False):
            return None

        topics = self.topic_classification.get('topics', {})
        if not topics:
            return None

        # 合并标题和内容进行分类
        text_to_classify = (article['title'] + ' ' + article['content']).lower()

        # 计算每个主题的匹配分数
        topic_scores = {}
        for topic_name, topic_config in topics.items():
            keywords = topic_config.get('keywords', [])
            if not keywords:
                continue

            score = 0
            for keyword in keywords:
                if keyword.lower() in text_to_classify:
                    score += 1

            if score > 0:
                # 标准化分数 (匹配关键词数 / 总关键词数)
                topic_scores[topic_name] = score / len(keywords)

        if not topic_scores:
            return None

        # 返回得分最高的主题
        best_topic = max(topic_scores.items(), key=lambda x: x[1])
        return best_topic[0] if best_topic[1] > 0.1 else None  # 至少10%关键词匹配

    def _are_cross_topic_articles(self, article1: Dict, article2: Dict) -> bool:
        """判断两篇文章是否属于不同主题

        Args:
            article1, article2: 文章信息

        Returns:
            True如果属于不同主题
        """
        if not self.topic_classification.get('enabled', False):
            return False

        topic1 = self._classify_article_topic(article1)
        topic2 = self._classify_article_topic(article2)

        # 如果任一文章无法分类，不认为是跨主题
        if topic1 is None or topic2 is None:
            return False

        return topic1 != topic2

    def process_articles_by_date(self, processing_result: Dict[str, Any],
                                move_files: bool = True) -> Dict[str, Any]:
        """按日期处理文章文件

        Args:
            processing_result: 检测结果
            move_files: 是否实际移动文件

        Returns:
            处理结果报告
        """
        kept_articles = processing_result['kept_articles']
        moved_articles = processing_result['moved_articles']
        processing_date = processing_result['processing_date']

        if not moved_articles:
            print("📊 没有需要移动的文章")
            return {
                'moved_count': 0,
                'kept_count': len(kept_articles),
                'new_articles_folder': f"{self.new_articles_folder}/{processing_date}",
                'old_articles_folder': f"{self.old_articles_folder}/{processing_date}"
            }

        # 创建按日期分类的文件夹
        new_articles_dir = Path(f"{self.new_articles_folder}/{processing_date}")
        old_articles_dir = Path(f"{self.old_articles_folder}/{processing_date}")

        if move_files:
            new_articles_dir.mkdir(parents=True, exist_ok=True)
            old_articles_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建文件夹:")
            print(f"  ✅ 保留文章: {new_articles_dir.absolute()}")
            print(f"  📦 相似文章: {old_articles_dir.absolute()}")

        moved_count = 0
        kept_count = 0

        # 1. 移动保留的文章到new-articles
        print(f"\n📝 处理保留文章 ({len(kept_articles)} 篇):")
        for article in kept_articles:
            if move_files:
                try:
                    source_path = Path(article['file_path'])
                    target_path = new_articles_dir / source_path.name

                    # 如果目标文件已存在，添加时间戳
                    if target_path.exists():
                        timestamp = datetime.now().strftime('%H%M%S')
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_name = f"{stem}_{timestamp}{suffix}"
                        target_path = new_articles_dir / target_name

                    shutil.move(str(source_path), str(target_path))
                    print(f"  ✅ 移动: {article['file_name']} → new-articles/{processing_date}/")
                    kept_count += 1

                except Exception as e:
                    print(f"  ❌ 移动失败 {article['file_name']}: {e}")
            else:
                print(f"  ✅ 待移动: {article['file_name']} → new-articles/{processing_date}/")
                kept_count += 1

        # 2. 移动相似的文章到old-articles
        print(f"\n📦 处理相似文章 ({len(moved_articles)} 篇):")
        for article in moved_articles:
            if move_files:
                try:
                    source_path = Path(article['file_path'])
                    target_path = old_articles_dir / source_path.name

                    # 如果目标文件已存在，添加时间戳
                    if target_path.exists():
                        timestamp = datetime.now().strftime('%H%M%S')
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_name = f"{stem}_{timestamp}{suffix}"
                        target_path = old_articles_dir / target_name

                    shutil.move(str(source_path), str(target_path))
                    similarity = article.get('similarity_to_base', 0)
                    base_article = article.get('base_article', 'unknown')
                    print(f"  📦 移动: {article['file_name']} → old-articles/{processing_date}/ (相似度: {similarity:.3f}, 基准: {base_article})")
                    moved_count += 1

                except Exception as e:
                    print(f"  ❌ 移动失败 {article['file_name']}: {e}")
            else:
                similarity = article.get('similarity_to_base', 0)
                base_article = article.get('base_article', 'unknown')
                print(f"  📦 待移动: {article['file_name']} → old-articles/{processing_date}/ (相似度: {similarity:.3f}, 基准: {base_article})")
                moved_count += 1

        result = {
            'moved_count': moved_count,
            'kept_count': kept_count,
            'new_articles_folder': str(new_articles_dir.absolute()) if move_files else f"{self.new_articles_folder}/{processing_date}",
            'old_articles_folder': str(old_articles_dir.absolute()) if move_files else f"{self.old_articles_folder}/{processing_date}",
            'processing_date': processing_date
        }

        print(f"\n✅ 文章分类处理完成:")
        print(f"  ✅ 保留文章: {kept_count} 篇")
        print(f"  📦 移动文章: {moved_count} 篇")

        return result


    def generate_duplicate_analysis_report(self, detection_result: Dict[str, Any], output_file: str = "duplicate_analysis_report.md") -> str:
        """为全连接图算法结果生成详细分析报告

        Args:
            detection_result: 全连接图检测结果
            output_file: 输出文件路径

        Returns:
            报告文件路径
        """
        print(f"📄 正在生成重复文章分析报告...")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])
        total_comparisons = detection_result.get('total_comparisons', 0)
        algorithm = detection_result.get('algorithm', 'graph_clustering')

        # 统计信息
        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        total_articles = total_duplicates + len(unique_articles)

        report_parts = []

        # 报告头部
        report_parts.append(f"""# 📊 重复文章群组分析报告

**生成时间**: {timestamp}
**检测算法**: {algorithm} (全连接图聚类)
**检测阈值**: {self.similarity_threshold}
**总文章数**: {total_articles}
**比较次数**: {total_comparisons}
**重复群组**: {len(duplicate_groups)} 个
**重复文章**: {total_duplicates} 篇
**独立文章**: {len(unique_articles)} 篇
**重复率**: {(total_duplicates/total_articles*100):.1f}%

---""")

        # 执行摘要
        if duplicate_groups:
            report_parts.append(f"""
## 🎯 执行摘要

本次检测使用全连接图聚类算法，确保数学完整性，无遗漏任何相似关系。

### 关键发现
- 📦 发现 **{len(duplicate_groups)}** 个重复文章群组
- 🔸 涉及 **{total_duplicates}** 篇重复文章
- ✅ **{len(unique_articles)}** 篇文章完全独立
- 📈 平均每群组 **{(total_duplicates/len(duplicate_groups)):.1f}** 篇文章

### 算法优势
- ✅ **数学完整性**: 所有文章对都进行了比较分析
- ✅ **传递性处理**: A→B→C关系被正确识别为一个群组
- ✅ **零遗漏**: 连通分量算法确保不遗漏任何相似关系
- ✅ **SEO友好**: 每个群组保留最早发布的文章（SEO价值最高）
""")

        # 重复群组详情
        if duplicate_groups:
            report_parts.append("\n## 📦 重复文章群组详情\n")

            for i, group in enumerate(duplicate_groups, 1):
                base_article = group['base_article']
                articles = group['articles']
                topic = group.get('topic', 'Unknown')

                # 群组标题
                base_date = self._get_article_effective_date(base_article).strftime('%Y-%m-%d')
                report_parts.append(f"""### 群组 {i}: {topic} 主题 ({len(articles)}篇文章)

**基准文章**: `{base_article['file_name']}` (发布日期: {base_date})
**群组主题**: {topic}
**相似度范围**: {min(a['similarity_to_base'] for a in articles if not a['is_base']):.3f} - {max(a['similarity_to_base'] for a in articles if not a['is_base']):.3f}

#### 文章列表:""")

                # 文章详情
                for article in articles:
                    if article['is_base']:
                        marker = "🔹 **基准**"
                        sim_text = "1.000"
                    else:
                        marker = "🔸"
                        sim_text = f"{article['similarity_to_base']:.3f}"

                    article_date = self._get_article_effective_date(article).strftime('%Y-%m-%d')
                    report_parts.append(f"- {marker} `{article['file_name']}` (相似度: {sim_text}, 日期: {article_date})")

                report_parts.append("")  # 空行分隔

        # SEO优化建议部分
        if duplicate_groups:
            report_parts.append(f"""
## 🔧 SEO优化处理建议

基于article_similarity_guide.md的最佳实践，为发现的{len(duplicate_groups)}个重复群组提供具体的SEO优化方案：

### 📋 处理策略总览

1. **301重定向 (推荐)**: 合并内容相似度>0.8的文章，设置永久重定向保护SEO权重
2. **Canonical标签**: 保留相似度0.5-0.8之间的文章，使用canonical标签指向主要版本
3. **内容差异化**: 相似度<0.7的文章可通过内容补充实现差异化

---""")

            # 为每个群组生成具体的SEO建议
            for i, group in enumerate(duplicate_groups, 1):
                base_article = group['base_article']
                articles = group['articles']
                topic = group.get('topic', 'Unknown')

                # 计算群组内最高相似度
                non_base_articles = [a for a in articles if not a['is_base']]
                if non_base_articles:
                    max_similarity = max(a['similarity_to_base'] for a in non_base_articles)
                    avg_similarity = sum(a['similarity_to_base'] for a in non_base_articles) / len(non_base_articles)
                else:
                    max_similarity = avg_similarity = 0.0

                report_parts.append(f"""
### 群组 {i} 处理建议: {topic}

**基准文章**: `{base_article['file_name']}`
**群组相似度**: 平均 {avg_similarity:.3f}, 最高 {max_similarity:.3f}

#### 🎯 推荐策略:""")

                if max_similarity >= 0.8:
                    # 高相似度：建议301重定向
                    report_parts.append(f"""
**301重定向方案** (相似度 ≥ 0.8)
- ✅ **保留**: `{base_article['file_name']}` (基准文章)
- 🔄 **重定向到基准文章**:""")
                    for article in non_base_articles:
                        if article['similarity_to_base'] >= 0.8:
                            report_parts.append(f"  - `{article['file_name']}` → `{base_article['file_name']}`")

                    report_parts.append(f"""
**操作步骤**:
1. 将重复文章的优质内容合并到基准文章 `{base_article['file_name']}`
2. 在网站配置中添加301重定向规则
3. 删除重复文章文件
4. 更新内部链接指向基准文章""")

                elif max_similarity >= 0.5:
                    # 中等相似度：建议Canonical标签
                    report_parts.append(f"""
**Canonical标签方案** (相似度 0.5-0.8)
- ✅ **主要文章**: `{base_article['file_name']}`
- 🏷️ **设置Canonical标签**:""")
                    for article in non_base_articles:
                        if 0.5 <= article['similarity_to_base'] < 0.8:
                            report_parts.append(f"  - `{article['file_name']}` → canonical指向 `{base_article['file_name']}`")

                    report_parts.append(f"""
**HTML标签示例**:
```html
<link rel="canonical" href="/articles/{base_article['file_name'].replace('.md', '.html')}" />
```

**操作说明**:
1. 保留所有文章，不删除任何内容
2. 在次要文章的HTML头部添加canonical标签
3. 告诉搜索引擎以基准文章为准进行索引""")

                else:
                    # 低相似度：建议内容差异化
                    report_parts.append(f"""
**内容差异化方案** (相似度 < 0.5)
- 📝 **差异化处理**: 各文章保持独立，增强内容差异性

**优化建议**:
1. 为每篇文章补充不同的案例、数据或观点
2. 调整文章角度：技术实现 vs 用户指南 vs 产品比较
3. 添加独特的应用场景或解决方案
4. 确保每篇文章都有明确的目标受众""")

                report_parts.append("")

        # 独立文章列表
        if unique_articles:
            report_parts.append(f"""
## ✅ 独立文章列表 ({len(unique_articles)}篇)

以下文章与其他文章不存在显著相似性，为独立原创内容：

""")
            for article in unique_articles:
                article_date = self._get_article_effective_date(article).strftime('%Y-%m-%d')
                word_count = article.get('word_count', 0)
                report_parts.append(f"- `{article['file_name']}` (日期: {article_date}, 字数: {word_count})")

        # 技术说明
        report_parts.append(f"""

---

## 🔬 技术说明

### 算法原理
1. **相似度矩阵构建**: 计算所有文章对的TF-IDF余弦相似度
2. **图构建**: 相似度≥{self.similarity_threshold}的文章对形成连接
3. **连通分量**: 使用DFS算法找出所有连通分量(重复群组)
4. **基准选择**: 每个群组选择最早发布的文章作为基准保留

### 相似度计算
- **标题权重**: 30%
- **内容权重**: 70%
- **同主题阈值**: {self.similarity_threshold}
- **跨主题阈值**: {getattr(self, 'cross_topic_threshold', 0.7)}

### 时间窗口
- **检测窗口**: {self.comparison_window_days} 天
- **字数门槛**: {self.config.get('min_content_length', 1000)} 字

---

*报告生成时间: {timestamp}*
*算法版本: Graph Clustering v2.3*""")

        # 生成报告文件
        report_content = '\n'.join(report_parts)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ 重复文章分析报告已生成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 报告生成失败: {e}")
            return ""

    def generate_seo_config_files(self, detection_result: Dict[str, Any], output_dir: str = ".") -> Dict[str, str]:
        """生成SEO优化配置文件 - redirects.yaml和canonical_mappings.json

        Args:
            detection_result: 检测结果
            output_dir: 输出目录

        Returns:
            生成的配置文件路径字典
        """
        import json
        import yaml

        print(f"📁 正在生成SEO配置文件...")

        duplicate_groups = detection_result.get('duplicate_groups', [])

        # 301重定向配置
        redirects_config = {'redirects': []}

        # Canonical标签映射
        canonical_mappings = {}

        # 内容差异化建议
        differentiation_suggestions = []

        for group in duplicate_groups:
            base_article = group['base_article']
            articles = group['articles']

            # 计算群组内最高相似度
            non_base_articles = [a for a in articles if not a['is_base']]
            if not non_base_articles:
                continue

            for article in non_base_articles:
                similarity = article['similarity_to_base']
                source_path = f"/articles/{article['file_name'].replace('.md', '.html')}"
                target_path = f"/articles/{base_article['file_name'].replace('.md', '.html')}"

                if similarity >= 0.8:
                    # 301重定向
                    redirects_config['redirects'].append({
                        'from': source_path,
                        'to': target_path,
                        'status': 301,
                        'reason': f'重复内容合并 (相似度: {similarity:.3f})',
                        'similarity': similarity
                    })

                elif similarity >= 0.5:
                    # Canonical标签
                    canonical_mappings[article['file_name']] = {
                        'canonical_url': target_path,
                        'canonical_file': base_article['file_name'],
                        'similarity': similarity,
                        'html_tag': f'<link rel="canonical" href="{target_path}" />'
                    }

                else:
                    # 内容差异化建议
                    differentiation_suggestions.append({
                        'file': article['file_name'],
                        'base_file': base_article['file_name'],
                        'similarity': similarity,
                        'suggestions': [
                            '为文章补充不同的案例、数据或观点',
                            '调整文章角度：技术实现 vs 用户指南 vs 产品比较',
                            '添加独特的应用场景或解决方案',
                            '确保文章有明确的目标受众'
                        ]
                    })

        # 生成配置文件
        config_files = {}

        # 1. 生成redirects.yaml
        if redirects_config['redirects']:
            redirects_file = os.path.join(output_dir, 'redirects.yaml')
            try:
                with open(redirects_file, 'w', encoding='utf-8') as f:
                    yaml.dump(redirects_config, f, default_flow_style=False,
                            allow_unicode=True, sort_keys=False)
                config_files['redirects'] = redirects_file
                print(f"✅ 301重定向配置已生成: {redirects_file}")
            except Exception as e:
                print(f"❌ 生成redirects.yaml失败: {e}")

        # 2. 生成canonical_mappings.json
        if canonical_mappings:
            canonical_file = os.path.join(output_dir, 'canonical_mappings.json')
            try:
                with open(canonical_file, 'w', encoding='utf-8') as f:
                    json.dump(canonical_mappings, f, indent=2, ensure_ascii=False)
                config_files['canonical'] = canonical_file
                print(f"✅ Canonical标签配置已生成: {canonical_file}")
            except Exception as e:
                print(f"❌ 生成canonical_mappings.json失败: {e}")

        # 3. 生成差异化建议文件
        if differentiation_suggestions:
            diff_file = os.path.join(output_dir, 'content_differentiation.json')
            try:
                with open(diff_file, 'w', encoding='utf-8') as f:
                    json.dump(differentiation_suggestions, f, indent=2, ensure_ascii=False)
                config_files['differentiation'] = diff_file
                print(f"✅ 内容差异化建议已生成: {diff_file}")
            except Exception as e:
                print(f"❌ 生成content_differentiation.json失败: {e}")

        # 4. 生成实施说明文档
        readme_content = f"""# SEO优化配置文件使用说明

本目录包含自动生成的SEO优化配置文件，帮助您处理网站中的重复内容问题。

## 📁 文件说明

### 1. redirects.yaml
**用途**: 301永久重定向配置
**适用场景**: 高相似度文章(≥0.8)的合并处理

**Hugo实施方法**:
```yaml
# 在Hugo配置文件(config.yaml)中添加:
outputs:
  home: ["HTML", "RSS", "REDIRECTS"]

# 将redirects.yaml内容添加到static/_redirects文件
```

**文件数量**: {len(redirects_config['redirects'])} 个重定向规则

### 2. canonical_mappings.json
**用途**: Canonical标签配置映射
**适用场景**: 中等相似度文章(0.5-0.8)的SEO优化

**实施方法**:
1. 在文章的Front Matter中添加canonical字段
2. 或在模板文件的<head>部分使用配置生成canonical标签

**文件数量**: {len(canonical_mappings)} 个canonical映射

### 3. content_differentiation.json
**用途**: 低相似度文章的差异化建议
**适用场景**: 相似度<0.5的文章优化指导

**文件数量**: {len(differentiation_suggestions)} 个差异化建议

## 🔧 实施步骤

1. **备份网站**: 在实施任何更改前，确保备份您的网站
2. **301重定向**: 根据redirects.yaml配置您的重定向规则
3. **Canonical标签**: 根据canonical_mappings.json为相关文章添加canonical标签
4. **内容优化**: 参考差异化建议改进文章内容
5. **测试验证**: 实施后使用工具验证重定向和canonical标签是否正确

## ⚠️ 注意事项

- 301重定向会永久改变URL访问，请谨慎操作
- 实施前请确认重定向目标文章确实是您想要保留的版本
- canonical标签不会影响用户访问，但会影响搜索引擎索引
- 建议分批实施，先测试少量文章的效果

---
*配置文件生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*质量检测工具版本: v2.3*
"""

        readme_file = os.path.join(output_dir, 'SEO_CONFIG_README.md')
        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            config_files['readme'] = readme_file
            print(f"✅ 实施说明文档已生成: {readme_file}")
        except Exception as e:
            print(f"❌ 生成说明文档失败: {e}")

        print(f"📊 配置文件生成完成，共生成 {len(config_files)} 个文件")
        return config_files

    def generate_simple_report(self, detection_result: Dict[str, Any], output_file: str = "simple_report.md") -> str:
        """生成简化版检测报告 - 适合快速检查

        Args:
            detection_result: 检测结果
            output_file: 输出文件路径

        Returns:
            报告文件路径
        """
        print(f"📄 正在生成简化报告...")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])

        # 统计信息
        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        total_articles = total_duplicates + len(unique_articles)

        report_parts = []

        # 简化报告头部
        report_parts.append(f"""# 📊 相似度检测结果 (简化版)

**检测时间**: {timestamp}
**检测阈值**: {self.similarity_threshold}
**文章总数**: {total_articles} 篇
**重复群组**: {len(duplicate_groups)} 个
**重复文章**: {total_duplicates} 篇
**独立文章**: {len(unique_articles)} 篇

---""")

        # 核心发现
        if duplicate_groups:
            # 计算最高相似度
            max_similarity = 0.0
            for group in duplicate_groups:
                non_base_articles = [a for a in group['articles'] if not a['is_base']]
                if non_base_articles:
                    group_max = max(a['similarity_to_base'] for a in non_base_articles)
                    max_similarity = max(max_similarity, group_max)

            report_parts.append(f"""## ⚠️ 发现问题

🔍 **检测到 {len(duplicate_groups)} 个重复群组**，最高相似度 {max_similarity:.3f}

### 📋 处理建议

""")

            # 按相似度分组处理建议
            high_similarity_groups = []
            medium_similarity_groups = []
            low_similarity_groups = []

            for group in duplicate_groups:
                non_base_articles = [a for a in group['articles'] if not a['is_base']]
                if non_base_articles:
                    max_sim = max(a['similarity_to_base'] for a in non_base_articles)
                    if max_sim >= 0.8:
                        high_similarity_groups.append(group)
                    elif max_sim >= 0.5:
                        medium_similarity_groups.append(group)
                    else:
                        low_similarity_groups.append(group)

            if high_similarity_groups:
                report_parts.append(f"""**🔴 高相似度群组 ({len(high_similarity_groups)}个) - 建议301重定向**
- 内容重复度高，建议合并文章并设置301重定向
- 保留基准文章，删除重复版本
""")

            if medium_similarity_groups:
                report_parts.append(f"""**🟡 中等相似度群组 ({len(medium_similarity_groups)}个) - 建议Canonical标签**
- 内容部分重复，建议保留但设置canonical标签
- 告知搜索引擎以基准文章为准
""")

            if low_similarity_groups:
                report_parts.append(f"""**🟢 低相似度群组 ({len(low_similarity_groups)}个) - 建议内容差异化**
- 相似度较低，通过内容优化可实现差异化
- 为各文章补充不同的观点、案例或数据
""")

            # 重复群组简要列表
            report_parts.append("\n### 📦 重复群组详情\n")
            for i, group in enumerate(duplicate_groups, 1):
                base_article = group['base_article']
                non_base_count = len([a for a in group['articles'] if not a['is_base']])
                max_sim = max((a['similarity_to_base'] for a in group['articles'] if not a['is_base']), default=0.0)

                status_icon = "🔴" if max_sim >= 0.8 else "🟡" if max_sim >= 0.5 else "🟢"

                report_parts.append(f"""**{status_icon} 群组 {i}** (相似度: {max_sim:.3f})
- **保留**: `{base_article['file_name']}`
- **重复**: {non_base_count} 篇文章
""")

        else:
            report_parts.append("""## ✅ 无重复内容

恭喜！未发现重复或高度相似的文章。您的内容具有良好的独特性。

""")

        # 简化技术说明
        report_parts.append(f"""---

## 📝 说明

- **检测算法**: 全连接图聚类 (确保数学完整性)
- **检测阈值**: {self.similarity_threshold} (相似度≥此值被认为重复)
- **时间窗口**: {self.comparison_window_days} 天
- **字数门槛**: {self.config.get('min_content_length', 1000)} 字

*生成时间: {timestamp} | 工具版本: v2.3*""")

        # 生成报告文件
        report_content = '\n'.join(report_parts)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ 简化报告已生成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 简化报告生成失败: {e}")
            return ""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='独立文章相似度检测工具')
    parser.add_argument('directory', nargs='?', help='要检测的文章目录路径')
    parser.add_argument('--config', default='../hugo_quality_standards.yml', help='配置文件路径')
    parser.add_argument('--threshold', type=float, help='相似度阈值 (0.0-1.0)')
    parser.add_argument('--output', default='similarity_report.md', help='报告输出文件')
    parser.add_argument('--auto-process', action='store_true',
                       help='自动移动重复文章到duplicate_articles文件夹')
    parser.add_argument('--dry-run', action='store_true',
                       help='只检测不移动文件（预览模式）')
    parser.add_argument('--window-days', type=int,
                       help='检测时间窗口（天数）')
    parser.add_argument('--compare', nargs=2, metavar=('FILE1', 'FILE2'),
                       help='对比两篇指定文章的相似度')
    parser.add_argument('--debug', action='store_true',
                       help='显示详细的比较过程和调试信息')
    parser.add_argument('--algorithm', choices=['linear', 'graph'], default='linear',
                       help='选择检测算法: linear(线性,默认) 或 graph(全连接图)')
    parser.add_argument('--generate-config', action='store_true',
                       help='生成SEO优化配置文件 (redirects.yaml, canonical_mappings.json等)')
    parser.add_argument('--config-output-dir', default='.',
                       help='配置文件输出目录 (默认: 当前目录)')
    parser.add_argument('--simple', action='store_true',
                       help='简化模式：输出精简的结果摘要，适合快速检查')

    args = parser.parse_args()

    if args.simple:
        print("🚀 相似度检测工具 (简化模式)")
    else:
        print("🚀 独立文章相似度检测工具")
        print("=" * 50)

    # 处理compare模式
    if args.compare:
        file1, file2 = args.compare
        print(f"🔍 对比模式启动")

        # 初始化检测器
        checker = SimilarityChecker(args.config)

        # 设置调试模式
        if args.debug:
            checker.debug_mode = True
            print("🐛 调试模式已启用")

        # 执行对比
        result = checker.compare_two_articles(file1, file2)

        if result:
            print("\n✅ 对比完成")
        else:
            print("\n❌ 对比失败")
            return 1

        return 0

    # 检查目录是否存在
    if not args.directory:
        print(f"❌ 请指定要检测的目录路径")
        return 1

    if not Path(args.directory).exists():
        print(f"❌ 目录不存在: {args.directory}")
        return 1

    # 初始化检测器
    checker = SimilarityChecker(args.config)

    # 设置调试模式
    if args.debug:
        checker.debug_mode = True
        print("🐛 调试模式已启用")

    # 覆盖配置参数
    if args.threshold:
        checker.similarity_threshold = args.threshold
        print(f"📊 使用自定义阈值: {args.threshold}")

    if args.window_days:
        checker.comparison_window_days = args.window_days
        print(f"⏰ 使用自定义时间窗口: {args.window_days} 天")

    try:
        # 1. 扫描文章
        if args.simple:
            print(f"📁 扫描: {args.directory}")
        else:
            print(f"\n📁 扫描目录: {args.directory}")
        articles = checker.scan_articles(args.directory)

        if not articles:
            print("❌ 没有找到可分析的文章")
            return 1

        # 2. 相似度检测 (根据算法选择)
        if args.algorithm == 'graph':
            if args.simple:
                print(f"🔍 检测相似度...")
            else:
                print(f"\n🔍 开始全连接图相似度检测...")
            detection_result = checker.detect_duplicate_groups(articles)
        else:
            if args.simple:
                print(f"🔍 检测相似度...")
            else:
                print(f"\n🔍 开始线性相似度检测...")
            detection_result = checker.detect_similarities(articles)

        # 3. 处理文章分类（可选）
        if args.auto_process and detection_result['moved_articles']:
            print(f"\n🔄 自动处理相似文章...")
            move_files = not args.dry_run
            if args.dry_run:
                print("⚠️ 预览模式：只显示操作，不实际移动文件")

            process_result = checker.process_articles_by_date(detection_result, move_files)

            if move_files:
                print(f"\n✅ 自动处理完成:")
                print(f"  ✅ 保留文章: {process_result['kept_count']} 篇")
                print(f"  📦 移动文章: {process_result['moved_count']} 篇")
                print(f"  📁 保留文章目录: {process_result['new_articles_folder']}")
                print(f"  📁 相似文章目录: {process_result['old_articles_folder']}")
            else:
                print(f"\n📋 预览结果:")
                print(f"  ✅ 将保留: {process_result['kept_count']} 篇文章")
                print(f"  📦 将移动: {process_result['moved_count']} 篇文章")

        # 4. 生成报告和显示总结
        if not args.simple:
            print(f"\n" + "=" * 50)

        if args.algorithm == 'graph':
            duplicate_groups = detection_result.get('duplicate_groups', [])
            unique_articles = detection_result.get('unique_articles', [])
            total_duplicates = sum(len(group['articles']) for group in duplicate_groups)

            if args.simple:
                # 简化模式输出
                print(f"🎉 检测完成！")
                if duplicate_groups:
                    print(f"⚠️  发现问题: {len(duplicate_groups)} 个重复群组，{total_duplicates} 篇重复文章")
                else:
                    print(f"✅ 未发现重复内容！{len(unique_articles)} 篇文章都是独立原创")
            else:
                # 详细模式输出
                print(f"🎉 全连接图检测完成！")
                print(f"📊 检测了 {len(articles)} 篇文章")
                print(f"📊 总比较次数: {detection_result['total_comparisons']}")
                print(f"📦 发现重复群组: {len(duplicate_groups)} 个")
                print(f"🔸 重复文章总数: {total_duplicates} 篇")
                print(f"✅ 独立文章: {len(unique_articles)} 篇")

            # 生成报告 (根据模式选择)
            if args.simple:
                print(f"\n📄 生成简化报告...")
                report_file = args.output.replace('.md', '_simple.md')
                checker.generate_simple_report(detection_result, report_file)
            else:
                print(f"\n📄 生成详细分析报告...")
                report_file = args.output.replace('.md', '_graph_analysis.md')
                checker.generate_duplicate_analysis_report(detection_result, report_file)

            # 生成SEO配置文件（可选）
            if args.generate_config and duplicate_groups:
                print(f"\n📁 生成SEO优化配置文件...")
                config_files = checker.generate_seo_config_files(detection_result, args.config_output_dir)
                if config_files:
                    print(f"📊 配置文件生成完成:")
                    for config_type, file_path in config_files.items():
                        print(f"  ✅ {config_type}: {file_path}")
                else:
                    print("⚠️ 未发现需要生成配置文件的重复群组")
            elif args.generate_config:
                print("ℹ️ 未发现重复群组，跳过配置文件生成")

        else:
            # 线性算法结果
            print(f"🎉 线性检测完成！")
            print(f"📊 检测了 {len(articles)} 篇文章")
            print(f"📊 总比较次数: {detection_result['total_comparisons']}")
            print(f"✅ 保留文章: {len(detection_result['kept_articles'])} 篇")
            print(f"📦 相似文章: {len(detection_result['moved_articles'])} 篇")

            if not args.auto_process and detection_result['moved_articles']:
                print(f"\n💡 提示: 使用 --auto-process 参数可自动移动相似文章")
                print(f"     使用 --dry-run 参数可预览操作而不实际移动文件")

        return 0

    except Exception as e:
        print(f"❌ 检测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())