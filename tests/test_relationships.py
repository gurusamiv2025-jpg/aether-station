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
        # New pipe-syntax: `a -->|label| b` (GitHub-renderer-friendly).
        assert f"{a} -->|" in out
        assert f"| {b}" in out


def test_mermaid_labels_have_no_unescaped_quotes():
    """GitHub's Mermaid parser chokes on embedded quotes inside edge labels."""
    out = to_mermaid()
    for line in out.splitlines():
        if "-->|" not in line:
            continue
        label = line.split("-->|", 1)[1].rsplit("|", 1)[0]
        assert '"' not in label
        assert "'" not in label
