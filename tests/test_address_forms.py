from llm import ADDRESS_FORMS, address_form


def test_park_calls_volkov_kostya():
    assert address_form("park", "volkov") == "Kostya"


def test_mira_uses_formal_titles():
    assert address_form("mira", "park") == "Commander Park"
    assert address_form("mira", "okafor") == "Dr. Okafor"


def test_unknown_pair_falls_back_to_titled_key():
    assert address_form("park", "nobody") == "Nobody"


def test_every_known_pair_resolves_for_built_in_cast():
    keys = ["park", "okafor", "mira", "volkov", "hua"]
    for a in keys:
        for b in keys:
            if a == b:
                continue
            form = address_form(a, b)
            assert form and len(form) > 0
