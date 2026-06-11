from foundry_iq import LocalRetriever


def test_park_coffee_retrievable():
    r = LocalRetriever()
    results = r.retrieve("Park coffee ritual four minutes pour", top_k=4)
    assert any("park-coffee" in p.source for p in results)


def test_chipped_cup_anecdote_lives_in_lore():
    r = LocalRetriever()
    results = r.retrieve("chipped cup steel mug 2089 EVA", top_k=4)
    assert any("park-coffee" in p.source for p in results)
