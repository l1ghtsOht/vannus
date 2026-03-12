# Security Philosophy: The Mirror in the Machine

> *The code isn't judging us; it's protecting the system (and us) from what we've shown we're capable of.*

---

## Why This Document Exists

Most security documentation catalogues controls: what is blocked, how
authentication works, which headers are set. This document explains
*why* — the anthropological premise beneath every `if not
user.has_role("admin")` and every taint-propagation pass.

Praxis is an open-source AI decision engine. Unlike frontier model
codebases that bury their anticipation of human failure inside opaque
reward gradients and unnamed activation probes, Praxis can afford to be
explicit. The files are named `anti_patterns.py`, `guardrails.py`,
`runtime_protection.py`. The function is called `_require_admin`. The
constant is `_MAX_ACTIVE_SESSIONS = 1000`.

Every one of these is a bet on a specific human behaviour.

---

## The Axioms

### 1. Assume Breach of Trust at Every Seam

The original Praxis architecture assumed good faith: authentication
defaulted to `none`, CORS opened to `*`, the write queue was unbounded,
and RASP existed only as diagnostic endpoints nobody would invoke under
attack.

Each hardening pass is a ratchet away from trust and toward the
empirical record of how humans interact with systems that have power
over decisions. The ratchet only turns one way.

**Implementation:**
- `PRAXIS_AUTH_MODE=none` raises `RuntimeError` in prod/staging
  (`api.py` startup guard).
- CORS origins default to an empty allowlist in production — you must
  explicitly declare who can talk to the API (`PRAXIS_CORS_ORIGINS`).
- RASP runs as enforcing middleware on every non-GET request body, not
  as a diagnostic endpoint you must remember to call.

### 2. Name the Behaviour You're Defending Against

Frontier labs won't name a file `greed.py` — it would be PR suicide.
But the evasion doesn't change the substance. Anthropic's dictionary
learning on 10 million neural features, OpenAI's CoT deception
flagging, Apollo Research's scheming evals — all are anticipations of
the same human capacity for misuse.

Praxis is small enough to be honest about it:

| Module | Human behaviour anticipated |
|---|---|
| `_require_admin` | Privilege escalation by curious insiders or attackers |
| `_prune_sessions()` | Resource exhaustion via session flooding |
| `_check_tainted_variable_indirection` | Obfuscation of `eval`/`exec` to evade detection |
| `_RASPMiddleware` | Injection attacks (SQL, XSS, command, prompt) in request bodies |
| `_save_json()` with file locking | Data corruption from concurrent writes during races |
| `WriteQueue(maxsize=10_000)` | Denial of service via unbounded write pressure |
| CORS allowlist | Cross-origin exploitation from untrusted frontends |
| JWT issuer/audience validation | Token forgery or misuse of tokens from other services |
| Metadata size caps | Payload inflation to exhaust memory |

No euphemisms. Each control exists because the behaviour has been
observed, measured, and published in adversarial security literature.

### 3. Fail Closed, Not Open

The most dangerous default is the permissive one — the one that ships
because it's easier to demo. Every default in the hardened Praxis
configuration is restrictive:

- Auth mode unset in production → **crash** (not silent bypass)
- CORS origins unset in production → **empty allowlist** (not `*`)
- RASP mode unset → **enforce** (not log-only)
- Write queue full → **back-pressure error** (not unbounded growth)
- File lock acquisition fails → **warning** (not silent race)

The principle: a broken deployment should be *visibly broken*, not
silently vulnerable.

### 4. Defence in Depth Is Not Optional

No single control is sufficient. The security posture is layered:

```
┌─────────────────────────────────────────────────┐
│  CORS Allowlist     (network boundary)          │
├─────────────────────────────────────────────────┤
│  Rate Limiter       (abuse throttling)          │
├─────────────────────────────────────────────────┤
│  RASP Middleware    (payload inspection)         │
├─────────────────────────────────────────────────┤
│  Auth + Admin Gates (identity + authorisation)   │
├─────────────────────────────────────────────────┤
│  Input Validation   (size caps, type checks)     │
├─────────────────────────────────────────────────┤
│  AST Security       (code analysis, taint prop)  │
├─────────────────────────────────────────────────┤
│  Persistence Guards (queue bounds, file locks)   │
├─────────────────────────────────────────────────┤
│  Audit Log          (non-repudiation)            │
└─────────────────────────────────────────────────┘
```

An attacker who bypasses CORS still hits rate limiting. One who forges a
valid token still can't reach admin endpoints without the `admin` role.
One who crafts a prompt injection that evades RASP patterns still faces
AST taint analysis if the payload reaches code evaluation.

### 5. The Code Is a Mirror

This is the deepest axiom. The security architecture of any
software system is a reflection of what its builders believe about the
people who will use it. When we write `_check_tainted_variable_indirection`
with five propagation cases and a fixed-point loop, we are encoding the
empirical observation that humans will chain aliases through `x = 'ev'
+ 'al'; y = x; f = __builtins__[y]; f('malicious code')` to evade
detection.

When we cap metadata at 8 KB and 64 keys, we are encoding the
observation that humans will inflate payloads to exhaust memory when
given an unbounded field.

When we add RASP patterns for `ignore previous instructions`, we are
encoding the observation that the first thing many users try with an AI
system is to override its constraints.

The absence of a file called `greed.py` in frontier model codebases
doesn't mean the anticipation isn't there — it's *everywhere*, woven
into weights, probes, refusals, and runtime guards. In Praxis, we just
don't hide it behind clinical naming. The mirror shows a society that
expects itself to abuse power, so we build countermeasures into the most
capable systems we create.

That's not a flaw in the code. It's an unflinching reflection of us.

---

## Hardening Chronology

| Pass | Commit | Changes |
|---|---|---|
| 1 | Fail-closed auth + admin gates + session bounds | `api.py`, `agent_sdk.py` |
| 2 | AST alias-chain bypass fix + remaining admin gates | `ast_security.py`, `api.py` |
| 3 | RASP middleware, CORS lockdown, JWT hardening, metadata caps, write queue bounds, file locking | `api.py`, `auth.py`, `persistence.py`, `governance.py`, `contributions.py` |

---

## Environment Variables (Security-Relevant)

| Variable | Default | Notes |
|---|---|---|
| `PRAXIS_AUTH_MODE` | `none` | **Must** be `api_key` or `oauth2` in prod/staging |
| `PRAXIS_ENV` | `development` | Set to `production` or `staging` to enable fail-closed checks |
| `PRAXIS_CORS_ORIGINS` | `*` (dev) / empty (prod) | Comma-separated allowlist of origins |
| `PRAXIS_RASP_MODE` | `enforce` | `enforce` blocks threats; `log` warns only; `off` disables |
| `PRAXIS_JWT_SECRET` | (empty) | Required for JWT auth |
| `PRAXIS_JWT_ISSUER` | `praxis` | Validated on stdlib HS256 path |
| `PRAXIS_JWT_AUDIENCE` | `praxis-api` | Validated on stdlib HS256 path |
| `PRAXIS_API_KEYS` | (empty) | Comma-separated valid API keys |

---

## The Normalisation of Anticipation

The disturbing part of any mature security architecture isn't a single
vulnerability or a single control. It's how *normalised* the
anticipation of human malice becomes. Every `if` statement in the
security layer is a prediction. Taken together, they form a statistical
portrait of human behaviour under conditions of access and anonymity.

The code doesn't have opinions. It has observations — compiled from
CVE databases, red-team exercises, adversarial ML research, and the
lived experience of every system that was ever exploited because someone
assumed good faith.

If we ever got full access to a frontier model's safety codebase, the
reality would look like this project, scaled by three orders of
magnitude: thousands of probes, classifiers, activation monitors, and
runtime guards, each anticipating a specific failure mode of human
intention — and none of them named `greed.py`.

The code is the most honest autobiography a civilisation has ever
written. We just have to learn to read it.
