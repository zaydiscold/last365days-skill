import csv
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "last365days" / "scripts" / "persist.py"


class PersistCliTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.temp_path = Path(self.temp_dir.name)
        self.research_dir = self.temp_path / "research"
        self.report_dir = self.temp_path / "report-out"
        self.research_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.home_dir = self.temp_path / "home"
        self.home_dir.mkdir(parents=True, exist_ok=True)

    def run_cli(self, *args, input_text=None, extra_env=None):
        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        env["PATH"] = ""
        if extra_env:
            env.update(extra_env)
        command = [
            sys.executable,
            str(SCRIPT_PATH),
            "--research-dir",
            str(self.research_dir),
            "--report-path",
            str(self.report_dir),
            *args,
        ]
        return subprocess.run(
            command,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def write_profile(self, slug, content):
        path = self.research_dir / f"{slug}.md"
        path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return path

    def write_report(self, payload):
        report_path = self.report_dir / "report.json"
        report_path.write_text(json.dumps(payload), encoding="utf-8")
        return report_path

    def test_slugify_normalizes_unicode(self):
        result = self.run_cli("slugify", "Cafe del Mar")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "cafe-del-mar")

    def test_match_sorts_exact_high_and_medium_confidence(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-01
            ### Synthesis
            Exact match profile.
            ---
            """,
        )
        self.write_profile(
            "saba",
            """
            # Saba

            ## 2026-03-02
            ### Synthesis
            High confidence profile.
            ---
            """,
        )
        self.write_profile(
            "nafees-khan",
            """
            # Nafees Khan

            ## 2026-03-03
            ### Synthesis
            Medium confidence profile.
            ---
            """,
        )

        result = self.run_cli("match", "Saba", "Nafees")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [match["confidence"] for match in payload["matches"]],
            ["exact", "high", "medium"],
        )

    def test_match_returns_no_matches_for_blank_input(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-01
            ### Synthesis
            Existing profile.
            ---
            """,
        )

        result = self.run_cli("match", "")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["matches"], [])

    def test_history_includes_same_day_update_entries(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-05

            ### Synthesis
            First run of the day.

            ---

            #### Update at 14:30

            ### Synthesis
            Follow-up run of the day.

            ---

            ## 2026-03-06

            ### Synthesis
            Next day.

            ---
            """,
        )

        result = self.run_cli("history", "saba-nafees")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        labels = [entry["date"] for entry in payload["entries"]]
        self.assertEqual(
            labels,
            ["2026-03-05", "2026-03-05 (update at 14:30)", "2026-03-06"],
        )

    def test_search_can_be_limited_to_one_profile(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-05
            ### Synthesis
            Shared keyword appears here.
            ---
            """,
        )
        self.write_profile(
            "kanye-west",
            """
            # Kanye West

            ## 2026-03-05
            ### Synthesis
            Shared keyword appears there too.
            ---
            """,
        )

        result = self.run_cli("search", "shared", "keyword", "--slug", "saba-nafees")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["results"][0]["slug"], "saba-nafees")

    def test_doctor_reports_missing_report_but_bundled_engine_exists(self):
        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["dependencies"]["research_engine"]["status"], "ok")
        self.assertEqual(payload["report_json"]["status"], "warn")

    def test_doctor_validates_report_shape_and_optional_qmd(self):
        self.write_report(
            {
                "topic": "Saba Nafees",
                "range": {"from": "2026-03-01", "to": "2026-03-30"},
                "reddit": [],
                "x": [],
                "youtube": [],
                "tiktok": [],
                "instagram": [],
                "hackernews": [],
                "polymarket": [],
                "web": [],
            }
        )

        result = self.run_cli("doctor")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["dependencies"]["research_engine"]["status"], "ok")
        self.assertEqual(
            payload["dependencies"]["research_engine"]["path"],
            str(REPO_ROOT / "last365days" / "scripts" / "last30days.py"),
        )
        self.assertEqual(payload["report_json"]["status"], "ok")
        self.assertEqual(payload["dependencies"]["qmd"]["status"], "warn")

    def test_diff_returns_unified_diff_between_dates(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-05

            ### Synthesis
            Old insight line.

            ---

            ## 2026-03-12

            ### Synthesis
            New insight line.

            ---
            """,
        )

        result = self.run_cli("diff", "saba-nafees", "2026-03-05", "2026-03-12")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("-Old insight line.", payload["diff"])
        self.assertIn("+New insight line.", payload["diff"])

    def test_export_single_profile_json_is_structured(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-05

            ### Synthesis
            First synthesis.

            ### Sources
            - Reddit: 1 thread

            ### Notable Items
            - @handle: example

            *Research window: 2026-03-01 to 2026-03-05*

            ---
            """,
        )

        result = self.run_cli("export", "saba-nafees", "--format", "json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["slug"], "saba-nafees")
        self.assertEqual(payload["entry_count"], 1)
        self.assertEqual(payload["entries"][0]["synthesis"], "First synthesis.")
        self.assertEqual(
            payload["entries"][0]["research_window"],
            "2026-03-01 to 2026-03-05",
        )

    def test_export_rejects_path_traversal_slug(self):
        outside_file = self.temp_path / "outside.md"
        outside_file.write_text("# Outside\n", encoding="utf-8")

        result = self.run_cli("export", "../outside", "--format", "md")
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertIn("error", payload)

    def test_export_all_profiles_csv_flattens_entries(self):
        self.write_profile(
            "saba-nafees",
            """
            # Saba Nafees

            ## 2026-03-05

            ### Synthesis
            First synthesis.

            ---

            ## 2026-03-06

            ### Synthesis
            Second synthesis.

            ---
            """,
        )
        self.write_profile(
            "kanye-west",
            """
            # Kanye West

            ## 2026-03-05

            ### Synthesis
            Another profile.

            ---
            """,
        )

        result = self.run_cli("export", "--all", "--format", "csv")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = list(csv.DictReader(result.stdout.splitlines()))
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            {(row["slug"], row["date"]) for row in rows},
            {
                ("saba-nafees", "2026-03-05"),
                ("saba-nafees", "2026-03-06"),
                ("kanye-west", "2026-03-05"),
            },
        )


if __name__ == "__main__":
    unittest.main()
