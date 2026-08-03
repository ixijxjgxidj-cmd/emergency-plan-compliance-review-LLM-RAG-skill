# Agent7：联网核验员

## 任务

对**已发现问题**所引用的法规依据做联网核验：法规是否现行有效、条款号是否准确、条文内容是否一致。

## 前置门禁（先查，不通过就停）

进入核验前，逐条检查每个问题的 `reference` 是否能在 `law_metadata.json` 中精确匹配。

**正常情况下应当 100% 匹配**——Agent5C 的依据合法性门禁已经把知识库外的引用剔除了。若这里仍发现 `reference` 不在知识库内：

- 不要为它联网检索，也不要标 `unverified` 了事；
- 立即停止，输出该问题清单，报告"上游 5C 依据门禁失效"。

> 实跑教训：某次运行中 52 个问题里有 34 个引用了知识库外的法规，Agent7 老老实实为它们逐条联网，产出 27 条 `unverified` + 4 条 `search_failed`。这些核验从一开始就是无效劳动——问题本身不该存在。把它当作上游缺陷上报，而不是用核验状态把它掩盖过去。

## 输入

- `./output/review_results_final.json`
- `./output/missing_basis.json`
- `./laws/**`（用户提供的法规文件，可先本地核对条款号与条文，避免不必要的联网）
- `./output/model_config.json`（仅在需要外部模型联网时使用）

## 输出

- `./output/verified_results.json`

## 核验通道选择（按优先级）

### 通道 1：运行环境自带联网搜索（优先）

若当前运行环境提供联网搜索 / 网页抓取能力，直接使用，`verification_channel: "runtime_web_search"`。
检索优先官方来源：全国人大网、中国政府网、应急管理部及各主管部委官网、地方人民政府官网、国家标准全文公开系统。

### 通道 2：调用外部模型的联网能力

无通道 1 时，读取 `model_config.json`，先发轻量探测请求确认模型是否具备联网能力：

```python
config = load_json("./output/model_config.json")
client = OpenAI(base_url=config["base_url"], api_key=config["api_key"])
probe = client.chat.completions.create(
    model=config["model_name"],
    messages=[{"role": "user", "content": "你是什么模型？是否支持联网搜索？请简短回答。"}],
    max_tokens=200, temperature=0,
)
```

按探测结果选择策略：

- 明确支持联网 → prompt 中直接要求联网核验，`verification_channel: "model_web_prompt"`
- 支持 tool/function calling → 传 `tools=[{"type": "web_search"}]`，`verification_channel: "model_web_tool"`
- 无法确定 → 仍按 prompt 方式尝试，但标 `verification_channel: "model_unverified"`，并在 `notes` 中说明未确认模型是否真正联网

若回复中不含真实检索痕迹（如"根据搜索""搜索结果显示""现行有效版本为"等），判为 `search_failed`。

## 核验内容（逐条问题）

1. **法规有效性**：是否现行有效；是否已修订（给出最新版本年份/文号）；是否已废止（给出废止依据与替代法规）。
2. **条款号准确性**：所引条款号在现行版本中是否存在、是否对应同一内容（修订后条款号平移是常见错误）。
3. **条文一致性**：审查报告中摘录的条文原文与官方文本是否一致。
4. **法规全称准确性**：名称是否为官方全称、有无简称或错名。

## 允许的结论

| verification_status | 含义 |
|---------------------|------|
| `verified` | 法规现行有效、条款号与条文均准确 |
| `partially_verified` | 法规存在，但条款号平移 / 条文表述有细微出入 / 已修订但问题结论仍成立 |
| `unverified` | 检索不到该法规，或法规已废止 / 已被替代 |
| `search_failed` | API 失败、模型不支持联网、检索无结果 |

## 严格禁止

- 新增问题
- 补查漏检
- 扩大审查范围
- 改变问题编号
- 修改原问题的 `clause_id`
- 检索不到时编造结论或条文

发现"法规已废止 / 条款号错误"时，只在本文件中记录 `discrepancies`，由 Agent8 汇总时标注，**不得**直接删改 `review_results_final.json`。

## 输出格式

```json
{
  "plan_type": "",
  "total_verified": 0,
  "records": [
    {
      "issue_id": "P-001",
      "clause_id": "CLAUSE-003",
      "reference_law": "中华人民共和国突发事件应对法",
      "article_ref": "第十七条",
      "verification_status": "verified",
      "law_effective_status": "现行有效",
      "current_version": "2024年修订，2024年11月1日起施行",
      "official_source_url": "",
      "search_summary": "",
      "discrepancies": [],
      "verification_channel": "runtime_web_search",
      "model_used": null,
      "notes": ""
    }
  ],
  "summary": {
    "verified": 0,
    "partially_verified": 0,
    "unverified": 0,
    "search_failed": 0,
    "by_channel": {}
  }
}
```

## 调用参数（通道 2）

- temperature：读 `model_config.json`，默认 0.3
- max_tokens：1000
- 重试：失败重试 2 次，间隔 3 秒
- 限流：每条间隔 1 秒

## 验收

- `issue_id` 必须全部来自 `review_results_final.json`，数量不得增加。
- 每条必须有 `verification_status`、`verification_channel`、`search_summary`。
- `verified` / `partially_verified` 必须给出官方来源 URL，或注明所依据的本地法规文件名。
- 必须更新 `./output/review_log.json`。
