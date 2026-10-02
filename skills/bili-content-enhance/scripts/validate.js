#!/usr/bin/env node
// 学习包质量门禁校验脚本（通用版）
// 用法: node validate.js <学习包目录>
// 校验 bili-content-enhance 生成的 6 份物料是否符合输出契约。
// 依赖: Node.js（无第三方包）。无 Node 时可按 SKILL.md「质量门禁」节人工核对。
"use strict";

const fs = require("fs");
const vm = require("vm");
const path = require("path");

const dir = process.argv[2] || ".";
const files = {
  "①智能摘要.md": "s1",
  "②术语表与通俗解释.md": "s2",
  "③知识导图.md": "s3",
  "④动画表达.html": "s4",
  "⑤补充知识.md": "s5",
  "⑥深度学习与理解文档.md": "s6"
};

function read(name) {
  try { return fs.readFileSync(path.join(dir, name), "utf8"); } catch (e) { return null; }
}

const results = {};
for (const [name, id] of Object.entries(files)) {
  const content = read(name);
  if (content === null) { results[id] = { name, pass: false, err: "文件不存在" }; continue; }
  const errs = [];
  switch (id) {
    case "s1": {
      if (!/^## 智能摘要/m.test(content)) errs.push("缺 ## 智能摘要");
      const chapters = content.match(/^### /gm) || [];
      if (chapters.length < 3 || chapters.length > 8) errs.push(`章节数 ${chapters.length} 不在 3-8`);
      if (content.length < 600) errs.push(`过短 ${content.length}`);
      break;
    }
    case "s2": {
      const lines = content.split("\n");
      const data = lines.filter(l => /^\|/.test(l) && !/^\|[\s-]+\|[\s-]+\|[\s-]+\|[\s-]+\|$/.test(l) && !/^\| 术语 /.test(l));
      if (data.length < 8 || data.length > 15) errs.push(`术语行数 ${data.length} 不在 8-15`);
      const bad = data.filter(l => {
        const cells = l.split("|").slice(1, -1);
        return cells.length !== 4 || cells.some(c => c.trim() === "");
      });
      if (bad.length) errs.push(`${bad.length} 行非4列或含空列`);
      break;
    }
    case "s3": {
      const m = content.match(/```mermaid\n([\s\S]*?)```/);
      if (!m) errs.push("缺 mermaid 代码块");
      else {
        const mm = m[1];
        if (!/^\s*root\(/m.test(mm)) errs.push("缺 root( 根节点");
        const nodeLines = mm.split("\n").filter(l => l.trim() && !l.trim().startsWith("mindmap") && !/^\s*root\(/.test(l));
        if (nodeLines.length > 20) errs.push(`mermaid 节点数 ${nodeLines.length} > 20`);
        const badChars = nodeLines.filter(l => /[\[\]()"']/.test(l));
        if (badChars.length) errs.push(`节点含禁用字符: ${badChars[0]}`);
      }
      if (!/^## 层级大纲/m.test(content)) errs.push("缺 ## 层级大纲");
      break;
    }
    case "s4": {
      if (/src\s*=\s*["']https?:|href\s*=\s*["']https?:/.test(content)) errs.push("含外部 http 资源");
      const scripts = content.match(/<script>([\s\S]*?)<\/script>/g) || [];
      if (!scripts.length) errs.push("缺 <script>");
      for (const s of scripts) {
        const body = s.replace(/^<script>/, "").replace(/<\/script>$/, "");
        try { new vm.Script(body); } catch (e) { errs.push(`JS 语法错误: ${e.message}`); }
      }
      if (!/播放|暂停|单步|重置/.test(content)) errs.push("缺交互控件关键词");
      if (!/<canvas/.test(content)) errs.push("缺 canvas");
      break;
    }
    case "s5": {
      const sections = ["背景知识", "延伸拓展", "常见误区", "实践建议"];
      for (const s of sections) if (!content.includes(`### ${s}`)) errs.push(`缺 ### ${s}`);
      if (!content.includes("📹")) errs.push("缺 📹 标签");
      if (!content.includes("➕")) errs.push("缺 ➕ 标签");
      if (content.length < 800) errs.push(`过短 ${content.length}`);
      break;
    }
    case "s6": {
      const sections = ["理解度自检", "核心心智模型", "概念地图补全", "自测题", "费曼输出题", "应用迁移", "与深度学习 / AI 的关联"];
      for (const s of sections) if (!content.includes(`### ${s}`)) errs.push(`缺 ### ${s}`);
      const checks = content.match(/- \[ \]/g) || [];
      if (checks.length < 3) errs.push(`自检项 ${checks.length} < 3`);
      break;
    }
  }
  results[id] = { name, pass: errs.length === 0, err: errs.join("; ") };
}

console.log("=== 学习包校验结果 ===");
let allPass = true;
for (const [id, r] of Object.entries(results)) {
  console.log(`${r.pass ? "PASS" : "FAIL"} ${r.name}${r.err ? " — " + r.err : ""}`);
  if (!r.pass) allPass = false;
}
console.log(allPass ? "\n全部通过 ✓" : "\n存在未通过项 ✗");
process.exit(allPass ? 0 : 1);
