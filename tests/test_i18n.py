from i18n import DEFAULT_LANG, LANGUAGES, STRINGS, t


def test_default_language_is_english():
    assert DEFAULT_LANG == "en"


def test_three_languages_supported():
    assert set(LANGUAGES) >= {"en", "es", "hi"}


def test_every_string_has_every_language():
    for key, bag in STRINGS.items():
        for lang in LANGUAGES:
            assert lang in bag, f"missing {lang} for key={key}"


def test_unknown_key_returns_key():
    assert t("nonexistent_key") == "nonexistent_key"


def test_unknown_lang_falls_back_to_default():
    en = t("welcome_par1", "en")
    # "ja" (Japanese) is not defined; should fall back to English.
    ja = t("welcome_par1", "ja")
    assert en == ja


def test_spanish_welcome_includes_recognizable_phrase():
    es = t("welcome_par1", "es")
    assert "Aether" in es or "Mira-7" in es
