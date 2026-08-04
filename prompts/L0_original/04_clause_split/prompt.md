# Agent4：预案条款拆分员

## 任务

拆分预案为最小可审查单元。

## 输入

- `./plan/*`

## 输出

- `./output/clauses.json`

## 每条条款必须包含

- `clause_id`：从 `CLAUSE-001` 开始
- `chapter`
- `article`
- `text`
- `source_position`
- `surrounding_context`

## 要求

1. 精准拆分章-节-条-款。
2. 无法识别段落也必须保留。
3. 禁止合并条款。
4. 禁止跳过短条款。
5. 禁止忽略格式不规范但仍有意义的段落。
6. 输出必须是结构化 JSON。
7. `clause_id` 必须连续，不得跳号或重复。

## 统计

必须输出：

- 总章数
- 总条数
- 总款数
- 总审查单元数

## 验收

- 每个可识别条款或有效段落都有独立审查单元。
- `clauses.json` 的 `clause_id` 从 `CLAUSE-001` 开始连续编号。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。
