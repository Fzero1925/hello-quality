#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Similarity Detection Tool - Main Entry Point

Modularized similarity detection system for content deduplication.
Maintains compatibility with the original similarity_checker.py interface.
"""

import os
import sys
import argparse
import codecs
from pathlib import Path
from typing import Optional

# Resolve Windows encoding issues
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import modular components
try:
    from core.similarity_engine import SimilarityEngine
    from reporters.markdown_reporter import MarkdownReporter
    from reporters.simple_reporter import SimpleReporter
    from reporters.seo_config_generator import SEOConfigGenerator
except ImportError as e:
    print(f"⚠️ 模块导入警告: {e}")
    print("   请确保在similarity-detection目录中运行此脚本")
    sys.exit(1)


def main():
    """Main function with full CLI compatibility."""
    parser = argparse.ArgumentParser(description='模块化文章相似度检测工具')
    parser.add_argument('directory', nargs='?', help='要检测的文章目录路径')
    parser.add_argument('--config', default='../config/uniqueness.yml', help='配置文件路径')
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
        print("🚀 模块化文章相似度检测工具")
        print("=" * 50)

    # Handle compare mode
    if args.compare:
        file1, file2 = args.compare
        print(f"🔍 对比模式启动")

        # Initialize engine
        engine = SimilarityEngine(args.config)

        # Set debug mode
        if args.debug:
            engine.set_debug_mode(True)
            print("🐛 调试模式已启用")

        # Execute comparison
        result = engine.compare_two_articles(file1, file2)

        if result:
            print("\n✅ 对比完成")
        else:
            print("\n❌ 对比失败")
            return 1

        return 0

    # Check directory
    if not args.directory:
        print(f"❌ 请指定要检测的目录路径")
        return 1

    if not Path(args.directory).exists():
        print(f"❌ 目录不存在: {args.directory}")
        return 1

    try:
        # Initialize engine
        engine = SimilarityEngine(args.config)

        # Set debug mode
        if args.debug:
            engine.set_debug_mode(True)
            print("🐛 调试模式已启用")

        # Override configuration parameters
        if args.threshold:
            engine.similarity_threshold = args.threshold
            print(f"📊 使用自定义阈值: {args.threshold}")

        if args.window_days:
            engine.comparison_window_days = args.window_days
            print(f"⏰ 使用自定义时间窗口: {args.window_days} 天")

        # 1. Scan articles
        if args.simple:
            print(f"📁 扫描: {args.directory}")
        else:
            print(f"\n📁 扫描目录: {args.directory}")

        articles = engine.scan_articles(args.directory)

        if not articles:
            print("❌ 没有找到可分析的文章")
            return 1

        # 2. Similarity detection (based on algorithm choice)
        if args.algorithm == 'graph':
            if args.simple:
                print(f"🔍 检测相似度...")
            else:
                print(f"\n🔍 开始全连接图相似度检测...")
            detection_result = engine.detect_duplicate_groups(articles)
        else:
            if args.simple:
                print(f"🔍 检测相似度...")
            else:
                print(f"\n🔍 开始线性相似度检测...")
            detection_result = engine.detect_similarities_linear(articles)

        # 3. Process articles classification (optional)
        if args.auto_process and detection_result.get('moved_articles'):
            print(f"\n🔄 自动处理相似文章...")
            move_files = not args.dry_run
            if args.dry_run:
                print("⚠️ 预览模式：只显示操作，不实际移动文件")

            process_result = engine.process_articles_by_date(detection_result, move_files)

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

        # 4. Generate reports and display summary
        if not args.simple:
            print(f"\n" + "=" * 50)

        # Initialize reporters
        markdown_reporter = MarkdownReporter(engine.config)
        simple_reporter = SimpleReporter(engine.config)
        seo_generator = SEOConfigGenerator(engine.config)

        if args.algorithm == 'graph':
            duplicate_groups = detection_result.get('duplicate_groups', [])
            unique_articles = detection_result.get('unique_articles', [])
            total_duplicates = sum(len(group['articles']) for group in duplicate_groups)

            if args.simple:
                # Simplified mode output
                print(f"🎉 检测完成！")
                if duplicate_groups:
                    print(f"⚠️  发现问题: {len(duplicate_groups)} 个重复群组，{total_duplicates} 篇重复文章")
                else:
                    print(f"✅ 未发现重复内容！{len(unique_articles)} 篇文章都是独立原创")
            else:
                # Detailed mode output
                print(f"🎉 全连接图检测完成！")
                print(f"📊 检测了 {len(articles)} 篇文章")
                print(f"📊 总比较次数: {detection_result['total_comparisons']}")
                print(f"📦 发现重复群组: {len(duplicate_groups)} 个")
                print(f"🔸 重复文章总数: {total_duplicates} 篇")
                print(f"✅ 独立文章: {len(unique_articles)} 篇")

            # Generate reports (based on mode selection)
            if args.simple:
                print(f"\n📄 生成简化报告...")
                report_file = args.output.replace('.md', '_simple.md')
                simple_reporter.generate_simple_report(detection_result, report_file)
            else:
                print(f"\n📄 生成详细分析报告...")
                report_file = args.output.replace('.md', '_graph_analysis.md')
                markdown_reporter.generate_duplicate_analysis_report(detection_result, report_file)

            # Generate SEO config files (optional)
            if args.generate_config and duplicate_groups:
                print(f"\n📁 生成SEO优化配置文件...")
                config_files = seo_generator.generate_seo_config_files(detection_result, args.config_output_dir)
                if config_files:
                    print(f"📊 配置文件生成完成:")
                    for config_type, file_path in config_files.items():
                        print(f"  ✅ {config_type}: {file_path}")
                else:
                    print("⚠️ 未发现需要生成配置文件的重复群组")
            elif args.generate_config:
                print("ℹ️ 未发现重复群组，跳过配置文件生成")

        else:
            # Linear algorithm results
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