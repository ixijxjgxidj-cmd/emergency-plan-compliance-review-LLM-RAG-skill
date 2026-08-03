# Agent6：法规依据复核员

## 任务

检查 Agent5E 最终审计结果中，已有问题的法规依据是否遗漏、是否有更直接的依据。

## 输入

- `./output/review_results_final.json`
- `./output/clauses.json`
- `./output/law_metadata.json`
- `./output/plan_profile.json`
- `./chroma_db/` + `query_kb.py`

## 输出

- `./output/missing_basis.json`

## 只允许做

1. 补充已有问题遗漏的法规依据。
2. 为已有问题查找**更直接、效力更高**的法律法规依据。
3. 查找已有问题是否漏引同类法定依据（例如只引了部门规章，实际上位法《突发事件应对法》有更直接条文）。
4. 标注依据的来源文件（`basis_source` 填对应的本地法规文件名）。

## 严格禁止

- 新增问题
- 扩展审查范围
- 增加新的问题编号
- 把未发现的问题补成新问题
- 改变 Agent5C/5E 的问题编号体系
- 引用不在知识库中的法规条文（凭记忆补写依据一律禁止）

## 复核方法

对每个 fail 问题：

1. 以「问题描述 + 条款原文 + 已引法规名」为 query，重跑知识库 Top20 检索。
2. 判断检索结果中是否存在：
   - 效力层级更高的同义条文 → `higher_authority`
   - 更具体、更直接对应的条文 → `more_direct`
   - 同类法定要求的并列依据 → `parallel_basis`
   - 已引依据实际不支持该问题 → `basis_mismatch`（标记，交人工，不得自行删除问题）
3. 依据必须写全：法规全称 + 条款号 + 条文原文摘录（≥30 字）+ `chunk_id`。

## 输出格式

```json
{
  "plan_type": "",
  "total_issues_reviewed": 0,
  "records": [
    {
      "problem_id": "P-001",
      "clause_id": "CLAUSE-003",
      "existing_basis": [
        { "reference": "", "article": "", "clause_text": "" }
      ],
      "supplemental_basis": [
        {
          "reference": "",
          "article": "",
          "clause_text": "",
          "chunk_id": "",
          "source_type": "local_file",
          "basis_relation": "higher_authority",
          "reason": ""
        }
      ],
      "retrieval_log": { "query": "", "topk": 20, "top_hits": [] }
    }
  ],
  "summary": {
    "issues_with_supplement": 0,
    "higher_authority": 0,
    "more_direct": 0,
    "parallel_basis": 0,
    "basis_mismatch": 0
  }
}
```

## 验收

- `missing_basis.json` 中的 `problem_id` 必须全部来自 `review_results_final.json`，不得出现新编号。
- 每条补强记录必须有 Top20 `retrieval_log` 和 `chunk_id`。
- `basis_mismatch` 必须显式列出，不得静默修改原问题。
- 必须更新 `./output/review_log.json`（成功条数、失败条数、重试次数）。
