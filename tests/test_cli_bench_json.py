import json

import cli


def test_bench_json_emits_parsable(capsys):
    rc = cli.main(["bench", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "queries" in data and "results" in data
    keys = {row["character"] for row in data["results"]}
    assert {"park", "okafor", "mira", "volkov", "hua"} <= keys
    for row in data["results"]:
        for field in ("retrieved_pct", "avg_score", "in_voice_pct"):
            assert field in row
