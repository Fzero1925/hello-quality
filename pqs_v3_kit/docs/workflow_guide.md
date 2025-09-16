# 工作流说明（daily_content_pqs_v3）
1) 生成 2–4 篇草稿（生成器自行决定主题/从关键词引擎读取）。
2) 运行 `iterative_refine.py` 自动修补（最多 3 轮）。
3) 跑 `quality_check_pqs_v3.py`：通过则提交；未过上传 `pqs_report.json` + 开 issue 标注失败原因。
4) artifacts：保存草稿、报告与日志，便于人工复盘/改模板。
