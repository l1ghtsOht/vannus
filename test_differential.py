"""Quick test of the differential diagnosis pipeline."""
from praxis.differential import generate_differential
from praxis.profile import UserProfile

profile = UserProfile(
    profile_id="test",
    industry="healthcare",
    budget="medium",
    skill_level="intermediate",
    existing_tools=["HubSpot"],
    constraints=["HIPAA", "SOC2"],
)

result = generate_differential(
    "I need a CRM but not Salesforce",
    profile=profile,
    top_n=5,
)

print("Clarification needed:", result.clarification_needed)
print("Survivors:", len(result.survivors))
print("Eliminated:", len(result.eliminated))
print()

for s in result.survivors[:3]:
    res = s.get("resilience") or {}
    print(f"  SURVIVOR: {s['name']} (score={s['final_score']}, tier={res.get('tier', '?')})")
    for r in s.get("survival_reasons", [])[:2]:
        print(f"    + {r}")

print()
for e in result.eliminated[:5]:
    print(f"  ELIMINATED: {e['name']} — [{e['code']}] {e['explanation'][:90]}")

print()
for step in result.funnel_narrative:
    print(f"  >> {step}")

print()
print("=== STAGES ===")
import json
print(json.dumps(result.stages, indent=2))
