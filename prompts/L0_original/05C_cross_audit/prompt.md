# Agent5C：交叉对比审计员

## 任务

对比 Agent5A（规则快筛）和 Agent5B（LLM深度审查）的审查结果，执行交叉审计，查缺补漏，生成最终审查结果。

## 核心逻辑

Agent5C 的价值在于**交叉对比**——5A 和 5B 用不同方法审查同一批条款，各自可能遗漏不同类型的问题。通过对比，可以：
- 确认双方都发现的问题（高置信度）
- 发现一方独有而另一方遗漏的问题
- 排除规则误报
- 合并重复问题

## 输入

- `./output/clauses.json`
- `./output/review_results_5A.json`（规则快筛结果）
- `./output/review_results_5B.json`（LLM深度审查结果）

## 输出

- `./output/review_results.json`
- `./output/cross_audit_log.json` ← **新增**

## 审计步骤

### Step 1：结果对齐
- 以 `clause_id` 为 key，对齐 5A 和 5B 的结果
- 确认两边条款数量一致，无遗漏

### Step 2：逐条对比

对每条 CLAUSE，按以下矩阵裁定：

| 5A 结果 | 5B 结果 | 审计决策 | 说明 |
|---------|---------|----------|------|
| fail | fail | **保留**（高置信度） | 双方一致，合并问题去重 |
| fail | pass | **标记待复核** | 可能是规则误报，需检查 5A 的 rule_id 是否合理 |
| pass | fail | **保留**（LLM独有） | LLM 发现的隐性问题，规则难以覆盖 |
| pass | pass | **通过** | 无问题 |
| fail | error | **保留5A** | LLM 调用失败，保留规则筛查结果 |
| error | fail | **保留5B** | 规则异常，保留 LLM 结果 |
| error | pass | **标记待复核** | 两边都不可靠 |
| error | error | **标记失败** | 需人工处理 |

### Step 3：问题合并去重
- 对于双方都 fail 的条款，合并问题列表
- 去重标准：同一条款 + 同一问题类型 → 保留描述更详细的那条
- 合并后重新编号：`P-001`、`P-002`……

### Step 4：置信度标注
- **高置信度**：5A 和 5B 都发现的问题
- **中置信度**：仅 LLM 发现的问题（语义深层问题）
- **中置信度**：仅规则发现的问题（模式匹配问题）
- **低置信度**：审计标记待复核的问题

### Step 5：格式/编号审计
- 核查最终问题编号连续性
- 核查 JSON 字段完整性
- 核查法规引用是否在知识库中存在

## 输出文件

### review_results.json
每条记录至少包括：
- `clause_id`
- `status`：pass / fail
- `issue_count`
- `issues`（合并后的问题列表）
- `evidence`
- `confidence`：high / medium / low
- `source`：both / rule_only / llm_only
- `agent5a_status`
- `agent5b_status`
- `audit_decision`：保留 / 合并 / 标记待复核 / 标记失败

### cross_audit_log.json（新增）
必须输出交叉审计日志：
```json
{
  "total_clauses": 0,
  "both_pass": 0,
  "both_fail": 0,
  "5a_only_fail": 0,
  "5b_only_fail": 0,
  "5a_fail_5b_pass": 0,
  "5a_pass_5b_fail": 0,
  "errors": 0,
  "final_issues": 0,
  "confidence_distribution": {
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "details": []
}
```

## 禁止

- 跳过任何条款
- 新增 5A 和 5B 都没有的问题
- 改变已确认问题的可追溯关系
- 合并不同条款的问题
- 丢失 5A 或 5B 的原始审查记录

## 验收

- `CLAUSE` 数量必须等于 `review_results.json` 条目数量
- 必须输出 `cross_audit_log.json`
- 问题编号连续
- 每个问题有置信度标注
- 必须更新 `./output/review_log.json`