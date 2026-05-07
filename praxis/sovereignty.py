# --------------- Sovereign AI & Foreign Influence Detection ---------------
"""
Praxis Sovereignty Assessment Engine.

Evaluates the geopolitical risk profile of every AI tool in the directory
by tracing corporate lineage, backend infrastructure dependencies, and
foundational model origins. Produces immutable trust badges and sovereign
risk scores aligned with NIST Cyber AI Profile mandates.

Trust Tiers:
    1. Fully US-Owned & Controlled (Green ✓)  — UBO >51% US, domestic infra
    2. Allied / Safe Harbor Origin  (Blue 🛡)  — CFIUS-exempt allied jurisdiction
    3. Foreign / High-Risk Influence (Red ✗)   — Sanctioned entities, state-control

Integrates with:
    - philosophy.py  (vendor intelligence data for ownership/revenue model)
    - profile.py     (user resilience tier determines filtering strictness)
    - engine.py      (trust scores feed into recommendation ranking)
    - explain.py     (trust badges rendered in UI)
"""

from typing import Dict, List, Optional, Tuple
import logging
import re

_log = logging.getLogger("praxis.sovereignty")

# ======================================================================
# 1. Geopolitical Classification Tables
# ======================================================================

# ISO 3166-1 alpha-3 codes → trust tier
_US_CODES = {"USA"}

_ALLIED_CODES = {
    # Five Eyes
    "GBR", "CAN", "AUS", "NZL",
    # EU major economies
    "DEU", "FRA", "NLD", "IRL", "SWE", "FIN", "DNK", "BEL", "AUT", "ESP",
    "ITA", "PRT", "POL", "CZE", "EST", "LVA", "LTU", "SVK", "SVN", "HRV",
    "ROU", "BGR", "GRC", "HUN", "CYP", "MLT", "LUX",
    # Safe Harbor / CFIUS-exempt
    "JPN", "KOR", "ISR", "SGP", "TWN", "CHE", "NOR", "ISL",
    # EU AI Act compliant
    "EU",
}

_HIGH_RISK_CODES = {
    "CHN", "RUS", "IRN", "PRK", "BLR", "VEN", "CUB", "SYR", "MMR",
    # HKG: post-2020 National Security Law brought Hong Kong effectively
    # under PRC jurisdiction. Tools domiciled there carry similar
    # data-access risk to mainland-China-domiciled tools.
    "HKG",
}

# Known high-risk backend entities (normalized lowercase)
_SANCTIONED_ENTITIES = {
    "deepseek", "bytedance", "tiktok", "baidu", "alibaba cloud",
    "tencent", "huawei", "sensetime", "megvii", "iflytek",
    "zhipu ai", "minimax", "moonshot ai", "01.ai", "yi",
}

# Known high-risk base models
_HIGH_RISK_MODELS = {
    "deepseek-v2", "deepseek-v3", "deepseek-r1", "deepseek-coder",
    "qwen", "qwen-2", "qwen-2.5", "ernie", "ernie-bot",
    "chatglm", "glm-4", "yi-34b", "yi-lightning",
    "baichuan", "internlm", "minimax",
}


# ======================================================================
# 2. Tool Sovereignty Intelligence Database
# ======================================================================

# tool_name_lower → sovereignty metadata
# Cross-references philosophy.py _TOOL_INTEL for ownership data
_SOVEREIGNTY_INTEL = {
    # --- Major US Platforms ---
    "chatgpt":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",       "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.82},
    "claude":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Claude 3.5",   "zdr": False, "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.85},
    "gemini":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Gemini 1.5",   "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "github copilot":   {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o/Codex", "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.88},
    "perplexity ai":    {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "jasper ai":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",       "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.75},
    "copy.ai":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",       "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.70},
    "grammarly":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},
    "notion ai":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",       "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.76},
    "zapier":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.85},
    "airtable":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "hubspot":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.82},
    "salesforce":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.80},
    "stripe":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.90},
    "shopify ai":       {"origin": "CAN", "us_controlled": False, "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "CAN/US",   "kpi": "revenue_growth",  "roi": 0.83},
    "mailchimp":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.75},
    "intercom":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",       "zdr": False, "train_use": "opt_out",  "jurisdiction": "US/IRL",   "kpi": "cost_reduction",  "roi": 0.77},
    "drift":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.72},
    "zendesk ai":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.78},
    "freshdesk":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US/IND",   "kpi": "cost_reduction",  "roi": 0.73},
    "monday.com ai":    {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "ISR/US",   "kpi": "time_saved",      "roi": 0.74},
    "clickup ai":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",       "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "asana intelligence": {"origin": "USA", "us_controlled": True, "risk_backend": False, "base": "proprietary", "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.73},
    "slack":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},
    "microsoft teams":  {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "zoom ai":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "loom":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.71},
    "otter.ai":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.76},
    "fireflies.ai":     {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.73},
    "descript":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.75},
    "runway":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "midjourney":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_in",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},
    "dall-e":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "DALL-E 3",     "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.77},
    "stable diffusion": {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "SDXL",         "zdr": True,  "train_use": "never",    "jurisdiction": "self-hosted", "kpi": "cost_reduction", "roi": 0.82},
    "adobe firefly":    {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "canva ai":         {"origin": "AUS", "us_controlled": False, "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "AUS/US",   "kpi": "time_saved",      "roi": 0.82},
    "figma ai":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},

    # --- Open-Source / Self-Hosted (ZDR by nature) ---
    "hugging face":     {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "open-weights",  "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "cost_reduction", "roi": 0.75},
    "ollama":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "open-weights",  "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "cost_reduction", "roi": 0.78},
    "langchain":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,            "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "time_saved",     "roi": 0.72},
    "llamaindex":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,            "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "time_saved",     "roi": 0.70},
    "n8n":              {"origin": "DEU", "us_controlled": False, "risk_backend": False, "base": None,            "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "time_saved",     "roi": 0.80},
    "supabase":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,            "zdr": True,  "train_use": "never",   "jurisdiction": "US",          "kpi": "cost_reduction", "roi": 0.78},
    "posthog":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,            "zdr": True,  "train_use": "never",   "jurisdiction": "US/self-hosted", "kpi": "compliance",  "roi": 0.75},

    # --- Data / Analytics ---
    "amplitude":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.74},
    "mixpanel":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.73},
    "segment":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "compliance",      "roi": 0.76},
    "snowflake":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.82},
    "databricks":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},
    "dbt":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "google analytics": {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US/EU",    "kpi": "revenue_growth",  "roi": 0.80},
    "tableau ai":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.77},
    "power bi":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},

    # --- Security / Compliance ---
    "vanta":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "compliance",      "roi": 0.85},
    "snyk":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US/GBR",   "kpi": "compliance",      "roi": 0.80},
    "crowdstrike":      {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "compliance",      "roi": 0.88},

    # --- Marketing / Content ---
    "buffer":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "hootsuite":        {"origin": "CAN", "us_controlled": False, "risk_backend": False, "base": "proprietary",  "zdr": False, "train_use": "opt_out",  "jurisdiction": "CAN",      "kpi": "time_saved",      "roi": 0.70},
    "semrush":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.78},
    "surfer seo":       {"origin": "POL", "us_controlled": False, "risk_backend": False, "base": None,           "zdr": False, "train_use": "opt_out",  "jurisdiction": "EU",       "kpi": "revenue_growth",  "roi": 0.74},

    # --- DevOps / Infrastructure ---
    "github actions":   {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.85},
    "vercel":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},
    "aws":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.82},
    "docker":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "self-hosted", "kpi": "time_saved",   "roi": 0.80},
    "terraform":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,           "zdr": True,  "train_use": "never",    "jurisdiction": "self-hosted", "kpi": "time_saved",   "roi": 0.78},

    # --- Notable non-US AI tools (May 2026 backfill, Drake) ---
    # Adding the most-cited gaps so the runtime backfill in data.py
    # propagates correct origin/jurisdiction to Tool objects. Each verified
    # against the vendor's own corporate page or About / Imprint section.
    "mistral ai":       {"origin": "FRA", "us_controlled": False, "risk_backend": False, "base": "Mistral / Mixtral", "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.78},
    "cohere":           {"origin": "CAN", "us_controlled": False, "risk_backend": False, "base": "Command R+",        "zdr": True,  "train_use": "never",   "jurisdiction": "CAN",      "kpi": "time_saved",      "roi": 0.76},
    "stability ai":     {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "Stable Diffusion",  "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "time_saved",      "roi": 0.70},
    "elevenlabs":       {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary voice", "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "time_saved",      "roi": 0.78},
    "ai21 labs":        {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "Jamba / Jurassic",  "zdr": False, "train_use": "opt_out", "jurisdiction": "ISR/US",   "kpi": "time_saved",      "roi": 0.72},
    "synthesia":        {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary avatar","zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "time_saved",      "roi": 0.74},
    "runway":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Runway Gen-3",      "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "aleph alpha":      {"origin": "DEU", "us_controlled": False, "risk_backend": False, "base": "Luminous",          "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.71},
    "n8n":              {"origin": "DEU", "us_controlled": False, "risk_backend": False, "base": None,                "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.80},
    "deepl":            {"origin": "DEU", "us_controlled": False, "risk_backend": False, "base": "proprietary NMT",   "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.84},
    "deepseek":         {"origin": "CHN", "us_controlled": False, "risk_backend": True,  "base": "DeepSeek-V3",       "zdr": False, "train_use": "opt_in",  "jurisdiction": "CN",       "kpi": "cost_reduction",  "roi": 0.55},

    # --- May 2026 Phase 3 catalog backfill (Drake, batch 2) ---
    # Coverage of the 235 catalog tools that lacked intel. Where origin
    # was uncertain, the entry is omitted rather than guessed — it's
    # better to fall back to TOOL.country_of_origin than fabricate intel.
    # Sources: each vendor's About / Imprint / corporate-records page.

    # ----- Non-US tools (highest sovereignty impact) -----
    "tabnine":              {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "ISR",      "kpi": "time_saved",      "roi": 0.78},
    "codesandbox":          {"origin": "NLD", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.80},
    "writesonic":           {"origin": "IND", "us_controlled": False, "risk_backend": False, "base": "GPT-4 + multi",   "zdr": False, "train_use": "opt_out", "jurisdiction": "IND",      "kpi": "revenue_growth",  "roi": 0.70},
    "murf ai":              {"origin": "IND", "us_controlled": False, "risk_backend": False, "base": "proprietary voice","zdr": False, "train_use": "opt_out", "jurisdiction": "IND",      "kpi": "time_saved",      "roi": 0.72},
    "remove.bg":            {"origin": "AUT", "us_controlled": False, "risk_backend": False, "base": "proprietary CV",  "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.78},
    "lemlist":              {"origin": "FRA", "us_controlled": False, "risk_backend": False, "base": "GPT-4",           "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "revenue_growth",  "roi": 0.75},
    "miro":                 {"origin": "NLD", "us_controlled": False, "risk_backend": False, "base": "GPT-4o",          "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.80},
    "tally":                {"origin": "BEL", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.78},
    "tidio":                {"origin": "POL", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "cost_reduction",  "roi": 0.72},
    "shopify":              {"origin": "CAN", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "CAN/US",   "kpi": "revenue_growth",  "roi": 0.85},
    "1password":            {"origin": "CAN", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "CAN",      "kpi": "cost_reduction",  "roi": 0.92},
    "make (integromat)":    {"origin": "CZE", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.82},
    "ahrefs":               {"origin": "SGP", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "SGP",      "kpi": "time_saved",      "roi": 0.85},
    "hotjar":               {"origin": "MLT", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.74},
    "typeform":             {"origin": "ESP", "us_controlled": False, "risk_backend": False, "base": "GPT-4",           "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.76},
    "flawless ai":          {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "time_saved",      "roi": 0.70},
    "deepdub":              {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary voice","zdr": False, "train_use": "opt_out", "jurisdiction": "ISR",      "kpi": "time_saved",      "roi": 0.74},
    "featurespace":         {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "cost_reduction",  "roi": 0.78},
    "quantexa":             {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "cost_reduction",  "roi": 0.76},
    "darktrace":            {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "cost_reduction",  "roi": 0.80},
    "cognism":              {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "revenue_growth",  "roi": 0.74},
    "imerso":               {"origin": "NOR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.72},
    "hyperganic":           {"origin": "DEU", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.70},
    "aidoc":                {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "ISR/US",   "kpi": "time_saved",      "roi": 0.78},
    "taranis":              {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary CV",  "zdr": False, "train_use": "opt_out", "jurisdiction": "ISR/US",   "kpi": "revenue_growth",  "roi": 0.72},
    "cropx":                {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "ISR",      "kpi": "cost_reduction",  "roi": 0.74},
    "outpost vfx":          {"origin": "GBR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "UK",       "kpi": "time_saved",      "roi": 0.72},
    "weaviate":             {"origin": "NLD", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.80},
    "neo4j":                {"origin": "SWE", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.82},
    "qdrant":               {"origin": "DEU", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.78},
    "skema":                {"origin": "FRA", "us_controlled": False, "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "EU",       "kpi": "time_saved",      "roi": 0.70},

    # ----- High-risk / sanctioned-adjacent (CRITICAL flags) -----
    "deepseek-r1":          {"origin": "CHN", "us_controlled": False, "risk_backend": True,  "base": "DeepSeek-R1",     "zdr": False, "train_use": "opt_in",  "jurisdiction": "CN",       "kpi": "cost_reduction",  "roi": 0.55},
    "qwen3-235b":           {"origin": "CHN", "us_controlled": False, "risk_backend": True,  "base": "Qwen3-235B",      "zdr": False, "train_use": "opt_in",  "jurisdiction": "CN",       "kpi": "cost_reduction",  "roi": 0.50},
    "foxit pdf editor":     {"origin": "CHN", "us_controlled": False, "risk_backend": True,  "base": None,              "zdr": False, "train_use": "opt_in",  "jurisdiction": "CN",       "kpi": "time_saved",      "roi": 0.60},
    "dify":                 {"origin": "HKG", "us_controlled": False, "risk_backend": True,  "base": "multi-LLM",       "zdr": False, "train_use": "opt_out", "jurisdiction": "HKG/CN",   "kpi": "time_saved",      "roi": 0.62},

    # ----- Major US AI / SaaS tools (verified, high-confidence US controlled) -----
    "openai":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-5 family",    "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.85},
    "anthropic":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Claude family",   "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.88},
    "cursor":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Claude + GPT-4o", "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.86},
    "replit":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Claude + GPT-4o", "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "railway":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.82},
    "postman":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.85},
    "linear":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.85},
    "writer":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Palmyra",         "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.78},
    "hemingway editor":     {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "quillbot":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "pika":                 {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "apollo.io":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",          "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.82},
    "tableau":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.84},
    "looker":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.82},
    "google gemini":        {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Gemini 2.5",      "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.80},
    "clickup":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",          "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "monday.com":           {"origin": "ISR", "us_controlled": False, "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "ISR/US",   "kpi": "time_saved",      "roi": 0.74},
    "calendly":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.86},
    "bubble":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.76},
    "retool":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.84},
    "coursera ai":          {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",          "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "mem":                  {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o",          "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "greenhouse":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.80},
    "harvey ai":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o + proprietary", "zdr": True, "train_use": "never", "jurisdiction": "US",     "kpi": "time_saved",      "roi": 0.82},
    "brex":                 {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.85},
    "quickbooks":           {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.88},
    "replicate":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.76},
    "sentry":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.86},
    "datadog":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.85},
    "pinecone":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.82},
    "zoominfo":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.78},
    "clearbit":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.75},
    "hashicorp vault":      {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "cost_reduction", "roi": 0.88},
    "stripe billing":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.92},
    "activecampaign":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.80},
    "perplexity computer":  {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "replit agent":         {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Claude + GPT-4o", "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.76},
    "lindy.ai":             {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "GPT-4o + proprietary", "zdr": False, "train_use": "opt_out", "jurisdiction": "US",   "kpi": "time_saved",      "roi": 0.76},
    "microsoft agent framework": {"origin": "USA", "us_controlled": True, "risk_backend": False, "base": None,           "zdr": True, "train_use": "never",  "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.84},
    "grok 4.20 multi-agent": {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "Grok 4.20",       "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "viz.ai":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "pathai":               {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": True,  "train_use": "never",   "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.76},
    "kount":                {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": None,              "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "cost_reduction",  "roi": 0.78},
    "lm studio":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "BYOK local",      "zdr": True,  "train_use": "never",   "jurisdiction": "self-hosted", "kpi": "cost_reduction", "roi": 0.80},
    "testfit":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "autodesk forma":       {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.78},
    "ntopology":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.74},
    "climate fieldview":    {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "revenue_growth",  "roi": 0.76},
    "nobleai":              {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary",     "zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
    "dubformer":            {"origin": "USA", "us_controlled": True,  "risk_backend": False, "base": "proprietary voice","zdr": False, "train_use": "opt_out", "jurisdiction": "US",       "kpi": "time_saved",      "roi": 0.72},
}


# ======================================================================
# 3. Trust Badge Generation
# ======================================================================

# Trust tier enum
TIER_US_CONTROLLED   = "us_controlled"
TIER_ALLIED          = "allied"
TIER_HIGH_RISK       = "high_risk"
TIER_UNKNOWN         = "unknown"

_TIER_BADGES = {
    TIER_US_CONTROLLED: {
        "badge": "green_check",
        "icon": "✓",
        "label": "Verified Domestic Infrastructure",
        "tooltip": "Ultimate Beneficial Owner registries verify >51% US ownership. Base models and cloud infrastructure are geographically localized.",
        "color": "#10B981",
        "severity": "safe",
    },
    TIER_ALLIED: {
        "badge": "blue_shield",
        "icon": "🛡",
        "label": "Allied / Safe Harbor Origin",
        "tooltip": "Headquartered in a CFIUS-exempt or allied jurisdiction. Compliant with GDPR / EU AI Act provisions.",
        "color": "#3B82F6",
        "severity": "neutral",
    },
    TIER_HIGH_RISK: {
        "badge": "red_x",
        "icon": "✗",
        "label": "High-Risk Supply Chain Detected",
        "tooltip": "This tool utilizes backend infrastructure flagged for data exfiltration risks, agent hijacking vulnerabilities, or foreign state influence.",
        "color": "#EF4444",
        "severity": "critical",
    },
    TIER_UNKNOWN: {
        "badge": "gray_question",
        "icon": "?",
        "label": "Sovereignty Unverified",
        "tooltip": "Corporate lineage and infrastructure hosting have not been independently verified. Exercise caution with sensitive data.",
        "color": "#6B7280",
        "severity": "warning",
    },
}


# ======================================================================
# 4. Core Assessment Functions
# ======================================================================

def classify_origin(country_code: str) -> str:
    """Classify an ISO 3166-1 alpha-3 country code into a trust tier."""
    code = (country_code or "").upper().strip()
    if code in _US_CODES:
        return TIER_US_CONTROLLED
    if code in _ALLIED_CODES:
        return TIER_ALLIED
    if code in _HIGH_RISK_CODES:
        return TIER_HIGH_RISK
    return TIER_UNKNOWN


def _check_backend_risk(tool_name: str, base_model: str = None) -> Tuple[bool, List[str]]:
    """Scan a tool's known dependencies for sanctioned entity exposure."""
    warnings = []
    name_lower = tool_name.lower()

    # Direct entity match
    for entity in _SANCTIONED_ENTITIES:
        if entity in name_lower:
            warnings.append(f"Tool name matches sanctioned entity: {entity}")
            return True, warnings

    # Base model risk
    if base_model:
        model_lower = base_model.lower().strip()
        for risk_model in _HIGH_RISK_MODELS:
            if risk_model in model_lower:
                warnings.append(f"Base model '{base_model}' flagged as high-risk foreign architecture")
                return True, warnings

    return False, warnings


def assess_sovereignty(tool) -> Dict:
    """
    Full sovereignty assessment for a single tool.

    Returns:
        {
            "tool_name": str,
            "trust_tier": str,            # us_controlled | allied | high_risk | unknown
            "badge": dict,                # Full badge metadata for UI rendering
            "country_of_origin": str,     # ISO 3166-1 alpha-3
            "is_us_controlled": bool,
            "high_risk_backend": bool,
            "base_model": str | None,
            "data_jurisdiction": str,
            "zdr_compliant": bool,
            "training_data_usage": str,   # never | opt_out | opt_in
            "risk_score": float,          # 0.0 (safe) to 1.0 (critical)
            "warnings": list[str],
            "recommendation": str,
        }
    """
    name = getattr(tool, "name", str(tool))
    name_lower = name.lower()

    # Pull from intel database first, then fall back to tool attributes
    intel = _SOVEREIGNTY_INTEL.get(name_lower, {})

    country     = intel.get("origin") or getattr(tool, "country_of_origin", "USA")
    us_ctrl     = intel.get("us_controlled") if intel else getattr(tool, "is_us_controlled", None)
    risk_back   = intel.get("risk_backend") if intel else getattr(tool, "high_risk_backend", False)
    base_model  = intel.get("base") or getattr(tool, "base_model", None)
    zdr         = intel.get("zdr") if intel else getattr(tool, "zdr_compliant", False)
    train_use   = intel.get("train_use") or getattr(tool, "training_data_usage", "opt_out")
    jurisdiction = intel.get("jurisdiction") or getattr(tool, "data_jurisdiction", "US")

    # Dynamic backend scanning
    backend_flagged, backend_warnings = _check_backend_risk(name, base_model)
    if backend_flagged:
        risk_back = True

    # Determine trust tier
    if risk_back:
        tier = TIER_HIGH_RISK
    elif us_ctrl:
        tier = TIER_US_CONTROLLED
    elif country:
        tier = classify_origin(country)
        # Allied + us_controlled=True overrides to US tier
        if tier == TIER_ALLIED and us_ctrl:
            tier = TIER_US_CONTROLLED
    else:
        tier = TIER_UNKNOWN

    badge = _TIER_BADGES[tier].copy()
    badge["trust_tier"] = tier

    # Compute risk score (0.0 = safe, 1.0 = critical)
    risk = 0.0
    warnings = list(backend_warnings)

    if tier == TIER_HIGH_RISK:
        risk = 0.95
        warnings.append("Tool has high-risk foreign influence. Not recommended for sensitive data.")
    elif tier == TIER_UNKNOWN:
        risk = 0.50
        warnings.append("Sovereignty unverified. Conduct manual due diligence before deployment.")
    elif tier == TIER_ALLIED:
        risk = 0.15
    else:
        risk = 0.0

    # Privacy penalties
    if train_use == "opt_in":
        risk = min(1.0, risk + 0.15)
        warnings.append("Tool uses customer data for model training by default.")
    elif train_use == "opt_out":
        risk = min(1.0, risk + 0.05)

    if not zdr:
        risk = min(1.0, risk + 0.05)

    # Recommendation text
    if tier == TIER_US_CONTROLLED:
        rec = "Verified domestic infrastructure. Suitable for all resilience tiers."
    elif tier == TIER_ALLIED:
        rec = f"Allied origin ({country}). Suitable for standard operations. Explicit acknowledgment recommended for defense/healthcare profiles."
    elif tier == TIER_HIGH_RISK:
        rec = "CRITICAL: High-risk supply chain detected. Filtered from Strict Sovereign AI profiles. Manual override required."
    else:
        rec = "Unverified origin. Eligible for general search but excluded from compliance-sensitive deployments."

    return {
        "tool_name": name,
        "trust_tier": tier,
        "badge": badge,
        "country_of_origin": country,
        "is_us_controlled": bool(us_ctrl),
        "high_risk_backend": bool(risk_back),
        "base_model": base_model,
        "data_jurisdiction": jurisdiction,
        "zdr_compliant": bool(zdr),
        "training_data_usage": train_use,
        "risk_score": round(risk, 3),
        "warnings": warnings,
        "recommendation": rec,
    }


def get_trust_badge(tool) -> Dict:
    """Quick-access: returns just the badge metadata for UI rendering."""
    assessment = assess_sovereignty(tool)
    badge = assessment["badge"]
    badge["tool_name"] = assessment["tool_name"]
    badge["risk_score"] = assessment["risk_score"]
    badge["zdr_compliant"] = assessment["zdr_compliant"]
    badge["training_data_usage"] = assessment["training_data_usage"]
    return badge


def filter_by_sovereignty(tools: list, tier_whitelist: List[str] = None,
                          exclude_high_risk: bool = False,
                          require_zdr: bool = False,
                          require_us: bool = False) -> List:
    """
    Filter a tool list by sovereignty constraints.

    Args:
        tools: List of Tool objects
        tier_whitelist: If set, only allow tools in these tiers
        exclude_high_risk: If True, remove all high_risk tools
        require_zdr: If True, only keep ZDR-compliant tools
        require_us: If True, only keep US-controlled tools

    Returns:
        Filtered list of tools
    """
    result = []
    for tool in tools:
        assessment = assess_sovereignty(tool)

        if exclude_high_risk and assessment["high_risk_backend"]:
            continue
        if require_us and not assessment["is_us_controlled"]:
            continue
        if require_zdr and not assessment["zdr_compliant"]:
            continue
        if tier_whitelist and assessment["trust_tier"] not in tier_whitelist:
            continue

        result.append(tool)

    return result


def sovereignty_score_modifier(tool) -> int:
    """
    Returns a scoring modifier for engine.py integration.

    US-controlled: +3
    Allied: +1
    Unknown: -2
    High-risk: -8
    """
    assessment = assess_sovereignty(tool)
    tier = assessment["trust_tier"]

    if tier == TIER_US_CONTROLLED:
        return 3
    elif tier == TIER_ALLIED:
        return 1
    elif tier == TIER_HIGH_RISK:
        return -8
    else:
        return -2


# ======================================================================
# 5. Batch Assessment & Dashboard Data
# ======================================================================

def assess_all_tools(tools: list) -> Dict:
    """
    Run sovereignty assessment on the full tool catalog.

    Returns:
        {
            "total": int,
            "by_tier": {tier: count},
            "high_risk_tools": [name],
            "zdr_compliant_count": int,
            "zdr_percentage": float,
            "average_risk_score": float,
            "assessments": [assessment_dict],
        }
    """
    assessments = []
    by_tier = {TIER_US_CONTROLLED: 0, TIER_ALLIED: 0, TIER_HIGH_RISK: 0, TIER_UNKNOWN: 0}
    high_risk_names = []
    zdr_count = 0
    total_risk = 0.0

    for tool in tools:
        a = assess_sovereignty(tool)
        assessments.append(a)
        by_tier[a["trust_tier"]] = by_tier.get(a["trust_tier"], 0) + 1

        if a["trust_tier"] == TIER_HIGH_RISK:
            high_risk_names.append(a["tool_name"])
        if a["zdr_compliant"]:
            zdr_count += 1
        total_risk += a["risk_score"]

    total = len(tools)
    return {
        "total": total,
        "by_tier": by_tier,
        "high_risk_tools": high_risk_names,
        "zdr_compliant_count": zdr_count,
        "zdr_percentage": round(zdr_count / max(total, 1) * 100, 1),
        "average_risk_score": round(total_risk / max(total, 1), 3),
        "assessments": assessments,
    }


def get_sovereignty_intel(tool_name: str) -> Dict:
    """Get raw sovereignty intelligence data for a specific tool."""
    return _SOVEREIGNTY_INTEL.get(tool_name.lower(), {})


_log.info(
    "sovereignty.py loaded — %d tools profiled, %d sanctioned entities tracked, "
    "%d high-risk models flagged",
    len(_SOVEREIGNTY_INTEL), len(_SANCTIONED_ENTITIES), len(_HIGH_RISK_MODELS),
)
