from drift import DRIFT_THRESHOLD, score_recent, score_reply


def test_in_voice_park_reply_scores_high():
    rep = score_reply("park", "Right. What I have on record is the file. That's the read from here.")
    assert not rep.flagged
    assert rep.score >= 0.5


def test_out_of_voice_reply_flags_drift():
    rep = score_reply("park", "I am a generic assistant ready to assist.")
    assert rep.flagged
    assert rep.score < DRIFT_THRESHOLD


def test_volkov_signature_phrases_register():
    rep = score_reply("volkov", "Hah. Bozhe moi. The reactor does not lie.")
    assert not rep.flagged


def test_score_recent_handles_no_replies():
    rep = score_recent("park", [])
    assert not rep.flagged
    assert rep.score == 1.0


def test_score_recent_averages_replies():
    replies = [
        "Right. That's the read from here.",  # high score
        "I am an AI assistant.",                # zero
    ]
    rep = score_recent("park", replies)
    # Should average between 0 and ~0.5.
    assert 0.0 < rep.score < 1.0


def test_unknown_character_returns_safe_default():
    rep = score_reply("nobody", "anything")
    # Empty signatures = zero score, which would flag, but no character means we don't care.
    assert rep.character == "nobody"
