#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Result Processor - Handles processing and organization of similarity detection results.

This module provides functionality to process detection results, move files,
and organize articles based on similarity analysis.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ResultProcessor:
    """
    Processes similarity detection results and handles file operations.
    """

    def __init__(self, config: Dict):
        """
        Initialize result processor.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.new_articles_folder = config.get('new_articles_folder', 'new-articles')
        self.old_articles_folder = config.get('old_articles_folder', 'old-articles')

    def process_by_date(self, detection_result: Dict[str, Any],
                       move_files: bool = True) -> Dict[str, Any]:
        """
        Process articles by date based on detection results.

        Args:
            detection_result: Results from similarity detection
            move_files: Whether to actually move files

        Returns:
            Processing results
        """
        kept_articles = detection_result.get('kept_articles', [])
        moved_articles = detection_result.get('moved_articles', [])
        processing_date = detection_result.get('processing_date',
                                              datetime.now().strftime('%Y-%m-%d'))

        if not moved_articles:
            print("📊 没有需要移动的文章")
            return {
                'moved_count': 0,
                'kept_count': len(kept_articles),
                'new_articles_folder': f"{self.new_articles_folder}/{processing_date}",
                'old_articles_folder': f"{self.old_articles_folder}/{processing_date}"
            }

        # Create date-based folders
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

        # Process kept articles
        print(f"\n📝 处理保留文章 ({len(kept_articles)} 篇):")
        for article in kept_articles:
            if move_files:
                try:
                    source_path = Path(article['file_path'])
                    target_path = new_articles_dir / source_path.name

                    # Handle file name conflicts
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

        # Process similar articles
        print(f"\n📦 处理相似文章 ({len(moved_articles)} 篇):")
        for article in moved_articles:
            if move_files:
                try:
                    source_path = Path(article['file_path'])
                    target_path = old_articles_dir / source_path.name

                    # Handle file name conflicts
                    if target_path.exists():
                        timestamp = datetime.now().strftime('%H%M%S')
                        stem = target_path.stem
                        suffix = target_path.suffix
                        target_name = f"{stem}_{timestamp}{suffix}"
                        target_path = old_articles_dir / target_name

                    shutil.move(str(source_path), str(target_path))
                    similarity = article.get('similarity_to_base', 0)
                    base_article = article.get('base_article', 'unknown')
                    print(f"  📦 移动: {article['file_name']} → old-articles/{processing_date}/ "
                          f"(相似度: {similarity:.3f}, 基准: {base_article})")
                    moved_count += 1

                except Exception as e:
                    print(f"  ❌ 移动失败 {article['file_name']}: {e}")
            else:
                similarity = article.get('similarity_to_base', 0)
                base_article = article.get('base_article', 'unknown')
                print(f"  📦 待移动: {article['file_name']} → old-articles/{processing_date}/ "
                      f"(相似度: {similarity:.3f}, 基准: {base_article})")
                moved_count += 1

        result = {
            'moved_count': moved_count,
            'kept_count': kept_count,
            'new_articles_folder': str(new_articles_dir.absolute()) if move_files
                                 else f"{self.new_articles_folder}/{processing_date}",
            'old_articles_folder': str(old_articles_dir.absolute()) if move_files
                                 else f"{self.old_articles_folder}/{processing_date}",
            'processing_date': processing_date
        }

        print(f"\n✅ 文章分类处理完成:")
        print(f"  ✅ 保留文章: {kept_count} 篇")
        print(f"  📦 移动文章: {moved_count} 篇")

        return result

    def organize_duplicate_groups(self, duplicate_groups: List[Dict],
                                 output_dir: str = "duplicate_groups") -> Dict[str, Any]:
        """
        Organize duplicate groups into separate folders.

        Args:
            duplicate_groups: List of duplicate groups
            output_dir: Base output directory

        Returns:
            Organization results
        """
        if not duplicate_groups:
            print("📊 没有重复群组需要组织")
            return {'organized_groups': 0, 'total_files': 0}

        base_dir = Path(output_dir)
        base_dir.mkdir(parents=True, exist_ok=True)

        organized_count = 0
        total_files = 0

        for i, group in enumerate(duplicate_groups, 1):
            group_dir = base_dir / f"group_{i:03d}_{group.get('topic', 'unknown')}"
            group_dir.mkdir(exist_ok=True)

            base_article = group['base_article']
            articles = group['articles']

            # Create group info file
            info_content = [
                f"# 重复群组 {i}",
                f"",
                f"**主题**: {group.get('topic', 'Unknown')}",
                f"**基准文章**: {base_article['file_name']}",
                f"**文章数量**: {len(articles)}",
                f"",
                f"## 文章列表",
                f""
            ]

            for article in articles:
                marker = "🔹 **基准**" if article.get('is_base', False) else "🔸"
                sim = article.get('similarity_to_base', 1.0 if article.get('is_base', False) else 0.0)
                info_content.append(f"- {marker} {article['file_name']} (相似度: {sim:.3f})")

            # Write group info
            with open(group_dir / "GROUP_INFO.md", 'w', encoding='utf-8') as f:
                f.write('\n'.join(info_content))

            organized_count += 1
            total_files += len(articles)

        print(f"✅ 重复群组组织完成:")
        print(f"  📦 组织群组: {organized_count} 个")
        print(f"  📄 涉及文章: {total_files} 篇")
        print(f"  📁 输出目录: {base_dir.absolute()}")

        return {
            'organized_groups': organized_count,
            'total_files': total_files,
            'output_directory': str(base_dir.absolute())
        }