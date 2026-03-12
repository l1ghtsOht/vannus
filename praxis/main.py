# ---------------- Praxis CLI — AI Decision Engine ----------------
"""
Interactive command-line interface for Praxis.

Supports two modes:
    1. Quick search  — type a query, get tool recommendations
    2. Guided flow   — build a profile, get a composed AI stack with explanations

Commands:
    profile          — create / update your user profile
    stack            — get a full stack recommendation (uses profile)
    search <query>   — quick keyword search (legacy mode)
    compare A vs B   — side-by-side tool comparison
    learn            — run the learning cycle (recompute signals from feedback)
    feedback / stats — view feedback summary
    categories       — list all tool categories
    help             — show available commands
    exit             — quit
"""

try:
    from .engine import find_tools
    from .interpreter import interpret
    from .data import get_all_categories
    from .feedback import record_feedback, summary, get_entries
    from .profile import UserProfile, build_profile_interactive, load_profile, save_profile
    from .stack import compose_stack, compare_tools
    from .explain import explain_tool
    from .learning import run_learning_cycle
except Exception:
    from engine import find_tools
    from interpreter import interpret
    from data import get_all_categories
    from feedback import record_feedback, summary, get_entries
    from profile import UserProfile, build_profile_interactive, load_profile, save_profile
    from stack import compose_stack, compare_tools
    from explain import explain_tool
    from learning import run_learning_cycle


# ======================================================================
# Helpers
# ======================================================================

def _print_separator():
    print("-" * 60)


def _print_stack_result(result, profile=None):
    """Pretty-print a stack recommendation."""
    stack = result.get("stack", [])
    explanation = result.get("explanation", {})
    alternatives = result.get("alternatives", [])

    if not stack:
        print("\nNo matching tools found for your profile.")
        return

    # Narrative
    print(f"\n{'=' * 60}")
    print("  YOUR RECOMMENDED AI STACK")
    print(f"{'=' * 60}")

    if explanation.get("narrative"):
        print(f"\n{explanation['narrative']}")

    if explanation.get("total_monthly_cost"):
        print(f"\nEstimated cost: {explanation['total_monthly_cost']}")
    if explanation.get("stack_fit_score"):
        print(f"Overall fit score: {explanation['stack_fit_score']}%")

    _print_separator()

    # Per-tool details
    for idx, entry in enumerate(stack, 1):
        tool = entry["tool"]
        role = entry["role"]
        tool_expl = None
        for te in explanation.get("tool_explanations", []):
            if te.get("tool_name") == tool.name:
                tool_expl = te
                break

        print(f"\n  [{idx}] {tool.name}  —  {role.upper()}")
        print(f"      {tool.description}")
        if tool.url:
            print(f"      URL: {tool.url}")

        # Pricing
        pricing = tool.pricing or {}
        if pricing:
            parts = []
            if pricing.get("free_tier"):
                parts.append("Free tier available")
            if pricing.get("starter"):
                parts.append(f"From ${pricing['starter']}/mo")
            if pricing.get("enterprise"):
                parts.append(f"Enterprise: {pricing['enterprise']}")
            if parts:
                print(f"      Pricing: {' • '.join(parts)}")

        # Explanation
        if tool_expl:
            if tool_expl.get("reasons"):
                print("      Why:")
                for r in tool_expl["reasons"][:4]:
                    print(f"        ✓ {r}")
            if tool_expl.get("caveats"):
                print("      Watch out:")
                for c in tool_expl["caveats"][:2]:
                    print(f"        ⚠ {c}")
            if tool_expl.get("fit_score"):
                print(f"      Fit: {tool_expl['fit_score']}%")

    # Integration notes
    int_notes = explanation.get("integration_notes", [])
    if int_notes:
        print(f"\n  Integrations:")
        for note in int_notes:
            print(f"    ↔ {note}")

    # Alternatives
    if alternatives:
        _print_separator()
        print("\n  Also considered:")
        for alt in alternatives[:3]:
            print(f"    • {alt.name} — {alt.description[:60]}...")

    _print_separator()


def _handle_feedback(results, intent_struct, user_input, filters, profile):
    """Handle the feedback flow after showing results."""
    sel = input("\nEnter the number of a tool you tried (or press Enter to skip): ").strip()
    if not sel:
        return
    try:
        sel_idx = int(sel) - 1
        # Flatten tools from stack or direct list
        if isinstance(results, list):
            tool_list = results
        else:
            tool_list = [e["tool"] for e in results.get("stack", [])]

        if 0 <= sel_idx < len(tool_list):
            chosen = tool_list[sel_idx]
            rating_input = input(f"Rate '{chosen.name}' 1-10 (or press Enter to skip): ").strip()
            if rating_input:
                try:
                    rating = int(rating_input)
                    if 1 <= rating <= 10:
                        details = {
                            "intent_struct": intent_struct,
                            "category_filters": filters,
                            "profile_id": profile.profile_id if profile else None,
                            "mode": "stack" if not isinstance(results, list) else "search",
                        }
                        accepted = rating >= 6
                        record_feedback(
                            intent_struct.get("raw", user_input),
                            chosen.name,
                            accepted=accepted,
                            rating=rating,
                            details=details,
                        )
                        print(f"Thanks — feedback recorded for {chosen.name} (rating: {rating})")
                    else:
                        print("Rating out of range; skipping feedback.")
                except ValueError:
                    print("Invalid rating; skipping feedback.")
        else:
            print("Invalid selection; skipping feedback.")
    except ValueError:
        print("Invalid input; skipping feedback.")


# ======================================================================
# Main loop
# ======================================================================

def run():
    print("\n" + "=" * 60)
    print("  PRAXIS — AI Decision Engine")
    print("  Find the right AI tools for your needs")
    print("=" * 60)
    print("\nCommands: profile | stack | compare | learn | feedback | categories | help | exit")
    print("Or just type what you need and press Enter.\n")

    # Try to load default profile
    profile = load_profile("default")
    if profile:
        print(f"Loaded profile: {profile.industry or 'general'} / {profile.budget} budget / {profile.skill_level} skill")
    else:
        print("No profile found. Type 'profile' to create one for personalized recommendations.")

    while True:
        user_input = input("\n> ").strip()
        if not user_input:
            continue

        cmd = user_input.lower()

        # ---- Exit ----
        if cmd == "exit":
            print("Goodbye.")
            break

        # ---- Help ----
        if cmd == "help":
            print("""
Available commands:
  profile          Create or update your user profile
  stack            Get a full AI stack recommendation
  compare X vs Y   Compare two tools side-by-side
  learn            Run the learning cycle (improve from feedback)
  feedback/stats   View feedback summary
  categories       List all tool categories
  help             Show this message
  exit             Quit

Or type any query to search for tools.
""")
            continue

        # ---- Profile ----
        if cmd == "profile":
            profile = build_profile_interactive("default")
            continue

        # ---- Feedback / Stats ----
        if cmd in ("show feedback", "feedback", "stats"):
            s = summary()
            print(f"\nFeedback — total: {s['total']}, accepted: {s['accepted']}, rejected: {s['rejected']}")
            show = input("Show recent entries? (y/n): ").strip().lower()
            if show.startswith("y"):
                entries = get_entries(50)
                if not entries:
                    print("No feedback entries yet.")
                else:
                    print("\nRecent feedback (newest first):")
                    for e in entries:
                        print(f"  {e['timestamp']} | {e['tool']} | rating={e.get('rating')} | accepted={e.get('accepted')}")
            continue

        # ---- Categories ----
        if cmd in ("categories", "list categories", "show categories"):
            cats = get_all_categories()
            print("\nAvailable categories:")
            for c in cats:
                print(f"  • {c}")
            continue

        # ---- Learn ----
        if cmd == "learn":
            print("Running learning cycle...")
            signals = run_learning_cycle()
            quality = signals.get("tool_quality", {})
            print(f"Processed {len(quality)} tools from feedback data.")
            top = sorted(quality.items(), key=lambda x: x[1].get("avg_rating", 0), reverse=True)[:5]
            if top:
                print("Top-rated tools:")
                for name, metrics in top:
                    print(f"  {name}: avg rating {metrics['avg_rating']}, "
                          f"accept rate {metrics['accept_rate']:.0%}, "
                          f"trend: {metrics['recent_trend']}")
            continue

        # ---- Compare ----
        if cmd.startswith("compare ") and " vs " in cmd:
            parts = cmd.replace("compare ", "").split(" vs ")
            if len(parts) == 2:
                result = compare_tools(parts[0].strip(), parts[1].strip(), profile)
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    a = result["tool_a"]
                    b = result["tool_b"]
                    print(f"\n  {a['name']} vs {b['name']}")
                    _print_separator()
                    for label, d in [("A", a), ("B", b)]:
                        print(f"  [{label}] {d['name']}")
                        print(f"      {d['description']}")
                        print(f"      Categories: {', '.join(d['categories'])}")
                        print(f"      Skill: {d['skill_level']}")
                        print(f"      Compliance: {', '.join(d['compliance']) or 'None listed'}")
                        p = d.get("pricing", {})
                        if p:
                            print(f"      Pricing: free={p.get('free_tier', '?')}, starter=${p.get('starter', '?')}/mo")
                        if d.get("fits_budget") is not None:
                            print(f"      Fits your budget: {'Yes' if d['fits_budget'] else 'No'}")
                        print()

                    if result.get("shared_categories"):
                        print(f"  Shared categories: {', '.join(result['shared_categories'])}")
                    if result.get("direct_integration"):
                        print("  Direct integration: Yes ✓")
                    if result.get("recommendation"):
                        print(f"\n  → {result['recommendation']}")
            else:
                print("Usage: compare Tool A vs Tool B")
            continue

        # ---- Stack recommendation ----
        if cmd == "stack":
            if not profile:
                print("No profile found. Let's create one first.")
                profile = build_profile_interactive("default")

            query = input("Describe what you need (or press Enter for general recommendation): ").strip()
            if not query:
                query = f"I need AI tools for {profile.industry or 'general'} work"

            intent_struct = interpret(query)

            # Show clarification if needed
            if intent_struct.get("clarification_needed"):
                print("\nI'd like to understand your needs better:")
                for q in intent_struct.get("suggested_questions", []):
                    print(f"  ? {q}")
                extra = input("Any additional context? ").strip()
                if extra:
                    query = f"{query}. {extra}"
                    intent_struct = interpret(query)

            filter_input = input("Filter by category? (comma-separated, or blank): ").strip()
            filters = [f.strip() for f in filter_input.split(",") if f.strip()] if filter_input else None

            print("\nComposing your AI stack...")
            result = compose_stack(intent_struct, profile=profile, categories_filter=filters)
            _print_stack_result(result, profile)
            _handle_feedback(result, intent_struct, query, filters, profile)
            continue

        # ---- Default: quick search ----
        intent_struct = interpret(user_input)

        # Show clarification if needed
        if intent_struct.get("suggested_questions") and not intent_struct.get("intent"):
            print("\nTo give better recommendations:")
            for q in intent_struct["suggested_questions"]:
                print(f"  ? {q}")

        filter_input = input("Filter by category? (comma-separated, or blank): ").strip()
        filters = [f.strip() for f in filter_input.split(",") if f.strip()] if filter_input else None

        results = find_tools(intent_struct, categories_filter=filters, profile=profile)

        if not results:
            print("No matching tools found. Try 'stack' for a guided recommendation.")
        else:
            print("\nRecommended tools:")
            for idx, tool in enumerate(results, 1):
                expl = explain_tool(tool, intent_struct, profile)
                print(f"\n  [{idx}] {tool.name}")
                print(f"      {tool.description}")
                if tool.url:
                    print(f"      {tool.url}")
                if expl["reasons"]:
                    print(f"      Why: {expl['reasons'][0]}")
                print(f"      Fit: {expl['fit_score']}%")

            _handle_feedback(results, intent_struct, user_input, filters, profile)


if __name__ == "__main__":
    run()