"""Tests for sheet_import.py.  Run:  python -m unittest discover -s site"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheet_import as si  # noqa: E402

POEM = """[17/10/26, 7:14 am] Makarand Joshi: *🙏॥ श्रीराम समर्थ ॥🙏*
*रामनाम हे जीवनाचे तत्व ।*
*24*7 चे महत्त्व*

*शांती समाधान मनी वसे ॥*
*भावछंद : घेई छंद मकरंद*"""

BASE = [{"n": 1, "d": "2025-01-01", "r": "", "inv": "", "g": "",
         "s": [["अरे तुझे मन का तळमळसी", "माणसा तुला का न झोप लागसी ।", "श्रीराम हा प्रश्न माणसाला करती"]],
         "e": []}]


class ParseTests(unittest.TestCase):
    def test_strips_copy_prefix_bold_and_splits_parts(self):
        inv, stanzas, sig = si.parse_poem(POEM)
        self.assertEqual(inv, "🙏॥ श्रीराम समर्थ ॥🙏")
        self.assertEqual(stanzas, [["रामनाम हे जीवनाचे तत्व ।", "24*7 चे महत्त्व"], ["शांती समाधान मनी वसे ॥"]])
        self.assertEqual(sig, "भावछंद : घेई छंद मकरंद")

    def test_export_style_prefix(self):
        _, stanzas, _ = si.parse_poem("17/10/26, 7:14 am - Makarand Joshi: ओळ एक\nओळ दोन")
        self.assertEqual(stanzas, [["ओळ एक", "ओळ दोन"]])

    def test_rejects_empty_and_oversized(self):
        self.assertIsNone(si.parse_poem(""))
        self.assertIsNone(si.parse_poem("*भावछंद : घेई छंद मकरंद*"))
        self.assertIsNone(si.parse_poem("क" * (si.MAX_POEM_CHARS + 1)))
        self.assertIsNone(si.parse_poem("\n".join(["ओळ"] * (si.MAX_LINES + 1))))


class DateTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(si.parse_date("17/10/2026 07:14:00"), "2026-10-17")
        self.assertEqual(si.parse_date("10/17/2026 07:14:00"), "2026-10-17")
        self.assertEqual(si.parse_date("05/10/2026", "DMY"), "2026-10-05")
        self.assertEqual(si.parse_date("05/10/2026", "MDY"), "2026-05-10")
        self.assertEqual(si.parse_date("2026-10-17"), "2026-10-17")
        self.assertIsNone(si.parse_date("31/02/2026"))
        self.assertIsNone(si.parse_date("yesterday"))


class UrlTests(unittest.TestCase):
    def test_only_google_sheets(self):
        si.check_url("https://docs.google.com/spreadsheets/d/e/2PACX-abc/pub?output=csv")
        for bad in ("http://docs.google.com/spreadsheets/d/x", "https://evil.example/spreadsheets/x",
                    "https://docs.google.com.evil.example/spreadsheets/x", "https://docs.google.com/document/d/x",
                    "file:///etc/passwd"):
            with self.assertRaises(ValueError):
                si.check_url(bad)


class MergeTests(unittest.TestCase):
    def test_new_poem_added_with_next_number_and_date(self):
        poems = copy.deepcopy(BASE)
        a, r, s = si.merge(poems, [("2026-10-17", POEM)], "2026-10-18")
        self.assertEqual((a, r, s), (1, 0, 0))
        self.assertEqual(poems[-1]["n"], 2)
        self.assertEqual(poems[-1]["d"], "2026-10-17")

    def test_rerun_is_idempotent(self):
        poems = copy.deepcopy(BASE)
        si.merge(poems, [("2026-10-17", POEM)], "2026-10-18")
        a, r, s = si.merge(poems, [("2026-10-17", POEM)], "2026-10-18")
        self.assertEqual((a, r, s), (0, 0, 1))
        self.assertEqual(len(poems), 2)

    def test_existing_poem_with_formatting_differences_is_skipped(self):
        poems = copy.deepcopy(BASE)
        text = "*अरे तुझे मन का तळमळसी*\n*माणसा तुला का न झोप लागसी*\n*श्रीराम हा प्रश्न माणसाला करती ।*"
        self.assertEqual(si.merge(poems, [(None, text)], "2026-10-18"), (0, 0, 1))

    def test_revision_keeps_old_text_as_earlier_version(self):
        poems = copy.deepcopy(BASE)
        text = "अरे तुझे मन का तळमळसी\nमाणसा तुला का न झोप लागसी ।\nश्रीराम हा प्रश्न माणसाला करिती"
        self.assertEqual(si.merge(poems, [("2026-10-17", text)], "2026-10-18"), (0, 1, 0))
        p = poems[0]
        self.assertEqual(p["s"][0][2], "श्रीराम हा प्रश्न माणसाला करिती")
        self.assertEqual(p["e"][0]["s"], BASE[0]["s"])
        self.assertEqual(p["e"][0]["d"], "2025-01-01")
        self.assertEqual(p["r"], "2026-10-17")

    def test_missing_date_uses_today(self):
        poems = copy.deepcopy(BASE)
        si.merge(poems, [(None, POEM)], "2026-10-18")
        self.assertEqual(poems[-1]["d"], "2026-10-18")


class CsvTests(unittest.TestCase):
    def test_form_layout(self):
        csv_text = 'Timestamp,Poem\n17/10/2026 07:14:00,"ओळ एक\nओळ दोन"\n,\n'
        self.assertEqual(si.rows_from_csv(csv_text), [("2026-10-17", "ओळ एक\nओळ दोन")])

    def test_headerless_single_column(self):
        self.assertEqual(si.rows_from_csv('"ओळ एक\nओळ दोन"\n'), [(None, "ओळ एक\nओळ दोन")])


if __name__ == "__main__":
    unittest.main()
