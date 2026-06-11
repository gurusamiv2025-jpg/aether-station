from i18n import LANGUAGES, STRINGS, t


def test_french_and_german_present():
    assert "fr" in LANGUAGES
    assert "de" in LANGUAGES
    assert LANGUAGES["fr"] == "Français"
    assert LANGUAGES["de"] == "Deutsch"


def test_every_string_has_french_and_german():
    for key, bag in STRINGS.items():
        for lang in ("fr", "de"):
            assert lang in bag, f"missing {lang} for key={key}"


def test_french_welcome_includes_recognizable_phrase():
    fr = t("welcome_par1", "fr")
    assert "Aether" in fr or "Mira-7" in fr


def test_german_welcome_includes_recognizable_phrase():
    de = t("welcome_par1", "de")
    assert "Aether" in de or "Mira-7" in de


def test_signoff_translated():
    assert t("welcome_par4", "fr") == "Enregistré."
    assert t("welcome_par4", "de") == "Protokolliert."
