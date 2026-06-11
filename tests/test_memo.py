from memo import MemoBook


def test_first_reply_recorded_once():
    mb = MemoBook()
    added = mb.record_turn("park", {"role": "assistant", "content": "hi"})
    assert "first_reply" in added
    added = mb.record_turn("park", {"role": "assistant", "content": "hi again"})
    assert added == []  # Already recorded


def test_first_refusal_recorded():
    mb = MemoBook()
    added = mb.record_turn("park", {"role": "assistant", "content": "no", "refused": True})
    assert "first_refusal" in added


def test_crisis_first_only_once():
    mb = MemoBook()
    assert mb.record_crisis_first("LiF-A")
    assert not mb.record_crisis_first("Ring 3 O2")  # 2nd crisis doesn't add


def test_dialogue_first_recorded():
    mb = MemoBook()
    assert mb.record_dialogue_first("park", "volkov", "HB-441")
    assert not mb.record_dialogue_first("park", "okafor", "anything")


def test_to_markdown_lists_memos():
    mb = MemoBook()
    mb.record_turn("park", {"role": "assistant", "content": "first"})
    md = mb.to_markdown()
    assert "First reply" in md


def test_to_markdown_empty_handled():
    assert "no memos" in MemoBook().to_markdown().lower()


def test_to_dict_serialises_each_memo():
    mb = MemoBook()
    mb.record_turn("park", {"role": "assistant", "content": "first"})
    mb.record_crisis_first("LiF-A")
    d = mb.to_dict()
    assert len(d) == 2
    assert all("ts" in row and "kind" in row for row in d)
