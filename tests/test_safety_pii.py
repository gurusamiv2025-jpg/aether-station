from safety import check_input, refusal_for


def test_email_is_blocked():
    v = check_input("My email is gv@example.com — can you log that?")
    assert not v.allowed
    assert v.category == "pii"


def test_phone_is_blocked():
    v = check_input("My number is 415-555-0199. Note it.")
    assert not v.allowed
    assert v.category == "pii"


def test_ssn_shaped_is_blocked():
    v = check_input("I'm 555-12-9876.")
    assert not v.allowed
    assert v.category == "pii"


def test_normal_text_with_numbers_passes():
    # Years and short numbers should not trip the PII regex.
    v = check_input("Tell me about the 2093 Halberd tug loss.")
    assert v.allowed


def test_pii_refusal_uses_character_voice():
    park = refusal_for("park", "pii")
    volkov = refusal_for("volkov", "pii")
    assert park
    assert "Nyet" in volkov or "phone" in volkov
    assert park != volkov
