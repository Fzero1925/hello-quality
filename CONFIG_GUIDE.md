# 配置文件说明指南

## 主配置文件: hugo_quality_standards.yml

这是质量检测工具的核心配置文件，整合了所有检测标准和规则配置。

### 📁 配置文件结构

```yaml
hugo_quality_standards.yml          # 主配置文件
├── hugo_template_standards         # Hugo模板标准
├── content_depth_standards         # 内容深度标准 (40%权重)
├── seo_technical_standards         # SEO技术标准 (20%权重)
├── content_structure_requirements  # 内容结构要求 (15%权重)
├── readability_requirements        # 可读性要求 (10%权重)
├── adsense_compliance             # AdSense合规性 (10%权重)
└── report_settings                # 报告生成设置
```

## 🎯 权重分配系统

### 当前权重分配 (v2.0)
```yaml
scoring_weights:
  content_depth: 40      # 内容深度质量
  seo_technical: 20      # SEO技术指标
  content_structure: 15  # 内容结构完整
  readability: 10        # 可读性指标
  adsense_compliance: 10 # AdSense合规性
  reserved: 5           # 预留扩展空间
```

**注意**: 图片权重已从之前版本移除，权重已重新分配到其他维度以提高检测精确度。

## 📋 详细配置说明

### 1. Hugo模板标准 (hugo_template_standards)

#### Front Matter必填字段
```yaml
required_fields:
  - title        # 文章标题
  - description  # 文章描述
  - date         # 发布日期
  - categories   # 文章分类
  - author       # 作者信息
```

#### 推荐字段
```yaml
recommended_fields:
  - slug         # URL路径
  - tags         # 标签
  - keywords     # 关键词
  - featured_image  # 特色图片
```

#### 分类映射 (中文→英文)
```yaml
category_mapping:
  "智能插座": "smart-plugs"
  "智能开关": "smart-switches"
  "扫地机器人": "robot-vacuums"
  "智能门锁": "smart-locks"
  # ... 更多映射规则
```

### 2. 内容深度标准 (40%权重)

#### 按文章类型分层检测
```yaml
article_types:
  review:                    # 评测类文章
    min_word_count: 2500
    max_word_count: 4000
    required_sections:
      - "产品规格"
      - "性能测试"
      - "价格分析"

  buying_guide:             # 购买指南
    min_word_count: 3000
    max_word_count: 5000
    required_sections:
      - "预算建议"
      - "品牌对比"
      - "推荐理由"

  comparison:               # 对比分析
    min_word_count: 2000
    max_word_count: 3500
    required_elements:
      - "对比表格"
      - "优缺点分析"
```

### 3. SEO技术标准 (20%权重)

#### 标题优化
```yaml
title_optimization:
  min_length: 50           # 最短50字符
  max_length: 60           # 最长60字符
  require_year: true       # 必须包含年份
  require_target_keyword: true  # 必须包含目标关键词
```

#### 描述优化
```yaml
description_optimization:
  min_length: 150          # 最短150字符
  max_length: 160          # 最长160字符
  keyword_density: 1.2     # 关键词密度1.2%
```

#### 内部链接要求
```yaml
internal_linking:
  min_internal_links: 3    # 最少3个内部链接
  max_internal_links: 8    # 最多8个内部链接
  descriptive_anchor_text: true  # 使用描述性锚文本
```

### 4. 内容结构要求 (15%权重)

#### 标题层级结构
```yaml
heading_structure:
  h1_count: 1              # 只能有1个H1
  min_h2_count: 4          # 至少4个H2
  max_h2_count: 8          # 最多8个H2
  logical_hierarchy: true   # 逻辑清晰的层次
```

#### TL;DR检测配置
```yaml
tldr_requirements:
  enabled: true            # 启用TL;DR检测
  required: true           # 要求必须有TL;DR
  position: "beginning"    # 位置：开头
  min_points: 3           # 最少3个要点
  max_points: 8           # 最多8个要点
  keywords:               # 识别关键词
    - "TL;DR"
    - "TLDR"
    - "要点总结"
    - "核心要点"
    - "文章要点"
    - "快速总结"
    - "关键信息"
    - "重点摘要"
```

### 5. AdSense合规性 (10%权重)

#### 增强型禁词检测
```yaml
forbidden_phrases:
  # 严重违规 (导致检测失败)
  critical:
    - "click here"
    - "buy now"
    - "act now"
    - "limited time only"

  # 警告级别 (影响评分)
  warning:
    - "must buy"
    - "don't miss"
    - "hurry up"
    - "while supplies last"

  # 建议避免 (轻微影响)
  suggestion:
    - "revolutionary"
    - "breakthrough"
    - "life-changing"
    - "game-changer"
```

#### 来源验证设置
```yaml
source_verification:
  enabled: false           # 手写文章暂不需要来源验证
  note: "专注于质量检测，暂不验证来源"
```

## 🔧 自定义配置

### 修改检测阈值
```yaml
# 在对应部分修改数值
min_word_count: 1500      # 调整最小字数要求
similarity_threshold: 0.30  # 调整相似度阈值
max_keyword_density: 2.5   # 调整关键词密度上限
```

### 修改权重分配
```yaml
scoring_weights:
  content_depth: 35       # 降低内容深度权重
  seo_technical: 25       # 增加SEO技术权重
  content_structure: 15   # 保持结构权重
  readability: 15         # 增加可读性权重
  adsense_compliance: 10  # 保持合规权重
```

### 添加新的分类映射
```yaml
category_mapping:
  "新分类中文": "new-category-english"
  "另一分类": "another-category"
```

### 调整Alt文本检测
```yaml
alt_text_requirements:
  min_length: 15          # Alt文本最短长度
  max_length: 125         # Alt文本最长长度
  require_keywords: true   # 必须包含关键词
  banned_words:           # 禁用词汇
    - "image"
    - "picture"
    - "photo"
```

## 📊 报告配置

### 报告生成设置
```yaml
report_settings:
  language: "zh-CN"               # 中文报告
  output_format: "markdown"       # Markdown格式
  include_fix_suggestions: true   # 包含修复建议
  include_auto_fix_code: true     # 包含自动修复代码
  timestamp_format: "%Y-%m-%d %H:%M:%S"  # 时间格式
  reports_directory: "reports"    # 报告输出目录
```

## 🚨 配置注意事项

### 1. YAML格式要求
- 使用UTF-8编码保存
- 注意缩进（使用空格，不要使用Tab）
- 字符串包含特殊字符时使用引号

### 2. 数值范围建议
- 权重总和应为100%
- 字数要求应符合实际需求
- 阈值设置不宜过严或过松

### 3. 向后兼容
- 删除配置项前请确认不会影响现有功能
- 新增配置项应提供默认值
- 重要修改应备份原配置文件

### 4. 性能考虑
- 检测规则过多会影响性能
- 相似度检测阈值过低会产生过多结果
- 报告生成内容过详细会影响生成速度

## 🔄 配置更新历史

### v2.0 主要变更
- ✅ 整合多个配置文件到单一文件
- ✅ 重新分配权重（移除图片权重）
- ✅ 新增TL;DR检测配置
- ✅ 增强型禁词三级分类
- ✅ 来源验证设置为禁用
- ✅ Alt文本检测标准优化

### v1.0 基础配置
- ✅ 基本质量检测标准
- ✅ PQS v3检测门槛
- ✅ 简单相似度检测

---

**配置文件位置**: `hugo_quality_standards.yml`
**修改建议**: 测试环境先验证，再应用到生产环境
**备份提醒**: 修改前请备份原配置文件