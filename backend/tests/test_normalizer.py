from __future__ import annotations

from app.services.normalizer import normalise, split_sections
from tests.conftest import RESUME_TEXT


def test_sections_are_split_by_heading():
    sections, prelude = split_sections(RESUME_TEXT)
    assert "experience" in sections
    assert "education" in sections
    assert any("Muhammad Haris" in line for line in prelude)


def test_contact_details_are_extracted():
    extracted = normalise(RESUME_TEXT)
    assert extracted["email"] == "haris@example.com"
    assert extracted["phone"]
    assert any("github.com/haris" in link for link in extracted["links"])


def test_name_is_guessed_from_the_prelude():
    assert normalise(RESUME_TEXT)["full_name"] == "Muhammad Haris"


def test_skills_list_is_parsed():
    skills = normalise(RESUME_TEXT)["listed_skills"]
    assert "React" in skills
    assert "Git" in skills


def test_experience_bullets_and_weak_phrases_are_detected():
    extracted = normalise(RESUME_TEXT)
    assert extracted["experience"]
    assert extracted["weak_bullets"]
    assert any("Responsible for" in bullet for bullet in extracted["weak_bullets"])


def test_quantified_bullets_are_counted():
    assert normalise(RESUME_TEXT)["quantified_bullets"] >= 1


def test_misspelling_is_detected():
    extracted = normalise("Experience\nResponsible for teh dashboard.")
    assert extracted["spelling_issues"]


def test_years_of_experience_parsed():
    assert normalise(RESUME_TEXT)["years_experience"] == 3.0


def test_empty_text_does_not_crash():
    extracted = normalise("")
    assert extracted["sections_present"] == []
    assert extracted["word_count"] == 0
