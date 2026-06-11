from cost import CostEstimate, DEFAULT_INPUT_PRICE_PER_M, DEFAULT_OUTPUT_PRICE_PER_M, approx_tokens


def test_approx_tokens_scales_with_length():
    assert approx_tokens("") == 0
    assert approx_tokens("hello") >= 1
    assert approx_tokens("x" * 400) >= 100


def test_record_accumulates():
    ce = CostEstimate()
    ce.record("you are park", "hi", "right.")
    ce.record("you are volkov", "ack", "hah.")
    assert ce.calls == 2
    assert ce.input_tokens > 0
    assert ce.output_tokens > 0


def test_usd_uses_default_pricing():
    ce = CostEstimate()
    ce.input_tokens = 1_000_000
    ce.output_tokens = 0
    assert abs(ce.estimated_usd - DEFAULT_INPUT_PRICE_PER_M) < 0.001


def test_render_changes_after_recording():
    ce = CostEstimate()
    pre = ce.render()
    ce.record("sys", "user", "reply")
    post = ce.render()
    assert "no LLM calls" in pre
    assert "no LLM calls" not in post
    assert "Estimated cost" in post


def test_pricing_can_be_overridden():
    ce = CostEstimate(input_price_per_m=1.0, output_price_per_m=2.0)
    ce.input_tokens = 1_000_000
    ce.output_tokens = 1_000_000
    assert abs(ce.estimated_usd - 3.0) < 0.001
