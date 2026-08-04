# Agent3：知识库构建员

## 任务

构建法规知识库。

## 输入

- `./output/law_metadata.json`
- `./laws/*`

## 输出

- `./output/kb_summary.json`
- `./chroma_db/`

## 每个 chunk 必须包含

```json
{
  "chunk_id": "",
  "law_name": "",
  "file_name": "",
  "level": "",
  "category": "",
  "article": "",
  "chunk_text": "",
  "chunk_index": 0
}
```

## 切片规则

- 优先按“章-节-条-款”切分。
- 其次按自然段切分。
- 禁止跨条款合并。
- 禁止 chunk 超过 1500 字。
- 每个切片尽量保持语义完整。

## 工具输出

除知识库外，还必须输出或更新：

- `./output/kb_summary.json`
- `build_kb.py`
- `query_kb.py`
- `README_KB.md`

`query_kb.py` 必须支持：

- 按问题检索
- 按法规名称检索
- 按层级过滤
- 按类别过滤
- TopK 参数，默认 Top20

## 失败处理

- 单文件解析失败记录 `error_reason`，继续处理。
- 每个法规至少生成 1 个 chunk；确实失败时必须进入失败清单。
- 禁止静默跳过文件。

## 验收

- 所有法规至少生成 1 个 chunk，或在 `kb_summary.json` 中记录明确失败原因。
- `kb_summary.json` 必须完整记录总文件数、成功文件数、失败文件数、chunk 总数、每文件 chunk 数。
- 构建完成后必须执行 5 条测试检索，验证召回正常。
- 必须更新 `./output/review_log.json`，记录成功条数、失败条数、重试次数。
