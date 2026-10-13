"""Validation, rendering and safety tests (stdlib unittest only)."""
import copy
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("noteglyph_render", ROOT / "scripts" / "render.py")
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


def load(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class ExamplesTests(unittest.TestCase):
    def test_all_examples_valid(self):
        for name in ("starter.json", "lunyu.json", "meditations.json"):
            with self.subTest(name=name):
                data = render.check_data(load(name))
                self.assertTrue(data["cards"])

    def test_docs_pages_match_examples(self):
        for name in ("lunyu", "meditations"):
            with self.subTest(name=name):
                expected = render.make_html(load(f"{name}.json"))
                actual = (ROOT / "docs" / f"{name}.html").read_text(encoding="utf-8")
                self.assertEqual(expected, actual, f"docs/{name}.html is stale; re-render it")

    def test_generates_standalone_html(self):
        text = render.make_html(load("lunyu.json"))
        self.assertIn("<!doctype html>", text.lower())
        self.assertIn('<html lang="zh-CN">', text)
        self.assertIn("<title>论语 · 视觉读书笔记</title>", text)
        for slot in ("__BOOK_DATA_JSON__", "__HTML_LANG__", "__PAGE_TITLE__"):
            self.assertNotIn(slot, text)

    def test_english_page(self):
        text = render.make_html(load("meditations.json"))
        self.assertIn('<html lang="en">', text)
        self.assertIn("<title>Meditations · Visual Reading Notes</title>", text)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.zh = load("starter.json")
        self.en = load("meditations.json")

    def assertInvalid(self, data):
        with self.assertRaises(ValueError):
            render.check_data(data)

    def test_rejects_duplicate_card_ids(self):
        self.zh["cards"][1]["number"] = 1
        self.assertInvalid(self.zh)

    def test_rejects_noncontinuous_ids_without_outline(self):
        self.zh["cards"][1]["number"] = 8
        self.zh["cards"][2]["number"] = 9
        self.assertInvalid(self.zh)

    def test_outline_allows_gaps_in_cards(self):
        data = load("lunyu.json")
        numbers = [c["number"] for c in data["cards"]]
        self.assertNotEqual(numbers, list(range(1, len(numbers) + 1)))
        render.check_data(data)

    def test_outline_must_cover_cards(self):
        data = load("lunyu.json")
        data["outline_entries"] = data["outline_entries"][:2]
        self.assertInvalid(data)

    def test_zh_topic_must_be_two_characters(self):
        self.zh["topics"]["三个字"] = "not allowed"
        self.assertInvalid(self.zh)

    def test_en_topics(self):
        ok = copy.deepcopy(self.en)
        ok["topics"]["Common Good"] = "two words are fine"
        render.check_data(ok)
        for bad in ("Three Word Topic", "Waytoolongtopiclabel", "中文", "Judgment!"):
            with self.subTest(topic=bad):
                data = copy.deepcopy(self.en)
                data["topics"][bad] = "x"
                self.assertInvalid(data)

    def test_rejects_unknown_lang_and_kind(self):
        self.zh["book"]["lang"] = "fr"
        self.assertInvalid(self.zh)
        data = load("starter.json")
        data["book"]["kind"] = "novel"
        self.assertInvalid(data)

    def test_legacy_quote_fields_are_normalised(self):
        data = load("starter.json")
        data["cards"][0]["quote"] = {"kind": "原文节选 / 中文意译", "zh": "译文", "en": "Original line"}
        quote = render.check_data(data)["cards"][0]["quote"]
        self.assertEqual(quote, {"kind": "quote_translation", "text": "译文", "original": "Original line"})

    def test_quote_translation_needs_original(self):
        self.en["cards"][0]["quote"] = {"kind": "quote_translation", "text": "A translation"}
        self.assertInvalid(self.en)

    def test_rejects_unknown_quote_kind(self):
        self.en["cards"][0]["quote"]["kind"] = "summary"
        self.assertInvalid(self.en)

    def test_title_must_have_two_lines(self):
        self.zh["cards"][0]["title"] = ["只有一行"]
        self.assertInvalid(self.zh)

    def test_source_locator_required(self):
        self.zh["cards"][0]["source"]["locator"] = " "
        self.assertInvalid(self.zh)


class SvgSafetyTests(unittest.TestCase):
    def setUp(self):
        self.data = load("starter.json")

    def with_svg(self, svg):
        data = copy.deepcopy(self.data)
        data["cards"][0]["diagram_svg"] = svg
        return data

    def assertRejected(self, svg):
        with self.assertRaises(ValueError):
            render.check_data(self.with_svg(svg))

    def test_rejects_script(self):
        self.assertRejected('<script>alert(1)</script>')

    def test_rejects_event_handler(self):
        self.assertRejected('<circle cx="20" cy="20" r="4" onclick="alert(1)" />')

    def test_rejects_foreign_object_and_image(self):
        self.assertRejected('<foreignObject><div/></foreignObject>')
        self.assertRejected('<image href="https://example.com/x.png"/>')

    def test_rejects_unknown_class(self):
        self.assertRejected('<circle cx="20" cy="20" r="4" class="red-fill"/>')

    def test_rejects_url_in_attribute(self):
        self.assertRejected('<rect x="0" y="0" width="5" height="5" fill="url(#x)"/>')

    def test_unique_shape_reference_only(self):
        render.check_data(self.with_svg('<use href="#ng-unique" transform="translate(40 40)" class="green-fill"/>'))
        self.assertRejected('<use href="#other" />')
        self.assertRejected('<use href="https://example.com/a.svg#x" />')
        self.assertRejected('<use />')
        self.assertRejected('<rect x="0" y="0" width="5" height="5" href="#ng-unique"/>')

    def test_rejects_non_http_source(self):
        data = copy.deepcopy(self.data)
        data["cards"][0]["source"]["url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            render.check_data(data)

    def test_script_breakout_is_escaped(self):
        data = copy.deepcopy(self.data)
        data["cards"][0]["summary"] = "</script><script>alert(1)</script>"
        page = render.make_html(data)
        self.assertNotIn("</script><script>alert(1)</script>", page)
        self.assertIn(r"\u003c/script\u003e", page)

    def test_title_is_html_escaped(self):
        data = copy.deepcopy(self.data)
        data["book"]["title"] = "<b>Book</b>"
        page = render.make_html(data)
        self.assertIn("<title>&lt;b&gt;Book&lt;/b&gt;", page)


class CliTests(unittest.TestCase):
    def test_check_only_exit_codes(self):
        self.assertEqual(render.main([str(ROOT / "examples" / "lunyu.json"), "--check-only"]), 0)
        with tempfile.TemporaryDirectory() as tmp:
            bad = pathlib.Path(tmp) / "bad.json"
            bad.write_text("{}", encoding="utf-8")
            self.assertEqual(render.main([str(bad), "--check-only"]), 1)


if __name__ == "__main__":
    unittest.main()
