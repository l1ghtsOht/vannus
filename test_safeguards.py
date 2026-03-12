"""End-to-end tests for 4 Cognitive Offloading Safeguard endpoints."""
import urllib.request
import urllib.error
import json
import sys
import time

BASE = "http://localhost:8000"
passed = 0
failed = 0


def test(name, url, body):
    global passed, failed
    for attempt in range(3):
        try:
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                f"{BASE}{url}", data=data,
                headers={"Content-Type": "application/json"},
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=10).read())
            time.sleep(0.3)
            return resp
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode()
            print(f"  FAIL {name}: HTTP {exc.code} — {body_text[:200]}")
            failed += 1
            return None
        except (ConnectionRefusedError, urllib.error.URLError) as exc:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f"  FAIL {name}: {exc}")
            failed += 1
            return None
        except Exception as exc:
            print(f"  FAIL {name}: {exc}")
            failed += 1
            return None


def ok(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS {name} {detail}")
        passed += 1
    else:
        print(f"  FAIL {name} {detail}")
        failed += 1


print("=" * 60)
print("Safeguard 1: Architectural Boundary Enforcement")
print("=" * 60)

r = test("S1-reject", "/safeguards/validate-boundaries",
         {"code": "import requests\nimport boto3\nx = 1", "layer": "domain"})
if r:
    ok("S1-reject", r["valid"] is False, f"violations={len(r['violations'])}")

r = test("S1-accept", "/safeguards/validate-boundaries",
         {"code": "import json\nimport math\nx = 1", "layer": "domain"})
if r:
    ok("S1-accept", r["valid"] is True, "clean domain code")

r = test("S1-adapter", "/safeguards/validate-boundaries",
         {"code": "import requests\nimport boto3\nx = 1", "layer": "adapters"})
if r:
    ok("S1-adapter", r["valid"] is True, "adapters can import anything")

r = test("S1-prompt", "/safeguards/generate-prompt",
         {"port_name": "find_tools", "input_types": {"query": "str"},
          "return_type": "List[Tool]", "domain_rules": ["max 50 results"]})
if r:
    ok("S1-prompt", len(r["prompt"]) > 100, f"{len(r['prompt'])} chars")

print()
print("=" * 60)
print("Safeguard 2: Complexity Ceiling Enforcement")
print("=" * 60)

r = test("S2-accept", "/safeguards/complexity-check",
         {"code": "def foo(x):\n  if x:\n    return 1\n  return 0\n"})
if r:
    ok("S2-accept", r["accepted"] is True, f"depth={r['max_nesting_depth']}")

deep = "def foo(x):\n"
deep += "  if x:\n"
deep += "    for i in range(10):\n"
deep += "      if i > 5:\n"
deep += "        while True:\n"
deep += "          try:\n"
deep += "            if i == 7:\n"
deep += "              pass\n"
deep += "          except: pass\n"
r = test("S2-reject", "/safeguards/complexity-check", {"code": deep})
if r:
    ok("S2-reject", r["accepted"] is False, f"depth={r['max_nesting_depth']}")

print()
print("=" * 60)
print("Safeguard 3: LLM-to-LLM Verification")
print("=" * 60)

r = test("S3-mutate", "/safeguards/mutation-test",
         {"code": "def check(x):\n  if x == 5:\n    return True\n  return x > 0\n"})
if r:
    ok("S3-mutate", len(r["mutations_applied"]) > 0,
       f"{len(r['mutations_applied'])} mutations")

r = test("S3-verify", "/safeguards/verify-consistency",
         {"code": "def check(x):\n  if x == 5:\n    return True\n  elif x < 3:\n    return False\n  return x > 0 and x != 10\n"})
if r:
    ok("S3-verify", "verified" in r, f"risk={r['hallucination_risk']} sim={r['similarity_score']}")

print()
print("=" * 60)
print("Safeguard 4: Boring Code Optimisation")
print("=" * 60)

r = test("S4-prompt", "/safeguards/boring-prompt",
         {"task_goal": "Parse CSV and return validated records",
          "verification_criteria": ["< 30 lines per function"]})
if r:
    ok("S4-prompt", "KERNEL" in r["prompt"] or "Explicit Constraints" in r["prompt"],
       f"{len(r['prompt'])} chars")

good_code = 'def process(x: int) -> bool:\n    """Check value."""\n    return x > 5\n'
r = test("S4-validate-pass", "/safeguards/boring-validate", {"code": good_code})
if r:
    ok("S4-validate-pass", r["compliant"] is True, "clean code passes")

bad_code = "def f(x):\n  return x\n"
r = test("S4-validate-fail", "/safeguards/boring-validate", {"code": bad_code})
if r:
    ok("S4-validate-fail", r["compliant"] is False,
       f"{len(r['violations'])} violations")

print()
print("=" * 60)
print("Full Analysis (all 4 safeguards combined)")
print("=" * 60)

clean_code = 'import json\ndef process(x: int) -> bool:\n    """Check value."""\n    return x > 5\n'
r = test("Full-pass", "/safeguards/full-analysis",
         {"code": clean_code, "layer": "domain"})
if r:
    ok("Full-pass", r["all_safeguards_pass"] is True, r["summary"][:60])

dirty_code = "import requests\ndef f(x):\n  if x:\n    for i in range(10):\n      if i > 5:\n        while True:\n          try:\n            if i == 7:\n              pass\n          except: pass\n"
r = test("Full-fail", "/safeguards/full-analysis",
         {"code": dirty_code, "layer": "domain"})
if r:
    ok("Full-fail", r["all_safeguards_pass"] is False, "correctly flags violations")

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
