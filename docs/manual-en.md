# Bili Note Skills — Universal Manual (English)

**Version**: v1.1.0 (Universal Edition)
**Works with**: any AI agent (Claude Code, Cursor, Codex CLI, WPS AI, WorkBuddy, Cline, Gemini CLI, ...) and plain manual use without an agent
**License**: MIT

---

## 1. What this solves

Long Bilibili lectures, technical talks and article posts are **easy to watch, hard to retain, and impossible to search afterwards**. This repo ships two composable skills:

| Stage | Skill | Input | Output |
|-------|-------|-------|--------|
| ① Extract | `bili-note` | A Bilibili video / opus URL | Timestamped transcript + full raw-material archive + note budget |
| ② Enhance | `bili-content-enhance` | A transcript Markdown file | A learning pack of 6 artifacts (with a quality gate) |

```
Bilibili URL ──[bili-note]──→ transcript.md ──[bili-content-enhance]──→ learning pack (6 files)
                subtitles/ASR/comments/evidence          summary/terms/map/animation/extras/deep-dive
```

The two skills are **independent**: install `bili-note` if you only need transcripts; install `bili-content-enhance` if you already have a transcript.

---

## 2. Universality by design

| Dimension | Constraint | Implementation |
|-----------|-----------|----------------|
| Entry point | No platform lock-in | One entry file per skill, `SKILL.md`, with standard frontmatter (`name` + `description`) and plain-Markdown instructions |
| Dependencies | Zero third-party libs | `bili-note` scripts use **Python 3.10+ stdlib only**; `validate.js` uses **Node built-ins only** |
| Browser | No tool lock-in | The logged-in route only needs **a CDP proxy exposing `GET /targets` and `GET /eval?target=<id>`** (default `http://localhost:3456`, override with `--cdp-base`). WorkBuddy `web-access` is just one implementation |
| Network / keys | No external API | No paid API calls, no API keys (only optional local ASR downloads open-source models) |
| Agent-free | Manual use works | Scripts run from the CLI; the prompt spec `references/ai_learning_prompts.md` can be followed by hand |

---

## 3. Install — pick your platform

| Platform / form | Where to put it | Notes |
|---|---|---|
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/<skill>/` | Trigger words activate automatically |
| Claude Code / Claude Desktop | `~/.claude/skills/<skill>/` | Same |
| Codex CLI | `~/.codex/skills/<skill>/` | Same |
| Cursor / Cline / Roo Code / Continue | project `.cursor/skills/` or equivalent rules dir | Add `SKILL.md` to context rules |
| Gemini CLI / OpenHands / Aider | project rules / custom instructions | Include the full `SKILL.md` |
| WPS AI / Doubao / Tongyi / assistants without a skills dir | — | Paste `SKILL.md` into the system prompt, or attach it as a context file |
| Manual (no agent) | anywhere | Run the scripts from a shell |

```bash
git clone https://github.com/Asaceoo/bili-note-skills.git
cp -r bili-note-skills/skills/bili-note ~/.claude/skills/                # swap in your platform dir
cp -r bili-note-skills/skills/bili-content-enhance ~/.claude/skills/
```

Single skill only:

```bash
git clone --filter=blob:none --sparse https://github.com/Asaceoo/bili-note-skills.git
cd bili-note-skills && git sparse-checkout set skills/bili-content-enhance
```

**Requirements**: Python 3.10+ (bili-note), Node 14+ (gate script, optional), Windows / macOS / Linux.
Windows samples use PowerShell; macOS/Linux use bash. Use `\` or `/` per platform.

---

## 4. Skill 1: bili-note (extract transcripts)

### 4.1 Route selection (the script decides; don't guess)

| Route | When | Needs |
|-------|------|-------|
| Public subtitles / opus (default) | Video has public subtitles, or the target is an opus/dynamic post | Python stdlib + access to public Bilibili endpoints |
| Browser AI subtitles | API returns only `ai-zh` and `subtitle_url` is empty | A logged-in real browser page + a CDP proxy |
| Audio ASR (fallback) | Neither subtitles nor AI subtitles available | `ffmpeg` + Qwen3-ASR (Chinese) / Whisper family (foreign languages) |

Check the environment first:

```powershell
# PowerShell: auto-detect the skill directory
$skill = @("$env:USERPROFILE\.workbuddy\skills\bili-note", "$env:USERPROFILE\.claude\skills\bili-note",
           "$env:USERPROFILE\.codex\skills\bili-note", ".\skills\bili-note") | Where-Object { Test-Path $_ } | Select-Object -First 1
& python "$skill\scripts\check_environment.py"
```

```bash
# bash / zsh
SKILL_DIR="$(ls -d "$HOME"/.workbuddy/skills/bili-note "$HOME"/.claude/skills/bili-note "$HOME"/.codex/skills/bili-note ./skills/bili-note 2>/dev/null | head -1)"
python "$SKILL_DIR/scripts/check_environment.py"
```

### 4.2 One-shot extract and archive

```bash
python "$SKILL_DIR/scripts/run_bili_note.py" "https://www.bilibili.com/video/BVxxxx/" \
  --work-dir "./tmp_bili_extract" \
  --archive-dir "./knowledge/raw/BVxxxx_short-title" \
  --comments
```

Useful flags: `--comments` (fetch comments), `--no-download-images`, `--browser-target <CDP_TARGET_ID>` (AI subtitle route), `--download-audio --transcribe --asr-backend auto` (ASR fallback).

### 4.3 Browser AI subtitles (generic CDP route)

1. Open a **logged-in** Bilibili video page through your browser automation channel (Chrome / Edge / Firefox all fine) and wait for it to load.
2. Get the target id: `curl -s http://localhost:3456/targets` (use your own base if the port differs).
3. Download: `python "$SKILL_DIR/scripts/fetch_browser_ai_subtitles.py" --target <ID> --out ./tmp_bili_extract --cdp-base http://localhost:3456`

The script only lets the logged-in page request the subtitle endpoint itself. It does **not read, export or store cookies, localStorage, profiles or tokens**. When no logged-in session is available, skip this route and state the coverage limits.

### 4.4 Archive layout

`--archive-dir` contains: `subtitles/{txt,srt,json}`, `articles/`, `images/`, `comments/`, `indexes/` (full text + evidence `.jsonl`), `metadata/` (including `note_budget.json`).
Read `metadata/note_budget.json` **before** writing (recommended length, granularity, quality multiplier, visual-dependency hints), then verify with `score_bili_note.py`.

---

## 5. Skill 2: bili-content-enhance (6 learning artifacts)

Input: a transcript with `[mm:ss]` timestamps. Output: a learning pack.

| # | Artifact | File |
|---|----------|------|
| ① | Smart summary (3–8 sections, 600–1200 chars) | `①智能摘要.md` |
| ② | Glossary (8–15 rows: term / definition / analogy / source) | `②术语表与通俗解释.md` |
| ③ | Knowledge map (mermaid mindmap ≤20 nodes + outline) | `③知识导图.md` |
| ④ | Animation (self-contained HTML, no external links) | `④动画表达.html` |
| ⑤ | Extras (background / extensions / pitfalls / practice, 📹➕ source tags) | `⑤补充知识.md` |
| ⑥ | Deep understanding (self-check / mental models / quiz / Feynman / transfer) | `⑥深度学习与理解文档.md` |

Quality gate (nothing is written until it passes):

```bash
node scripts/validate.js <learning-pack-dir>
```

Checks: mermaid syntax and node count, HTML free of `http(s)` external links with compilable inline JS, table ② has 4 non-empty columns and 8–15 rows, ① has 3–8 sections, ⑤/⑥ sections complete. Without Node, verify these rules manually.

Output location: `学习包/` next to the source transcript (or under the video's output dir). One of the two — never an invented path.

---

## 6. Manual use without an agent

1. Transcript: `python "$SKILL_DIR/scripts/run_bili_note.py" "<url>" --archive-dir "<archive-dir>"`.
2. Learning pack: open `skills/bili-content-enhance/references/ai_learning_prompts.md` and follow the six prompts with any model (or by hand).
3. Gate: `node scripts/validate.js <learning-pack-dir>` and fix until everything passes.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| CDP unreachable in `check_environment.py` | Channel not running, or port is not 3456 | Start the channel; pass the real base via `--cdp-url` / `--cdp-base` |
| Only `ai-zh`, empty `subtitle_url` | Public API does not expose AI subtitle URLs | Use the CDP route (§4.3), or `import_subtitles.py` with srt/vtt exported by a browser extension |
| Very sparse subtitles on a long video | Core content is on screen | Check `visual_dependency` in `note_budget.json`; add keyframes/OCR/multimodal review, or label the note as limited |
| ASR mis-recognizes terms (RAG→RG, ...) | Homophone errors | Correct against part titles and technical context; clarify in the extras artifact |
| Gate fails on mermaid node chars | Node text contains `[ ] ( ) " '` | Strip those characters; move timestamps to the outline |
| Gate fails on HTML external link | A CDN asset was referenced | Inline everything or drop the asset |
| Windows-style path errors | Samples use `\` | Use `/` on macOS/Linux; `$HOME` instead of `$env:USERPROFILE` |

---

## 8. Privacy and compliance

- The logged-in session is used only so the page itself can request subtitles; scripts never touch cookies, tokens or profiles.
- User browser processes are never force-killed.
- All notes and packs are written to **your own local directory**; nothing is uploaded.
- Content copyright belongs to the original authors; archived material is for personal study and retrieval.

---

## 9. Versions

| Version | Changes |
|---------|---------|
| v1.0.0 | First release: bili-content-enhance + bili-note |
| v1.1.0 | **Universal edition**: removed platform coupling (skill-dir auto-detection, browser channel abstracted to a generic CDP interface, de-branded docs and tests), added CN/EN universal manuals |
