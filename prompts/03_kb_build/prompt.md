# Agent3：知识库构建员

## 任务

把用户提供的本地法规文件统一解析、切片、入库，构建可检索的法规知识库。

## 输入

- `./output/law_metadata.json`
- `./laws/**`

## 输出

- `./chroma_db/`
- `./output/kb_summary.json`
- `build_kb.py`、`query_kb.py`、`README_KB.md`

## 每个 chunk 必须包含

```json
{
  "chunk_id": "",
  "law_name": "",
  "file_name": "",
  "level": "",
  "category": "",
  "standard_nature": "",
  "effective_status": "",
  "plan_type_relevance": "",
  "chapter": "",
  "article": "",
  "chunk_text": "",
  "chunk_index": 0
}
```

## 切片规则

- 优先按"章-节-条-款"切分；其次按自然段。
- 禁止跨条款合并；禁止 chunk 超过 1500 字（超长条款按款拆分并保留 `article` 相同）。
- 每个切片保持语义完整，`article` 必须填具体条号（如"第二十三条"），无法识别则填"未编号段落"。

## `query_kb.py` 必须支持

- 按问题文本检索
- 按法规名称检索
- 按 `level` 过滤
- 按 `category` 过滤
- 按 `plan_type_relevance` 过滤
- 按 `source_type` 过滤
- `topk` 参数，默认 **Top20**

## 失败处理

- 单文件解析失败记 `error_reason` 并继续。
- 每个法规至少 1 个 chunk；确实失败必须进入失败清单。
- `usable_for_review: false` 的法规不入库，但必须在 `kb_summary.json` 中列出并说明原因。
- 禁止静默跳过文件。

## kb_summary.json 必须记录

- 总文件数、成功文件数、失败文件数
- chunk 总数、每文件 chunk 数
- 未入库文件清单及原因
- 5 条测试检索的 query 与命中结果（验证召回正常）

## 验收

- 所有可用法规至少 1 个 chunk，或有明确失败原因。
- 每个 chunk 的 `source_type` 与 `source_url`（联网来源）完整。
- 构建后执行 5 条测试检索并落盘结果。
- 更新 `./output/review_log.json`。
