# ADR-005: Vendor Trust Scoring Matrix

**Status:** Accepted  
**Date:** 2025-06-07  
**Deciders:** Architecture team  

## Context

Praxis recommends third-party AI tools but has no governance layer to
assess vendor risk. Enterprise customers need assurance that recommended
tools meet compliance requirements (SOC2, GDPR, HIPAA) and are actively
maintained.

The architecture report specifies a multi-dimensional trust matrix with
weighted dimensions covering compliance certifications, update frequency,
CVE exposure, and community health.

## Decision

Implement `praxis/vendor_trust.py` with:

1. **VendorProfile** dataclass — raw compliance and health data per vendor.
2. **VendorTrustEngine** — computes weighted composite scores across 7
   dimensions:
   - SOC 2 Type II (0.25)
   - GDPR DPA (0.15)
   - ISO 27001 (0.15)
   - HIPAA BAA (0.10)
   - Update frequency (0.15) — decay function on days-since-update
   - Open CVE count (0.10) — linear penalty
   - Community health (0.10) — stars, contributors, security policy
3. **Risk tiers:** low (≥0.8), medium (≥0.5), high (≥0.3), critical (<0.3).
4. **Auto-fail gate:** composite < 0.4 OR CVEs > 5 → blocked.
5. **annotate_recommendations()** — attaches trust scores to tool results.

## Consequences

- **Positive:** Enterprises can filter recommendations by compliance posture.
- **Positive:** Risk tier enables UI badges (green/yellow/red/blocked).
- **Positive:** Weights are configurable per deployment.
- **Negative:** VendorProfile data must be sourced (manual entry initially;
  future: NVD/OSV API + GitHub API enrichment).
- **Negative:** Binary compliance checks (soc2=True/False) are simplistic;
  future: attestation level differentiation.

## Alternatives Considered

- **OWASP Dependency-Check integration:** Focuses on code dependencies, not
  vendor SaaS compliance. Complementary but different scope.
- **External GRC platform (Vanta, Drata):** Enterprise-grade but requires
  paid integration. The built-in scorer serves as a lightweight alternative.
