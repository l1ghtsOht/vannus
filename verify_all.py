"""End-to-end verification for differential diagnosis pipeline."""
import urllib.request, json, sys, time

BASE = "http://localhost:8000"
ok = 0
fail = 0

def check(label, url, method="GET", data=None, expect=200):
    global ok, fail
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, method=method)
            if data:
                req.add_header("Content-Type", "application/json")
                req.data = json.dumps(data).encode()
            resp = urllib.request.urlopen(req, timeout=30)
            status = resp.status
            body = json.loads(resp.read().decode()) if "/differential" in url and "/static/" not in url else None
            if status == expect:
                ok += 1
                extra = ""
                if body and "survivors" in body:
                    extra = f" | {len(body['survivors'])} survivors, {len(body['eliminated'])} eliminated"
                elif body and "positive_intents" in body:
                    extra = f" | severity={body['ambiguity_flags']['severity']}"
                elif body and "hard_constraints" in body:
                    extra = f" | {len(body['hard_constraints']['compliance_mandates'])} compliance mandates"
                elif body and "total_overrides" in body:
                    extra = f" | {body['total_overrides']} total overrides"
                print(f"  PASS  {label} -> {status}{extra}")
            else:
                fail += 1
                print(f"  FAIL  {label} -> {status} (expected {expect})")
            return
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                fail += 1
                print(f"  FAIL  {label} -> {e}")

print("=== Frontend Pages ===")
for page in ["home.html", "differential.html", "tools.html", "manifesto.html", "tuesday-test.html", "rfp.html"]:
    check(page, f"{BASE}/static/{page}")

print("\n=== Differential API Endpoints ===")
check("POST /differential (marketing query)",
      f"{BASE}/differential",
      method="POST",
      data={"query": "I need email marketing automation for a small team"})

check("POST /differential (healthcare + compliance)",
      f"{BASE}/differential",
      method="POST",
      data={"query": "CRM for healthcare clinic", "profile": {"industry": "healthcare", "compliance_needs": ["HIPAA"], "budget": "medium"}})

check("POST /differential/intent",
      f"{BASE}/differential/intent",
      method="POST",
      data={"query": "I need a CRM but not Salesforce, must be HIPAA compliant"})

check("POST /differential/intent (vague)",
      f"{BASE}/differential/intent",
      method="POST",
      data={"query": "help with my team"})

check("POST /differential/constraint-matrix",
      f"{BASE}/differential/constraint-matrix",
      method="POST",
      data={"industry": "healthcare", "compliance_needs": ["HIPAA", "SOC2"], "budget": "medium", "risk_tolerance": "low"})

check("POST /differential/challenge",
      f"{BASE}/differential/challenge",
      method="POST",
      data={"tool_name": "TestTool", "reason_code": "COMPLIANCE_FAILURE", "user_comment": "verification test"})

check("GET /differential/override-stats",
      f"{BASE}/differential/override-stats")

check("GET /differential/filter-health",
      f"{BASE}/differential/filter-health")

print(f"\n=== Results: {ok} passed, {fail} failed ===")
sys.exit(0 if fail == 0 else 1)
