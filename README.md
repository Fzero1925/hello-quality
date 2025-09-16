# Hugo文章质量检测工具 v2.3

专为手写文章设计的模块化质量检测和优化工具，集成Hugo模板修复、SEO优化和全连接图相似度检测算法。

## 🎯 主要功能

### ✅ 核心功能
- **Hugo模板合规检测与自动修复** - 智能识别并修复Front Matter问题
- **SEO优化分析** - 基于最佳实践的综合SEO检测
- **增强型禁词检测** - 三级禁词检测（严重/警告/建议）
- **智能质量评分** - 多维度文章质量评估系统
- **中文质量报告** - 详细的改进建议和自动修复代码

### 🛠️ 独立工具
- **相似度检测工具** - `scripts/similarity_checker.py` 批量检测重复文章 (🆕 v2.0模块化版本)
- **模块化相似度系统** - `similarity-detection/` 新一代模块化架构，更易维护扩展
- **图片优化指南** - `docs/image_analysis_guide.md` 完整的图片标准文档

### 🚀 新特性 (v2.3 - 全连接图算法版本)
- **全连接图聚类算法** - 数学完整性检测，确保零遗漏的相似关系识别
- **SEO优化增强** - 集成301重定向和Canonical标签自动生成
- **智能配置文件生成** - 自动生成redirects.yaml、canonical_mappings.json等
- **简化模式** - `--simple`参数提供精简输出，适合快速检查
- **智能SEO决策** - 基于相似度自动推荐301重定向、Canonical标签或内容差异化策略

### 🔧 技术特点
- **智能修改分类**: 自动修复 vs 人工确认分类
- **多维度质量标准**: 按文章类型和SEO意图分层检测
- **权重平衡**: 内容深度40% + SEO技术20% + 结构完整15% + 可读性10% + 合规性10%
- **中文友好**: 全中文界面和报告，适合中文内容创作

## 📁 项目结构

```
quality-detection-tool/
├── check_articles.py              # 主检测脚本 (核心入口)
├── hugo_quality_standards.yml     # 质量标准配置文件
├── modules/
│   ├── hugo_template_fixer.py     # Hugo模板自动修复器 (增强版)
│   ├── chinese_reporter.py        # 中文报告生成器 (简化版)
│   ├── alt_text_generator.py      # Alt文本智能生成器
│   ├── tldr_checker.py            # TL;DR要点总结检测器
│   ├── quality_control/           # 质量控制模块
│   └── deduplication/             # 去重检测模块
├── scripts/
│   ├── quality_check.py           # 核心质量检测脚本
│   ├── similarity_checker.py      # 🆕 相似度检测代理脚本 (v2.0兼容性)
│   ├── similarity_checker_legacy.py # 原始相似度检测工具 (v1.0遗留版本)
│   └── content_uniqueness_guard.py
├── similarity-detection/           # 🆕 模块化相似度检测系统 (v2.0)
│   ├── main.py                    # 新系统主入口
│   ├── core/                      # 核心功能模块
│   ├── algorithms/                # 算法模块 (TF-IDF, SimHash, 语义相似度等)
│   ├── reporters/                 # 报告生成器
│   ├── utils/                     # 工具模块
│   └── config/                    # 配置文件
├── docs/
│   └── image_analysis_guide.md    # 🆕 图片优化完整指南
├── pqs_v3_kit/                    # PQS v3质量检测套件
├── config/                        # 配置文件
├── configs/                       # 质量门槛配置
├── archived_workflows/            # 已归档的自动化工作流
├── reports/                       # 质量检测报告 (运行时创建)
└── duplicate_articles/            # 重复文章存储 (相似度工具创建)
```

## 🚀 快速开始

### 安装依赖

```bash
pip install pyyaml sentence-transformers scikit-learn numpy
```

### 核心质量检测

```bash
# 检测指定目录的所有文章
python check_articles.py "D:/path/to/articles"

# 检测单个文章
python check_articles.py "article.md"

# 禁用自动修复
python check_articles.py "D:/path/to/articles" --no-auto-fix

# 保存修复后的文章
python check_articles.py "D:/path/to/articles" --save-changes
```

### 独立相似度检测

```bash
# 使用代理脚本 (推荐，保持兼容性)
python scripts/similarity_checker.py "D:/path/to/articles"

# 直接使用模块化系统 (高级用户)
cd similarity-detection && python main.py "D:/path/to/articles"

# 自动处理重复文章
python scripts/similarity_checker.py "D:/path/to/articles" --auto-process

# 预览模式（不实际移动文件）
python scripts/similarity_checker.py "D:/path/to/articles" --auto-process --dry-run

# 自定义相似度阈值
python scripts/similarity_checker.py "D:/path/to/articles" --threshold 0.4

# 使用旧版本 (如遇兼容性问题)
python scripts/similarity_checker_legacy.py "D:/path/to/articles"
```

### 默认检测目标

如果不指定路径，默认检测：
```
D:/Users/Fzero/project/ai-smarthome/content-generation-tool/articles/
```

## 📋 检测标准

### Hugo模板合规检测 (自动修复，不计分)
- ✅ **必填字段**: title, description, date, categories, author
- ✅ **推荐字段**: slug, tags, keywords, featured_image
- ✅ **分类标准化**: 中文自动转换为英文标准分类
- ✅ **格式规范**: 日期ISO格式、标签去重、slug生成

### 质量评分维度 (100分制)
1. **内容深度质量 (40%)** - 按文章类型分层检测
   - 评测类: 2500-4000字，包含性能分析、价格对比等
   - 购买指南: 3000-5000字，包含预算分析、品牌对比等
   - 对比分析: 2000-3500字，必须包含对比表格

2. **SEO技术指标 (20%)** - 基于SEO_CHECKLIST.md
   - 标题长度: 50-60字符，包含年份和关键词
   - 描述优化: 150-160字符，包含主要关键词
   - 关键词密度: 0.8%-2.0%，自然分布
   - 内部链接: 3-8个相关链接

3. **内容结构完整 (15%)**
   - 标题层级: 1个H1，4-8个H2
   - 必需元素: 目录、FAQ、结论
   - 可读性: 短段落、项目符号、编号列表

4. **可读性指标 (10%)**
   - 段落长度控制
   - 使用子标题分段
   - 列表和要点展示

5. **AdSense合规性 (10%)**
   - 避免禁用短语
   - 必需免责声明
   - 85%原创内容要求

### 图片优化标准 (权重已分摊)
- **数量要求**: 最少3张 (1张featured + 2张inline)
- **格式标准**: WebP优先，JPEG备选
- **SEO优化**: Alt文本50-125字符，包含关键词
- **路径规范**: static/images/{分类}/{slug}/格式

## 📊 报告系统

### 核心质量报告
1. **检查总结** - 总分、各维度得分、问题统计
2. **Hugo模板修复结果** - 自动修复项目、智能确认建议
3. **图片优化指南引用** - 引用独立的详细图片指南文档
4. **具体改动建议** - 按严重程度分类的问题列表和修复建议
5. **自动修复代码** - 可直接复制的Front Matter修改内容
6. **相似度检测提示** - 推荐使用独立工具进行详细分析

### 独立工具报告
- **相似度报告**: `similarity_report.md` - 详细的重复文章分析
- **图片指南**: `docs/image_analysis_guide.md` - 完整的图片优化标准

### 报告文件
- **质量报告位置**: `reports/` 文件夹
- **相似度报告**: 脚本运行目录
- **格式**: Markdown格式，中文内容
- **命名**: `quality_report_时间戳_文章名.md`

## 🔍 相似度检测 (v2.3 全连接图算法)

### 🚨 v2.3 重大突破
- **数学完整性**: 全连接图聚类算法确保零遗漏，所有相似关系都被正确识别
- **智能SEO优化**: 基于相似度自动推荐301重定向、Canonical标签或内容差异化
- **配置文件自动生成**: 输出可直接使用的网站配置文件
- **简化模式**: 精简输出适合快速检查和决策

### 全连接图算法特点
- **完整性保证**: 计算所有文章对的相似度，构建完整的相似度矩阵
- **图论聚类**: 使用连通分量算法识别重复群组，避免传递性错误
- **SEO友好**: 每个群组保留最早发布的文章作为基准，保护SEO价值
- **智能分类**: 90天时间窗口，1000字最低门槛，确保检测质量

### SEO优化处理策略
- **高相似度 (≥0.8)**: 推荐301重定向 - 合并文章，删除重复版本
- **中等相似度 (0.5-0.8)**: 推荐Canonical标签 - 保留文章，标记主要版本
- **低相似度 (<0.5)**: 推荐内容差异化 - 通过内容补充实现独特性

### 自动生成配置文件
- **redirects.yaml**: Hugo 301重定向规则配置
- **canonical_mappings.json**: Canonical标签映射文件
- **content_differentiation.json**: 内容差异化建议
- **SEO_CONFIG_README.md**: 完整的实施指南文档

## ⚙️ 配置文件

### hugo_quality_standards.yml
主配置文件，包含：
- 权重分配设置
- Hugo模板标准
- SEO检测指标
- 内容深度标准
- 图片优化要求

### 自定义配置
可以修改配置文件来调整：
- 质量检测阈值
- 权重分配比例
- 分类映射规则
- 相似度检测参数

## 🛠️ 命令行选项

### 核心质量检测
```bash
python check_articles.py [path] [options]

参数:
  path                 要检测的文章文件或目录路径

选项:
  --config CONFIG      配置文件路径 (默认: hugo_quality_standards.yml)
  --output-dir DIR     报告输出目录 (默认: reports)
  --no-auto-fix        禁用Hugo模板自动修复
  --save-changes       保存修复后的文章到原文件

示例:
  python check_articles.py                                    # 检测默认目录
  python check_articles.py "article.md"                       # 检测单个文件
  python check_articles.py "articles/" --save-changes         # 检测并保存修改
  python check_articles.py "articles/" --no-auto-fix          # 只检测不修复
```

### 独立相似度检测 (v2.3)
```bash
python scripts/similarity_checker.py [directory] [options]

参数:
  directory            要检测的文章目录路径

核心选项:
  --config CONFIG      配置文件路径 (默认: ../hugo_quality_standards.yml)
  --threshold FLOAT    相似度阈值 (0.0-1.0, 默认: 0.5)
  --output OUTPUT      报告输出文件 (默认: similarity_report.md)
  --algorithm TYPE     检测算法: linear(线性) 或 graph(全连接图, 推荐)

处理选项:
  --auto-process       自动移动重复文章到duplicate_articles文件夹
  --dry-run            预览模式，不实际移动文件
  --window-days INT    检测时间窗口（天数，默认: 90)

SEO优化选项 (v2.3新增):
  --generate-config    生成SEO优化配置文件 (redirects.yaml, canonical_mappings.json等)
  --config-output-dir  配置文件输出目录 (默认: 当前目录)
  --simple             简化模式：输出精简的结果摘要，适合快速检查

高级选项:
  --compare FILE1 FILE2  对比两篇指定文章的相似度
  --debug              显示详细的比较过程和调试信息

示例:
  # v2.3 推荐用法 - 全连接图算法 + SEO配置生成
  python scripts/similarity_checker.py "articles/" --algorithm graph --generate-config

  # 简化模式 - 快速检查
  python scripts/similarity_checker.py "articles/" --simple --algorithm graph

  # 传统用法
  python scripts/similarity_checker.py "articles/" --auto-process --threshold 0.4

  # 对比两篇文章
  python scripts/similarity_checker.py --compare "article1.md" "article2.md"
```

### 🔧 模块化相似度系统 (v2.0)

新的模块化系统提供更好的维护性和扩展性：

```bash
# 进入模块化系统目录
cd similarity-detection

# 基本使用
python main.py "D:/path/to/articles"

# 使用简化模式
python main.py "D:/path/to/articles" --simple

# 使用图聚类算法
python main.py "D:/path/to/articles" --algorithm graph

# 对比两篇文章
python main.py --compare article1.md article2.md

# 自动处理相似文章（移动到分类文件夹）
python main.py "D:/path/to/articles" --auto-process

# 生成SEO优化配置文件
python main.py "D:/path/to/articles" --algorithm graph --generate-config

# 模块测试
python test_modules.py
```

**模块化优势:**
- 🧩 **模块化架构**: 23个独立模块，便于维护和升级
- 🔄 **向后兼容**: 完全兼容原始接口
- ⚡ **性能优化**: 更好的内存管理和并行处理
- 🛠️ **易于扩展**: 支持新算法和报告格式
- 📖 **详细文档**: 完整的使用和开发文档

## 📈 使用建议

### 推荐工作流程
1. **核心质量检测**: 使用主脚本检测文章质量
2. **查看质量报告**: 检查生成的详细报告和修复建议
3. **应用自动修复**: 使用自动生成的Front Matter修复代码
4. **手动优化**: 根据人工确认建议优化内容
5. **相似度检测**: 使用模块化系统或代理脚本进行批量相似度分析
6. **图片优化**: 参考图片指南文档进行图片优化
7. **重新检测**: 验证修改效果

### 🚀 新用户推荐
- **首次使用**: 建议使用代理脚本 `scripts/similarity_checker.py` 保持兼容性
- **高级用户**: 可直接使用模块化系统 `similarity-detection/main.py` 获得更好性能
- **开发者**: 使用模块化系统进行二次开发和算法扩展

### 最佳实践
- **分离关注点**: 使用专门工具处理专门问题
- **定期维护**: 定期运行质量检测和相似度检测
- **优先级管理**: 优先修复严重问题，再处理警告项目
- **文档参考**: 充分利用图片指南等独立文档
- **自动化优先**: 优先使用自动修复，减少人工重复工作
- **验证效果**: 修改后重新检测，确保改进有效

## 🔄 版本更新

### v2.3 全连接图算法版本 (当前版本) - 2025-09-15
- 🚨 **数学完整性突破** - 全连接图聚类算法确保零遗漏检测
- 🆕 **SEO优化增强** - 集成301重定向和Canonical标签自动生成
- 🆕 **智能配置文件生成** - 自动生成redirects.yaml、canonical_mappings.json等
- 🆕 **简化模式** - `--simple`参数提供精简输出，适合快速检查
- 🆕 **智能SEO决策系统** - 基于相似度自动推荐最佳处理策略
- 🆕 **两篇文章对比功能** - `--compare`参数支持指定文章对比
- ⚡ **算法优化** - 90天时间窗口，1000字门槛，提升检测质量

### v2.2 线性检测算法版本 - 2025-09-15
- 🚨 **修复重大误判问题** - 从495对相似文章降低到16对，准确率提升到87%+
- 🆕 **线性检测算法** - 最早文章vs其他文章，避免传递性分组错误
- 🆕 **SEO友好策略** - 保留最早文章，保护域名权重和外链价值
- 🆕 **差异化阈值** - 同类别0.5，跨类别0.7，精准去重
- 🆕 **智能时间识别** - 从文件名提取日期，支持多种格式
- 🆕 **按日期分类存储** - new-articles和old-articles按日期分文件夹
- ⚡ **性能优化** - 7天时间窗口，大幅提升检测效率

### v2.1 特性 (已保留)
- 🆕 **独立相似度检测工具** - 专门的批量相似度检测脚本
- 🆕 **图片分析指南文档** - 完整的图片优化标准和检查清单
- 🆕 **模块化设计** - 核心检测与专门工具分离

### v2.0 特性 (已保留)
- ✅ 智能Hugo模板修复
- ✅ Alt文本智能分析与修复建议
- ✅ TL;DR要点总结检测
- ✅ 增强型三级禁词检测
- ✅ 权重优化分配
- ✅ 中文友好界面和报告
- ✅ 多维度内容深度检测

### v1.0 基础功能 (已保留)
- ✅ 基础质量检测
- ✅ PQS v3检测标准
- ✅ 去重检测功能

## 📞 技术支持

### 常见问题
1. **模块导入失败** - 检查Python环境和依赖安装
2. **配置文件错误** - 验证YAML格式正确性
3. **编码问题** - 确保文件使用UTF-8编码
4. **权限问题** - 检查文件和目录访问权限

### 系统要求
- Python 3.7+
- 依赖包: pyyaml, sentence-transformers, scikit-learn, numpy
- 操作系统: Windows/Linux/macOS

---

**开发时间**: 2025-09-15
**版本**: v2.3 - 全连接图算法版本
**用途**: 专为手写Hugo文章设计的模块化质量检测工具

## 🔥 v2.3 重大突破

### 核心改进
1. **数学完整性突破** - 全连接图聚类算法确保零遗漏的相似关系识别
2. **SEO优化自动化** - 集成301重定向和Canonical标签自动生成
3. **智能决策系统** - 基于相似度自动推荐最佳处理策略
4. **配置文件生成** - 自动输出可直接使用的网站配置文件

### 功能提升
- 🔗 **全连接图算法**: 数学完整性保证，零遗漏检测
- 🚀 **SEO配置自动生成**: redirects.yaml、canonical_mappings.json等
- 📊 **简化模式**: 精简输出适合快速检查
- 🎯 **智能策略推荐**: 301重定向 vs Canonical标签 vs 内容差异化
- ⚡ **对比功能**: 支持两篇指定文章相似度对比
- 🛡️ **SEO保护**: 智能选择保留策略，保护域名权重

### v2.3 推荐用法
```bash
# 完整检测 + SEO配置生成 + 简化输出
python scripts/similarity_checker.py "articles/" --algorithm graph --generate-config --simple

# 生成的配置文件直接可用于网站优化
ls *.yaml *.json *.md  # redirects.yaml, canonical_mappings.json, SEO_CONFIG_README.md
```