# 生成器对接契约（必须满足）

## Front‑matter 字段（必填）
- `title` / `date` / `author`
- `category`（slug，如 `smart-plugs`）
- `keyword`（主关键词，用于密度检测与 JSON‑LD）
- `featured_image`（生成时就写入）
- `images[]` 与 `image_meta[]`（每张 `alt/caption/credit/license`）

## 正文必备段落
- `## Summary`（结论先行）
- `## Comparison Table`（≥ 6 行）或 `## Who should buy...`
- `## Compatibility Matrix`
- `## Installation & Troubleshooting`
- `## FAQ`（≥ 5 条）
- `## Sources`（≥ 2）与 `## Disclosure`（首屏也要有披露短句）

## JSON‑LD
- 注入 `Article`；如有 FAQ，使用 `FAQPage` 并在 Article 中以 `hasPart` 关联（可按模板渲染）。

## 图片
- 至少 1×封面 + 2×插图；ALT 8–120 字符，包含实体 token（见 config/pqs_config.yml）。

## 失败处理
- 若生成不达标，**不得跳过**；交由 `scripts/iterative_refine.py` 自动修补，最多 3 轮；仍未达标则开 issue。
