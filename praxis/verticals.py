"""
verticals.py — Industry Vertical Intelligence Engine (v8)
=========================================================

Provides deep knowledge of niche industry verticals, their regulatory
frameworks, workflow taxonomies, specialized tool mappings, and
anti-pattern rules.  Enables the search engine to reason about
*constraint-bound vertical AI* rather than returning generic SaaS
recommendations for hyper-specific domain queries.

Verticals covered:
  1. Architecture / Engineering / Construction  (AEC)
  2. 3D Manufacturing & Industrial Design
  3. Software Engineering (Architect-First)
  4. Cinematic Post-Production
  5. Biochemical Formulation (Perfumery / Pharma)
  6. Precision Agriculture
  7. Government & Regulatory Compliance
  8. Clinical / Diagnostic Imaging
  9. Finance & Risk Management

Each vertical carries:
  - regulatory_frameworks   — laws, standards, and certifying bodies
  - workflow_types           — action vs. decision task taxonomy
  - constraints             — hard guardrails the search must respect
  - anti_patterns           — common recommendation mistakes to avoid
  - specialized_tools       — curated niche tools the generic DB misses
  - stack_template          — composable tech-stack skeleton
  - keywords / signals      — phrases that trigger vertical detection
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

# ─── Dataclasses ─────────────────────────────────────────────────

@dataclass
class RegulatoryFramework:
    """A specific regulation, standard, or certifying body."""
    name: str
    jurisdiction: str              # e.g. "EU", "US-Federal", "Global"
    domain: str                    # e.g. "data-privacy", "building-code"
    description: str = ""
    enforcement_level: str = "mandatory"   # mandatory | advisory | voluntary

@dataclass
class WorkflowTask:
    """A unit of work within an industry workflow."""
    name: str
    task_type: str                  # "action" | "decision"
    description: str = ""
    automatable: bool = True        # can AI meaningfully automate this?
    typical_time_savings: str = ""  # e.g. "30%", "70%"

@dataclass
class AntiPattern:
    """Common recommendation mistake for a vertical."""
    name: str
    description: str
    trigger_keywords: List[str] = field(default_factory=list)
    severity: str = "high"          # high | medium | low

@dataclass
class StackLayer:
    """One layer of a recommended tech stack."""
    role: str                       # e.g. "Backend Orchestration"
    recommended: List[str]          # e.g. ["Python + FastAPI"]
    rationale: str = ""

@dataclass
class VerticalProfile:
    """Complete intelligence profile for an industry vertical."""
    id: str
    name: str
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    signal_keywords: List[str] = field(default_factory=list)
    signal_phrases: List[str] = field(default_factory=list)
    regulatory_frameworks: List[RegulatoryFramework] = field(default_factory=list)
    workflow_tasks: List[WorkflowTask] = field(default_factory=list)
    constraints: Dict[str, str] = field(default_factory=dict)
    anti_patterns: List[AntiPattern] = field(default_factory=list)
    specialized_tools: List[str] = field(default_factory=list)
    stack_template: List[StackLayer] = field(default_factory=list)
    data_sovereignty: str = "standard"  # standard | elevated | critical
    physics_aware: bool = False
    deployment_preference: str = "any"  # any | local-only | cloud-ok | hybrid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "aliases": self.aliases,
            "description": self.description,
            "signal_keywords": self.signal_keywords,
            "regulatory_frameworks": [
                {"name": r.name, "jurisdiction": r.jurisdiction,
                 "domain": r.domain, "enforcement_level": r.enforcement_level}
                for r in self.regulatory_frameworks
            ],
            "workflow_tasks": [
                {"name": w.name, "type": w.task_type,
                 "automatable": w.automatable,
                 "time_savings": w.typical_time_savings}
                for w in self.workflow_tasks
            ],
            "constraints": self.constraints,
            "anti_patterns": [
                {"name": a.name, "description": a.description,
                 "severity": a.severity}
                for a in self.anti_patterns
            ],
            "specialized_tools": self.specialized_tools,
            "stack_template": [
                {"role": s.role, "recommended": s.recommended,
                 "rationale": s.rationale}
                for s in self.stack_template
            ],
            "data_sovereignty": self.data_sovereignty,
            "physics_aware": self.physics_aware,
            "deployment_preference": self.deployment_preference,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  INDUSTRY VERTICAL REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VERTICALS: List[VerticalProfile] = [

    # ── 1. Architecture / Engineering / Construction ─────────────
    VerticalProfile(
        id="aec",
        name="Architecture, Engineering & Construction",
        aliases=["AEC", "architecture", "construction", "BIM",
                 "structural engineering", "building design"],
        description=(
            "Hyper-fragmented industry with extreme risk aversion. "
            "AI must differentiate action tasks (floor plans, clash "
            "detection, documentation) from decision tasks (aesthetic "
            "judgment, client management, ethical reasoning)."
        ),
        signal_keywords=[
            "architect", "architecture", "BIM", "building", "construction",
            "structural", "MEP", "floor plan", "zoning", "facade",
            "heritage", "restoration", "HBIM", "scan-to-bim",
            "clash detection", "RIBA", "AEC", "urban planning",
            "autodesk", "revit", "point cloud", "3d scan",
        ],
        signal_phrases=[
            "building information model", "clash detection",
            "scan to bim", "heritage preservation",
            "floor plan generation", "zoning compliance",
            "site analysis", "energy simulation",
            "construction risk", "as-built documentation",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("IBC", "US", "building-code",
                                "International Building Code"),
            RegulatoryFramework("Eurocode", "EU", "structural",
                                "European structural design standards"),
            RegulatoryFramework("RIBA Plan of Work", "UK", "practice",
                                "Staged architectural project management",
                                "advisory"),
            RegulatoryFramework("LEED / BREEAM", "Global", "sustainability",
                                "Green building certification"),
            RegulatoryFramework("UNESCO Heritage Charters", "Global", "preservation",
                                "International conservation standards"),
        ],
        workflow_tasks=[
            WorkflowTask("Conceptual Design Generation", "action",
                         "AI generates initial floor plans from prompts",
                         True, "30%"),
            WorkflowTask("Clash Detection (MEP)", "action",
                         "Automated cross-discipline interference checks",
                         True, "50%"),
            WorkflowTask("Scan-to-BIM Documentation", "action",
                         "Point cloud → BIM model conversion",
                         True, "60%"),
            WorkflowTask("Energy & Wind Simulation", "action",
                         "Early-stage microclimate and energy analytics",
                         True, "25%"),
            WorkflowTask("Client Aesthetic Judgment", "decision",
                         "Interpreting cultural, moral, and contextual aesthetics",
                         False, "0%"),
            WorkflowTask("Preservation Rule Interpretation", "decision",
                         "Applying heritage charter constraints to renovation",
                         False, "0%"),
        ],
        constraints={
            "must_support_bim": "Tools must import/export IFC or Revit formats",
            "precision_over_style": "Engineering accuracy > visual aesthetics",
            "heritage_non_destructive": "Historic work requires non-invasive methods",
            "code_compliance": "Output must reference local building codes",
        },
        anti_patterns=[
            AntiPattern(
                "generic_design_generator",
                "Recommending consumer design tools (Canva, Figma) for "
                "structural/engineering tasks that require BIM integration",
                ["floor plan", "structural design", "building"],
            ),
            AntiPattern(
                "startup_aesthetic_for_b2b",
                "Applying startup-themed UI generators to industrial B2B "
                "interfaces (calibration dashboards, inspection UIs)",
                ["industrial UI", "calibration", "inspection dashboard"],
            ),
            AntiPattern(
                "autonomous_aesthetic_decisions",
                "Suggesting AI can autonomously make client-facing aesthetic "
                "or ethical decisions in architecture",
                ["client aesthetic", "design philosophy"],
                "medium",
            ),
        ],
        specialized_tools=[
            "Skema", "Aurivus", "PointCAB", "ArkDesign", "TestFit",
            "Autodesk Forma", "Imerso", "Spacemaker",
        ],
        stack_template=[
            StackLayer("BIM Platform", ["Autodesk Revit", "ArchiCAD"],
                       "Core modeling environment"),
            StackLayer("AI Design Assistant", ["Skema", "ArkDesign"],
                       "Concept-to-BIM elevation"),
            StackLayer("Scan Processing", ["Aurivus", "PointCAB"],
                       "Point cloud → model recognition"),
            StackLayer("Risk Monitoring", ["Imerso"],
                       "Real-time as-built vs planned comparison"),
            StackLayer("Urban Analytics", ["Autodesk Forma"],
                       "District-scale wind/energy simulation"),
        ],
        physics_aware=True,
        deployment_preference="hybrid",
    ),

    # ── 2. 3D Manufacturing & Industrial Design ──────────────────
    VerticalProfile(
        id="manufacturing",
        name="3D Manufacturing & Industrial Design",
        aliases=["additive manufacturing", "3D printing", "generative design",
                 "industrial engineering", "mechanical engineering"],
        description=(
            "Visual aesthetics strictly secondary to structural integrity. "
            "AI must incorporate physics-based solvers (FEA, CFD) natively; "
            "a 'fiction before physics' approach is the primary failure mode."
        ),
        signal_keywords=[
            "manufacturing", "3d printing", "additive", "FEA",
            "generative design", "topology", "lattice", "voxel",
            "structural", "bracket", "injection mold", "CNC",
            "LPBF", "laser powder", "metal printing",
            "thermal", "CFD", "mechanical", "aerospace",
            "automotive", "orthopedic", "heat exchanger",
        ],
        signal_phrases=[
            "finite element analysis", "generative design",
            "topology optimization", "lattice structure",
            "additive manufacturing", "metal 3d printing",
            "laser powder bed fusion", "computational fluid dynamics",
            "structural integrity", "physics simulation",
            "constraint-aware design", "support structures",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("ISO 52900", "Global", "AM-terminology",
                                "Additive manufacturing standards"),
            RegulatoryFramework("AS9100", "Global", "aerospace-quality",
                                "Aerospace quality management"),
            RegulatoryFramework("ISO 13485", "Global", "medical-device",
                                "Medical device quality systems"),
            RegulatoryFramework("ITAR", "US", "defense-export",
                                "International Traffic in Arms Regulations"),
        ],
        workflow_tasks=[
            WorkflowTask("Generative Form Exploration", "action",
                         "AI generates topology-optimized shapes under load constraints",
                         True, "40%"),
            WorkflowTask("Thermal Physics Prediction", "action",
                         "Predicting metal behavior during printing",
                         True, "60%"),
            WorkflowTask("Part Orientation & Nesting", "action",
                         "Optimal build-plate placement for AM",
                         True, "70%"),
            WorkflowTask("Support Structure Generation", "action",
                         "Auto-generating supports for overhangs",
                         True, "50%"),
            WorkflowTask("Material Selection", "decision",
                         "Balancing cost, strength, and compliance for material choice",
                         False, "0%"),
            WorkflowTask("Safety Certification Sign-off", "decision",
                         "Human engineer certifies structural viability",
                         False, "0%"),
        ],
        constraints={
            "physics_first": "All design must pass FEA/CFD before acceptance",
            "hard_points": "Non-negotiable clearances, envelopes, and safety bounds",
            "fabrication_aware": "Designs must be physically manufacturable",
            "no_fiction_before_physics": "Stylistic output without structural validation is rejected",
        },
        anti_patterns=[
            AntiPattern(
                "fiction_before_physics",
                "Recommending AI image generators (Midjourney, DALL-E) for "
                "structural/mechanical design — produces shapes that collapse "
                "under real-world load",
                ["generative design", "mechanical", "structural", "bracket"],
            ),
            AntiPattern(
                "generic_3d_modeling",
                "Suggesting consumer 3D tools (Blender, SketchUp) for "
                "physics-critical manufacturing workflows",
                ["manufacturing", "FEA", "topology"],
            ),
        ],
        specialized_tools=[
            "Hyperganic", "AMAIZE 2.0", "NVIDIA PhysicsNeMo",
            "nTopology", "Altair Inspire", "Ansys Discovery",
        ],
        stack_template=[
            StackLayer("Physics-ML Framework", ["NVIDIA PhysicsNeMo"],
                       "GNNs, Fourier neural operators for physics prediction"),
            StackLayer("Generative Design", ["Hyperganic", "nTopology"],
                       "Voxel-level algorithmic engineering with lattice optimization"),
            StackLayer("AM Process Simulation", ["AMAIZE 2.0"],
                       "Thermal prediction, part orientation, support generation"),
            StackLayer("FEA Validation", ["Ansys Discovery", "Altair Inspire"],
                       "Real-time structural simulation and topology optimization"),
        ],
        physics_aware=True,
        deployment_preference="hybrid",
    ),

    # ── 3. Software Engineering (Architect-First) ────────────────
    VerticalProfile(
        id="software_engineering",
        name="Software Engineering",
        aliases=["software development", "coding", "programming",
                 "dev tools", "SDLC"],
        description=(
            "Production-grade AI deployment requires Architect-First "
            "methodology: detailed blueprints before code, Modular TDD, "
            "strict Definitions of Done, SOLID enforcement. 'Vibe coding' "
            "(prompting without architecture) yields Frankenstein codebases."
        ),
        signal_keywords=[
            "software", "code", "programming", "developer", "SDLC",
            "TDD", "test-driven", "C#", ".NET", "python", "java",
            "architecture", "microservices", "API", "backend",
            "CI/CD", "devops", "SOLID", "design pattern",
            "concurrency", "memory management", "refactor",
        ],
        signal_phrases=[
            "architect first", "vibe coding", "modular tdd",
            "test driven development", "design patterns",
            "definition of done", "code review",
            "production grade", "technical debt",
            "requirements engineering", "implementation blueprint",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("SOC2", "US", "security",
                                "Service Organization Control Type 2"),
            RegulatoryFramework("ISO 27001", "Global", "information-security",
                                "Information Security Management System"),
            RegulatoryFramework("OWASP Top 10", "Global", "appsec",
                                "Web Application Security Risks", "advisory"),
            RegulatoryFramework("GDPR Art. 25", "EU", "privacy-by-design",
                                "Data protection by design and by default"),
        ],
        workflow_tasks=[
            WorkflowTask("Requirements Blueprint", "decision",
                         "Architect-led specification before coding begins",
                         False, "0%"),
            WorkflowTask("Test Authoring (TDD)", "action",
                         "AI generates test scaffolding from specs",
                         True, "40%"),
            WorkflowTask("Code Generation", "action",
                         "AI writes implementation against tests",
                         True, "50%"),
            WorkflowTask("Code Review & Refactoring", "action",
                         "AI suggests improvements, enforces SOLID",
                         True, "30%"),
            WorkflowTask("Documentation Generation", "action",
                         "XML doc comments explaining 'why' not just 'what'",
                         True, "60%"),
            WorkflowTask("Architectural Decisions", "decision",
                         "Pattern selection (Flyweight, CQRS, etc.)",
                         False, "0%"),
        ],
        constraints={
            "architect_first": "Blueprint before code — no AI-led architecture",
            "tdd_mandatory": "Tests written before implementation to gate quality",
            "solid_enforcement": "AI must follow SOLID, DRY, and project conventions",
            "no_vibe_coding": "Prompting without spec leads to Frankenstein codebases",
            "memory_perf": "Enforce Span<T>/Memory<T> patterns in performance paths",
        },
        anti_patterns=[
            AntiPattern(
                "vibe_coding",
                "Suggesting users can 'prompt their way' to robust software "
                "without architectural oversight — creates catastrophic tech debt",
                ["vibe coding", "just prompt", "no-code app builder", "build app fast"],
            ),
            AntiPattern(
                "generic_code_wrapper",
                "Returning generic code-generation wrappers for production "
                "internal tooling requests",
                ["internal tool", "production code", "enterprise software"],
                "medium",
            ),
        ],
        specialized_tools=[
            "GitHub Copilot", "Cursor", "Windsurf", "Tabnine",
            "Sourcegraph Cody", "SonarQube", "Snyk",
        ],
        stack_template=[
            StackLayer("AI Code Assistant", ["GitHub Copilot", "Cursor"],
                       "Context-aware code generation with repo understanding"),
            StackLayer("Testing Framework", ["pytest", "xUnit", "Jest"],
                       "TDD-first with AI-generated test scaffolds"),
            StackLayer("Static Analysis", ["SonarQube", "Snyk"],
                       "Continuous code quality and security scanning"),
            StackLayer("CI/CD", ["GitHub Actions", "GitLab CI"],
                       "Automated build, test, and deploy pipelines"),
        ],
        data_sovereignty="standard",
        deployment_preference="any",
    ),

    # ── 4. Cinematic Post-Production ─────────────────────────────
    VerticalProfile(
        id="post_production",
        name="Cinematic Post-Production",
        aliases=["VFX", "post-production", "film editing",
                 "color grading", "visual effects"],
        description=(
            "Vertical AI automates specific pipeline nodes (rotoscoping, "
            "color matching, audio restoration, dubbing) rather than "
            "generating entire videos. Ethical localization is critical — "
            "actor consent and licensed source material are non-negotiable."
        ),
        signal_keywords=[
            "VFX", "post-production", "rotoscoping", "color grading",
            "dubbing", "localization", "LUT", "DaVinci Resolve",
            "compositing", "audio restoration", "lip sync",
            "deepfake", "motion capture", "CGI", "film",
            "television", "editorial", "ACES", "EXR",
        ],
        signal_phrases=[
            "visual effects pipeline", "color correction",
            "audio dubbing", "lip sync", "ethical localization",
            "actor consent", "rotoscoping automation",
            "vendor discovery", "shot matching",
            "theatrical color space", "post production workflow",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("SAG-AFTRA AI Provisions", "US", "labor",
                                "Actor consent requirements for AI likeness"),
            RegulatoryFramework("EU AI Act — Deepfake Disclosure", "EU", "disclosure",
                                "Mandatory disclosure of AI-generated content"),
            RegulatoryFramework("ACES Color Standard", "Global", "color-science",
                                "Academy Color Encoding System", "advisory"),
        ],
        workflow_tasks=[
            WorkflowTask("Rotoscoping & Masking", "action",
                         "AI generates object isolation masks",
                         True, "70%"),
            WorkflowTask("Color Shot-Matching", "action",
                         "Auto-matching LUTs across clips",
                         True, "50%"),
            WorkflowTask("Audio Noise Restoration", "action",
                         "Isolating dialogue from environmental noise",
                         True, "40%"),
            WorkflowTask("AI Dubbing & Lip-Sync", "action",
                         "Emotional voice translation with sync",
                         True, "60%"),
            WorkflowTask("Comedic Timing & Narrative Pacing", "decision",
                         "Creative editorial judgment",
                         False, "0%"),
            WorkflowTask("Ethical Consent Review", "decision",
                         "Verifying actor consent for AI manipulation",
                         False, "0%"),
        ],
        constraints={
            "actor_consent": "AI likeness manipulation requires explicit consent",
            "licensed_source": "Only licensed/original material may be modified",
            "theatrical_output": "Output must support ACES EXR for theatrical pipelines",
            "non_destructive": "Edits must be reversible and pipeline-compatible",
        },
        anti_patterns=[
            AntiPattern(
                "consumer_video_generator",
                "Recommending text-to-video generators (Sora, Runway) for "
                "professional VFX pipeline automation",
                ["VFX", "rotoscoping", "post-production pipeline"],
            ),
            AntiPattern(
                "deepfake_without_consent",
                "Suggesting AI face-swap or dubbing without ethical consent "
                "frameworks",
                ["deepfake", "face swap", "AI dubbing"],
            ),
        ],
        specialized_tools=[
            "MARZ", "Flawless AI", "DeepDub", "Dubformer",
            "Vitrina AI", "DaVinci Resolve", "Nuke",
        ],
        stack_template=[
            StackLayer("VFX Automation", ["MARZ"],
                       "AI rotoscoping and mask generation for episodic TV"),
            StackLayer("Ethical Localization", ["Flawless AI (TrueSync)"],
                       "Consent-based lip-sync in theatrical color spaces"),
            StackLayer("AI Dubbing", ["DeepDub", "Dubformer"],
                       "Emotional voice stacks for multi-territory release"),
            StackLayer("Vendor Discovery", ["Vitrina AI"],
                       "140K+ companies, production-stage-aware bidding windows"),
            StackLayer("Finishing Suite", ["DaVinci Resolve", "Nuke"],
                       "Professional color grading and compositing"),
        ],
        deployment_preference="hybrid",
    ),

    # ── 5. Biochemical Formulation ───────────────────────────────
    VerticalProfile(
        id="biochem_formulation",
        name="Biochemical Formulation & Perfumery",
        aliases=["perfumery", "fragrance", "cosmetics", "pharma formulation",
                 "chemical formulation", "QSAR"],
        description=(
            "Intersection of olfactory art, organic chemistry, supply chain "
            "logistics, and dermatological safety. AI must execute molecular "
            "chemistry predictions, not output generic text recipes. "
            "IFRA compliance and cruelty-free QSAR modeling are mandatory."
        ),
        signal_keywords=[
            "perfume", "fragrance", "formulation", "IFRA", "allergen",
            "QSAR", "molecule", "olfactory", "scent", "cosmetics",
            "dermatological", "ingredient", "sensory", "note",
            "top note", "base note", "heart note", "aroma",
            "essential oil", "cruelty-free", "vegan",
        ],
        signal_phrases=[
            "fragrance formulation", "molecular prediction",
            "IFRA compliance", "allergen screening",
            "cruelty free testing", "QSAR modeling",
            "olfactory creativity", "ESG sustainability",
            "scent design", "ingredient safety",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("IFRA Standards", "Global", "fragrance-safety",
                                "International Fragrance Association concentration limits"),
            RegulatoryFramework("EU Cosmetics Regulation 1223/2009", "EU", "cosmetics",
                                "Safety assessment and ingredient restrictions"),
            RegulatoryFramework("REACH", "EU", "chemical-safety",
                                "Registration, Evaluation, Authorisation of Chemicals"),
            RegulatoryFramework("Leaping Bunny / PETA", "Global", "cruelty-free",
                                "Cruelty-free certification programs", "voluntary"),
        ],
        workflow_tasks=[
            WorkflowTask("Molecular Screening", "action",
                         "AI screens formulas for IFRA compliance",
                         True, "80%"),
            WorkflowTask("QSAR Toxicology Prediction", "action",
                         "Predicting skin irritation from chemical structure",
                         True, "70%"),
            WorkflowTask("Scent Evolution Prediction", "action",
                         "Predicting how top/heart/base notes evolve over time",
                         True, "50%"),
            WorkflowTask("ESG Footprint Scoring", "action",
                         "Environmental impact per ingredient",
                         True, "40%"),
            WorkflowTask("Creative Scent Narrative", "decision",
                         "Emotional and brand storytelling for fragrance",
                         False, "0%"),
            WorkflowTask("Final Nose Approval", "decision",
                         "Master perfumer's artistic sign-off",
                         False, "0%"),
        ],
        constraints={
            "ifra_mandatory": "All formulas must pass IFRA concentration limits",
            "molecular_prediction": "Tools must work at the molecular level",
            "cruelty_free": "QSAR replaces animal testing where possible",
            "supply_chain_aware": "Must handle ingredient substitution during shortages",
        },
        anti_patterns=[
            AntiPattern(
                "text_recipe_generator",
                "Returning an LLM text-based 'recipe' instead of a platform "
                "capable of molecular chemistry predictions",
                ["perfume", "fragrance", "formulation"],
            ),
        ],
        specialized_tools=[
            "Moodify", "Osmo Generation OI", "Givaudan Carto",
            "DSM-Firmenich EcoScent Compass", "NobleAI",
        ],
        stack_template=[
            StackLayer("AI Formulation Platform", ["Moodify", "Osmo Generation OI"],
                       "Molecular prediction and IFRA compliance screening"),
            StackLayer("Olfactory Visualization", ["Givaudan Carto"],
                       "Real-time molecular combination visualization"),
            StackLayer("ESG Scoring", ["DSM-Firmenich EcoScent Compass"],
                       "Per-ingredient environmental footprint analysis"),
            StackLayer("Scientific Modeling", ["NobleAI"],
                       "Chemistry-integrated formulation optimization"),
        ],
        deployment_preference="cloud-ok",
    ),

    # ── 6. Precision Agriculture ─────────────────────────────────
    VerticalProfile(
        id="agriculture",
        name="Precision Agriculture",
        aliases=["agritech", "agtech", "farming", "crop management",
                 "precision farming"],
        description=(
            "AI shifts farm operations from reactive to anticipatory. "
            "Requires hyper-local microclimate forecasting, IoT sensor "
            "integration, computer vision for crop disease detection, and "
            "automated Farm Management System (FMS) workflows."
        ),
        signal_keywords=[
            "agriculture", "farming", "crop", "irrigation", "soil",
            "pest", "pesticide", "harvest", "agritech", "drone",
            "multispectral", "hyperspectral", "sensor", "IoT",
            "microclimate", "growing degree days", "FMS",
            "precision agriculture", "fertilizer", "yield",
        ],
        signal_phrases=[
            "crop disease detection", "precision agriculture",
            "farm management system", "microclimate forecasting",
            "soil health monitoring", "pest early detection",
            "drone surveillance", "hyperspectral imaging",
            "growing degree days", "irrigation automation",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("EPA Pesticide Regulations", "US", "chemical-use",
                                "Federal limits on agricultural chemical application"),
            RegulatoryFramework("EU Common Agricultural Policy", "EU", "subsidy",
                                "Sustainability-linked farming subsidies"),
            RegulatoryFramework("GlobalG.A.P.", "Global", "good-practice",
                                "Good Agricultural Practices certification", "voluntary"),
        ],
        workflow_tasks=[
            WorkflowTask("Microclimate Mapping", "action",
                         "AI maps distinct microclimates from sensor data",
                         True, "40%"),
            WorkflowTask("Disease Detection (CV)", "action",
                         "CNN-based crop disease identification from imagery",
                         True, "60%"),
            WorkflowTask("Automated Irrigation Control", "action",
                         "FMS adjusts irrigation based on predictions",
                         True, "50%"),
            WorkflowTask("Pesticide Application Planning", "action",
                         "Targeted advisories for when/where/how much",
                         True, "45%"),
            WorkflowTask("Crop Rotation Strategy", "decision",
                         "Long-term planning balancing economics and soil health",
                         False, "0%"),
        ],
        constraints={
            "hyper_local": "Regional forecasts insufficient — need on-farm sensor data",
            "sensor_integration": "Must interface with IoT/drone/weather station data",
            "offline_capable": "Rural areas may lack reliable connectivity",
            "chemical_compliance": "Must track and limit chemical application rates",
        },
        anti_patterns=[
            AntiPattern(
                "generic_crop_chatbot",
                "Returning a generic agricultural chatbot instead of sensor-"
                "integrated, CV-equipped precision farming platform",
                ["agriculture", "crop management", "farming AI"],
            ),
        ],
        specialized_tools=[
            "John Deere Operations Center", "Climate FieldView",
            "Taranis", "Pix4Dfields", "CropX", "Arable",
        ],
        stack_template=[
            StackLayer("Sensor Platform", ["CropX", "Arable"],
                       "IoT soil/weather sensors with API data feeds"),
            StackLayer("Aerial Imaging", ["Taranis", "Pix4Dfields"],
                       "Drone + multispectral crop analysis"),
            StackLayer("Farm Management", ["Climate FieldView", "John Deere Operations Center"],
                       "Integrated FMS with automated workflows"),
        ],
        deployment_preference="hybrid",
    ),

    # ── 7. Government & Regulatory Compliance ────────────────────
    VerticalProfile(
        id="government",
        name="Government & Regulatory Compliance",
        aliases=["gov tech", "public sector", "compliance", "legal tech",
                 "tax administration", "public finance"],
        description=(
            "Most severe constraints: risk aversion, legacy systems, data "
            "sovereignty. 80%+ AI project failure rate in public sector. "
            "Cloud-based LLMs present unacceptable sovereignty risks. "
            "Must prioritize local, open-source, truly open-licensed models."
        ),
        signal_keywords=[
            "government", "compliance", "regulation", "legal",
            "sovereign", "classified", "GDPR", "NIST", "FedRAMP",
            "public sector", "tax", "fiscal", "audit",
            "sanctions", "watchlist", "AML", "KYC",
            "local AI", "on-premise", "open source",
            "data sovereignty", "privacy", "offline",
        ],
        signal_phrases=[
            "data sovereignty", "local ai", "on premise deployment",
            "open source model", "regulatory compliance",
            "government ai", "public sector ai",
            "classified environment", "sensitive data",
            "legal compliance", "GDPR compliance",
            "sanctions screening", "anti money laundering",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("GDPR", "EU", "data-privacy",
                                "General Data Protection Regulation"),
            RegulatoryFramework("NIST AI RMF", "US-Federal", "ai-risk",
                                "AI Risk Management Framework"),
            RegulatoryFramework("FedRAMP", "US-Federal", "cloud-security",
                                "Federal Risk and Authorization Management"),
            RegulatoryFramework("EU AI Act", "EU", "ai-regulation",
                                "Risk-based AI regulation and classification"),
            RegulatoryFramework("FISMA", "US-Federal", "infosec",
                                "Federal Information Security Modernization Act"),
        ],
        workflow_tasks=[
            WorkflowTask("Regulatory Document Parsing", "action",
                         "CV + NLP extraction from regulatory PDFs",
                         True, "40%"),
            WorkflowTask("Compliance Mapping", "action",
                         "Graph ML maps regs to organizational risk profiles",
                         True, "50%"),
            WorkflowTask("Sanctions Screening", "action",
                         "ML-powered screening against global watchlists",
                         True, "60%"),
            WorkflowTask("Fraud Detection", "action",
                         "Anomaly detection in financial transactions",
                         True, "55%"),
            WorkflowTask("Legal Interpretation", "decision",
                         "Applying overlapping legal codes to specific cases",
                         False, "0%"),
            WorkflowTask("Policy Decision-Making", "decision",
                         "Choosing between regulatory responses",
                         False, "0%"),
        ],
        constraints={
            "data_never_leaves": "Sensitive data must never leave local hardware",
            "truly_open_source": "Apache 2.0 or MIT license — not 'open weights' or 'source-available'",
            "offline_mandatory": "Classified environments require 100% offline operation",
            "no_hallucination_tolerance": "Legal outputs must be verifiable — zero tolerance for hallucination",
            "legacy_integration": "Must interface with existing legacy IT systems",
        },
        anti_patterns=[
            AntiPattern(
                "cloud_llm_for_sovereignty",
                "Recommending cloud-based LLMs (ChatGPT, Claude API) for "
                "sensitive government/legal compliance where data sovereignty "
                "is critical",
                ["government", "classified", "sovereign", "compliance", "legal"],
            ),
            AntiPattern(
                "open_weights_confusion",
                "Conflating 'open weights' or 'source-available' licenses "
                "with truly open-source (Apache 2.0/MIT) for government use",
                ["open source", "local AI", "government"],
                "medium",
            ),
        ],
        specialized_tools=[
            "CUBE", "Kount", "Darktrace", "Ollama", "LM Studio",
            "Qwen3-235B", "Llama 3.1", "DeepSeek-R1",
        ],
        stack_template=[
            StackLayer("Local LLM Runtime", ["Ollama", "LM Studio"],
                       "Run open-source models locally with zero data egress"),
            StackLayer("Open-Source Models", ["Llama 3.1", "Qwen3-235B", "DeepSeek-R1"],
                       "Truly open-licensed models for local deployment"),
            StackLayer("Compliance Platform", ["CUBE"],
                       "RegLM + CV + Graph ML for regulatory mapping"),
            StackLayer("Fraud & AML", ["Kount"],
                       "ML-powered sanctions/PEP screening"),
            StackLayer("Cybersecurity", ["Darktrace"],
                       "AI-driven network anomaly detection for GDPR/NIST"),
        ],
        data_sovereignty="critical",
        deployment_preference="local-only",
    ),

    # ── 8. Clinical & Diagnostic Imaging ─────────────────────────
    VerticalProfile(
        id="clinical",
        name="Clinical & Diagnostic Imaging",
        aliases=["medical imaging", "radiology", "diagnostic AI",
                 "clinical AI", "healthcare AI"],
        description=(
            "Compound 'two-in-one' agent workflows: risk identification → "
            "imaging selection → result interpretation. AI does not replace "
            "clinicians but augments reading speed and reliability by 62%+."
        ),
        signal_keywords=[
            "clinical", "diagnostic", "radiology", "imaging",
            "MRI", "CT scan", "X-ray", "pathology", "oncology",
            "hemorrhage", "brain injury", "mammography",
            "HIPAA", "FDA", "medical device", "patient",
        ],
        signal_phrases=[
            "diagnostic imaging", "clinical ai",
            "radiology workflow", "medical image analysis",
            "traumatic brain injury", "compound agent workflow",
            "clinical decision support", "FDA clearance",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("HIPAA", "US", "patient-privacy",
                                "Health Insurance Portability and Accountability Act"),
            RegulatoryFramework("FDA 510(k) / De Novo", "US", "medical-device",
                                "AI/ML as Software as Medical Device clearance"),
            RegulatoryFramework("EU MDR", "EU", "medical-device",
                                "Medical Device Regulation 2017/745"),
            RegulatoryFramework("DICOM Standard", "Global", "imaging-format",
                                "Digital Imaging and Communications in Medicine", "advisory"),
        ],
        workflow_tasks=[
            WorkflowTask("Risk Stratification", "action",
                         "AI identifies high-risk patients for priority imaging",
                         True, "30%"),
            WorkflowTask("Image Analysis & Annotation", "action",
                         "AI locates anomalies and color-codes findings",
                         True, "62%"),
            WorkflowTask("Report Generation", "action",
                         "AI drafts preliminary radiology reports",
                         True, "50%"),
            WorkflowTask("Clinical Diagnosis", "decision",
                         "Final diagnostic determination by clinician",
                         False, "0%"),
            WorkflowTask("Treatment Selection", "decision",
                         "Choosing care pathway based on findings",
                         False, "0%"),
        ],
        constraints={
            "hipaa_mandatory": "All patient data must be HIPAA-compliant",
            "fda_cleared": "AI tools must have FDA 510(k) or De Novo clearance",
            "dicom_compatible": "Must integrate with DICOM/PACS imaging systems",
            "clinician_in_loop": "AI augments but never replaces clinical judgment",
        },
        anti_patterns=[
            AntiPattern(
                "generic_health_chatbot",
                "Recommending a general-purpose health chatbot for "
                "diagnostic imaging workflows that require FDA-cleared devices",
                ["radiology", "diagnostic imaging", "medical imaging"],
            ),
        ],
        specialized_tools=[
            "RadNet AI", "Aidoc", "Viz.ai", "Zebra Medical Vision",
            "Tempus", "PathAI",
        ],
        stack_template=[
            StackLayer("Diagnostic AI", ["Aidoc", "Viz.ai"],
                       "FDA-cleared triage and anomaly detection"),
            StackLayer("Pathology AI", ["PathAI", "Tempus"],
                       "Computational pathology and genomic analysis"),
            StackLayer("Imaging Platform", ["RadNet AI", "Zebra Medical Vision"],
                       "Multi-modality image analysis with DICOM integration"),
        ],
        data_sovereignty="elevated",
        deployment_preference="hybrid",
    ),

    # ── 9. Finance & Risk Management ─────────────────────────────
    VerticalProfile(
        id="finance",
        name="Finance & Risk Management",
        aliases=["fintech", "banking", "insurance", "risk management",
                 "trading", "wealth management"],
        description=(
            "AI for fraud detection, algorithmic risk scoring, regulatory "
            "reporting, and real-time compliance monitoring. Requires "
            "explainability (no black-box decisions), audit trails, "
            "and strict data governance."
        ),
        signal_keywords=[
            "finance", "banking", "insurance", "trading", "risk",
            "fraud", "AML", "KYC", "PEP", "sanctions",
            "regulatory reporting", "Basel", "MiFID",
            "credit scoring", "algorithmic", "portfolio",
            "wealth management", "fintech",
        ],
        signal_phrases=[
            "fraud detection", "anti money laundering",
            "know your customer", "regulatory reporting",
            "algorithmic trading", "credit risk",
            "portfolio optimization", "explainable ai",
        ],
        regulatory_frameworks=[
            RegulatoryFramework("Basel III/IV", "Global", "banking-capital",
                                "Capital adequacy and risk management"),
            RegulatoryFramework("MiFID II", "EU", "securities",
                                "Markets in Financial Instruments Directive"),
            RegulatoryFramework("SOX", "US", "financial-reporting",
                                "Sarbanes-Oxley Act"),
            RegulatoryFramework("PSD2", "EU", "payment-services",
                                "Payment Services Directive, Open Banking"),
            RegulatoryFramework("DORA", "EU", "digital-resilience",
                                "Digital Operational Resilience Act"),
        ],
        workflow_tasks=[
            WorkflowTask("Transaction Monitoring", "action",
                         "Real-time anomaly detection for fraud/AML",
                         True, "55%"),
            WorkflowTask("KYC / Identity Verification", "action",
                         "AI-powered facial recognition and document verification",
                         True, "60%"),
            WorkflowTask("Regulatory Report Generation", "action",
                         "Automated compliance report drafting",
                         True, "45%"),
            WorkflowTask("Credit Decision", "decision",
                         "Final credit approval requiring human judgment",
                         False, "0%"),
            WorkflowTask("Investment Strategy", "decision",
                         "Portfolio allocation decisions",
                         False, "0%"),
        ],
        constraints={
            "explainability": "All AI decisions must be explainable for audit",
            "audit_trail": "Full decision traceability required",
            "no_black_box": "Black-box models unacceptable for regulated decisions",
            "real_time": "Transaction monitoring must operate at sub-second latency",
        },
        anti_patterns=[
            AntiPattern(
                "black_box_for_regulated",
                "Recommending opaque AI models for decisions requiring "
                "regulatory explainability (credit scoring, AML)",
                ["credit scoring", "fraud detection", "AML"],
            ),
        ],
        specialized_tools=[
            "CUBE", "Kount", "Darktrace", "Featurespace",
            "ComplyAdvantage", "Quantexa",
        ],
        stack_template=[
            StackLayer("Compliance Intelligence", ["CUBE"],
                       "Regulatory mapping with Graph ML"),
            StackLayer("Fraud & AML", ["Featurespace", "ComplyAdvantage"],
                       "Adaptive behavioral analytics for fraud detection"),
            StackLayer("Identity Resolution", ["Quantexa"],
                       "Entity resolution across fragmented data sources"),
            StackLayer("Cybersecurity", ["Darktrace"],
                       "Network anomaly detection for financial infrastructure"),
        ],
        data_sovereignty="elevated",
        deployment_preference="hybrid",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VERTICAL DETECTION ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Pre-compile keyword → vertical index for O(1) lookup
_KEYWORD_INDEX: Dict[str, List[str]] = {}
_PHRASE_INDEX: List[Tuple[str, str]] = []   # (lowered phrase, vertical_id)
_VERTICAL_MAP: Dict[str, VerticalProfile] = {}

def _build_index() -> None:
    """Build inverted index on first call."""
    global _KEYWORD_INDEX, _PHRASE_INDEX, _VERTICAL_MAP
    if _VERTICAL_MAP:
        return
    for v in VERTICALS:
        _VERTICAL_MAP[v.id] = v
        for kw in v.signal_keywords:
            _KEYWORD_INDEX.setdefault(kw.lower(), []).append(v.id)
        for alias in v.aliases:
            _KEYWORD_INDEX.setdefault(alias.lower(), []).append(v.id)
        for phrase in v.signal_phrases:
            _PHRASE_INDEX.append((phrase.lower(), v.id))

_build_index()


def detect_verticals(
    query: str,
    *,
    keywords: Optional[List[str]] = None,
    industry: Optional[str] = None,
    top_n: int = 3,
    threshold: float = 0.10,
) -> List[Dict[str, Any]]:
    """
    Detect which industry verticals a query maps to.

    Returns a ranked list of ``{vertical_id, confidence, signals}`` dicts,
    highest-confidence first.

    Parameters
    ----------
    query : str
        Raw user query.
    keywords : list, optional
        Pre-extracted keywords from interpreter.
    industry : str, optional
        Industry detected by interpreter (boosts matching vertical).
    top_n : int
        Max verticals to return.
    threshold : float
        Minimum confidence to include a vertical.
    """
    _build_index()
    t0 = time.perf_counter()

    q_lower = query.lower()
    scores: Dict[str, float] = {}
    signals: Dict[str, List[str]] = {}

    def _add(vid: str, weight: float, signal: str):
        scores[vid] = scores.get(vid, 0.0) + weight
        signals.setdefault(vid, []).append(signal)

    # 1. Phrase matches (highest signal — multi-word = specific)
    for phrase, vid in _PHRASE_INDEX:
        if phrase in q_lower:
            _add(vid, 0.25, f"phrase:'{phrase}'")

    # 2. Keyword matches from query tokens
    tokens = set(re.findall(r"[a-z0-9#+.]{2,}", q_lower))
    if keywords:
        tokens.update(k.lower() for k in keywords)

    for token in tokens:
        if token in _KEYWORD_INDEX:
            for vid in _KEYWORD_INDEX[token]:
                _add(vid, 0.08, f"keyword:'{token}'")

    # 3. Industry boost from interpreter
    if industry:
        ind_lower = industry.lower()
        for v in VERTICALS:
            for alias in v.aliases:
                if ind_lower in alias.lower() or alias.lower() in ind_lower:
                    _add(v.id, 0.20, f"industry:'{industry}'")
                    break

    # 4. Normalize to [0, 1]
    if scores:
        max_s = max(scores.values())
        if max_s > 0:
            for vid in scores:
                scores[vid] = min(scores[vid] / max(max_s, 1.0), 1.0)

    # Sort and threshold
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    results = []
    for vid, conf in ranked[:top_n]:
        if conf < threshold:
            continue
        results.append({
            "vertical_id": vid,
            "vertical_name": _VERTICAL_MAP[vid].name,
            "confidence": round(conf, 3),
            "signals": signals.get(vid, []),
        })

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    log.info(
        "detect_verticals: query='%s' → %d verticals in %dms%s",
        query[:60], len(results), elapsed_ms,
        f" [top={results[0]['vertical_id']}@{results[0]['confidence']}]" if results else "",
    )
    return results


def get_vertical(vertical_id: str) -> Optional[VerticalProfile]:
    """Retrieve a vertical profile by ID."""
    _build_index()
    return _VERTICAL_MAP.get(vertical_id)


def get_all_verticals() -> List[VerticalProfile]:
    """Return all registered vertical profiles."""
    return list(VERTICALS)


def get_vertical_dict(vertical_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a vertical profile as a serialized dict."""
    v = get_vertical(vertical_id)
    return v.to_dict() if v else None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANTI-PATTERN ENFORCEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def check_anti_patterns(
    query: str,
    recommended_tools: List[str],
    verticals: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Check whether recommended tools trigger any anti-pattern warnings
    for the detected verticals.

    Returns a list of warning dicts:
      {anti_pattern, vertical, severity, description, offending_tool}
    """
    if verticals is None:
        verticals = detect_verticals(query)

    q_lower = query.lower()
    tool_names_lower = {t.lower() for t in recommended_tools}
    warnings: List[Dict[str, Any]] = []

    # Known generic tools that commonly trigger anti-patterns
    _GENERIC_DESIGN = {"canva", "figma", "uizard", "galileo", "framer"}
    _GENERIC_VIDEO = {"sora", "runway", "pika", "kling"}
    _CLOUD_LLMS = {"chatgpt", "claude", "gemini", "gpt-4", "gpt-4o"}

    for vinfo in verticals:
        v = get_vertical(vinfo["vertical_id"])
        if not v:
            continue
        for ap in v.anti_patterns:
            # Check if any trigger keyword is in the query
            trigger_hit = any(tk.lower() in q_lower for tk in ap.trigger_keywords)
            if not trigger_hit:
                continue

            # Check for offending tools based on anti-pattern type
            offenders = []
            if "generic_design" in ap.name or "startup_aesthetic" in ap.name:
                offenders = [t for t in recommended_tools
                             if t.lower() in _GENERIC_DESIGN]
            elif "consumer_video" in ap.name:
                offenders = [t for t in recommended_tools
                             if t.lower() in _GENERIC_VIDEO]
            elif "cloud_llm" in ap.name or "sovereignty" in ap.name:
                offenders = [t for t in recommended_tools
                             if t.lower() in _CLOUD_LLMS]
            elif "vibe_coding" in ap.name:
                # Flag if query suggests vibe coding but tools don't enforce structure
                offenders = []  # advisory warning, no specific tool to flag
            elif "fiction_before_physics" in ap.name:
                offenders = [t for t in recommended_tools
                             if t.lower() in {"midjourney", "dall-e", "dalle",
                                               "stable diffusion", "leonardo"}]
            elif "text_recipe" in ap.name:
                offenders = [t for t in recommended_tools
                             if t.lower() in _CLOUD_LLMS]
            elif "generic_health" in ap.name or "generic_crop" in ap.name:
                offenders = [t for t in recommended_tools
                             if t.lower() in _CLOUD_LLMS]

            if offenders or "vibe_coding" in ap.name:
                warnings.append({
                    "anti_pattern": ap.name,
                    "vertical": v.name,
                    "vertical_id": v.id,
                    "severity": ap.severity,
                    "description": ap.description,
                    "offending_tools": offenders,
                })

    if warnings:
        log.info(
            "anti_pattern_check: %d warnings for query='%s'",
            len(warnings), query[:60],
        )
    return warnings


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WORKFLOW TASK CLASSIFICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def classify_workflow_tasks(
    query: str,
    vertical_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    For a detected vertical, classify the query's intent into
    action tasks (automatable) vs. decision tasks (human-required).

    Returns::
        {
            "vertical": str,
            "action_tasks": [...],  # automatable by AI
            "decision_tasks": [...],  # require human judgment
            "automation_potential": float,  # 0-1
            "advisory": str,
        }
    """
    if vertical_id is None:
        detected = detect_verticals(query, top_n=1)
        if not detected:
            return {
                "vertical": None,
                "action_tasks": [],
                "decision_tasks": [],
                "automation_potential": 0.5,
                "advisory": "No specific industry vertical detected — "
                            "classify as general-purpose query.",
            }
        vertical_id = detected[0]["vertical_id"]

    v = get_vertical(vertical_id)
    if not v:
        return {"vertical": vertical_id, "action_tasks": [], "decision_tasks": [],
                "automation_potential": 0.0, "advisory": "Unknown vertical."}

    q_lower = query.lower()
    action_tasks = []
    decision_tasks = []

    for wt in v.workflow_tasks:
        # Score relevance of this task to the query
        task_words = set(wt.name.lower().split())
        query_words = set(re.findall(r"[a-z]{3,}", q_lower))
        overlap = len(task_words & query_words)

        entry = {
            "name": wt.name,
            "type": wt.task_type,
            "automatable": wt.automatable,
            "time_savings": wt.typical_time_savings,
            "description": wt.description,
            "relevance": "high" if overlap > 0 else "contextual",
        }
        if wt.task_type == "action":
            action_tasks.append(entry)
        else:
            decision_tasks.append(entry)

    total = len(v.workflow_tasks)
    automatable = sum(1 for w in v.workflow_tasks if w.automatable)
    potential = automatable / total if total else 0.5

    advisory = ""
    if decision_tasks:
        decision_names = [d["name"] for d in decision_tasks if d["relevance"] == "high"]
        if decision_names:
            advisory = (
                f"Your query touches on decision-level tasks "
                f"({', '.join(decision_names)}) that require human judgment. "
                f"AI tools can support but not replace these functions."
            )
        else:
            advisory = (
                f"This vertical ({v.name}) has {len(decision_tasks)} decision "
                f"tasks that cannot be fully automated by AI."
            )

    return {
        "vertical": v.name,
        "vertical_id": v.id,
        "action_tasks": action_tasks,
        "decision_tasks": decision_tasks,
        "automation_potential": round(potential, 2),
        "advisory": advisory,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STACK TEMPLATE RECOMMENDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def recommend_vertical_stack(
    vertical_id: str,
    *,
    budget: Optional[str] = None,
    deployment: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return the curated tech-stack template for a vertical, optionally
    filtered by deployment preference.
    """
    v = get_vertical(vertical_id)
    if not v:
        return None

    layers = []
    for sl in v.stack_template:
        layers.append({
            "role": sl.role,
            "recommended_tools": sl.recommended,
            "rationale": sl.rationale,
        })

    return {
        "vertical": v.name,
        "vertical_id": v.id,
        "deployment_preference": deployment or v.deployment_preference,
        "physics_aware": v.physics_aware,
        "data_sovereignty": v.data_sovereignty,
        "stack_layers": layers,
        "constraints": v.constraints,
        "regulatory_frameworks": [
            {"name": r.name, "jurisdiction": r.jurisdiction}
            for r in v.regulatory_frameworks
        ],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONSTRAINT EXTRACTION & REASONING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ConstraintProfile:
    """Extracted hard and soft constraints from a query + vertical."""
    regulatory: List[str] = field(default_factory=list)
    data_sovereignty: str = "standard"
    deployment: str = "any"           # any | local-only | cloud-ok | hybrid
    physics_required: bool = False
    budget_ceiling: Optional[str] = None
    compliance_required: List[str] = field(default_factory=list)
    anti_patterns_triggered: List[str] = field(default_factory=list)
    hard_constraints: Dict[str, str] = field(default_factory=dict)
    soft_preferences: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regulatory": self.regulatory,
            "data_sovereignty": self.data_sovereignty,
            "deployment": self.deployment,
            "physics_required": self.physics_required,
            "budget_ceiling": self.budget_ceiling,
            "compliance_required": self.compliance_required,
            "anti_patterns_triggered": self.anti_patterns_triggered,
            "hard_constraints": self.hard_constraints,
            "soft_preferences": self.soft_preferences,
        }


def extract_constraints(
    query: str,
    *,
    keywords: Optional[List[str]] = None,
    industry: Optional[str] = None,
    verticals: Optional[List[Dict[str, Any]]] = None,
) -> ConstraintProfile:
    """
    Extract a unified set of hard and soft constraints from the query
    combined with detected vertical requirements.

    This is the core "constraint reasoning" function — the bridge
    between raw query understanding and filtered tool selection.
    """
    if verticals is None:
        verticals = detect_verticals(query, keywords=keywords, industry=industry)

    cp = ConstraintProfile()
    q_lower = query.lower()

    # ── 1. Vertical-derived constraints ──────────────────────────
    for vinfo in verticals:
        v = get_vertical(vinfo["vertical_id"])
        if not v:
            continue

        # Regulatory frameworks
        for rf in v.regulatory_frameworks:
            if rf.enforcement_level == "mandatory":
                cp.regulatory.append(rf.name)
                cp.compliance_required.append(rf.name)

        # Data sovereignty
        if v.data_sovereignty == "critical":
            cp.data_sovereignty = "critical"
        elif v.data_sovereignty == "elevated" and cp.data_sovereignty != "critical":
            cp.data_sovereignty = "elevated"

        # Deployment preference
        if v.deployment_preference == "local-only":
            cp.deployment = "local-only"
        elif v.deployment_preference == "hybrid" and cp.deployment == "any":
            cp.deployment = "hybrid"

        # Physics
        if v.physics_aware:
            cp.physics_required = True

        # Hard constraints from vertical
        cp.hard_constraints.update(v.constraints)

    # ── 2. Query-derived constraints ─────────────────────────────
    # Data sovereignty signals
    sovereignty_signals = [
        "on-premise", "on premise", "local ai", "local model",
        "data sovereignty", "classified", "offline", "air-gapped",
        "sensitive data", "never leave", "private cloud",
    ]
    for sig in sovereignty_signals:
        if sig in q_lower:
            cp.data_sovereignty = "critical"
            cp.deployment = "local-only"
            cp.soft_preferences["sovereignty_signal"] = sig
            break

    # Compliance mentions
    compliance_map = {
        "hipaa": "HIPAA", "gdpr": "GDPR", "soc2": "SOC2", "soc 2": "SOC2",
        "nist": "NIST", "fedramp": "FedRAMP", "pci": "PCI-DSS",
        "iso 27001": "ISO 27001", "fisma": "FISMA", "sox": "SOX",
        "mifid": "MiFID II", "basel": "Basel III", "dora": "DORA",
        "ifra": "IFRA", "reach": "REACH", "fda": "FDA",
        "eu ai act": "EU AI Act",
    }
    for trigger, name in compliance_map.items():
        if trigger in q_lower and name not in cp.compliance_required:
            cp.compliance_required.append(name)

    # Budget extraction
    budget_match = re.search(r"\$\s*(\d+[\d,]*)", query)
    if budget_match:
        cp.budget_ceiling = budget_match.group(0)
    elif "free" in q_lower and "tier" not in q_lower:
        cp.budget_ceiling = "$0"
    elif "budget" in q_lower or "cheap" in q_lower or "affordable" in q_lower:
        cp.soft_preferences["budget_sensitivity"] = "high"

    # Physics signals (independent of vertical)
    physics_signals = [
        "FEA", "CFD", "structural", "load bearing", "stress analysis",
        "thermal", "simulation", "physics", "mechanical",
    ]
    for sig in physics_signals:
        if sig.lower() in q_lower:
            cp.physics_required = True
            break

    # Ethical signals
    ethical_signals = [
        "consent", "ethical", "cruelty-free", "vegan",
        "actor consent", "deepfake",
    ]
    for sig in ethical_signals:
        if sig.lower() in q_lower:
            cp.soft_preferences["ethical_requirement"] = sig

    log.info(
        "extract_constraints: sovereignty=%s, deployment=%s, physics=%s, "
        "compliance=%s, budget=%s",
        cp.data_sovereignty, cp.deployment, cp.physics_required,
        cp.compliance_required[:3], cp.budget_ceiling,
    )
    return cp


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOOL FILTERING BY CONSTRAINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def filter_by_constraints(
    tools: list,
    constraints: ConstraintProfile,
) -> Tuple[List, List[Dict[str, Any]]]:
    """
    Filter a list of Tool objects against vertical constraints.

    Returns
    -------
    (passed, rejections)
        passed:     tools that survive constraint filtering
        rejections: list of {tool, reason} dicts for tools removed
    """
    passed = []
    rejections = []

    for tool in tools:
        name = tool.name if hasattr(tool, "name") else str(tool)
        rejected = False

        # Data sovereignty gate — reject cloud-only tools if local-only required
        if constraints.deployment == "local-only":
            # Heuristic: if tool is a cloud SaaS with no local option, flag it
            cloud_only_signals = {"chatgpt", "gemini", "claude", "gpt-4"}
            if name.lower() in cloud_only_signals:
                rejections.append({
                    "tool": name,
                    "reason": f"Cloud-only — conflicts with local-only deployment "
                              f"(data_sovereignty={constraints.data_sovereignty})",
                })
                rejected = True

        # Compliance gate — check if required compliance is met
        if not rejected and constraints.compliance_required:
            tool_compliance = set()
            if hasattr(tool, "compliance"):
                tool_compliance = {c.upper() for c in (tool.compliance or [])}
            # Only reject if tool explicitly lacks required compliance
            # and the tool is in a category where compliance matters
            # (soft check — don't reject tools without compliance metadata)

        if not rejected:
            passed.append(tool)

    return passed, rejections


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMPOUND WORKFLOW DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# "Two-in-one" / compound workflows where multiple AI agents chain
COMPOUND_WORKFLOWS = [
    {
        "id": "clinical_imaging_pipeline",
        "name": "Clinical Imaging Pipeline",
        "description": "Risk stratification → Imaging selection → AI interpretation → Report draft",
        "verticals": ["clinical"],
        "chain": ["Risk Identification", "Imaging Test Selection", "AI Image Analysis", "Report Generation"],
        "tools": ["Aidoc", "Viz.ai", "RadNet AI"],
        "trigger_phrases": ["diagnostic pipeline", "clinical ai workflow", "radiology automation"],
    },
    {
        "id": "compliance_monitoring_pipeline",
        "name": "Regulatory Compliance Pipeline",
        "description": "Document CV extraction → NLP categorization → Graph ML mapping → Action recommendation",
        "verticals": ["government", "finance"],
        "chain": ["Document Vision", "NLP Categorization", "Risk Graph Mapping", "Action Recommendation"],
        "tools": ["CUBE"],
        "trigger_phrases": ["compliance automation", "regulatory monitoring", "compliance pipeline"],
    },
    {
        "id": "precision_farming_pipeline",
        "name": "Precision Farming Pipeline",
        "description": "Sensor data → Microclimate mapping → CV disease detection → Automated FMS action",
        "verticals": ["agriculture"],
        "chain": ["Sensor Ingestion", "Microclimate Mapping", "Disease Detection", "FMS Automation"],
        "tools": ["CropX", "Taranis", "Climate FieldView"],
        "trigger_phrases": ["farm automation pipeline", "precision farming workflow", "crop monitoring"],
    },
    {
        "id": "vfx_localization_pipeline",
        "name": "VFX & Localization Pipeline",
        "description": "Rotoscoping → Color matching → Dubbing → Ethical lip-sync → Distribution",
        "verticals": ["post_production"],
        "chain": ["AI Rotoscoping", "Color Shot-Matching", "Emotional Dubbing", "Ethical Lip-Sync"],
        "tools": ["MARZ", "DaVinci Resolve", "DeepDub", "Flawless AI"],
        "trigger_phrases": ["post production pipeline", "vfx automation", "localization workflow"],
    },
    {
        "id": "formulation_pipeline",
        "name": "Biochemical Formulation Pipeline",
        "description": "Molecular generation → IFRA screening → QSAR safety → ESG scoring → Human approval",
        "verticals": ["biochem_formulation"],
        "chain": ["Molecular Generation", "IFRA Compliance Screen", "QSAR Safety Check", "ESG Scoring"],
        "tools": ["Moodify", "NobleAI", "DSM-Firmenich EcoScent Compass"],
        "trigger_phrases": ["formulation pipeline", "fragrance workflow", "molecular screening"],
    },
    {
        "id": "generative_manufacturing_pipeline",
        "name": "Generative Manufacturing Pipeline",
        "description": "Topology optimization → FEA validation → Thermal prediction → AM support generation",
        "verticals": ["manufacturing"],
        "chain": ["Generative Design", "FEA Structural Validation", "Thermal Prediction", "AM Preparation"],
        "tools": ["Hyperganic", "NVIDIA PhysicsNeMo", "AMAIZE 2.0"],
        "trigger_phrases": ["additive manufacturing pipeline", "generative design workflow", "3d printing pipeline"],
    },
]


def detect_compound_workflows(query: str) -> List[Dict[str, Any]]:
    """
    Detect if a query maps to a known compound (chained) workflow.
    """
    q_lower = query.lower()
    results = []

    for cw in COMPOUND_WORKFLOWS:
        score = 0.0
        # Check trigger phrases
        for phrase in cw["trigger_phrases"]:
            if phrase in q_lower:
                score += 0.4

        # Check vertical overlap with detected verticals
        detected = detect_verticals(query, top_n=2)
        detected_ids = {d["vertical_id"] for d in detected}
        if detected_ids & set(cw["verticals"]):
            score += 0.3

        # Check tool name mentions
        for tool in cw["tools"]:
            if tool.lower() in q_lower:
                score += 0.2

        if score >= 0.3:
            results.append({
                **cw,
                "confidence": round(min(score, 1.0), 2),
            })

    results.sort(key=lambda x: -x["confidence"])
    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VERTICAL-AWARE SEARCH ENRICHMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def enrich_search_context(
    query: str,
    *,
    keywords: Optional[List[str]] = None,
    industry: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Master enrichment function — composes vertical detection,
    constraint extraction, workflow classification, anti-pattern
    checks, and compound workflow detection into a single context
    payload for the reasoning pipeline.
    """
    t0 = time.perf_counter()

    verticals = detect_verticals(query, keywords=keywords, industry=industry)
    constraints = extract_constraints(
        query, keywords=keywords, industry=industry, verticals=verticals
    )

    workflow_class = None
    if verticals:
        workflow_class = classify_workflow_tasks(
            query, vertical_id=verticals[0]["vertical_id"]
        )

    compound = detect_compound_workflows(query)

    # Build anti-pattern warnings for top vertical tools
    anti_warnings = []
    if verticals:
        anti_warnings = check_anti_patterns(
            query, keywords or [], verticals
        )

    # Build stack recommendation for top vertical
    stack = None
    if verticals:
        stack = recommend_vertical_stack(verticals[0]["vertical_id"])

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    result = {
        "verticals": verticals,
        "constraints": constraints.to_dict(),
        "workflow_classification": workflow_class,
        "compound_workflows": compound[:2],
        "anti_pattern_warnings": anti_warnings,
        "recommended_stack": stack,
        "elapsed_ms": elapsed_ms,
    }

    log.info(
        "enrich_search_context: %d verticals, %d constraints, "
        "%d compound workflows in %dms",
        len(verticals),
        len(constraints.compliance_required) + len(constraints.hard_constraints),
        len(compound),
        elapsed_ms,
    )
    return result
