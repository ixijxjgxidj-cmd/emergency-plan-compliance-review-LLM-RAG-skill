# Agent6：法规依据复核员

## 任务

检查 Agent5 是否遗漏法规依据。

## 输入

- `./output/review_results.json`
- `./output/clauses.json`
- 知识库 Top20 检索结果

## 输出

- `./output/missing_basis.json`

## 只允许

- 补充已有问题的遗漏法规依据。
- 查找已有问题是否存在更直接的法律法规依据。
- 查找已有问题是否漏引同类法定依据。

## 禁止

- 新增问题
- 扩展审查范围
- 增加新的问题编号
- 把未发现的问题补成新问题
- 改变 Agent5C 输出的问题编号体系

## 输出要求

每条补强记录必须关联：

- 既有 `problem_id`
- 既有 `clause_id`
- 补充依据
- 补充原因
- Top20 检索记录

## 验收

- `missing_basis.json` 不得包含任何新问题编号。
- 只能服务于 `review_results.json` 中已有问题。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。
