#!/usr/bin/env python3
"""NoteGlyph renderer: validate a notes JSON file and build a standalone HTML gallery.

Standard library only, works offline. The JSON is written by an agent or editor;
SVG diagram fragments are checked against a small allow-list of elements,
attributes and semantic classes before they are embedded.

    python scripts/render.py notes.json --check-only
    python scripts/render.py notes.json --out notes.html
"""
import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

__version__ = '1.3.0'

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'assets' / 'gallery-template.html'

LANGS = {'zh', 'en'}
KINDS = {'book', 'paper', 'article'}
# Canonical quote kinds. Chinese labels from v1.2 files are accepted as aliases.
QUOTE_KINDS = {'quote', 'quote_translation', 'paraphrase', 'editorial'}
QUOTE_ALIASES = {
    '原文节选': 'quote',
    '原文节选 / 中文意译': 'quote_translation',
    '意译': 'paraphrase',
    '编辑提炼': 'editorial',
}
VERBATIM_KINDS = {'quote', 'quote_translation'}

ALLOWED_ELEMENTS = {'g', 'line', 'path', 'circle', 'rect', 'text', 'ellipse', 'polyline', 'polygon', 'use'}
ALLOWED_ATTRS = {
    'class', 'd', 'x', 'y', 'x1', 'y1', 'x2', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
    'width', 'height', 'transform', 'text-anchor', 'stroke-width', 'stroke-dasharray',
    'fill', 'stroke', 'opacity', 'points', 'stroke-linecap', 'stroke-linejoin',
    'font-size', 'font-weight', 'letter-spacing', 'aria-hidden', 'href'
}
ALLOWED_CLASSES = {
    'tx', 'sm', 'mid', 'strong', 'tiny', 'grey-shape', 'grey-stroke',
    'grey-stroke-strong', 'green-fill', 'green-stroke', 'wash-fill',
    'dash', 'you', 'you-tx'
}
UNIQUE_SHAPE_REF = '#ng-unique'
ZH_TOPIC = re.compile(r'[\u4e00-\u9fff]{2}')
EN_TOPIC = re.compile(r"[A-Za-z][A-Za-z'\-]*(?: [A-Za-z][A-Za-z'\-]*)?")
EN_TOPIC_MAX = 16


class NoteError(ValueError):
    pass


class Checker:
    """Validates one notes file. Messages follow the deck language."""

    def __init__(self, lang='zh'):
        self.lang = lang if lang in LANGS else 'zh'

    def t(self, zh, en):
        return en if self.lang == 'en' else zh

    def fail(self, zh, en):
        raise NoteError(self.t(zh, en))

    def nonempty_str(self, value, where):
        if not isinstance(value, str) or not value.strip():
            self.fail(f'{where}: 需要非空字符串', f'{where}: must be a non-empty string')
        return value

    def safe_url(self, url, where):
        if url in (None, ''):
            return
        if not isinstance(url, str):
            self.fail(f'{where}: 必须是字符串', f'{where}: must be a string')
        p = urlparse(url)
        if p.scheme not in {'https', 'http'} or not p.netloc:
            self.fail(f'{where}: 仅允许完整 http(s) URL', f'{where}: only absolute http(s) URLs are allowed')

    def topic_ok(self, tag):
        if self.lang == 'en':
            return len(tag) <= EN_TOPIC_MAX and EN_TOPIC.fullmatch(tag) is not None
        return ZH_TOPIC.fullmatch(tag) is not None

    def check_diagram(self, svg, where):
        if not isinstance(svg, str) or len(svg) > 32000:
            self.fail(f'{where}: diagram_svg 必须是小于 32k 字符的 SVG 图元片段',
                      f'{where}: diagram_svg must be an SVG fragment under 32k characters')
        try:
            root = ET.fromstring('<root>' + svg + '</root>')
        except ET.ParseError as exc:
            self.fail(f'{where}: diagram_svg XML 解析失败: {exc}', f'{where}: diagram_svg is not valid XML: {exc}')
        for el in root.iter():
            if el is root:
                continue
            if el.tag not in ALLOWED_ELEMENTS:
                self.fail(f'{where}: 不允许的 SVG 标签 {el.tag!r}', f'{where}: SVG element {el.tag!r} is not allowed')
            for attr, value in el.attrib.items():
                if attr not in ALLOWED_ATTRS:
                    self.fail(f'{where}: SVG 属性 {attr!r} 不允许', f'{where}: SVG attribute {attr!r} is not allowed')
                if attr == 'class' and not set(value.split()).issubset(ALLOWED_CLASSES):
                    self.fail(f'{where}: 出现未定义的 SVG 语义类: {value!r}', f'{where}: unknown semantic class {value!r}')
                if attr == 'href' and (el.tag != 'use' or value != UNIQUE_SHAPE_REF):
                    self.fail(f'{where}: href 只能用于 <use href="{UNIQUE_SHAPE_REF}">',
                              f'{where}: href is only allowed as <use href="{UNIQUE_SHAPE_REF}">')
                low = value.lower()
                if 'url(' in low or 'javascript:' in low or '<' in value:
                    self.fail(f'{where}: SVG 属性出现不允许的内容', f'{where}: SVG attribute contains disallowed content')
            if el.tag == 'use' and el.get('href') != UNIQUE_SHAPE_REF:
                self.fail(f'{where}: <use> 必须写 href="{UNIQUE_SHAPE_REF}"', f'{where}: <use> needs href="{UNIQUE_SHAPE_REF}"')
        if len(list(root)) == 0:
            self.fail(f'{where}: diagram_svg 不能为空', f'{where}: diagram_svg is empty')

    def normalize_quote(self, quote, where):
        """Return a quote dict with canonical keys: kind, text, original."""
        if not isinstance(quote, dict):
            self.fail(f'{where}.quote 必须是对象', f'{where}.quote must be an object')
        kind = QUOTE_ALIASES.get(quote.get('kind'), quote.get('kind'))
        if kind not in QUOTE_KINDS:
            self.fail(f'{where}.quote.kind 无效：可用 quote / quote_translation / paraphrase / editorial（或旧版中文标签）',
                      f'{where}.quote.kind must be one of quote / quote_translation / paraphrase / editorial')
        # v1.3 fields: text (deck language) + original (source-language excerpt).
        # v1.2 fields: zh + en. Read them as text + original.
        text = quote['text'] if 'text' in quote else quote.get('zh')
        original = quote['original'] if 'original' in quote else quote.get('en', '')
        self.nonempty_str(text, f'{where}.quote.text')
        if original is None:
            original = ''
        if not isinstance(original, str):
            self.fail(f'{where}.quote.original 必须是字符串', f'{where}.quote.original must be a string')
        if kind == 'quote_translation' and not original.strip():
            self.fail(f'{where}: quote_translation 需要 original（原语言节选）',
                      f'{where}: quote_translation needs the source-language excerpt in "original"')
        return {'kind': kind, 'text': text, 'original': original}

    def check(self, data):
        if not isinstance(data, dict):
            self.fail('顶层必须是 JSON 对象', 'top level must be a JSON object')
        book = data.get('book')
        if not isinstance(book, dict):
            self.fail('缺少 book 对象', 'missing "book" object')
        lang = book.get('lang', 'zh')
        if lang not in LANGS:
            self.fail('book.lang 只能是 "zh" 或 "en"', 'book.lang must be "zh" or "en"')
        self.lang = lang
        kind = book.get('kind', 'book')
        if kind not in KINDS:
            self.fail('book.kind 只能是 book / paper / article', 'book.kind must be book / paper / article')
        for field in ('title', 'subtitle', 'intro', 'source_name'):
            self.nonempty_str(book.get(field), f'book.{field}')
        self.safe_url(book.get('source_url', ''), 'book.source_url')
        volume = book.get('volume', 1)
        if type(volume) is not int or volume < 1:
            self.fail('book.volume 必须是正整数', 'book.volume must be a positive integer')

        topics = data.get('topics')
        if not isinstance(topics, dict) or not topics:
            self.fail('topics 必须是带描述的主题映射', '"topics" must map each topic to a one-line summary')
        for tag, summary in topics.items():
            if not self.topic_ok(tag):
                self.fail(f'主题 {tag!r} 不是两个汉字', f'topic {tag!r} must be one or two words, at most {EN_TOPIC_MAX} characters')
            self.nonempty_str(summary, f'topics.{tag}')

        cards = data.get('cards')
        if not isinstance(cards, list) or not cards:
            self.fail('cards 必须包含至少一张卡片', '"cards" needs at least one card')
        nums = []
        for index, card in enumerate(cards):
            where = f'cards[{index}]'
            if not isinstance(card, dict):
                self.fail(f'{where}: 应为对象', f'{where}: must be an object')
            number = card.get('number')
            if type(number) is not int or number < 1:
                self.fail(f'{where}.number 必须是正整数', f'{where}.number must be a positive integer')
            nums.append(number)
            if card.get('topic') not in topics:
                self.fail(f'{where}.topic 未在 topics 中声明', f'{where}.topic is not declared in "topics"')
            title = card.get('title')
            if not isinstance(title, list) or len(title) != 2:
                self.fail(f'{where}.title 必须是两个独立行的字符串数组', f'{where}.title must be an array of exactly two lines')
            for i, line in enumerate(title):
                self.nonempty_str(line, f'{where}.title[{i}]')
            self.nonempty_str(card.get('summary'), f'{where}.summary')
            self.nonempty_str(card.get('diagram_alt'), f'{where}.diagram_alt')
            self.check_diagram(card.get('diagram_svg'), where)
            card['quote'] = self.normalize_quote(card.get('quote'), where)
            source = card.get('source')
            if not isinstance(source, dict):
                self.fail(f'{where}.source 必须存在', f'{where}.source is required')
            self.nonempty_str(source.get('locator'), f'{where}.source.locator')
            self.safe_url(source.get('url', ''), f'{where}.source.url')
            note = card.get('interpretation_note')
            if note is not None and not isinstance(note, str):
                self.fail(f'{where}.interpretation_note 必须是字符串', f'{where}.interpretation_note must be a string')
        if nums != sorted(set(nums)):
            self.fail('卡片编号必须按升序排列且不可重复', 'card numbers must be ascending and unique')

        outlines = data.get('outline_entries')
        if outlines is not None:
            if not isinstance(outlines, list) or not outlines:
                self.fail('outline_entries 必须是非空列表', '"outline_entries" must be a non-empty list')
            ids = []
            for i, item in enumerate(outlines):
                where = f'outline_entries[{i}]'
                if not isinstance(item, dict) or type(item.get('number')) is not int:
                    self.fail(f'{where}.number 必须是整数', f'{where}.number must be an integer')
                ids.append(item['number'])
                if item.get('topic') not in topics:
                    self.fail(f'{where}.topic 必须是已有主题', f'{where}.topic is not declared in "topics"')
                for field in ('title', 'summary'):
                    self.nonempty_str(item.get(field), f'{where}.{field}')
                if item.get('source') is not None:
                    if not isinstance(item['source'], dict):
                        self.fail(f'{where}.source 必须是对象', f'{where}.source must be an object')
                    self.safe_url(item['source'].get('url', ''), f'{where}.source.url')
            if ids != list(range(ids[0], ids[0] + len(ids))):
                self.fail('文字提要必须全局编号连续', 'outline numbers must be consecutive')
            if not set(nums).issubset(set(ids)):
                self.fail('outline_entries 必须包含每一张已制卡的编号', '"outline_entries" must include every card number')
        elif nums != list(range(nums[0], nums[0] + len(nums))):
            self.fail('卡片编号必须连续；若有待制卡条目，请提供 outline_entries',
                      'card numbers must be consecutive; use "outline_entries" to list items not yet carded')
        if nums[0] != 1:
            print(self.t(f'提示：这一份是续写卡组，编号从 #{nums[0]:02d} 开始。',
                         f'Note: this deck continues from #{nums[0]:02d}.'), file=sys.stderr)
        return data


def check_data(data):
    """Validate a notes dict in place (quotes are normalised) and return it."""
    return Checker().check(data)


def make_html(data):
    """Validate (on a copy) and return the standalone HTML page as a string."""
    data = check_data(json.loads(json.dumps(data)))
    template = TEMPLATE.read_text('utf-8')
    for slot in ('__BOOK_DATA_JSON__', '__HTML_LANG__', '__PAGE_TITLE__'):
        if template.count(slot) != 1:
            raise NoteError(f'template slot {slot} must appear exactly once')
    book = data['book']
    lang = book.get('lang', 'zh')
    suffix = {
        'zh': {'book': '视觉读书笔记', 'paper': '视觉论文笔记', 'article': '视觉阅读笔记'},
        'en': {'book': 'Visual Reading Notes', 'paper': 'Visual Paper Notes', 'article': 'Visual Reading Notes'},
    }[lang][book.get('kind', 'book')]
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    # Keep JSON inert inside an inline <script>.
    payload = payload.replace('<', r'\u003c').replace('>', r'\u003e').replace('&', r'\u0026')
    payload = payload.replace('\u2028', r'\u2028').replace('\u2029', r'\u2029')
    return (template
            .replace('__HTML_LANG__', 'en' if lang == 'en' else 'zh-CN')
            .replace('__PAGE_TITLE__', html.escape(f"{book['title']} · {suffix}"))
            .replace('__BOOK_DATA_JSON__', payload))


def main(argv=None):
    ap = argparse.ArgumentParser(description='Validate NoteGlyph JSON and render a standalone HTML gallery.')
    ap.add_argument('input', type=Path, help='notes JSON file')
    ap.add_argument('--out', type=Path, help='output HTML path (default: input name with .html)')
    ap.add_argument('--check-only', action='store_true', help='validate only, do not write HTML')
    ap.add_argument('--version', action='version', version=f'NoteGlyph {__version__}')
    args = ap.parse_args(argv)
    try:
        data = check_data(json.loads(args.input.read_text(encoding='utf-8')))
        en = data['book'].get('lang') == 'en'
        if args.check_only:
            msg = (f"OK: {data['book']['title']}, {len(data['cards'])} cards, {len(data['topics'])} topics" if en
                   else f"验证通过：{data['book']['title']}，{len(data['cards'])} 张，{len(data['topics'])} 个主题")
            print(msg)
            return 0
        out = args.out or args.input.with_suffix('.html')
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(make_html(data), encoding='utf-8')
        print(f'{"Wrote" if en else "已生成"} {out.resolve()} | {len(data["cards"])} {"cards" if en else "张卡片"}')
        return 0
    except (NoteError, OSError, json.JSONDecodeError) as exc:
        print(f'错误 / Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
