# PQS v3 落地包（质量检查 + 生成改造 + 迭代闭环）
生成时间：2025-09-10 16:16

本包用于把你的站点生产线升级为：**每天强制 2–4 篇 → 不达标自动修补 → 直到达标才发布**。

## 目录
- docs/pqs_v3_spec.md —— 质量标准（硬闸门 + 100 分制）
- docs/scoring_rubric_table.md —— 可打印评分表（逐项打勾/打分）
- docs/generator_guidelines.md —— 内容生成脚本改造说明（结构/图片/证据/Schema）
- docs/failure_playbook.md —— 常见不达标现象与修复（自动 + 人工）
- docs/workflow_guide.md —— GitHub Actions：生成 → 修补 → 质检 → 发布
- scripts/quality_check_pqs_v3.py —— 质量检查器（严格模式）
- scripts/iterative_refine.py —— 自动修补脚本（图片/结构/Schema/证据占位）
- scripts/generator_contract.md —— 生成器对接契约（必须输出的字段/段落/Front‑matter）
- scripts/generator_hooks_stub.py —— 生成器挂钩示例（把结构化段落/JSON‑LD/图片回写）
- templates/article_jsonld.jsonld / faq_jsonld.jsonld —— 结构化数据模板
- templates/markdown_injections.md —— 对比表/兼容矩阵/安装排错等标准段落模板
- config/pqs_config.yml —— 可调阈值与实体词
- config/evidence_seeder.json —— 证据链接种子（按类目填充）
- workflows/daily_content_pqs_v3.yml —— GitHub Actions（每日 2–4 篇 + 迭代）

## 快速开始
1) 将 `scripts/`、`templates/`、`config/` 拷贝到你的仓库（建议根目录）。
2) 把 `workflows/daily_content_pqs_v3.yml` 复制为 `.github/workflows/daily_content_pqs_v3.yml`。
3) 在仓库 Settings → Variables 设置：`CI_QUALITY_STRICT=true`（建议）。
4) 触发一次工作流：它会**生成 2–4 篇草稿 → 自动修补 → 质检**；只有通过才提交；未过会上传 `pqs_report.json` 并开 issue。





## 一、交付物（可下载 ZIP）

- `README.md` —— 套件总览与快速开始
- `docs/`
  - `pqs_v3_spec.md` —— **硬闸门 + 100 分制** 规范
  - `scoring_rubric_table.md` —— 可打印评分表
  - `generator_guidelines.md` —— 生成脚本改造要点
  - `failure_playbook.md` —— 不达标→修复对照表
  - `workflow_guide.md` —— **生成→修补→质检→发布** 流程
- `scripts/`
  - `quality_check_pqs_v3.py` —— 质量检查器（严格）
  - `iterative_refine.py` —— 自动修补（图片/结构/Schema/证据）
  - `generator_contract.md` —— 生成器**对接契约**（字段/段落/Front‑matter）
  - `generator_hooks_stub.py` —— 生成器挂钩示例
- `templates/`
  - `article_jsonld.jsonld`、`faq_jsonld.jsonld` —— JSON‑LD 模板
  - `markdown_injections.md` —— 对比表/兼容矩阵/安装排错模板段
- `config/`
  - `pqs_config.yml` —— 阈值 & 实体词 & 权重
  - `evidence_seeder.json` —— 证据链接种子（按类目）
- `workflows/`
  - `daily_content_pqs_v3.yml` —— GitHub Actions 工作流
- `samples/top_picks_example.json` —— 示例关键词输入

> 下载地址：**见左侧聊天区提供的 ZIP 链接**。

------

## 二、如何落地（5 分钟）

1. 复制 `scripts/`、`templates/`、`config/` 到仓库根目录；
2. 将 `workflows/daily_content_pqs_v3.yml` 放入 `.github/workflows/`；
3. 仓库 **Settings → Variables**：添加 `CI_QUALITY_STRICT=true`；
4. 手动触发工作流：会生成 2–4 篇草稿 → 自动修补 ≤3 轮 → 质检；**通过才提交**；未过会上传 `pqs_report.json` 并自动开 issue；
5. 把你的生成器接入 `generator_contract.md` 所需的字段与段落，或先用 `iterative_refine.py` 兜底修补。

------

## 三、质量检查（要点）

- **硬闸门**（任一不满足即失败）：
  - 有 `featured_image` + 正文 ≥2 插图；所有 ALT 8–120 字符，并包含**实体 token**（如 Matter/Thread/Zigbee/本地控制/功率等）；
  - **证据外链 ≥2**（品牌规格/标准组织/认证数据库），且 200 可达；
  - 有 `Article` JSON‑LD；若含 FAQ → `FAQPage` 并 `hasPart` 关联；
  - 有对比/框架（对比表≥6行 或 `ItemList`≥3项 或 “谁该买/不该买/替代品”）；
  - 不得宣称“实测”；如出现“测试/评测”，必须有 `Methodology/How we evaluate`；
  - 主关键词密度 ≤2.5%，严禁直译堆叠；
  - **实体覆盖 ≥3**（协议/功率/本地控制/是否需网关/2.4G 等）。
- **打分**（≥85 发布）：深度30 + 证据20 + 图片15 + 结构15 + 可读性10 + 合规10。

------

## 四、生成端改造（“生成即合格”）

- 必备段落：Summary → Comparison Table → Compatibility Matrix → Installation & Troubleshooting → FAQ(≥5) → Sources → Disclosure；
- 图片策略：至少 1×封面 + 2×正文；图库失败则调用信息图兜底；ALT 必含实体 token；
- 自动注入 JSON‑LD；把 `featured_image/images[]/image_meta[]` 写入 front‑matter；
- 内压硬校验：关键词密度≤2.5%、实体覆盖≥3、Sources≥2。

------

## 五、常见不达标 → 自动修补

- 无图/少图 → **占位 + 信息图兜底**（写回 front‑matter）；
- 无证据 → 从 `evidence_seeder.json` 注入 2–3 条权威外链 + `## Sources`；
- 无结构化数据 → 渲染 `templates/*jsonld` 注入；
- 对比表/兼容矩阵/安装排错/FAQ 缺失 → 用 `markdown_injections.md` 补齐；
- 关键词堆叠/实体不足 → 改写/插入“兼容矩阵”；
- 披露缺失 → 插入联盟披露（中英）。

------

## 六、策略说明

- **不降低阈值**：PQS 只加严不放松；
- **连续失败的定义**：3 轮修补仍未过 → 自动开 issue 标注“模板/生成器需升级”；
- **目标**：提升“可验证性/结构化/可视化”，减少“规模化模板导购”的风险，确保 AdSense 审核通过并长期稳态变现。