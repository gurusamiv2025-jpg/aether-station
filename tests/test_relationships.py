from characters import CHARACTERS
from relationships import EDGES, to_mermaid


def test_every_edge_endpoint_is_a_real_character():
    for a, b, _ in EDGES:
        assert a in CHARACTERS, a
        assert b in CHARACTERS, b


def test_mermaid_output_compiles():
    out = to_mermaid()
    assert out.startswith("graph LR")
    for a, b, _ in EDGES:
        assert f"{a} --" in out
        assert f"--> {b}" in out
