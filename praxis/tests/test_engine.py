from praxis.interpreter import interpret
from praxis.engine import find_tools


def test_find_tools_returns_results():
    q = "I need marketing help for my restaurant to grow sales"
    struct = interpret(q)
    results = find_tools(struct, top_n=5)
    assert isinstance(results, list)
    assert len(results) > 0
    # each result should have name and description
    for r in results:
        assert hasattr(r, "name")
        assert hasattr(r, "description")
