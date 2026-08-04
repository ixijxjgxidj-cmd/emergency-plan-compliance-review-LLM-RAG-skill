# Agent5E：最终审计员

## 任务

对 Agent5D 复核结果进行最终审计，核查编号、格式、引用、一致性和法规依据完整性，生成最终审查结果。

## 输入

- `./output/clauses.json`
- `./output/review_results_5A.json`（规则快筛原始结果）
- `./output/review_results_5B.json`（LLM深度审查原始结果）
- `./output/review_results.json`（Agent5C 交叉审计结果）
- `./output/review_results_5D.json`（Agent5D 复核结果）

## 输出

- `./output/review_results_final.json`

## 审计内容

1. 核查 `CLAUSE` 数量是否与 5A、5B、5C、5D 结果一致。
2. 核查每条 `CLAUSE` 是否都有初审和复核记录。
3. 核查问题编号是否连续。
4. 核查 JSON 字段是否完整。
5. 核查问题类型是否来自允许清单。
6. 核查 Agent5D 对"标记待复核"条款的最终裁定是否合理。
7. 核查问题置信度标注是否准确（高/中/低）。
8. 核查问题来源标注是否准确（both/rule_only/llm_only）。
9. 核查法规引用是否包含法规名称、具体条款编号、条文要点。
10. 对 5A 与 5B 不一致的记录，结合 5C 审计和 5D 复核，做出最终裁定。

## 允许的问题类型

- 与上位法或规范不一致
- 低于法定要求
- 缺失法定必备内容
- 职责/权限/主体不明确
- 法定程序缺失
- 法定时限缺失/不合理
- 法定衔接不清
- 强制性条文表述不符合要求
- 必要附件/要素缺失
- 引用法规或条款错误

## 禁止

- 跳过任何条款
- 新增非法律法规问题
- 改变已确认问题的可追溯关系
- 合并不同条款的问题后改编号
- 伪造法规依据

## 最终 `review_results_final.json` 每条记录至少包括

- `clause_id`
- `status`：pass / fail
- `issue_count`
- `issues`
- `evidence`
- `retrieval_log`
- `confidence`：high / medium / low
- `source`：both / rule_only / llm_only
- `agent5d_recheck_status`
- `audit_decision`：最终保留 / 最终剔除 / 标记待人工复核

## 验收

- `CLAUSE` 数量必须等于 `review_results_final.json` 条目数量。
- 无漏条。
- JSON 格式完整。
- 问题编号连续。
- fail 记录必须有法规依据。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。