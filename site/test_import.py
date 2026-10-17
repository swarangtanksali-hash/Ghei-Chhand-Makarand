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

    def test_order_inferred_from_any_unambiguous_value(self):
        self.assertEqual(si.infer_order(["05/10/2026", "10/17/2026"]), "MDY")
        self.assertEqual(si.infer_order(["05/10/2026", "17/10/2026"]), "DMY")
        self.assertEqual(si.infer_order(["05/10/2026"], "MDY"), "MDY")


class UrlTests(unittest.TestCase):
    def test_only_google_sheets(self):
        si.check_url("https://docs.google.com/spreadsheets/d/e/2PACX-abc/pub?output=csv")
        for bad in ("http://docs.google.com/spreadsheets/d/x", "https://evil.example/spreadsheets/x",
                    "https://docs.google.com.evil.example/spreadsheets/x", "https://docs.google.com/document/d/x",
                    "file:///etc/passwd"):
            with self.assertRaises(ValueError):
                si.check_url(bad)


class MergeTests(unittest.TestCase):
    def run_merge(self, poems, rows, imported=None):
        imported = set() if imported is None else imported
        return si.merge(poems, rows, "2026-10-18", imported), imported

    def test_new_poem_added_with_next_number_and_date(self):
        poems = copy.deepcopy(BASE)
        counts, _ = self.run_merge(poems, [("2026-10-17", POEM, "r1")])
        self.assertEqual(counts, (1, 0, 0))
        self.assertEqual(poems[-1]["n"], 2)
        self.assertEqual(poems[-1]["d"], "2026-10-17")

    def test_rerun_never_adds_the_same_row_twice(self):
        poems = copy.deepcopy(BASE)
        _, imported = self.run_merge(poems, [("2026-10-17", POEM, "r1")])
        counts, _ = self.run_merge(poems, [("2026-10-17", POEM, "r1")], imported)
        self.assertEqual(counts, (0, 1, 0))
        self.assertEqual(len(poems), 2)

    def test_repost_of_an_old_poem_on_a_new_date_is_published(self):
        poems = copy.deepcopy(BASE)
        text = "\n".join(BASE[0]["s"][0])
        counts, _ = self.run_merge(poems, [("2026-10-17", text, "r1")])
        self.assertEqual(counts[0], 1)
        self.assertEqual(poems[-1]["s"], BASE[0]["s"])
        self.assertEqual(poems[-1]["d"], "2026-10-17")
        self.assertEqual(poems[0]["e"], [])  # the old poem is left alone

    def test_double_submit_on_the_same_day_is_published_once(self):
        poems = copy.deepcopy(BASE)
        counts, _ = self.run_merge(poems, [("2026-10-17", POEM, "r1"), ("2026-10-17", POEM, "r2")])
        self.assertEqual(counts, (1, 0, 1))

    def test_edited_row_is_published_as_a_new_entry(self):
        poems = copy.deepcopy(BASE)
        _, imported = self.run_merge(poems, [("2026-10-17", POEM, "r1")])
        edited = POEM.replace("तत्व", "सत्व")
        counts, _ = self.run_merge(poems, [("2026-10-17", edited, "r1-edited")], imported)
        self.assertEqual(counts[0], 1)

    def test_missing_date_uses_today(self):
        poems = copy.deepcopy(BASE)
        self.run_merge(poems, [(None, POEM, "r1")])
        self.assertEqual(poems[-1]["d"], "2026-10-18")


class CsvTests(unittest.TestCase):
    @staticmethod
    def dates_and_text(rows):
        return [(d, p) for d, p, _ in rows]

    def test_form_layout(self):
        csv_text = 'Timestamp,Poem\n17/10/2026 07:14:00,"ओळ एक\nओळ दोन"\n,\n'
        self.assertEqual(self.dates_and_text(si.rows_from_csv(csv_text)), [("2026-10-17", "ओळ एक\nओळ दोन")])

    def test_us_form_layout_with_date_and_email_columns(self):
        # The layout of the real Form: Timestamp, Date, Poem, Email Address; US month-first dates.
        csv_text = ('Timestamp,Date,Poem,Email Address\n'
                    '10/17/2026 9:31:33,10/17/2026,"ओळ एक",\n'
                    '11/05/2026 7:00:00,,"ओळ दोन",\n'             # no Date: falls back to Timestamp, 5 Nov
                    '11/06/2026 7:00:00,11/04/2026,"ओळ तीन",\n')  # Date wins over Timestamp
        self.assertEqual(self.dates_and_text(si.rows_from_csv(csv_text)), [
            ("2026-10-17", "ओळ एक"), ("2026-11-05", "ओळ दोन"), ("2026-11-04", "ओळ तीन")])

    def test_row_ids_differ_per_submission_and_are_stable(self):
        csv_text = 'Timestamp,Poem\n10/17/2026 9:31:33,"ओळ"\n10/17/2026 9:31:59,"ओळ"\n'
        ids = [r[2] for r in si.rows_from_csv(csv_text)]
        self.assertNotEqual(ids[0], ids[1])
        self.assertEqual(ids, [r[2] for r in si.rows_from_csv(csv_text)])

    def test_headerless_single_column(self):
        self.assertEqual(self.dates_and_text(si.rows_from_csv('"ओळ एक\nओळ दोन"\n')), [(None, "ओळ एक\nओळ दोन")])


if __name__ == "__main__":
    unittest.main()
