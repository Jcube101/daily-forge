"""Tests for streak logic, timezone, and text utilities."""

from datetime import date

import pytest

from daily_forge.models import (
    build_heatmap,
    build_weekly_recap,
    calculate_streaks,
    count_x_characters,
    effective_dates,
    format_thread,
    get_daily_prompt,
    split_text_to_chunks,
    split_thread_items,
    today_in_timezone,
)


class TestTimezone:
    def test_today_in_timezone_utc(self):
        result = today_in_timezone("UTC")
        assert isinstance(result, date)

    def test_today_in_timezone_invalid_falls_back(self):
        result = today_in_timezone("Not/A/Timezone")
        assert isinstance(result, date)


class TestStreaks:
    def test_new_user(self):
        current, longest, status, _ = calculate_streaks(set(), date(2026, 6, 28))
        assert current == 0
        assert longest == 0
        assert status == "new"

    def test_posted_today(self):
        dates = {"2026-06-28"}
        current, _, status, _ = calculate_streaks(dates, date(2026, 6, 28))
        assert current == 1
        assert status == "posted_today"

    def test_at_risk_not_posted_today(self):
        dates = {"2026-06-27"}
        current, _, status, _ = calculate_streaks(dates, date(2026, 6, 28))
        assert current == 1
        assert status == "at_risk"

    def test_broken_streak(self):
        dates = {"2026-06-25"}
        current, _, status, _ = calculate_streaks(dates, date(2026, 6, 28))
        assert current == 0
        assert status == "broken"

    def test_consecutive_streak(self):
        dates = {"2026-06-26", "2026-06-27", "2026-06-28"}
        current, longest, status, _ = calculate_streaks(dates, date(2026, 6, 28))
        assert current == 3
        assert longest == 3
        assert status == "posted_today"

    def test_longest_streak_with_gap(self):
        dates = {"2026-06-01", "2026-06-02", "2026-06-03", "2026-06-10", "2026-06-11"}
        _, longest, _, _ = calculate_streaks(dates, date(2026, 6, 11))
        assert longest == 3

    def test_freeze_extends_streak(self):
        entries = {"2026-06-27"}
        freezes = {"2026-06-28"}
        active = effective_dates(entries, freezes)
        current, _, status, _ = calculate_streaks(entries, date(2026, 6, 28), freezes)
        assert "2026-06-28" in active
        assert current == 2
        assert status == "posted_today"


class TestHeatmap:
    def test_heatmap_ends_today_exactly_52_weeks(self):
        today = date(2026, 6, 29)
        cells = build_heatmap(set(), today, weeks=52)
        assert len(cells) == 52 * 7
        assert cells[0]["date"] == "2025-07-01"
        assert cells[-1]["date"] == "2026-06-29"

    def test_heatmap_includes_freeze_level(self):
        cells = build_heatmap(
            {"2026-06-27"},
            date(2026, 6, 28),
            weeks=2,
            freeze_dates={"2026-06-28"},
        )
        frozen = next(c for c in cells if c["date"] == "2026-06-28")
        assert frozen["level"] == 1
        assert frozen["frozen"] is True
        assert frozen["posted"] is False


class TestCharCount:
    def test_plain_text(self):
        assert count_x_characters("hello") == 5

    def test_url_weighted(self):
        text = "Check https://example.com/very/long/path now"
        assert count_x_characters(text) < len(text)
        assert count_x_characters(text) == len(text) - len("https://example.com/very/long/path") + 23

    def test_empty(self):
        assert count_x_characters("") == 0


class TestThreadSplit:
    def test_short_text_single_chunk(self):
        chunks = split_text_to_chunks("Short post", 280)
        assert chunks == ["Short post"]

    def test_long_text_multiple_chunks(self):
        text = "word " * 100
        chunks = split_text_to_chunks(text.strip(), 50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert count_x_characters(chunk) <= 50

    def test_split_thread_items(self):
        items = ["First point", "Second point"]
        chunks = split_thread_items(items, 280)
        assert len(chunks) == 2
        assert chunks[0]["text"].startswith("1/2")
        assert chunks[1]["text"].startswith("2/2")

    def test_format_thread(self):
        result = format_thread(["A", "B"])
        assert "1/2 A" in result
        assert "2/2 B" in result


class TestWeeklyRecap:
    def test_recap_structure(self):
        entries = [
            {
                "entry_date": "2026-06-28",
                "content": "Hello world",
                "post_type": "single",
                "posted_at": "2026-06-28T12:00:00+00:00",
            }
        ]
        recap = build_weekly_recap({"2026-06-28"}, entries, date(2026, 6, 28))
        assert recap["posts_this_week"] == 1
        assert len(recap["week_days"]) == 7
        assert len(recap["streak_trend"]) == 7


class TestPrompts:
    def test_prompt_stable_per_day(self):
        d = date(2026, 6, 28)
        assert get_daily_prompt(d) == get_daily_prompt(d)
        assert isinstance(get_daily_prompt(d), str)