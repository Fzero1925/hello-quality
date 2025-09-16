#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Reporter

Generates simplified, concise reports for quick similarity detection overview.
"""

from datetime import datetime
from typing import Dict, List, Any


class SimpleReporter:
    """
    Generates simplified reports for quick review of similarity detection results.
    """

    def __init__(self, config: Dict):
        """
        Initialize simple reporter.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.comparison_window_days = config.get('comparison_window_days', 90)

    def generate_simple_report(self, detection_result: Dict[str, Any],
                              output_file: str = "simple_report.md") -> str:
        """
        Generate simplified detection report.

        Args:
            detection_result: Detection results
            output_file: Output file path

        Returns:
            Report file path
        """
        print(f"📄 正在生成简化报告...")

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])

        # Statistics
        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        total_articles = total_duplicates + len(unique_articles)

        report_parts = []

        # Simplified header
        report_parts.append(f"""# 📊 相似度检测结果 (简化版)

**检测时间**: {timestamp}
**检测阈值**: {self.similarity_threshold}
**文章总数**: {total_articles} 篇
**重复群组**: {len(duplicate_groups)} 个
**重复文章**: {total_duplicates} 篇
**独立文章**: {len(unique_articles)} 篇

---""")

        # Core findings
        if duplicate_groups:
            # Calculate highest similarity
            max_similarity = 0.0
            for group in duplicate_groups:
                non_base_articles = [a for a in group['articles'] if not a.get('is_base', False)]
                if non_base_articles:
                    group_max = max(a['similarity_to_base'] for a in non_base_articles)
                    max_similarity = max(max_similarity, group_max)

            report_parts.append(f"""## ⚠️ 发现问题

🔍 **检测到 {len(duplicate_groups)} 个重复群组**，最高相似度 {max_similarity:.3f}

### 📋 处理建议

""")

            # Group recommendations by similarity level
            high_similarity_groups = []
            medium_similarity_groups = []
            low_similarity_groups = []

            for group in duplicate_groups:
                non_base_articles = [a for a in group['articles'] if not a.get('is_base', False)]
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

            # Brief group details
            report_parts.append("\n### 📦 重复群组详情\n")
            for i, group in enumerate(duplicate_groups, 1):
                base_article = group['base_article']
                non_base_count = len([a for a in group['articles'] if not a.get('is_base', False)])
                max_sim = max((a['similarity_to_base'] for a in group['articles'] if not a.get('is_base', False)), default=0.0)

                status_icon = "🔴" if max_sim >= 0.8 else "🟡" if max_sim >= 0.5 else "🟢"

                report_parts.append(f"""**{status_icon} 群组 {i}** (相似度: {max_sim:.3f})
- **保留**: `{base_article['file_name']}`
- **重复**: {non_base_count} 篇文章
""")

        else:
            report_parts.append("""## ✅ 无重复内容

恭喜！未发现重复或高度相似的文章。您的内容具有良好的独特性。

""")

        # Simplified technical info
        report_parts.append(f"""---

## 📝 说明

- **检测算法**: 全连接图聚类 (确保数学完整性)
- **检测阈值**: {self.similarity_threshold} (相似度≥此值被认为重复)
- **时间窗口**: {self.comparison_window_days} 天
- **字数门槛**: {self.config.get('min_content_length', 1000)} 字

*生成时间: {timestamp} | 工具版本: v2.3*""")

        # Generate report file
        report_content = '\n'.join(report_parts)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ 简化报告已生成: {output_file}")
            return output_file

        except Exception as e:
            print(f"❌ 简化报告生成失败: {e}")
            return ""

    def generate_quick_summary(self, detection_result: Dict[str, Any]) -> str:
        """
        Generate a very brief summary for console output.

        Args:
            detection_result: Detection results

        Returns:
            Summary string
        """
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])
        total_comparisons = detection_result.get('total_comparisons', 0)

        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        total_articles = total_duplicates + len(unique_articles)

        if duplicate_groups:
            # Calculate severity
            high_similarity_count = 0
            for group in duplicate_groups:
                non_base_articles = [a for a in group['articles'] if not a.get('is_base', False)]
                if non_base_articles:
                    max_sim = max(a['similarity_to_base'] for a in non_base_articles)
                    if max_sim >= 0.8:
                        high_similarity_count += 1

            severity = "🔴 高" if high_similarity_count > 0 else "🟡 中等"

            summary = f"""📊 检测完成！发现 {len(duplicate_groups)} 个重复群组
   ⚠️ 风险等级: {severity}
   📄 总文章: {total_articles} 篇 | 重复: {total_duplicates} 篇 | 独立: {len(unique_articles)} 篇
   🔍 比较次数: {total_comparisons}"""
        else:
            summary = f"""✅ 检测完成！未发现重复内容
   📄 检测文章: {total_articles} 篇 (全部独立)
   🔍 比较次数: {total_comparisons}"""

        return summary

    def generate_console_output(self, detection_result: Dict[str, Any]) -> None:
        """
        Generate formatted console output for detection results.

        Args:
            detection_result: Detection results
        """
        print("\n" + "="*60)
        print("🎉 相似度检测结果摘要")
        print("="*60)

        summary = self.generate_quick_summary(detection_result)
        print(summary)

        duplicate_groups = detection_result.get('duplicate_groups', [])
        if duplicate_groups:
            print(f"\n📋 需要处理的重复群组:")

            for i, group in enumerate(duplicate_groups[:5], 1):  # Show first 5 groups
                base_article = group['base_article']
                non_base_count = len([a for a in group['articles'] if not a.get('is_base', False)])
                max_sim = max((a['similarity_to_base'] for a in group['articles'] if not a.get('is_base', False)), default=0.0)

                status = "🔴 高风险" if max_sim >= 0.8 else "🟡 中等风险" if max_sim >= 0.5 else "🟢 低风险"
                print(f"   {i}. {status} | 基准: {base_article['file_name']} | 重复: {non_base_count} 篇 | 相似度: {max_sim:.3f}")

            if len(duplicate_groups) > 5:
                print(f"   ... 以及其他 {len(duplicate_groups) - 5} 个群组")

            print(f"\n💡 建议查看详细报告获取完整的处理指导")

        print("="*60)

    def generate_statistics_only(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate statistics summary without full report.

        Args:
            detection_result: Detection results

        Returns:
            Statistics dictionary
        """
        duplicate_groups = detection_result.get('duplicate_groups', [])
        unique_articles = detection_result.get('unique_articles', [])
        total_comparisons = detection_result.get('total_comparisons', 0)

        total_duplicates = sum(len(group['articles']) for group in duplicate_groups)
        total_articles = total_duplicates + len(unique_articles)

        # Calculate similarity distribution
        similarity_distribution = {'high': 0, 'medium': 0, 'low': 0}
        max_overall_similarity = 0.0

        for group in duplicate_groups:
            non_base_articles = [a for a in group['articles'] if not a.get('is_base', False)]
            if non_base_articles:
                max_sim = max(a['similarity_to_base'] for a in non_base_articles)
                max_overall_similarity = max(max_overall_similarity, max_sim)

                if max_sim >= 0.8:
                    similarity_distribution['high'] += 1
                elif max_sim >= 0.5:
                    similarity_distribution['medium'] += 1
                else:
                    similarity_distribution['low'] += 1

        return {
            'total_articles': total_articles,
            'unique_articles': len(unique_articles),
            'duplicate_groups': len(duplicate_groups),
            'duplicate_articles': total_duplicates,
            'duplicate_rate': (total_duplicates / total_articles * 100) if total_articles > 0 else 0,
            'total_comparisons': total_comparisons,
            'max_similarity': max_overall_similarity,
            'similarity_distribution': similarity_distribution,
            'detection_threshold': self.similarity_threshold
        }