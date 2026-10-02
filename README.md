# Bili-Note 内容增强技能包（bili-content-enhance）

> 把一份 B 站转录稿 / 学习 markdown，自动生成 **6 类学习物料**的学习包：智能摘要、术语表、知识导图、动画 HTML、补充知识、深度理解文档。全部由当前 AI 模型直接执行，零外部 API 依赖，带质量门禁校验。

## 它能做什么

输入：一份带 `[mm:ss]` 时间戳的 B 站视频转录稿（markdown）。
输出：一个 `学习包/` 目录，内含 6 份成品物料：

| # | 物料 | 文件 | 用途 |
|---|------|------|------|
| ① | 智能摘要 | `①智能摘要.md` | 3–8 章节带时间戳的结构化摘要，快速掌握主干 |
| ② | 术语表与通俗解释 | `②术语表与通俗解释.md` | 8–15 条术语，每条配一句话定义 + 生活化类比 |
| ③ | 知识导图 | `③知识导图.md` | mermaid mindmap（≤20 节点）+ 层级大纲含关系标注 |
| ④ | 动画表达 | `④动画表达.html` | self-contained HTML 动画，可视化核心抽象概念 |
| ⑤ | 补充知识 | `⑤补充知识.md` | 背景 / 延伸 / 误区 / 实践四节，区分 📹 视频来源与 ➕ 补充来源 |
| ⑥ | 深度学习与理解文档 | `⑥深度学习与理解文档.md` | 自检清单 / 心智模型 / 概念地图 / 自测题 / 费曼输出 / 应用迁移 |

每份物料生成后都经过**质量门禁**校验（mermaid 语法、HTML 自包含且 JS 可执行、表格列数、章节数量等），未通过自动回灌重试，全部通过才落盘。

## 快速开始

### 1. 安装

把本仓库作为技能包安装到你的 AI 助手技能目录：

```bash
# WorkBuddy
git clone https://github.com/Asaceoo/bili-note-skills.git ~/.workbuddy/skills/bili-content-enhance

# Claude Code / Codex（二选一，取决于你的环境）
git clone https://github.com/Asaceoo/bili-note-skills.git ~/.claude/skills/bili-content-enhance
```

> 也可以手动复制整个目录（含 `references/ai_learning_prompts.md`）到技能目录。

### 2. 准备转录稿

你需要一份 B 站视频转录稿 markdown，最好带 `[mm:ss]` 时间戳。获取方式：
- 用 [Bili-Note](https://github.com/Asaceoo/bili-note) 桌面应用 / bili-note 技能抓取 AI 字幕或本地 ASR 转写；
- 或其他任何字幕/转写工具导出。

### 3. 触发

在 AI 助手中说：
> 用提示词跑一份文档 / 生成学习包 / 按 ai_learning_prompts 生成

并把转录稿 markdown 发给它。技能会自动读取 `references/ai_learning_prompts.md` 规范，执行 6 类提示词，校验后落盘到转录稿同级的 `学习包/` 目录。

## 目录结构

```
bili-content-enhance/
├── SKILL.md                        # 技能主文件（frontmatter + 流程 + 质量门禁）
├── references/
│   └── ai_learning_prompts.md      # 6 类提示词完整规范 v3.1（输出契约 / 门禁 / 风格护栏）
├── README.md                       # 本文件
└── LICENSE                         # MIT
```

## 设计要点

- **零依赖**：不需要任何外部 API key 或额外工具链；6 类物料全部由当前对话的 AI 模型直接生成，Node 只用于可选的质量门禁校验（无 Node 时自动降级为人工核对）。
- **反幻觉护栏**：摘要/术语/导图/动画必须来自转录稿；补充知识区分「📹 来自视频」与「➕ 补充」，补充内容只给可检索方向，严禁编造论文标题/作者/URL。
- **时间戳引用**：所有物料回扣原视频位置 `[mm:ss]`，方便跳回视频核对。
- **可复现**：`ai_learning_prompts.md` 定义了每份物料的输出契约与解码参数（温度/seed/max_tokens），保证风格一致。

## 常见问题

**Q: 没有 `[mm:ss]` 时间戳的文档能用吗？**
A: 可以。技能会按章节/段落定位引用（引用格式改用章节名），其余不变。

**Q: 转录稿超过 50KB 怎么办？**
A: 技能要求按章节分批生成，不得整篇塞入单次生成，避免信息丢失。

**Q: 质量门禁是什么？**
A: 每份物料落盘前做结构校验（见 SKILL.md「质量门禁」节），失败自动回灌重试，最多 2 次，仍失败则打标 `[需人工复核]` 并继续其余物料。

## 许可证

[MIT](LICENSE)。提示词规范文件 `references/ai_learning_prompts.md` 源自 [Bili-Note](https://github.com/Asaceoo/bili-note) 项目（MIT License），随本仓库一并分发并致谢上游。
