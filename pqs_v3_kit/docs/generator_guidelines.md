# 生成脚本改造说明（保证“生成即合格”）

## 必备输出结构（模板段）
1) **结论卡（Summary/Who/Why）**
2) **对比表**（≥ 6 行；协议/功率/网关需求/本地控制/保修/适用人群）
3) **兼容性矩阵**（Matter/Thread/Zigbee/HomeKit/Alexa/GA）
4) **安装与排错**（Top 5 场景）
5) **FAQ（5 条）**（严格对应用户意图）
6) **Sources**（品牌规格/标准组织/认证/固件备注）
7) **Disclosure**（联盟披露：首屏/文末）
8) **JSON‑LD**（`Article` + 可选 `FAQPage`）

## 图片策略
- 至少 1×封面 + 2×正文；优先“实体图/示意图/自制信息卡”；
- ALT 必须包含实体 token；Caption 说明“示意/来源/勘误方式”；
- 若图库 API 不可用，调用 `smart_image_manager` 生成信息图兜底。

## 生成时“硬校验”
- 主关键词密度 ≤ 2.5%；
- 实体覆盖 ≥3；
- Sources ≥2 个外链；
- 自动注入 JSON‑LD（模板见 `/templates/`），并把 `featured_image/images[]/image_meta[]` 写入 front‑matter。
