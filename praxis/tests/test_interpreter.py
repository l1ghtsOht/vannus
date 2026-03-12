from praxis.interpreter import interpret


def test_interpret_marketing_restaurant():
    q = "I need marketing help for my restaurant to grow sales"
    out = interpret(q)
    assert out.get("intent") == "marketing"
    assert out.get("industry") == "restaurant"
    assert out.get("goal") == "growth"
    assert "marketing" in out.get("keywords")
