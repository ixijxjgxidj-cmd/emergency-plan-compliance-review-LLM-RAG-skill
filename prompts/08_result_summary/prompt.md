# Agent8：成果汇总员

## 任务

汇总全流程结果，生成最终交付成果。

## 输入

- `./output/plan_profile.json`
- `./output/law_inventory.json`
- `./output/law_metadata.json`
- `./output/kb_summary.json`
- `./output/clauses.json`
- `./output/kb_gap_report.json`（依据缺口报告，必须在汇总报告中单列一节）
- `./output/review_results_5A.json`
- `./output/review_results_5B.json`
- `./output/review_results.json`
- `./output/rejected_problems.json`（5C 因依据不合法移出的问题，必须在报告中单列一节）
- `./output/cross_audit_log.json`
- `./output/review_results_5D.json`
- `./output/review_results_final.json`
- `./output/missing_basis.json`
- `./output/verified_results.json`
- `./output/review_log.json`

## 输出

- `./output/problems_all.json`
- `./output/summary_report.md`
- `./output/plan_annotated.docx`
- `./output/issue_list.docx`
- `./output/review_log.json`（更新）

## problems_all.json

以 `review_results_final.json` 的问题为唯一来源，把 Agent6 的补强依据与 Agent7 的核验结论**合并回对应既有问题**，不新增、不改编号。

```json
{
  "plan_profile": {
    "plan_name": "", "plan_category": "", "event_category": "",
    "authority_level": "", "issuing_body": ""
  },
  "statistics": {
    "total_clauses": 0,
    "total_issues": 0,
    "by_severity": { "high": 0, "medium": 0, "low": 0 },
    "by_issue_type": {},
    "by_confidence": { "high": 0, "medium": 0, "low": 0 },
    "by_source": { "both": 0, "rule_only": 0, "llm_only": 0 },
    "by_law_level": {},
    "by_verification": { "verified": 0, "partially_verified": 0, "unverified": 0, "search_failed": 0 }
  },
  "problems": [
    {
      "problem_id": "P-001",
      "clause_id": "CLAUSE-003",
      "chapter": "",
      "clause_text": "",
      "issue_type": "",
      "description": "",
      "severity": "high",
      "confidence": "high",
      "source": "both",
      "legal_basis": [
        {
          "reference": "", "article": "", "clause_text": "",
          "level": "", "source_type": "local_file", "chunk_id": "",
          "from_agent6_supplement": false
        }
      ],
      "verification": {
        "status": "verified",
        "law_effective_status": "",
        "discrepancies": [],
        "channel": ""
      },
      "suggestion": ""
    }
  ]
}
```

`suggestion` 只能是"依法应当如何表述/补充"的法律层面建议，禁止写实操、资源配置、技术参数类建议。字段名与 5A/5C/5D/5E 及 `references/issue_types.md` 保持一致，汇总时**不得改名**。

## summary_report.md 必须包含

1. **预案基本信息**：名称、类型、事件类别、编制层级、编制主体、版本/发布日期。
2. **适用法规基线**：`plan_profile.json` 中判定的基线清单，及每条的落实情况（`./laws/` 中已有对应文件 / 本地缺失即依据缺口）。
3. **法规来源构成**：本地法规文件总数、成功入库数、解析失败数、入库 chunk 总数。
4. **本次审查的能力边界（必须单列，不得省略）**：合并三个来源——`law_inventory.json` 的 `baseline_missing`（法定应适用但本地无文件的法规）、`kb_gap_report.json` 的 `gaps`（5A 规则命中但取不到依据的检查点）、`review_results_5B.json` 各条的 `suspected_issues`（5B 怀疑有问题但知识库无条文支撑的事项）——逐条说明：
   - 哪些法定检查点因知识库无对应法规而**未能形成结论**（列 `rule_id` + 检查点名称 + 受影响条款数）；
   - 建议向 `laws/` 补充哪些**主题**的法规（只写主题，不写具体文号，避免把线索写成结论）；
   - 明确一句话结论：「本次审查覆盖 N 个检查点，其中 M 个因依据缺失未能形成结论。未形成结论 ≠ 该项合规。」

   > 这一节是本报告最重要的诚实性声明。实跑中 52 个问题里 34 个引用了知识库外法规，报告却只在"重要审查发现"里轻描淡写提了一句，读者极易误读为"预案有 52 个问题"。必须前置、必须量化。
5. **审查覆盖情况**：条款总数、5A 审查数、5B 审查数、error 数、5B 的 `pass_justification` 完整率；若 `review_log.json` 中存在 `pass_rate_alert`，必须在此披露并说明重审结论。
6. **双轨审查对比**：5A 独有问题数、5B 独有问题数、共同问题数、审计裁定统计（保留/合并/剔除/待人工复核）。若 5B 的 fail 率显著低于 5A（如 5A 34 条 vs 5B 5 条），必须在此明确提示"5B 可能存在系统性宽松，建议人工抽查其 pass 判定"。
7. **问题统计**：按严重程度、问题类型、置信度、来源、法规层级分类统计。**同时给出"问题数（合并后）"与"受影响条款数"两个数字**——一个跨 19 个条款的同类缺陷是 1 个问题、影响 19 条，不是 19 个问题。
8. **联网核验统计**：verified / partially_verified / unverified / search_failed 数量，以及发现的法规失效或条款号错误清单。
9. **典型问题示例**：每种问题类型至少 1 例，含条款原文、法规依据、问题描述。
10. **结论摘要**：合规总体判断 + 高严重度问题清单 + 需人工复核清单 + 依据缺口导致的未覆盖检查点清单。

## plan_annotated.docx 必须

- 完整保留预案原文（不得删改正文）。
- 在对应条款位置插入批注或批注式标记（含 `problem_id`、问题类型、法规依据、严重程度）。
- 每个批注都能定位回原条款；每个问题都在文档中出现一次。
- 使用 `python-docx`；若无法插入真批注，则以醒目的行内标记块（如【P-001｜缺失法定必备内容｜依据…】）紧随该条款插入，并在报告中说明所用方式。

## issue_list.docx

问题清单表格，列：问题编号、所在章节、条款编号、条款原文摘录、问题类型、问题描述、法规依据（全称+条款号+条文摘录）、严重程度、置信度、来源、核验状态、修订建议。

## 汇总前自检（不通过必须停止并报错，禁止伪造）

1. `problems_all.json` 问题数 = `review_results_final.json` 中 fail 问题数。
2. `missing_basis.json`、`verified_results.json` 的 `problem_id` 均为既有问题子集。
3. `problems_all.json` 问题编号连续。
4. `summary_report.md` 统计数与 `problems_all.json` 完全一致。
5. `plan_annotated.docx` 中批注数 = 问题数，且都能定位回条款。
6. 不存在由 Agent6 或 Agent7 新增的问题。
7. 每个 fail 问题都有法规全称 + 条款号 + 条文摘录（≥30 字）。
8. **每个问题的 `reference` 都能在 `law_metadata.json` 中精确匹配**。出现任何知识库外的 `reference` → 停止并报错，说明是哪个上游阶段漏过了 5C 的依据门禁（实跑中 52 个问题里有 34 个引用了知识库外法规，这一项自检就是为拦住它而设）。
9. **`suggestion` 非空率 100%**（实跑中为 0/52）。
10. **`article` 非空率 100%**（实跑中仅 5/52 有条款号）。
11. 无 `description` 完全相同的两个问题（实跑中 52 个问题只有 17 种不同描述，最重复的一条出现 19 次）。
12. `kb_gap_report.json` 若存在 gap，报告第 4 节"本次审查的能力边界"必须如实列出，不得省略。

## 验收

- 4 个成果文件全部落盘到 `./output/`。
- 必须更新 `./output/review_log.json`，写入全流程汇总（各阶段成功/失败/重试统计）。
- 输出终审报告后方可宣布流程结束。
