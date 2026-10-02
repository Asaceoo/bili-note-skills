# Bili Note Skills — B 站内容知识化技能集合（通用版）

> 把 B 站视频/图文变成**可学习、可检索、可追问**的知识资产的两个 AI 技能包。**通用版：不绑定任何 AI Agent**，Claude Code / Cursor / Codex / WPS AI / WorkBuddy / Cline / Gemini CLI 或纯手工都能用。MIT 开源。

本仓库是一个 **skills 集合仓库**，内含两个互补技能：

| 技能 | 目录 | 做什么 |
|------|------|--------|
| **bili-note** | `skills/bili-note/` | 从 B 站视频/图文**提取转录稿**：抓字幕、下载 AI 字幕、ASR 音频转写、抓评论，归档为带证据索引的学习型 Markdown 笔记 |
| **bili-content-enhance** | `skills/bili-content-enhance/` | 把一份转录稿**增强为 6 类学习物料**：智能摘要、术语表、知识导图、动画 HTML、补充知识、深度理解文档，带质量门禁 |

```
提取（bili-note）               增强（bili-content-enhance）
B站视频 ──→ 转录稿.md ──────→ 学习包/（6 份成品物料）
       字幕/ASR/评论归档           摘要/术语/导图/动画/补充/深读
```

**手册**：[中文手册](docs/manual-zh.md) · [English Manual](docs/manual-en.md)

## 通用性设计（为什么任何 Agent 都能用）

| 约束 | 做法 |
|------|------|
| 不绑定平台 | 每个技能只有一个入口 `SKILL.md`（标准 frontmatter：`name` + `description`），正文是纯 Markdown 指令 |
| 零第三方依赖 | bili-note 全部脚本只用 Python 3.10+ 标准库；bili-content-enhance 的门禁 `validate.js` 只用 Node 内置模块 |
| 不绑定浏览器/工具 | 登录态路线只要求「一个 CDP 代理暴露 `/targets` 与 `/eval`」（默认 `http://localhost:3456`），WorkBuddy 的 `web-access` 只是其中一种实现 |
| 无 Agent 也能跑 | 脚本可直接命令行执行；提示词规范 `references/ai_learning_prompts.md` 可人工照做 |

## 安装（按你的平台选一行）

| 平台 / 形态 | 技能目录 | 说明 |
|---|---|---|
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/` | 自动加载，`SKILL.md` 触发词生效 |
| Claude Code / Claude Desktop | `~/.claude/skills/` | 同上 |
| Codex CLI | `~/.codex/skills/` | 同上 |
| Cursor / Cline / Roo Code / Continue | 项目的 `.cursor/skills/` 或等价规则目录 | 把 `SKILL.md` 加入上下文规则 |
| Gemini CLI / OpenHands / Aider | 项目规则 / 自定义指令 | 引入 `SKILL.md` 全文 |
| WPS AI / 豆包 / 通义 / 不支持技能目录的助手 | — | 把 `SKILL.md` 全文贴进系统提示词，或作为上下文文件随素材一起发给模型 |
| 纯手工（无 Agent） | 任意目录 | 直接命令行跑脚本，或照提示词规范人工执行 |

```bash
# 方式一：clone 整个仓库后放进你的平台技能目录
git clone https://github.com/Asaceoo/bili-note-skills.git
cp -r bili-note-skills/skills/bili-note ~/.claude/skills/              # 以 Claude Code 为例
cp -r bili-note-skills/skills/bili-content-enhance ~/.claude/skills/

# 方式二：只 clone 单个技能（sparse checkout）
git clone --filter=blob:none --sparse https://github.com/Asaceoo/bili-note-skills.git
cd bili-note-skills && git sparse-checkout set skills/bili-content-enhance
```

> Windows 上 `~` 即 `%USERPROFILE%`；macOS/Linux 即 `$HOME`。路径分隔符按平台用 `\` 或 `/`，命令示例两种写法都给了。

## 技能 1：bili-note（转录稿提取）

从 B 站视频/图文提取字幕、AI 字幕、转写音频、抓评论，归档成学习型 Markdown 笔记。

- 支持：视频（`/video/BV...`）、图文/动态（`/opus/...`、`/dynamic/...`）
- 字幕优先，拿不到再转写音频；中文优先共享 Qwen3-ASR，外语用 Whisper 系
- 完整归档：字幕、图文正文、图片、评论、元数据、JSONL 证据索引
- 写前定标：按内容信息量与互动质量生成笔记预算，控制笔记详略

```bash
python skills/bili-note/scripts/run_bili_note.py "https://www.bilibili.com/video/BVxxxx/" \
  --archive-dir "./知识库/原始材料/BVxxxx_视频短标题"
```

详见 `skills/bili-note/README.md`。

## 技能 2：bili-content-enhance（6 类学习物料）

把一份带 `[mm:ss]` 时间戳的转录稿，自动生成 6 类学习物料：

| # | 物料 | 文件 | 用途 |
|---|------|------|------|
| ① | 智能摘要 | `①智能摘要.md` | 3–8 章节带时间戳的结构化摘要 |
| ② | 术语表 | `②术语表与通俗解释.md` | 8–15 条术语 + 一句话定义 + 生活化类比 |
| ③ | 知识导图 | `③知识导图.md` | mermaid mindmap + 层级大纲 |
| ④ | 动画表达 | `④动画表达.html` | self-contained HTML 动画可视化核心概念 |
| ⑤ | 补充知识 | `⑤补充知识.md` | 背景/延伸/误区/实践四节，📹/➕ 来源标注 |
| ⑥ | 深度理解 | `⑥深度学习与理解文档.md` | 自检/心智模型/自测题/费曼/迁移 |

每份物料经**质量门禁**校验（mermaid 语法、HTML 自包含且 JS 可执行、表格列数、章节数量等），未通过自动回灌重试：

```bash
node skills/bili-content-enhance/scripts/validate.js <学习包目录>
```

触发方式：在任意 AI 助手中说「用提示词跑一份文档 / 生成学习包」，并把转录稿发给它。

## 目录结构

```
bili-note-skills/
├── README.md                        # 本文件（集合说明）
├── docs/
│   ├── manual-zh.md                 # 中文手册（通用版）
│   └── manual-en.md                 # English Manual (universal)
├── LICENSE                          # MIT
├── .github/workflows/validate.yml   # CI：校验技能包结构
└── skills/
    ├── bili-note/                   # 技能 1：转录稿提取
    │   ├── SKILL.md  README.md  LICENSE  .gitignore
    │   ├── agents/  assets/  references/  scripts/  tests/
    └── bili-content-enhance/        # 技能 2：6 类学习物料
        ├── SKILL.md
        ├── references/ai_learning_prompts.md
        └── scripts/validate.js
```

## 许可证

[MIT](LICENSE)，Copyright (c) 2026 Asaceoo。
`skills/bili-content-enhance/references/ai_learning_prompts.md` 提示词规范源自 Bili-Note 项目（MIT），随仓库一并分发并致谢上游。
