#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
相似度检测工具 - 代理脚本

此脚本作为新模块化相似度检测系统的入口代理，保持向后兼容性。
新的模块化系统位于 similarity-detection/ 目录中，提供更好的维护性和扩展性。

🔄 升级说明：
- 旧版本: scripts/similarity_checker_legacy.py (1757行单文件)
- 新版本: similarity-detection/ (23个模块化文件)

💡 建议：
- 新项目请直接使用: python similarity-detection/main.py
- 现有脚本可继续使用此代理保持兼容性
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """代理主函数：转发调用到新的模块化系统"""

    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    modular_script = project_root / "similarity-detection" / "main.py"

    # 检查模块化版本是否存在
    if not modular_script.exists():
        print("❌ 错误：找不到新的模块化相似度检测系统")
        print(f"   预期路径: {modular_script}")
        print(f"   请确保 similarity-detection/ 目录存在")
        print(f"   或使用旧版本: python scripts/similarity_checker_legacy.py")
        return 1

    # 显示升级提示（仅在首次运行或调试模式）
    if "--debug" in sys.argv or "--help" in sys.argv:
        print("🔄 正在使用模块化相似度检测系统（v2.0）")
        print(f"   模块化版本: {modular_script}")
        print(f"   Legacy版本: {script_dir}/similarity_checker_legacy.py")
        print("=" * 60)

    try:
        # 构建命令参数 - 保持所有原始参数
        cmd_args = [sys.executable, str(modular_script)] + sys.argv[1:]

        # 执行新的模块化系统
        result = subprocess.run(cmd_args, cwd=str(project_root))
        return result.returncode

    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
        return 130
    except Exception as e:
        print(f"❌ 代理执行错误: {e}")
        print(f"🔧 备用方案：python {script_dir}/similarity_checker_legacy.py")
        return 1

if __name__ == '__main__':
    # 添加提示信息
    if len(sys.argv) == 1 or "--help" in sys.argv:
        print("📊 模块化相似度检测工具 - 代理脚本")
        print()
        print("🔄 此脚本自动转发到新的模块化系统:")
        print(f"   → similarity-detection/main.py")
        print()
        print("💡 直接使用新系统 (推荐):")
        print(f"   cd similarity-detection && python main.py [参数]")
        print()
        print("📚 使用旧版本 (兼容性):")
        print(f"   python scripts/similarity_checker_legacy.py [参数]")
        print()
        print("=" * 60)

    sys.exit(main())