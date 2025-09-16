# 📊 模块化相似度检测系统

重构后的相似度检测工具，将原有的大型脚本拆分为独立的模块，便于维护、扩展和问题定位。

## 🏗️ 目录结构

```
similarity-detection/
├── main.py                          # 主入口文件
├── test_modules.py                   # 模块测试脚本
├── config/                           # 配置文件目录
│   ├── similarity_config.yml         # 主配置文件
│   ├── algorithms.yml                # 算法参数配置
│   └── uniqueness.yml                # 原有配置文件
├── core/                             # 核心功能模块
│   ├── similarity_engine.py          # 相似度检测引擎
│   ├── article_analyzer.py           # 文章分析器
│   ├── comparison_algorithms.py      # 算法接口
│   └── result_processor.py           # 结果处理器
├── algorithms/                       # 算法模块
│   ├── tfidf_similarity.py          # TF-IDF算法
│   ├── simhash_similarity.py        # SimHash算法
│   ├── semantic_similarity.py       # 语义相似度算法
│   └── linear_comparison.py         # 线性比较算法
├── reporters/                        # 报告生成器
│   ├── markdown_reporter.py         # Markdown报告生成
│   ├── simple_reporter.py           # 简化报告生成
│   └── seo_config_generator.py      # SEO配置生成
└── utils/                            # 工具模块
    ├── file_handler.py              # 文件处理工具
    ├── text_processor.py            # 文本处理工具
    └── date_helper.py               # 日期处理工具
```

## 🚀 快速开始

### 基本使用

```bash
# 切换到模块化目录
cd similarity-detection

# 检测指定目录的文章相似度
python main.py /path/to/articles

# 使用简化模式
python main.py /path/to/articles --simple

# 使用图聚类算法
python main.py /path/to/articles --algorithm graph

# 对比两篇文章
python main.py --compare article1.md article2.md
```

### 高级功能

```bash
# 自动处理相似文章（移动到分类文件夹）
python main.py /path/to/articles --auto-process

# 预览模式（不实际移动文件）
python main.py /path/to/articles --auto-process --dry-run

# 生成SEO优化配置文件
python main.py /path/to/articles --algorithm graph --generate-config

# 自定义参数
python main.py /path/to/articles --threshold 0.8 --window-days 30
```

## 🧩 模块说明

### 核心模块

- **SimilarityEngine**: 主控制器，协调各个模块完成相似度检测
- **ArticleAnalyzer**: 负责文章扫描、解析和信息提取
- **ResultProcessor**: 处理检测结果，执行文件移动等操作

### 算法模块

- **TFIDFSimilarity**: 基于TF-IDF和余弦相似度的算法
- **SimHashSimilarity**: 基于SimHash的快速近似匹配
- **SemanticSimilarity**: 基于AI语义理解的高精度检测
- **LinearComparison**: 优化的线性时序比较算法

### 报告模块

- **MarkdownReporter**: 生成详细的Markdown分析报告
- **SimpleReporter**: 生成简化的快速查看报告
- **SEOConfigGenerator**: 生成SEO优化配置文件

### 工具模块

- **FileHandler**: 文件和目录操作工具
- **TextProcessor**: 文本处理和标准化工具
- **DateHelper**: 日期解析和处理工具

## ⚙️ 配置说明

### 主配置文件 (config/similarity_config.yml)

```yaml
similarity_detection:
  similarity_threshold: 0.7           # 相似度阈值
  comparison_window_days: 90          # 比较时间窗口
  min_content_length: 1000           # 最小内容长度

algorithms:
  tfidf:
    title_weight: 0.3               # 标题权重
    content_weight: 0.7             # 内容权重

  simhash:
    hamming_threshold: 16           # 汉明距离阈值

  semantic:
    similarity_threshold: 0.86      # 语义相似度阈值
    embedding_model: 'all-MiniLM-L6-v2'
```

## 🧪 测试和验证

运行模块测试验证功能完整性：

```bash
cd similarity-detection
python test_modules.py
```

预期输出：
```
🚀 Starting modular structure functionality tests...

🧪 Testing basic module imports...
  ✅ Utils modules imported successfully
  ✅ Algorithm modules imported successfully
  ✅ Reporter modules imported successfully
  ✅ Core modules imported successfully

🧪 Testing module instantiation...
  ✅ Utils classes instantiated successfully
  ✅ Algorithm classes instantiated successfully
  ✅ Reporter classes instantiated successfully
  ✅ Core classes instantiated successfully

🧪 Testing basic functionality...
  ✅ Text normalization: ...
  ✅ Date extraction: ...
  ✅ TF-IDF similarity calculation: ...
  ✅ Report statistics generation: ...

📊 Test Results: 3/3 tests passed
🎉 All tests passed! Modular structure is functional.
```

## 🔧 扩展和定制

### 添加新算法

1. 在 `algorithms/` 目录创建新的算法文件
2. 实现 `calculate_similarity()` 方法
3. 在 `core/comparison_algorithms.py` 中注册新算法

### 添加新报告格式

1. 在 `reporters/` 目录创建新的报告生成器
2. 实现标准的报告生成接口
3. 在 `main.py` 中添加命令行选项

### 自定义文本处理

在 `utils/text_processor.py` 中扩展文本处理功能，支持：
- 自定义正则表达式
- 特定语言的处理规则
- 领域特定的术语标准化

## 📈 性能优化

- **算法选择**: 根据数据集大小选择合适的算法
- **缓存机制**: 利用SimHash和语义嵌入缓存
- **并行处理**: 配置文件中启用并行处理（实验性）
- **内存管理**: 大数据集时使用稀疏矩阵

## 🔄 向后兼容

模块化系统保持与原始 `similarity_checker.py` 的完全兼容：
- 相同的命令行接口
- 相同的配置文件格式支持
- 相同的输出格式

## ⚠️ 故障排除

### 常见问题

1. **导入错误**: 确保在 `similarity-detection` 目录中运行脚本
2. **依赖缺失**: 安装所需的Python包
3. **配置错误**: 检查配置文件语法和路径

### 调试模式

```bash
python main.py /path/to/articles --debug
```

### 日志信息

模块化系统提供详细的进度输出和错误信息，便于问题定位。

## 📋 未来规划

- [ ] 增加更多相似度算法
- [ ] 支持更多文件格式
- [ ] Web界面和API接口
- [ ] 分布式处理支持
- [ ] 机器学习模型集成

---

*模块化重构完成时间: 2025-09-16*
*工具版本: v2.0.0*