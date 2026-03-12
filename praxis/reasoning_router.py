# ────────────────────────────────────────────────────────────────────
# reasoning_router.py — Complexity-Aware Reasoning Router
# ────────────────────────────────────────────────────────────────────
"""
Implements the Three Regimes of Problem Complexity from the Praxis
Cognitive Resilience blueprint:

1. **Low Complexity**  — Standard LLMs outperform LRMs in accuracy and
   token efficiency. Route to lightweight models; bypass expensive
   reasoning modules.
2. **Medium Complexity** — LRMs demonstrate clear advantage with
   extended Chain-of-Thought. Route to dedicated reasoning models.
3. **High Complexity**  — Both LLMs and LRMs collapse to zero accuracy.
   Decompose into medium-complexity sub-tasks with deterministic
   verification scaffolding.

Also implements:
- Controllable Complexity metrics (Tower of Hanoi, Checker Jumping,
  River Crossing, Blocks World)
- Inference-time scaling limit detection
- Overthinking / underthinking detection in reasoning traces
- Task decomposition for high-complexity workloads
"""

from __future__ import annotations

import math
import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. COMPLEXITY REGIMES                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

class ComplexityRegime(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ComplexityAssessment:
    """Result of assessing a task's compositional complexity."""
    regime: ComplexityRegime
    score: float                      # 0.0 – 1.0
    compositional_depth: int          # estimated nesting / recursion depth
    estimated_moves: int              # estimated optimal solution steps
    recommended_model_tier: str       # "standard" | "reasoning" | "decompose"
    reasoning: str                    # human-readable explanation
    token_budget_estimate: int        # expected tokens for solution
    overthink_risk: float             # 0.0 – 1.0
    collapse_risk: float              # 0.0 – 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regime": self.regime.value,
            "score": round(self.score, 4),
            "compositional_depth": self.compositional_depth,
            "estimated_moves": self.estimated_moves,
            "recommended_model_tier": self.recommended_model_tier,
            "reasoning": self.reasoning,
            "token_budget_estimate": self.token_budget_estimate,
            "overthink_risk": round(self.overthink_risk, 4),
            "collapse_risk": round(self.collapse_risk, 4),
        }


# ── Puzzle Environment Simulators ─────────────────────────────────

PUZZLE_ENVIRONMENTS: Dict[str, Dict[str, Any]] = {
    "tower_of_hanoi": {
        "name": "Tower of Hanoi",
        "description": "Transferring N stacked disks across three pegs",
        "scaling": "exponential",
        "formula": "2^N - 1 moves",
        "cognitive_demands": [
            "recursive_thinking",
            "working_memory",
            "constraint_satisfaction",
        ],
    },
    "checker_jumping": {
        "name": "Checker Jumping",
        "description": "Swapping positions of red and blue checkers",
        "scaling": "quadratic",
        "formula": "(N+1)^2 - 1 moves",
        "cognitive_demands": [
            "spatial_reasoning",
            "lookahead_planning",
            "state_space_exploration",
        ],
    },
    "river_crossing": {
        "name": "River Crossing",
        "description": "Transporting N actors under safety constraints",
        "scaling": "near_linear",
        "formula": "~3N moves",
        "cognitive_demands": [
            "multi_agent_coordination",
            "dynamic_constraints",
            "state_tracking",
        ],
    },
    "blocks_world": {
        "name": "Blocks World",
        "description": "Rearranging N blocks into interleaved target",
        "scaling": "linear",
        "formula": "~2N moves",
        "cognitive_demands": [
            "forward_thinking",
            "dependency_resolution",
            "temporary_state_caching",
        ],
    },
}


def compute_optimal_moves(puzzle: str, n: int) -> int:
    """Compute optimal move count for a puzzle at parameter N."""
    puzzle = puzzle.lower().replace(" ", "_").replace("-", "_")
    if puzzle == "tower_of_hanoi":
        return (2 ** n) - 1
    elif puzzle == "checker_jumping":
        return ((n + 1) ** 2) - 1
    elif puzzle == "river_crossing":
        return max(1, 3 * n)
    elif puzzle == "blocks_world":
        return max(1, 2 * n)
    return n


def compute_compositional_depth(puzzle: str, n: int) -> int:
    """Estimate the recursive / compositional depth of a puzzle."""
    puzzle = puzzle.lower().replace(" ", "_").replace("-", "_")
    if puzzle == "tower_of_hanoi":
        return n  # recursion depth = N
    elif puzzle == "checker_jumping":
        return min(n * 2, 20)
    elif puzzle == "river_crossing":
        return min(n + 2, 15)
    elif puzzle == "blocks_world":
        return min(n, 10)
    return max(1, n // 2)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. COMPLEXITY ASSESSMENT                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

# Thresholds calibrated from the "Illusion of Thinking" research
LOW_COMPLEXITY_CEILING = 0.30
HIGH_COMPLEXITY_FLOOR = 0.70

# Token/efficiency breakpoints
OVERTHINK_TOKEN_RATIO = 3.0   # tokens-used / optimal-tokens > this ⇒ overthinking
COLLAPSE_DEPTH_THRESHOLD = 12 # compositional depth above which collapse is likely


def assess_complexity(
    task_description: str,
    *,
    estimated_steps: int = 0,
    nesting_depth: int = 0,
    constraint_count: int = 0,
    state_space_size: int = 0,
    puzzle: Optional[str] = None,
    puzzle_n: int = 0,
) -> ComplexityAssessment:
    """
    Assess the complexity regime of a task.

    The function uses heuristic signals (estimated steps, nesting depth,
    constraint count, state-space size) plus optional puzzle parameters
    to place the task in one of three regimes.
    """
    # If puzzle is given, use deterministic calculation
    if puzzle and puzzle_n > 0:
        moves = compute_optimal_moves(puzzle, puzzle_n)
        depth = compute_compositional_depth(puzzle, puzzle_n)
    else:
        moves = max(estimated_steps, 1)
        depth = max(nesting_depth, 1)

    # Normalize score via sigmoid-like mapping
    raw = (
        0.3 * min(depth / 15.0, 1.0)
        + 0.3 * min(moves / 500.0, 1.0)
        + 0.2 * min(constraint_count / 20.0, 1.0)
        + 0.2 * min(math.log2(max(state_space_size, 1) + 1) / 30.0, 1.0)
    )
    score = min(1.0, max(0.0, raw))

    # Classify regime
    if score <= LOW_COMPLEXITY_CEILING:
        regime = ComplexityRegime.LOW
        tier = "standard"
        reasoning = (
            "Task has low compositional depth. Standard LLMs outperform "
            "reasoning models in accuracy and token efficiency. Bypass "
            "expensive reasoning modules."
        )
    elif score <= HIGH_COMPLEXITY_FLOOR:
        regime = ComplexityRegime.MEDIUM
        tier = "reasoning"
        reasoning = (
            "Task requires moderate compositional depth. LRMs demonstrate "
            "clear advantage with extended Chain-of-Thought exploration. "
            "Route to dedicated reasoning model."
        )
    else:
        regime = ComplexityRegime.HIGH
        tier = "decompose"
        reasoning = (
            "Task exceeds the accuracy collapse threshold. Both LLMs and "
            "LRMs fall to zero performance at this depth. Must decompose "
            "into medium-complexity sub-tasks with deterministic "
            "verification scaffolding."
        )

    # Overthinking / collapse risk
    overthink = min(1.0, max(0.0, 1.0 - score) * 0.8) if regime == ComplexityRegime.LOW else 0.0
    collapse = min(1.0, max(0.0, (score - HIGH_COMPLEXITY_FLOOR) / 0.3)) if regime == ComplexityRegime.HIGH else 0.0

    token_budget = int(moves * 15 + depth * 200)

    return ComplexityAssessment(
        regime=regime,
        score=score,
        compositional_depth=depth,
        estimated_moves=moves,
        recommended_model_tier=tier,
        reasoning=reasoning,
        token_budget_estimate=token_budget,
        overthink_risk=overthink,
        collapse_risk=collapse,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. TASK DECOMPOSITION                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class SubTask:
    """A decomposed sub-task of a high-complexity problem."""
    task_id: str
    description: str
    parent_id: Optional[str] = None
    complexity: Optional[ComplexityAssessment] = None
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"   # pending | in_progress | completed | failed
    verification_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "parent_id": self.parent_id,
            "complexity": self.complexity.to_dict() if self.complexity else None,
            "dependencies": self.dependencies,
            "status": self.status,
            "verification_required": self.verification_required,
        }


def decompose_task(
    task_description: str,
    assessment: ComplexityAssessment,
    *,
    max_subtasks: int = 8,
    target_regime: ComplexityRegime = ComplexityRegime.MEDIUM,
) -> List[SubTask]:
    """
    Decompose a high-complexity task into medium-complexity sub-tasks.

    This implements the core mandate from the Illusion of Thinking research:
    middleware cannot function as a passive passthrough. It must decompose
    high-complexity tasks into components that models can reliably process.
    """
    if assessment.regime != ComplexityRegime.HIGH:
        # No decomposition needed for low/medium tasks
        return [SubTask(
            task_id=hashlib.md5(task_description.encode()).hexdigest()[:12],
            description=task_description,
            complexity=assessment,
            verification_required=(assessment.regime != ComplexityRegime.LOW),
        )]

    # Estimate number of subtasks needed
    depth = assessment.compositional_depth
    target_depth = COLLAPSE_DEPTH_THRESHOLD // 2  # aim for half the collapse threshold
    num_subtasks = min(max_subtasks, max(2, math.ceil(depth / max(target_depth, 1))))

    subtasks: List[SubTask] = []
    parent_id = hashlib.md5(task_description.encode()).hexdigest()[:12]

    for i in range(num_subtasks):
        step_desc = f"Sub-task {i + 1} of {num_subtasks}: decomposed segment of '{task_description[:60]}...'"
        sub_depth = max(1, depth // num_subtasks)
        sub_moves = max(1, assessment.estimated_moves // num_subtasks)

        sub_assessment = ComplexityAssessment(
            regime=target_regime,
            score=min(HIGH_COMPLEXITY_FLOOR - 0.05, assessment.score / num_subtasks + 0.15),
            compositional_depth=sub_depth,
            estimated_moves=sub_moves,
            recommended_model_tier="reasoning",
            reasoning=f"Decomposed from high-complexity parent (depth {depth}).",
            token_budget_estimate=int(sub_moves * 15 + sub_depth * 200),
            overthink_risk=0.0,
            collapse_risk=0.0,
        )

        deps = [subtasks[-1].task_id] if subtasks else []
        subtasks.append(SubTask(
            task_id=hashlib.md5(f"{parent_id}_{i}".encode()).hexdigest()[:12],
            description=step_desc,
            parent_id=parent_id,
            complexity=sub_assessment,
            dependencies=deps,
            verification_required=True,
        ))

    return subtasks


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. REASONING TRACE ANALYSIS                                     ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class TraceAnalysis:
    """Analysis of a model's Chain-of-Thought reasoning trace."""
    total_tokens: int
    useful_tokens: int           # tokens that advance toward solution
    wasted_tokens: int           # tokens in wrong-path exploration
    efficiency_ratio: float      # useful / total
    overthinking_detected: bool
    underthinking_detected: bool
    early_fixation: bool         # locked onto wrong path early
    self_correction_count: int   # number of backtrack/correction events
    reasoning_phases: List[str]  # ordered list of detected phases

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "useful_tokens": self.useful_tokens,
            "wasted_tokens": self.wasted_tokens,
            "efficiency_ratio": round(self.efficiency_ratio, 4),
            "overthinking_detected": self.overthinking_detected,
            "underthinking_detected": self.underthinking_detected,
            "early_fixation": self.early_fixation,
            "self_correction_count": self.self_correction_count,
            "reasoning_phases": self.reasoning_phases,
        }


def analyze_reasoning_trace(
    trace_text: str,
    *,
    optimal_tokens: int = 0,
) -> TraceAnalysis:
    """
    Analyze a Chain-of-Thought reasoning trace for cognitive efficiency.

    Detects overthinking (correct answer found early but search continues)
    and underthinking (rapid fixation on erroneous paths).
    """
    total = len(trace_text.split())
    if total == 0:
        return TraceAnalysis(
            total_tokens=0, useful_tokens=0, wasted_tokens=0,
            efficiency_ratio=0.0, overthinking_detected=False,
            underthinking_detected=False, early_fixation=False,
            self_correction_count=0, reasoning_phases=[],
        )

    # Heuristic phase detection via keywords
    phases: List[str] = []
    lower = trace_text.lower()

    phase_markers = [
        ("problem_identification", ["the problem", "we need to", "the task"]),
        ("exploration", ["let's try", "consider", "what if", "perhaps"]),
        ("backtracking", ["wait", "actually", "correction", "mistake", "wrong"]),
        ("verification", ["verify", "check", "confirm", "validate"]),
        ("conclusion", ["therefore", "the answer", "solution is", "result"]),
    ]

    for phase_name, markers in phase_markers:
        if any(m in lower for m in markers):
            phases.append(phase_name)

    # Count self-corrections
    correction_markers = ["wait", "actually", "correction", "no,", "mistake"]
    corrections = sum(1 for m in correction_markers if m in lower)

    # Estimate useful vs wasted tokens
    if "conclusion" in phases:
        conclusion_idx = lower.rfind("therefore")
        if conclusion_idx < 0:
            conclusion_idx = lower.rfind("the answer")
        if conclusion_idx < 0:
            conclusion_idx = lower.rfind("solution")
        if conclusion_idx > 0:
            useful_ratio = max(0.3, conclusion_idx / len(trace_text))
        else:
            useful_ratio = 0.7
    else:
        useful_ratio = 0.4 if "exploration" in phases else 0.2

    useful = int(total * useful_ratio)
    wasted = total - useful
    efficiency = useful / total if total > 0 else 0.0

    # Overthinking detection
    overthinking = False
    if optimal_tokens > 0 and total > optimal_tokens * OVERTHINK_TOKEN_RATIO:
        overthinking = True
    elif "backtracking" in phases and corrections > 3:
        overthinking = True

    # Underthinking detection (rapid fixation)
    underthinking = "exploration" not in phases and "backtracking" not in phases
    early_fixation = underthinking and total < (optimal_tokens * 0.3 if optimal_tokens > 0 else 50)

    return TraceAnalysis(
        total_tokens=total,
        useful_tokens=useful,
        wasted_tokens=wasted,
        efficiency_ratio=efficiency,
        overthinking_detected=overthinking,
        underthinking_detected=underthinking,
        early_fixation=early_fixation,
        self_correction_count=corrections,
        reasoning_phases=phases,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. INFERENCE SCALING MONITOR                                    ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class ScalingProfile:
    """Tracks reasoning effort across increasing complexity levels."""
    model_id: str
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    collapse_detected: bool = False
    collapse_threshold: Optional[float] = None

    def record(self, complexity_score: float, tokens_used: int, correct: bool):
        """Record a single observation."""
        self.data_points.append({
            "complexity": round(complexity_score, 4),
            "tokens_used": tokens_used,
            "correct": correct,
            "timestamp": time.time(),
        })
        self._detect_collapse()

    def _detect_collapse(self):
        """Detect when reasoning effort drops despite increasing complexity."""
        if len(self.data_points) < 3:
            return
        sorted_pts = sorted(self.data_points, key=lambda d: d["complexity"])
        # Look for peak then decline in tokens used
        peak_idx = 0
        peak_tokens = 0
        for i, pt in enumerate(sorted_pts):
            if pt["tokens_used"] > peak_tokens:
                peak_tokens = pt["tokens_used"]
                peak_idx = i

        # Check if later (higher complexity) points have fewer tokens
        if peak_idx < len(sorted_pts) - 1:
            later_avg = sum(p["tokens_used"] for p in sorted_pts[peak_idx + 1:]) / max(1, len(sorted_pts) - peak_idx - 1)
            if later_avg < peak_tokens * 0.6:
                self.collapse_detected = True
                self.collapse_threshold = sorted_pts[peak_idx]["complexity"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "data_point_count": len(self.data_points),
            "collapse_detected": self.collapse_detected,
            "collapse_threshold": self.collapse_threshold,
            "data_points": self.data_points[-20:],  # last 20
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. ROUTING ENGINE                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

# Model tier configurations
MODEL_TIERS = {
    "standard": {
        "tier": "standard",
        "models": ["gpt-4o-mini", "claude-3-haiku", "gemini-flash"],
        "max_complexity": LOW_COMPLEXITY_CEILING,
        "cost_multiplier": 1.0,
        "description": "Fast, cost-efficient models for low-complexity tasks",
    },
    "reasoning": {
        "tier": "reasoning",
        "models": ["o3-mini", "deepseek-r1", "claude-3.7-sonnet-thinking"],
        "max_complexity": HIGH_COMPLEXITY_FLOOR,
        "cost_multiplier": 5.0,
        "description": "Extended Chain-of-Thought models for medium complexity",
    },
    "decompose": {
        "tier": "decompose",
        "models": ["o3-mini", "deepseek-r1"],
        "max_complexity": 1.0,
        "cost_multiplier": 8.0,
        "description": "Decomposition + verification for high complexity",
    },
}


@dataclass
class RoutingDecision:
    """The router's decision for how to handle a task."""
    task_id: str
    assessment: ComplexityAssessment
    selected_tier: str
    requires_decomposition: bool
    subtasks: List[SubTask] = field(default_factory=list)
    estimated_cost_multiplier: float = 1.0
    verification_strategy: str = "none"  # none | checksum | deterministic | consensus

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "assessment": self.assessment.to_dict(),
            "selected_tier": self.selected_tier,
            "requires_decomposition": self.requires_decomposition,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "estimated_cost_multiplier": round(self.estimated_cost_multiplier, 2),
            "verification_strategy": self.verification_strategy,
        }


def route_task(
    task_description: str,
    *,
    estimated_steps: int = 0,
    nesting_depth: int = 0,
    constraint_count: int = 0,
    state_space_size: int = 0,
    puzzle: Optional[str] = None,
    puzzle_n: int = 0,
) -> RoutingDecision:
    """
    Route a task to the appropriate model tier based on complexity assessment.
    High-complexity tasks are automatically decomposed.
    """
    assessment = assess_complexity(
        task_description,
        estimated_steps=estimated_steps,
        nesting_depth=nesting_depth,
        constraint_count=constraint_count,
        state_space_size=state_space_size,
        puzzle=puzzle,
        puzzle_n=puzzle_n,
    )

    task_id = hashlib.md5(task_description.encode()).hexdigest()[:12]
    tier_info = MODEL_TIERS[assessment.recommended_model_tier]

    subtasks: List[SubTask] = []
    needs_decomp = assessment.regime == ComplexityRegime.HIGH

    if needs_decomp:
        subtasks = decompose_task(task_description, assessment)
        verification = "deterministic"
    elif assessment.regime == ComplexityRegime.MEDIUM:
        verification = "checksum"
    else:
        verification = "none"

    return RoutingDecision(
        task_id=task_id,
        assessment=assessment,
        selected_tier=assessment.recommended_model_tier,
        requires_decomposition=needs_decomp,
        subtasks=subtasks,
        estimated_cost_multiplier=tier_info["cost_multiplier"],
        verification_strategy=verification,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  7. MODULE-LEVEL UTILITIES                                       ║
# ╚════════════════════════════════════════════════════════════════════╝

def get_puzzle_environments() -> Dict[str, Dict[str, Any]]:
    """Return all supported puzzle environments."""
    return dict(PUZZLE_ENVIRONMENTS)


def get_model_tiers() -> Dict[str, Dict[str, Any]]:
    """Return model tier configurations."""
    return dict(MODEL_TIERS)


def router_summary() -> Dict[str, Any]:
    """Return a summary of the reasoning router state."""
    return {
        "puzzle_environments": list(PUZZLE_ENVIRONMENTS.keys()),
        "model_tiers": list(MODEL_TIERS.keys()),
        "complexity_thresholds": {
            "low_ceiling": LOW_COMPLEXITY_CEILING,
            "high_floor": HIGH_COMPLEXITY_FLOOR,
        },
        "collapse_depth_threshold": COLLAPSE_DEPTH_THRESHOLD,
        "overthink_token_ratio": OVERTHINK_TOKEN_RATIO,
    }
