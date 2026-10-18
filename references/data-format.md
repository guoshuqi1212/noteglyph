# JSON 数据格式

一份 JSON 就是一个卡组，也是续写时的工作底稿。完整可运行的例子：

- `examples/starter.json`：原创结构模板，用到了全部固定图形。
- `examples/lunyu.json`：中文卡组，含 `outline_entries`（8 条提要，5 张卡）。
- `examples/meditations.json`：英文卡组。

新书请复制结构，**替换全部内容**。

## 顶层

```json
{
  "book": {
    "lang": "zh",
    "kind": "book",
    "title": "书名",
    "subtitle": "原书名 / 作者 / 版本或译者",
    "volume": 1,
    "intro": "一句话说明本卡组的范围。",
    "source_name": "书目、版本、译者",
    "source_url": "https://example.com/source",
    "editorial_note": "哪些是原文，哪些是编者归纳；参照了哪些注释。"
  },
  "topics": {
    "学习": "本主题的一句话提要。",
    "行事": "另一个主题。"
  },
  "outline_entries": [],
  "cards": []
}
```

| 字段 | 说明 |
|---|---|
| `book.lang` | `"zh"`（默认）或 `"en"`。决定界面文案、主题标签规则、报错语言。 |
| `book.kind` | `"book"`（默认）、`"paper"`、`"article"`。决定标题后缀，如“读书笔记 / 论文笔记”。 |
| `book.volume` | 正整数，默认 1。 |
| `book.source_url`、卡片 `source.url` | 可留空；填写时只接受完整的 `http(s)` 地址。 |
| `topics` 的键 | 中文卡组：**恰好两个汉字**。英文卡组：一到两个英文单词，最长 16 个字符（如 `Judgment`、`Common Good`）。 |

## 卡片

```json
{
  "number": 13,
  "topic": "学习",
  "title": ["前半句的结论，", "后半句补出因果"],
  "summary": "这条观点的准确含义、适用边界和原文背景。",
  "diagram_alt": "给读屏软件的图示文字说明",
  "diagram_svg": "<line x1=\"280\" y1=\"14\" x2=\"280\" y2=\"214\" class=\"grey-stroke dash\" stroke-width=\"1.2\"/>",
  "quote": {
    "kind": "quote",
    "text": "卡组语言写的引文或意译。",
    "original": "可选：原语言节选。"
  },
  "source": { "locator": "第 3 章第二节", "url": "" },
  "interpretation_note": "可选：跨章节综合、借用注释或编者推论的说明。"
}
```

- `title` 必须正好两行。
- `diagram_svg` 只写 `viewBox 0 0 560 228` 内的子元素，规则见 `design-system.md` 第 5 节。
- `source.locator` 必填，要诚实，例如“用户提供的第 3 章摘录”；不知道页码就不写页码。

### `quote.kind`

| 值 | 中文标签 | 英文标签 | 含义 |
|---|---|---|---|
| `quote` | 原文节选 | Quote | `text` 是逐字原文（或注明译者的已出版译文） |
| `quote_translation` | 原文节选 / 中文意译 | Quote / Translation | `original` 是逐字原文，`text` 是你的翻译 |
| `paraphrase` | 意译 | Paraphrase | 忠实转述，不是逐字 |
| `editorial` | 编辑提炼 | Editorial | 编者自己的总结 |

`quote_translation` 必须填写 `original`。页面上只有逐字内容会加引号。

v1.2 的旧写法仍然有效：`kind` 写中文标签，`zh` / `en` 两个字段会被当作 `text` / `original` 读取。

## 编号与 `outline_entries`

- `cards[].number` 升序、不重复。没有 `outline_entries` 时必须连续。
- 先整理长文时，把全部候选写进 `outline_entries`：编号整体连续，每条有 `number`、`topic`、`title`、`summary`，可选 `source`。整本书就列全书的候选，不只列已制卡的。
- 卡片张数没有上限，渲染器也不限制数量；张数由内容决定（见 `SKILL.md` 规则 ④）。
- 已制卡的编号必须出现在 `outline_entries` 里；提要视图会把它们标成“已制卡 ✓”，其余标“待制卡”。

```json
"outline_entries": [
  { "number": 1, "topic": "学习", "title": "第一条主张", "summary": "简述", "source": { "locator": "第 1 章", "url": "" } },
  { "number": 2, "topic": "学习", "title": "还没画成卡的第二条", "summary": "简述与判断", "source": { "locator": "第 2 章", "url": "" } }
]
```

## 续写

1. 备份旧文件，例如 `my-notes.json` → `my-notes.backup.json`。
2. 保留旧卡的内容与编号；新卡从最大编号接着编。
3. 证据不足以画图的候选，先放进 `outline_entries`。
4. `python scripts/render.py my-notes.json --check-only` 通过后再生成 HTML。
5. 检查筛选、深色模式、来源链接、单卡存图，然后交付 HTML 和 JSON。
