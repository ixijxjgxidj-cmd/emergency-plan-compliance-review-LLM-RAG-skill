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

**先读 `./output/review_config.json`。** `basis_gate_a` / `basis_gate_b` 三态决定本步动作：

| 取值 | 动作 |
|------|------|
| `off` | 不查，全部候选问题直接进 Step 4 |
| `annotate` | 照下面的规则判定，但**不移出任何问题**，只在该问题上写 `basis_status`（`basis_outside_kb` / `citation_unverifiable` / `incomplete_fields` + 缺失字段清单） |
| `filter` | 照下面的规则判定并移出不合格问题 |

判定逻辑三态相同，只是处置不同。`annotate` 下仍须产出 `rejected_problems.json`（记录"若按 L3 会被移出的问题"），但这些问题**同时**留在 `review_results.json` 里并带标记。

门禁分两级。**混用一个动作处理两种性质的缺陷，会把可修复的问题当不成立的问题扔掉**——这是上一版的实际缺陷。

#### A 级：依据合法性（不过即剔除）

问题是否有**知识库内的**法规依据支撑。

**按数组判定，不是按单个字段判定。** 遍历该问题 `legal_basis` 的全部条目（`reference` 只是其中主依据），逐条检查：

1. 该条目的 `reference` 能否在 `law_metadata.json` 中按 `law_name` 精确匹配？
2. 匹配到的记录 `usable_for_review` 是否为 `true`？

**任一条目两项全过 → A 级通过**，并把未通过的库外条目从 `legal_basis` 中摘除、记入 `kb_gap_report.json`（保留"这条依据本地没有"的事实），用库内条目作为该问题的正式依据。

**全部条目都不过 → 剔除**，写入 `./output/rejected_problems.json`，`reject_reason` 取 `no_basis_in_kb` / `law_unusable`，并在 `kb_gap_report.json` 登记依据缺口。

> 为什么必须遍历数组：实跑中有问题同时引了《突发事件应对法》第八十六条（库外）与《江西省突发事件应对条例》第四十九条（库内），只查单个 `reference` 字段就把它整条剔掉了，而它明明有库内的替代依据。

#### `引用法规或条款错误` 类型的特殊处理（**A 级判定前先做**）

这个类型的语义与其他类型相反：被写进 `reference` 的往往是**预案里那个被质疑的引用**，不是支撑本发现的权威依据。直接套 A 级会把真问题剔掉。

因此该类型必须拆成两个字段：

| 字段 | 含义 | 参与门禁 |
|------|------|----------|
| `challenged_citation` | 预案中被质疑的那个引用（法规名/文号/条款号） | **不参与** |
| `reference` | 支撑"该引用有误"这一判断的知识库内依据 | 参与 A 级 |

- 上游把被质疑引用错填进 `reference` 时，5C 负责搬到 `challenged_citation`，再重新取 `reference`。
- 取不到库内依据支撑（例如被质疑的是一份本地没有的上级预案，无从判断其名称是否准确）→ 这不是"引用错误"问题，而是**无法核验**：剔除，`reject_reason: citation_unverifiable`，转入 `kb_gap_report.json`。
- 库内有依据（例如预案引"《安全生产法》第九十九条"而库内该法无此条）→ A 级通过，`reference` 填《中华人民共和国安全生产法》。

#### B 级：字段完备性（不过则退回补齐，不直接剔除）

A 级通过后再查。这些缺陷是"判断可能对但没写全"，不是"判断不成立"：

3. `article` 是否为具体条号？`clause_text` 是否 ≥30 字且能在知识库中找到对应原文？
4. `quoted_text` 是否非空、≥10 字，且能在该 `clause_id` 的条款原文中精确匹配？
5. `suggestion` 是否非空且为法律层面的修订方向？

**任一不过 → 标 `gate_status: needs_completion`**，列出缺失字段，**重跑该问题的 Top20 检索尝试补齐**：

- 补齐成功 → `gate_status: passed`，正常进入合并流程。
- 补齐失败 → 才剔除，`reject_reason` 用 `no_article_after_retry` / `no_clause_text_after_retry` / `no_quoted_text_after_retry` / `no_suggestion_after_retry`，与 A 级的"无依据"在语义上明确区分。

被剔除的问题一律**不占用 `P-` 编号**，不进入 `review_results.json`，不流向 5C2/5D/5E/6/7。

#### 上游违约告警（**必须执行**）

5A 已被明令要求"取不到库内依据就记 `advisory`，不生成问题"，5B 同理。**因此在正常流程中 A 级门禁应拦到约 0 条。**

统计 `a_level_rejected / raw_candidate_count`：

- 比率 > 0.1 → 在 `cross_audit_log.json` 与 `review_log.json` 写入 `upstream_basis_violation_alert`，明确指出是 5A 或 5B 违反了该约束（列出违约问题的 `origin` 与涉及的库外法规名），并在 Agent8 报告中披露。
- **门禁拦到东西不是门禁在正常工作，是上游失效的信号。** 静默剔除会把这个信号吞掉——上一版就是这样，导致 5E 那条"出现 `reference_not_in_kb` 即判门禁失效"的检查永远收不到输入，成了死代码。

<!-- GATE-END -->

> 为什么 A 级必须是"剔除"而不是"降为低置信度"：实跑中 52 个问题里 34 个引用了知识库外的法规（《危险化学品安全管理条例》《GB/T 29639》《GB 30077》《突发环境事件应急管理办法》）。当时只把它们标为低置信度继续下传，结果 Agent6 花 36 次复核标 `insufficient_basis_outside_kb`、Agent7 花 27 次联网核验标 `unverified`，最终报告里 65% 的问题是不成立的——审查结论被无依据条目稀释，用户无法分辨哪 18 条是真的。**无依据的问题不是低置信度问题，它不是问题。**
>
> 但反过来也不能一刀切：B 级那三项（条款号、错误原文、修订建议）缺失时，判断本身可能是对的，只是没写全。上一版把这五项混成一个剔除动作，等于把可修复的缺陷也当成不成立的问题扔掉。

### Step 4 问题合并去重

**第一层：同条款内合并**

- 同一 `clause_id` + 同一 `type` + 同一 `reference`+`article` → 同一问题，保留描述更详细的一条，另一条记入 `merged_from`。
- 同一 `clause_id` + 同一 `type` 但依据不同法规 → 两个问题，均保留。

**第二层：跨条款同因归并**（`cross_clause_aggregation: filter` 时执行；`off` 时跳过本层，每条款各自保留独立编号）

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
- 统计 Step 3 各级结果写入 `cross_audit_log.json`：`a_level_rejected`、`b_level_needs_completion`、`b_level_completed`、`b_level_rejected_after_retry`、`basis_trimmed_to_kb_only`、`citation_field_relocated`。
- `a_level_rejected / raw_issues_in > 0.1` 时写入 `upstream_basis_violation_alert`。

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
  "a_level_rejected": 0,
  "b_level_needs_completion": 0,
  "b_level_completed": 0,
  "b_level_rejected_after_retry": 0,
  "basis_trimmed_to_kb_only": 0,
  "citation_field_relocated": 0,
  "upstream_basis_violation_alert": null,
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

字段含义：`a_level_rejected` 无库内依据被剔；`b_level_needs_completion` 字段不全被退回补齐；其中 `b_level_completed` 补齐成功、`b_level_rejected_after_retry` 补不齐才剔；`basis_trimmed_to_kb_only` 有库内依据但摘掉了库外条目的问题数；`citation_field_relocated` 把被质疑引用从 `reference` 搬到 `challenged_citation` 的问题数。

`raw_issues_in` → `final_issues` 的每一次减少都必须在 `rejected_details` 或 `merged_pairs` 中有对应记录，数量必须自洽：

```
raw_issues_in
  - a_level_rejected
  - b_level_rejected_after_retry
  - merged_pairs
  = final_issues
```

注意 `b_level_needs_completion` **不**出现在这个等式里——退回补齐不是剔除，补齐成功的问题仍在清单内。等式对不上就是审计逻辑有漏，必须停下报错，不得凑数。

`a_level_rejected / raw_issues_in > 0.1` 时必须写入 `upstream_basis_violation_alert`，内容含违约问题的 `origin`（`5A:P-xxx` / `5B:P2-xxx`）与涉及的库外法规名清单。

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
