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
- `./output/fulltext_crosscheck.json`（5C2 全文反证裁定）
- `./output/refuted_problems.json`（5C2 判为误报移出的问题，必须在报告中单列一节）
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
      "affected_clauses": ["CLAUSE-003"],
      "chapter": "",
      "clause_text": "",
      "quoted_text": "",
      "issue_type": "",
      "challenged_citation": null,
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
6. **全文反证结果**：5C2 裁定统计（误报剔除 / 降级 / 成立 各多少条）、误报剔除的问题逐条列出（含原描述与落实位置的原文），说明"这些主张在全文范围内不成立"。**这一节让审阅者能反查是否误剔**，不得省略或只给数字。
7. **双轨审查对比**：5A 独有问题数、5B 独有问题数、共同问题数、审计裁定统计（保留/合并/剔除/待人工复核）。若 5B 的 fail 率显著低于 5A（如 5A 34 条 vs 5B 5 条），必须在此明确提示"5B 可能存在系统性宽松，建议人工抽查其 pass 判定"。
8. **问题统计**：按严重程度、问题类型、置信度、来源、法规层级分类统计。**同时给出"问题数（合并后）"与"受影响条款数"两个数字**——一个跨 19 个条款的同类缺陷是 1 个问题、影响 19 条，不是 19 个问题。
9. **联网核验统计**：verified / partially_verified / unverified / search_failed 数量，以及发现的法规失效或条款号错误清单。
10. **典型问题示例**：每种问题类型至少 1 例，含条款原文、法规依据、问题描述。
11. **结论摘要**：合规总体判断 + 高严重度问题清单 + 需人工复核清单 + 依据缺口导致的未覆盖检查点清单。

## plan_annotated.docx 必须

### 批注位置：锚定到出错的那句话，不是整段、不是标题

- 完整保留预案原文（不得删改正文、不得改动样式）。
- 批注**锚定范围必须是 `quoted_text`（错误原文）在正文中的精确字符区间**，用 `w:commentRangeStart` / `w:commentRangeEnd` 包住那句话。禁止把整段包进批注范围，禁止锚在章节标题、目录、页眉页脚上。
- 一个 `problem_id` 在文档中只出现一次。若同一问题跨多条款（`affected_clauses` 有多项），锚在**首个**出现位置，批注正文用一行列出其余条款号，其余位置不重复插批注。
- `quoted_text` 在正文中找不到精确匹配时（跨段落、被表格拆分、含软换行）→ 退化为锚定该 `clause_id` 对应的段落，并在 `annotation_log.json` 中记 `anchor_fallback: paragraph`，报告中汇总退化条数。禁止静默退化。

### 批注正文模板（**唯一允许的格式**，不得增删字段、不得改字段名、不得改顺序）

```
问题：{issue_type}——{description}

错误原文：{quoted_text}

依据：《{reference}》{article}
{clause_text}

改进建议：{suggestion}

——————————
严重度：{高|中|低}　置信度：{高|中|低}　联网核验：{已核验|部分核验|未核验|核验失败}
{核验说明：仅当核验有实质发现时增加此行}
```

前四个字段是审阅者要读的内容，必须在前；末尾一行是判定标签，用分隔线隔开，不得插到四个字段中间。

**四个正文字段的硬要求：**

| 字段 | 要求 |
|------|------|
| 问题 | 问题类型 + 一句话说清"预案怎么写的 / 法定怎么要求的 / 差在哪"。禁止写规则触发条件（如"涉及X但未涉及Y"），那是命中日志不是问题 |
| 错误原文 | 从预案正文**逐字**摘出的出错文字，≥10 字。这是"错在哪一句"的唯一凭证，不得为空、不得用整段代替、不得改写 |
| 依据 | `《法规全称》第X条` + **紧随其后另起一行给出该条文原文**（≥30 字，逐字来自知识库）。三者缺一即不得出现在交付件中 |
| 改进建议 | 依法应当如何表述或补充，须指向具体的法定表述/法定要素。禁止实操、资源配置、技术参数类建议 |

**三个判定标签的硬要求（必须用中文值，禁止直接输出英文枚举名）：**

| 标签 | 取值映射 | 含义 |
|------|----------|------|
| 严重度 | `high`→高、`medium`→中、`low`→低 | 违反法律/行政法规/强制性标准→高；违反部门规章/地方性法规/推荐性标准→中；引用格式瑕疵/表述不严谨→低 |
| 置信度 | `high`→高、`medium`→中、`low`→低 | 高＝5A 与 5B 都发现且依据精确到条号；中＝仅一方发现但依据齐备；低＝依据法规状态待核实 |
| 联网核验 | `verified`→已核验、`partially_verified`→部分核验、`unverified`→未核验、`search_failed`→核验失败 | 指 Agent7 对该问题所引法规的现行有效性与条款号准确性的核验结论 |

**核验说明行**只在联网核验有实质发现时才加，且只能写一句事实结论，例如：

- `核验说明：该法规 2021 年修订，原第X条已调整为第Y条，建议按修订后条款号引用。`
- `核验说明：该法规现行有效，条款号与条文内容均一致。`（仅当需要向审阅者证明依据可靠时才写）

禁止把检索过程写进来（如"百度百科核验""国家法规库检索"），禁止写削弱结论可信度的表述（如"依据来源存疑""需人工确认来源"）——依据在不在知识库内已由 5C 门禁把关，能出现在交付件里的问题依据一律是库内依据，不存在"存疑"情形。

### 批注正文禁止出现的内容

以下是内部流程痕迹，**一律不得写入批注**：`origin`、`source`(rule_only/llm_only/both)、`basis_status`、`insufficient_basis_outside_kb`、`chunk_id`、`retrieval_log`、Agent5A/5B/5C/5D/5E/6/7 等阶段代号、英文枚举原值。

严重度/置信度/联网核验必须以上表的中文值呈现，读者不需要知道它们出自哪个阶段。

> 实跑教训：上一版批注写成了这样——
> `[合规问题 P-001] 严重度:低 置信度:medium 来源:rule_only / 问题类型: 缺失法定必备内容 / 问题描述: 涉及危险化学品经营/储存/使用/生产但未涉及许可、资质或安全条件要求 / 法规依据: 危险化学品安全管理条例 / 依据状态(Agent6): insufficient_basis_outside_kb / 联网核验(Agent7): unverified / 核验说明: 百度/国家行政法规库核验:...但该法规不在用户提供的知识库中,依据来源存疑`
>
> 病根不在"带了严重度和置信度"，而在四件事：**没有错误原文**（批注挂在整段上，最多的一段挂了 5 条批注，审阅者不知道哪句话错了）；**依据只有法规名，没有第X条、没有条文原文**（52 条里只有 5 条有条款号）；**完全没有改进建议**（0/52）；**判定标签混在正文里且直接吐英文枚举和阶段代号**，还带上"依据来源存疑"这种自我否定的话。
>
> 判定标签本身是有用的——审阅者靠严重度排整改优先级、靠置信度决定是否需要人工复核、靠联网核验判断法条引用能不能直接用。所以保留，但要求：放在末尾、中文值、与正文用分隔线隔开。

### 生成方式

- 优先用 `python-docx` + 直接操作 `word/comments.xml` 插入**真 Word 批注**（`w:commentRangeStart` / `w:commentRangeEnd` / `w:commentReference` 三件套齐全，`comments.xml` 与 `[Content_Types].xml`、`document.xml.rels` 均须正确注册）。
- 真批注确实无法插入时，退化为紧随 `quoted_text` 所在段落之后插入醒目行内块，格式仍严格遵循上述四字段模板，并在报告中说明所用方式与退化原因。
- 落盘后**必须重新打开生成的 docx 自检**：`comments.xml` 定义数 == `document.xml` 中 `commentReference` 数 == `commentRangeStart` 数 == 问题数，无孤儿批注；抽查 3 条批注的锚定文字是否等于其 `quoted_text`。自检不通过必须报错，不得交付。

## issue_list.docx

问题清单表格，列的顺序与批注模板保持一致，便于对照：问题编号、所在章节、条款编号（多条款时全部列出）、**错误原文**、问题类型、问题描述、**依据（《法规全称》+第X条+条文原文摘录）**、**改进建议**、严重程度、置信度、来源、核验状态。

其中"错误原文""依据""改进建议"三列必须与 `plan_annotated.docx` 中同一 `problem_id` 的批注内容**逐字一致**，不得出现两处表述不同的情况。

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
13. **`quoted_text` 非空率 100%**，且每条都能在预案原文中找到（精确匹配或已记录 `anchor_fallback`）。
14. **重新打开 `plan_annotated.docx` 校验批注三件套**：`comments.xml` 定义数 == `commentReference` 数 == `commentRangeStart` 数 == 问题数，无孤儿批注。
15. **抽查 3 条批注的锚定文字 == 其 `quoted_text`**；批注正文严格为"四字段 + 分隔线 + 判定标签行"结构，判定标签为中文值，且不含 `origin`/`source`/`chunk_id`/阶段代号/英文枚举原值。
16. `issue_list.docx` 中"错误原文""依据""改进建议"三列与同一 `problem_id` 的批注内容逐字一致；"严重程度""置信度""核验状态"三列与批注末尾标签行的中文值一致。
17. 批注中的"联网核验"值与 `verified_results.json` 中该 `problem_id` 的 `status` 一一对应，无错配；`search_failed` 与 `unverified` 不得混用。

## 验收

- 4 个成果文件全部落盘到 `./output/`。
- 必须更新 `./output/review_log.json`，写入全流程汇总（各阶段成功/失败/重试统计）。
- 输出终审报告后方可宣布流程结束。
