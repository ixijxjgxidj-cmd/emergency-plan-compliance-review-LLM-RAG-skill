# 应急预案法律法规合规审查系统（通用版）

本仓库是一个**通用应急预案合规审查 skill 包**。入口文件是根目录的 [SKILL.md](SKILL.md)。

## 给 agent 的指令

1. 先完整读取 `SKILL.md`，它定义了适用范围、绝对边界、工作流总览和验收标准。
2. 再读 `prompts/master.md` 作为总控。
3. **每个阶段派发一个独立子智能体去执行**，它读该阶段的 `prompts/<阶段>/prompt.md`、落盘、回报统计后结束。主流程只编排与校验，不亲自做阶段的活。
   - 唯一例外：5B 且用户提供了模型 key（模式 B）→ 直接按 `model_config.json` 调外部 API，不派子智能体。
   - 派发指令必须自带六项：阶段 prompt 路径、`SKILL.md` 第 2 节（绝对边界）、`review_config.json`（挡位）、输入路径清单、输出路径清单、回报格式（**只回统计，不回传产出内容**）。
   - 阶段之间：核对该阶段"验收"节每一项 → 更新 `./output/review_log.json` → 不通过最多重派一次，仍不通过即停止，**不得跳过阶段**。
   - 两处需要二级派发（由该阶段子智能体自己完成）：5B 模式 A 按 batch 切分、5C2 路径 2（预案 > 30000 字）按待查主张切分。
4. 类型判定与法规基线查 `references/plan_type_matrix.md`；问题类型只能取自 `references/issue_types.md`。

## 执行顺序（严格）

```
Agent0 → 挡位选择 → Agent1 → Agent2 → Agent3 → Agent4 → [模型配置]
      → Agent5A → Agent5B → Agent5C → Agent5C2 → Agent5D → Agent5E
      → Agent6 → Agent7 → Agent8
```

模型配置仅在用户自带模型/key 时需要，默认跳过。挡位默认 L2；选 L0 时 5C/5D 改读 `prompts/L0_original/` 下的原始 prompt 并跳过 5C2。挡位定义见 `references/strictness_levels.md`。

每完成一个阶段：落盘输出文件 → 更新 `./output/review_log.json` → 输出完成报告（成功/失败/重试条数）→ 停下汇报。
在全部完成前，不得输出"任务结束"。

## 法规来源

法规知识库只有一条合法来源：用户放入 `./laws/`（含子目录）的法规/标准/规范文件，由 Agent1 盘点。

**不得凭模型记忆生成任何法规条文。** 基线清单中本地缺失的法规，只记入 `baseline_missing` 作为事实，不得据此编造条文。

## 运行前准备

1. 待审预案放入 `plan/`（支持 .docx / .pdf / .md / .txt）。
2. 适用的法规/标准/规范文件放入 `laws/`（不可为空，知识库唯一来源）。
3. `output/` 保持为空或仅含历史输出。
4. 从 Agent0 开始逐阶段执行，首次运行不建议全流程连跑。

## 使用示例（Codex CLI）

```powershell
codex --cd "emergency-plan-compliance-review" --sandbox workspace-write --ask-for-approval on-request
```

进入后：

```text
请读取 AGENTS.md、SKILL.md、prompts/master.md，并严格按总控流程执行。先只执行 Agent0，完成后落盘输出文件，然后停下来汇报。
```

后续逐阶段下达"继续执行 AgentX"。
