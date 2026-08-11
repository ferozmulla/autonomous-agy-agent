"""Unit tests for src/config.py — slugify and naming functions."""

import pytest

from src.config import (
    get_ca_backend_service_name,
    get_dataset_name,
    get_frontend_service_name,
    slugify,
)


class TestSlugify:
    """Tests for the slugify() function."""

    def test_simple_name(self) -> None:
        assert slugify("SiriusXM") == "siriusxm"

    def test_two_word_name(self) -> None:
        assert slugify("JPMorgan Chase") == "jpmorgan_chase"

    def test_ampersand(self) -> None:
        assert slugify("AT&T") == "at_t"

    def test_leading_trailing_spaces(self) -> None:
        assert slugify("  Procter & Gamble  ") == "procter_gamble"

    def test_hyphens_become_underscores(self) -> None:
        assert slugify("Coca-Cola") == "coca_cola"

    def test_multiple_spaces(self) -> None:
        assert slugify("Bank  of   America") == "bank_of_america"

    def test_special_characters(self) -> None:
        assert slugify("Yahoo!") == "yahoo"

    def test_single_word(self) -> None:
        assert slugify("Apple") == "apple"

    def test_numbers_preserved(self) -> None:
        assert slugify("3M Company") == "3m_company"

    def test_mixed_case(self) -> None:
        assert slugify("McKinsey") == "mckinsey"

    def test_dots_become_underscores(self) -> None:
        assert slugify("S&P Global") == "s_p_global"

    def test_empty_string(self) -> None:
        assert slugify("") == ""


class TestNamingFunctions:
    """Tests for dataset and service naming functions."""

    def test_get_dataset_name(self) -> None:
        assert get_dataset_name("siriusxm") == "siriusxm_demo"
        assert get_dataset_name("jpmorgan_chase") == "jpmorgan_chase_demo"

    def test_get_frontend_service_name(self) -> None:
        assert get_frontend_service_name("siriusxm") == "siriusxm-frontend"
        assert get_frontend_service_name("apple") == "apple-frontend"

    def test_get_ca_backend_service_name(self) -> None:
        assert get_ca_backend_service_name("siriusxm") == "siriusxm-ca-backend"
        assert get_ca_backend_service_name("apple") == "apple-ca-backend"
