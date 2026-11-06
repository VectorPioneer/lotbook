from conftest import d

from lotbook.dates import add_years, is_long_term


def test_add_years_same_day():
    assert add_years(d("2024-03-10"), 1) == d("2025-03-10")


def test_add_years_leap_day_maps_to_28_february():
    assert add_years(d("2024-02-29"), 1) == d("2025-02-28")


def test_sold_on_anniversary_is_short_term():
    assert not is_long_term(d("2024-03-10"), d("2025-03-10"))


def test_sold_day_after_anniversary_is_long_term():
    assert is_long_term(d("2024-03-10"), d("2025-03-11"))


def test_leap_day_start():
    assert not is_long_term(d("2024-02-29"), d("2025-02-28"))
    assert is_long_term(d("2024-02-29"), d("2025-03-01"))
