#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键文章质量检测脚本
整合Hugo模板修复、质量检测、相似度分析和中文报告生成
"""

import os
import sys
import argparse
import shutil
import time
from pathlib import Path
from datetime import datetime
import codecs
import logging
from typing import Dict, List, Optional, Any

# 解决Windows编码问题
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入模块
try:
    from modules.hugo_template_fixer import HugoTemplateFixer
    from modules.chinese_reporter import ChineseReporter
    from modules.alt_text_generator import AltTextGenerator
    from modules.tldr_checker import TLDRChecker
    from modules.quality_control.semantic_deduplication import SemanticDeduplicator
    from scripts.quality_check import ComprehensiveQualityChecker
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    print("请确保所有依赖模块都存在")
    sys.exit(1)

class ArticleQualityChecker:
    """一键文章质量检测器"""

    def __init__(self, config_path: str = "hugo_quality_standards.yml"):
        """初始化"""
        self.config_path = config_path
        self.start_time = time.time()

        # 初始化各个组件
        try:
            self.template_fixer = HugoTemplateFixer(config_path)
            self.quality_checker = ComprehensiveQualityChecker(pqs_mode=False)
            self.alt_generator = AltTextGenerator(config_path)
            self.tldr_checker = TLDRChecker(config_path)
            self.reporter = ChineseReporter(config_path)
            self.deduplicator = SemanticDeduplicator()
            print("✅ 所有检测模块初始化成功")
        except Exception as e:
            print(f"❌ 模块初始化失败: {e}")
            sys.exit(1)

    def check_single_article(self, file_path: str, auto_fix: bool = True, save_changes: bool = False) -> Dict:
        """检查单篇文章

        Args:
            file_path: 文章文件路径
            auto_fix: 是否自动修复Hugo模板问题
            save_changes: 是否保存修改后的文章

        Returns:
            检测结果字典
        """
        print(f"\n🔍 正在检测文章: {file_path}")

        # 读取文章内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return {'error': f"无法读取文件: {e}"}

        # 1. Hugo模板修复
        hugo_fix_results = {}
        fixed_content = original_content
        if auto_fix:
            print("  📝 正在修复Hugo模板...")
            fixed_content, hugo_fix_results = self.template_fixer.fix_article(original_content, file_path)

            if save_changes and fixed_content != original_content:
                # 保存修复后的文章
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    print(f"  ✅ 已保存修复后的文章")
                except Exception as e:
                    print(f"  ⚠️ 保存失败: {e}")

        # 2. Alt文本分析
        print("  🖼️ 正在分析图片Alt文本...")
        # 提取Front Matter数据用于Alt分析
        try:
            front_matter_data = self._extract_front_matter_data(fixed_content)
        except Exception as e:
            print(f"  ⚠️ Front Matter解析失败: {e}")
            front_matter_data = {}

        alt_analysis_results = self.alt_generator.analyze_images(
            fixed_content, front_matter_data, file_path
        )

        # 3. TL;DR检测
        print("  📋 正在检测TL;DR结构...")
        tldr_results = self.tldr_checker.check_tldr(fixed_content)

        # 4. 质量检测
        print("  📊 正在执行质量检测...")
        quality_results = self.quality_checker.check_article_quality(file_path)

        # 5. 相似度检测（简化版，推荐使用独立工具）
        print("  🔍 正在进行简单相似度检测...")
        similarity_results = {}
        try:
            # 简化的相似度检测，主要用于单文章分析
            # 对于批量相似度检测，推荐使用模块化相似度检测系统或代理脚本

            # 提取文章元数据
            metadata = {
                'title': front_matter_data.get('title', ''),
                'date': front_matter_data.get('date', ''),
                'file_path': file_path
            }

            # 使用语义去重器进行简单检测
            is_similar, similarity_data = self.deduplicator.check_content_similarity(fixed_content, metadata)
            similarity_results = {
                'is_similar': is_similar,
                'similar_articles': similarity_data.get('similarities', [])[:3],  # 最多显示3个
                'max_similarity': similarity_data.get('max_similarity', 0.0),
                'use_independent_tool': True  # 标记推荐使用独立工具
            }

            if is_similar:
                print(f"  ⚠️ 检测到可能的相似文章，最高相似度: {similarity_results['max_similarity']:.3f}")
                print(f"  💡 建议使用模块化系统进行详细分析: python scripts/similarity_checker.py")
            else:
                print("  ✅ 未检测到明显相似文章")

        except Exception as e:
            print(f"  ⚠️ 相似度检测失败: {e}")
            similarity_results = {
                'error': str(e),
                'use_independent_tool': True
            }

        # 6. 统计信息
        article_stats = self._calculate_stats(fixed_content, file_path)

        return {
            'file_path': file_path,
            'original_content': original_content,
            'fixed_content': fixed_content,
            'hugo_fix_results': hugo_fix_results,
            'alt_analysis_results': alt_analysis_results,
            'tldr_results': tldr_results,
            'quality_results': quality_results,
            'similarity_results': similarity_results,
            'article_stats': article_stats,
            'check_duration': time.time() - self.start_time
        }

    def check_directory(self, directory: str, pattern: str = "*.md", auto_fix: bool = True) -> List[Dict]:
        """检查目录中的所有文章

        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            auto_fix: 是否自动修复

        Returns:
            所有文章的检测结果列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"❌ 目录不存在: {directory}")
            return []

        # 查找所有Markdown文件
        md_files = list(dir_path.glob(pattern))
        if not md_files:
            print(f"❌ 目录中没有找到匹配的文件: {pattern}")
            return []

        print(f"📁 找到 {len(md_files)} 个文件，开始检测...")

        results = []
        for i, file_path in enumerate(md_files, 1):
            print(f"\n[{i}/{len(md_files)}] 处理文件: {file_path.name}")
            try:
                result = self.check_single_article(str(file_path), auto_fix)
                results.append(result)
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                results.append({
                    'file_path': str(file_path),
                    'error': str(e)
                })

        return results


    def generate_report(self, result: Dict, output_dir: str = "reports") -> str:
        """生成检测报告

        Args:
            result: 检测结果
            output_dir: 输出目录

        Returns:
            报告文件路径
        """
        if 'error' in result:
            return ""

        print("  📄 正在生成检测报告...")

        # 提取报告所需的数据
        quality_scores = self._extract_quality_scores(result['quality_results'])
        issues = self._extract_issues(result['quality_results'])

        # 生成报告（使用新的简化版本）
        report_content = self.reporter.generate_report(
            file_path=result['file_path'],
            quality_scores=quality_scores,
            hugo_fix_results=result['hugo_fix_results'],
            issues=issues,
            article_stats=result['article_stats'],
            similarity_results=result['similarity_results']
        )

        # 保存报告
        report_file = self.reporter.save_report(
            report_content,
            result['file_path'],
            output_dir
        )

        return report_file

    def _calculate_stats(self, content: str, file_path: str) -> Dict:
        """计算文章统计信息"""
        # 移除Front Matter
        if content.startswith('---'):
            end_index = content.find('\n---', 3)
            if end_index != -1:
                article_content = content[end_index + 4:]
            else:
                article_content = content
        else:
            article_content = content

        # 计算字数（中文按字符计算，英文按单词计算）
        chinese_chars = len([c for c in article_content if '\u4e00' <= c <= '\u9fff'])
        english_words = len([w for w in article_content.split() if any(c.isalpha() for c in w)])
        word_count = chinese_chars + english_words

        return {
            'word_count': word_count,
            'char_count': len(article_content),
            'check_duration': time.time() - self.start_time,
            'total_rules': 12,
            'file_size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
        }

    def _extract_quality_scores(self, quality_results: Dict) -> Dict:
        """从质量检测结果中提取评分"""
        # 这里需要根据实际的quality_checker返回格式调整
        return {
            'total_score': quality_results.get('total_score', 75),
            'content_depth': quality_results.get('content_depth', 80),
            'seo_technical': quality_results.get('seo_technical', 75),
            'content_structure': quality_results.get('content_structure', 85),
            'readability': quality_results.get('readability', 80),
            'adsense_compliance': quality_results.get('adsense_compliance', 90)
        }

    def _extract_issues(self, quality_results: Dict) -> List[Dict]:
        """从质量检测结果中提取问题列表"""
        # 这里需要根据实际的quality_checker返回格式调整
        issues = []

        # 示例问题提取逻辑
        if quality_results.get('seo_issues'):
            for issue in quality_results['seo_issues']:
                issues.append({
                    'title': issue.get('title', '未知问题'),
                    'severity': 'warning',
                    'description': issue.get('description', ''),
                    'suggestion': issue.get('suggestion', '')
                })

        return issues

    def _extract_front_matter_data(self, content: str) -> Dict:
        """提取Front Matter数据"""
        try:
            import yaml

            if not content.startswith('---'):
                return {}

            end_index = content.find('\n---', 3)
            if end_index == -1:
                return {}

            front_matter_text = content[3:end_index]
            return yaml.safe_load(front_matter_text) or {}
        except Exception:
            return {}

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Hugo文章质量检测工具')
    parser.add_argument('path', nargs='?', default='D:/Users/Fzero/project/ai-smarthome/content-generation-tool/articles',
                       help='要检测的文章文件或目录路径')
    parser.add_argument('--config', default='hugo_quality_standards.yml',
                       help='配置文件路径')
    parser.add_argument('--output-dir', default='reports',
                       help='报告输出目录')
    parser.add_argument('--no-auto-fix', action='store_true',
                       help='禁用自动修复Hugo模板')
    parser.add_argument('--save-changes', action='store_true',
                       help='保存修复后的文章到原文件')

    args = parser.parse_args()

    print("🚀 Hugo文章质量检测工具 v2.1")
    print(f"📁 目标路径: {args.path}")
    print(f"⚙️ 配置文件: {args.config}")
    print(f"🔧 自动修复: {'启用' if not args.no_auto_fix else '禁用'}")
    print(f"💾 保存修改: {'是' if args.save_changes else '否'}")
    print("-" * 50)

    # 检查路径是否存在
    path = Path(args.path)
    if not path.exists():
        print(f"❌ 路径不存在: {args.path}")
        return 1

    # 初始化检测器
    try:
        checker = ArticleQualityChecker(args.config)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1

    # 创建报告目录
    Path(args.output_dir).mkdir(exist_ok=True)

    start_time = time.time()

    # 执行检测
    if path.is_file():
        # 单文件检测
        result = checker.check_single_article(
            str(path),
            auto_fix=not args.no_auto_fix,
            save_changes=args.save_changes
        )

        if 'error' not in result:
            # 生成报告
            report_file = checker.generate_report(result, args.output_dir)
            if report_file:
                print(f"\n📄 报告已生成: {report_file}")

            # 相似度检测提示
            if result.get('similarity_results', {}).get('is_similar'):
                print(f"\n💡 检测到相似文章，建议使用模块化系统进行详细分析:")
                print(f"   python scripts/similarity_checker.py \"{path.parent}\" --auto-process")
                print(f"   或直接使用: cd similarity-detection && python main.py \"{path.parent}\" --auto-process")
        else:
            print(f"❌ 检测失败: {result['error']}")
            return 1

    else:
        # 目录检测
        results = checker.check_directory(
            str(path),
            auto_fix=not args.no_auto_fix
        )

        if not results:
            print("❌ 没有找到任何文章")
            return 1

        # 处理结果
        successful_results = [r for r in results if 'error' not in r]
        failed_results = [r for r in results if 'error' in r]

        print(f"\n📊 检测完成: 成功 {len(successful_results)} 篇，失败 {len(failed_results)} 篇")

        # 生成报告
        report_files = []
        similar_articles_detected = 0

        for result in successful_results:
            # 生成报告
            report_file = checker.generate_report(result, args.output_dir)
            if report_file:
                report_files.append(report_file)

            # 统计相似文章
            if result.get('similarity_results', {}).get('is_similar'):
                similar_articles_detected += 1

        if report_files:
            print(f"\n📄 共生成 {len(report_files)} 份报告:")
            for report_file in report_files[:5]:  # 只显示前5个
                print(f"   - {Path(report_file).name}")
            if len(report_files) > 5:
                print(f"   ... 和其他 {len(report_files) - 5} 份报告")

        # 相似度检测建议
        if similar_articles_detected > 0:
            print(f"\n🔍 检测到 {similar_articles_detected} 篇文章可能存在相似内容")
            print(f"💡 建议使用模块化相似度检测系统进行批量分析:")
            print(f"   python scripts/similarity_checker.py \"{path}\" --auto-process")
            print(f"   或直接使用: cd similarity-detection && python main.py \"{path}\" --auto-process")

    # 显示总耗时
    total_time = time.time() - start_time
    print(f"\n⏱️ 总检测时间: {total_time:.1f} 秒")
    print("✅ 检测完成！")

    # 功能提示
    print(f"\n🛠️ 可用的独立工具:")
    print(f"   📊 相似度检测: python scripts/similarity_checker.py (模块化v2.0)")
    print(f"   🧩 直接使用模块化: cd similarity-detection && python main.py")
    print(f"   📖 图片分析指南: docs/image_analysis_guide.md")

    return 0

if __name__ == '__main__':
    sys.exit(main())