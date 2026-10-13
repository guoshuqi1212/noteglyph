# 让 Agent 帮你安装 · Install with your agent

把下面一段发给能操作终端和文件的 Agent（Claude Code、Codex、Cursor 等）。纯网页聊天的助手无法替你安装。

## 中文

```text
请在当前项目里安装并验证 Agent Skill「NoteGlyph（图见）」：https://github.com/guoshuqi1212/noteglyph

1. 先读仓库里的 README.md、SKILL.md 和 LICENSE，看一下 scripts/ 里会运行的脚本。
2. 如果有 Node.js，运行 npx skills add guoshuqi1212/noteglyph（默认装到当前项目，不要加 -g）。
   没有 npx 时，按你（当前 Agent）的约定，把整个仓库目录复制到项目的 skills 目录里，包括 SKILL.md、references/、assets/、scripts/、examples/。
3. 不要全局安装、不要申请管理员权限、不要改无关配置；遇到权限或安全提示先问我。
4. 装好后确认能识别 name: noteglyph。有 Python 3.9+ 的话，在 Skill 目录里运行：
   python -m unittest discover -s tests -v
   python scripts/render.py examples/lunyu.json --check-only
5. 告诉我安装路径、识别结果、测试结果和遇到的限制。没验证通过之前，不要说安装成功。
```

## English

```text
Install and verify the NoteGlyph Agent Skill in my current project: https://github.com/guoshuqi1212/noteglyph

1. Read README.md, SKILL.md and LICENSE, and look at the scripts in scripts/ before running anything.
2. If Node.js is available, run `npx skills add guoshuqi1212/noteglyph` (project scope by default; do not add -g).
   Without npx, copy the whole repository into your project's skills directory for this agent, including SKILL.md, references/, assets/, scripts/ and examples/.
3. Do not install globally, request admin rights or change unrelated settings; ask me before any permission or security prompt.
4. Confirm the skill is detected as `noteglyph`. If Python 3.9+ is available, run inside the skill directory:
   python -m unittest discover -s tests -v
   python scripts/render.py examples/meditations.json --check-only
5. Report the install path, detection result, test results and any blockers. Do not claim success until verification passes.
```

## 从本地文件夹安装 · From a local folder

还没发布或无法访问 GitHub 时，把上面链接换成本地解压后的文件夹路径，并让 Agent 走“没有 npx”那一步。

If the repository is not reachable, replace the URL with the path to an unzipped copy and have the agent follow the “without npx” step.
