# Contributing · 参与贡献

Thanks for improving NoteGlyph! 欢迎改进。

1. For changes to behaviour or to the visual grammar, open an issue first. 改动行为或图形语义前，请先开 issue 讨论。
2. Keep the meaning of every shape and color. Do not add colors or decorative icons. 保持符号含义不变，不加新颜色或装饰图标。
3. Run the checks / 提交前运行：

   ```bash
   python -m unittest discover -s tests -v
   python scripts/render.py examples/lunyu.json --check-only
   python scripts/render.py examples/meditations.json --check-only
   ```

4. If you change the template, renderer or example JSON, rebuild the demo pages (CI fails if they are stale). 改了模板、渲染器或示例数据，要重新生成示例页面（不同步时 CI 会失败）：

   ```bash
   python scripts/render.py examples/lunyu.json --out docs/lunyu.html
   python scripts/render.py examples/meditations.json --out docs/meditations.html
   ```

5. Examples must be original, public domain, or explicitly licensed for redistribution. Never add copyrighted books, long excerpts, PDFs/EPUBs or private data. 示例只用原创、公版或明确可再分发的材料。
6. Keep sourced quotations, translations and editorial synthesis clearly separated. 原文、译文和编者归纳要分开标注。

All contributions are made under the project's MIT License. 所有贡献均以本项目的 MIT 许可发布。
