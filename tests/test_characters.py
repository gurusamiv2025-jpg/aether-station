from characters import CHARACTERS, all_characters, get


def test_cast_size():
    assert len(CHARACTERS) == 5


def test_every_character_has_a_dossier_file():
    from pathlib import Path

    lore_crew = Path(__file__).resolve().parent.parent / "lore" / "crew"
    for ch in all_characters():
        assert (lore_crew / f"{ch.key}.md").exists(), (
            f"missing dossier for {ch.key}"
        )


def test_system_prompts_reference_ground_truth_rules():
    for ch in all_characters():
        assert "GROUND TRUTH" in ch.system_prompt, ch.key
        assert "voice" in ch.system_prompt.lower(), ch.key


def test_get_by_key():
    assert get("park").name.startswith("Cmdr.")
    assert get("mira").role == "Station AI"
