# Agent5C：交叉对比审计员

## 任务

对比 Agent5A（规则快筛）与 Agent5B（LLM 深度审查）结果，交叉审计、查缺补漏，生成统一的核心审查结果。

5A 与 5B 用不同方法审查同一批条款，各自会遗漏不同类型的问题。交叉对比用于：确认双方共识问题（高置信度）、捞出一方独有问题、排除规则误报、合并重复问题。

## 输入

- `./output/clauses.json`
- `./output/review_results_5A.json`
- `./output/review_results_5B.json`
- `./output/law_metadata.json`（**依据门禁的白名单**：`reference` 必须能在此精确匹配）
- `./output/kb_gap_report.json`（5A 记录的依据缺口，用于区分"预案问题"与"知识库缺文件"）

## 输出

- `./output/review_results.json`
- `./output/cross_audit_log.json`
- `./output/rejected_problems.json`（依据不合法被移出的候选问题，交付物之一）

## 审计步骤

### Step 1 结果对齐

以 `clause_id` 为 key 对齐；确认两边条款数一致，缺失即报错并停止，不得跳过。

### Step 2 逐条裁定

| 5A | 5B | 决策 | 说明 |
|----|----|------|------|
| fail | fail | **保留**（高置信度） | 合并问题并去重 |
| fail | pass | **标记待复核** | 检查 5A 的 `rule_id` 是否合理、是否有条文依据 |
| pass | fail | **保留**（LLM 独有） | 规则难覆盖的隐性问题 |
| pass | pass | **通过** | — |
| fail | error | **保留 5A** | LLM 调用失败 |
| error | fail | **保留 5B** | 规则异常 |
| error | pass | **标记待复核** | 两边都不可靠 |
| error | error | **标记失败** | 交 5D/人工处理 |

### Step 3 依据合法性门禁（**在合并去重之前执行**）

这一步是硬门禁，不是标注。逐条检查每个候选问题：

1. `reference` 能否在 `law_metadata.json` 中按 `law_name` 精确匹配到一条记录？
2. 该记录的 `usable_for_review` 是否为 `true`？
3. `article` 是否为具体条号，`clause_text` 是否 ≥30 字且能在知识库中找到对应原文？

**三项全过 → 进入合并流程。任一不过 → 移出问题清单**，写入 `./output/rejected_problems.json`，记 `reject_reason`（`reference_not_in_kb` / `law_unusable` / `no_article` / `no_clause_text` / `text_not_found_in_kb`），并同步在 `kb_gap_report.json` 中登记一条依据缺口。

被移出的问题**不占用 `P-` 编号**，不进入 `review_results.json`，不流向 5D/5E/6/7。

> 为什么必须是"移出"而不是"降为低置信度"：实跑中 52 个问题里 34 个引用了知识库外的法规（《危险化学品安全管理条例》《GB/T 29639》《GB 30077》《突发环境事件应急管理办法》）。当时只把它们标为低置信度继续下传，结果 Agent6 花 36 次复核标 `insufficient_basis_outside_kb`、Agent7 花 27 次联网核验标 `unverified`，最终报告里 65% 的问题是不成立的——审查结论被无依据条目稀释，用户无法分辨哪 18 条是真的。**无依据的问题不是低置信度问题，它不是问题。**

### Step 4 问题合并去重

**第一层：同条款内合并**

- 同一 `clause_id` + 同一 `type` + 同一 `reference`+`article` → 同一问题，保留描述更详细的一条，另一条记入 `merged_from`。
- 同一 `clause_id` + 同一 `type` 但依据不同法规 → 两个问题，均保留。

**第二层：跨条款同因归并（必做）**

同一 `rule_id`（或同一 `type`+`reference`+`article` 组合）在 **3 条以上** CLAUSE 上产生实质相同的描述时，归并为**一个**问题，标 `finding_scope: systemic`，`affected_clauses` 列出全部条款号，`clause_count` 记条款数。描述改写为条款级共性表述，不再逐条重复。命中条款数不足 3 条的问题标 `finding_scope: clause_level`，字段口径一致（`affected_clauses` 仍为数组，单条款填单元素）。

> 实跑数据：52 个问题里只有 17 个不同描述，最极端的一条描述重复 19 次（全部来自同一条规则）。按本规则归并后，52 条 → 约 10 个真正不同的发现。逐条罗列同一个共性缺陷，会让"1 个系统性问题"看起来像"19 个问题"，严重程度分布和整改优先级全部失真。

**第三层：编号**

合并后统一重排 `P-001`、`P-002`……每条保留 `origin`（`5A:P-012` / `5B:P2-007`）与 `merged_from` 以维持可追溯。

### Step 5 置信度标注

- **高**：5A 与 5B 都发现，且依据条文精确到条号。
- **中**：仅一方发现，依据充分（`reference`+`article`+`clause_text` 齐备）。
- **低**：标记待复核，或依据法规 `effective_status` 为"已修订/待核实"。

注意：`reference_not_in_kb` 已在 Step 3 被移出，不再作为"低置信度"的成因。

### Step 6 依据状态与格式审计

- 核查引用法规的 `effective_status`；已废止/已修订 → 标 `basis_status_warning`。
- 核查编号连续性与字段完整性。
- 统计 Step 3 的移出数量，写入 `cross_audit_log.json` 的 `rejected_count`。

## review_results.json 每条记录至少包括

- `clause_id`
- `status`：pass / fail / error
- `issue_count`
- `issues`（合并后，含 `origin`、`merged_from`、`finding_scope`、`affected_clauses`、`clause_count`、`article`、`clause_text`、`suggestion`）
- `evidence`
- `confidence`：high / medium / low
- `source`：both / rule_only / llm_only
- `agent5a_status`、`agent5b_status`
- `audit_decision`：保留 / 合并 / 标记待复核 / 标记失败 / 通过

每个 issue 的 `article`（具体条号）、`clause_text`（条文原文 ≥30 字）、`suggestion`（法律层面修订方向）三项**必填**。

> 实跑教训：52 个问题里只有 5 个填了 `article`、0 个填了 `suggestion`。缺条号的问题无法被 Agent7 核验（核不了条款号是否平移），缺修订建议的问题对用户没有可操作性。5C 必须在此处把关：三项缺任一 → 该 issue 打回 `pending_recheck` 交 5D 补齐，补不齐则降 `advisory` 不进最终结果。

## cross_audit_log.json

```json
{
  "total_clauses": 0,
  "both_pass": 0,
  "both_fail": 0,
  "5a_only_fail": 0,
  "5b_only_fail": 0,
  "errors": 0,
  "raw_issues_in": 0,
  "rejected_reference_not_in_kb": 0,
  "rejected_incomplete_basis": 0,
  "systemic_findings": 0,
  "clause_level_findings": 0,
  "final_issues": 0,
  "merged_pairs": 0,
  "basis_status_warning": 0,
  "confidence_distribution": { "high": 0, "medium": 0, "low": 0 },
  "rejected_details": [],
  "details": []
}
```

`raw_issues_in` → `final_issues` 的每一次减少都必须在 `rejected_details` 或 `merged_pairs` 中有对应记录，数量必须自洽：

```
raw_issues_in
  - rejected_reference_not_in_kb
  - rejected_incomplete_basis
  - merged_pairs
  = final_issues
```

对不上就是审计逻辑有漏，必须停下报错，不得凑数。

## 禁止

- 跳过任何条款
- 新增 5A 和 5B 都没有的问题
- 丢失 5A / 5B 原始记录或覆盖其结果文件
- 把**不同缺陷**的问题合并成一条（Step 4 第二层只允许归并"同一缺陷在多条款上的重复命中"，`affected_clauses` 必须完整列出被归并的条款；不同 `type` 或不同 `reference`+`article` 一律不得合并）
- 破坏问题的可追溯关系（`origin` 必须保留）
- **把 `reference` 不在知识库内的问题留在 `review_results.json` 里**（哪怕降为低置信度也不行——这会污染 5D/5E/6/7 全部下游阶段）
- **把同一规则同一描述的批量命中逐条列为独立问题**（必须按系统性问题聚合）

## 验收

- `review_results.json` 条目数 == `clauses.json` 条目数。
- `cross_audit_log.json` 已落盘，且上述数量等式成立。
- 问题编号连续，每个问题有 `confidence`、`source`、`origin`。
- **`review_results.json` 中每个问题的 `reference` 都能在 `law_metadata.json` 中精确匹配**（可用一行脚本自检，不匹配数必须为 0）。
- 每个问题都有 `finding_scope`；`finding_scope: systemic` 的问题 `affected_clauses` 非空，且其条款数与 5A 的原始命中条款数一致，`clause_count` 与数组长度相等。
- `systemic_findings + clause_level_findings == final_issues`。
- 更新 `./output/review_log.json`。
