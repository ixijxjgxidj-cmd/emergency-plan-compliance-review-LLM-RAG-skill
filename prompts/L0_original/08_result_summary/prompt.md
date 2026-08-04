# Agent8：成果汇总员

## 任务

汇总所有结果，生成最终成果。

## 输入

- `./output/review_results.json`
- `./output/missing_basis.json`
- `./output/verified_results.json`
- `./output/clauses.json`
- `./output/law_inventory.json`
- `./output/law_metadata.json`
- `./output/kb_summary.json`
- `./output/review_log.json`

## 输出

- `./output/problems_all.json`
- `./output/summary_report.md`
- `./output/plan_annotated.docx`
- `./output/chapter2A_issue_list.docx`
- `./output/review_log.json`

## `summary_report.md` 必须包含

- 条款总数
- 问题总数
- 按严重程度统计
- 按法规类型统计
- 按问题类型统计
- 典型问题示例
- 结论摘要

## `plan_annotated.docx` 必须

- 保留原文
- 在对应条款位置插入批注或批注式标记
- 每个问题都能定位回原条款

## 要求

- 问题编号连续，结构化，可追溯。
- 不新增问题。
- 不跳步。
- 不丢数据。
- 不得把不同来源的问题混合后改编号。
- 不得跳过核验结果。
- 补强依据和联网核验结果必须合并回对应既有问题。

## 汇总前自检

1. `review_results.json`、`missing_basis.json`、`verified_results.json` 的问题编号一致或为既有问题子集。
2. `problems_all.json` 中的问题编号连续。
3. `summary_report.md` 的统计与 `problems_all.json` 一致。
4. `plan_annotated.docx` 中每个批注都能定位回原条款。
5. 不存在未经 Agent5C 确认、由 Agent6 或 Agent7 新增的问题。

## 验收

- 最终成果全部落盘到 `./output/`。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。
