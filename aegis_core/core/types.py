"""Shared dataclasses — the contract between Streams A/B/C/D.

All four engineers import from this file. Do not change a field name
without coordinating with the others.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional


# ──────────────────────────────────────────────────────────────────────────────
# Inputs
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """A single CUA task to run wide."""
    task_id: str
    instruction: str            # natural-language goal handed to the agent
    site_url: str               # starting page
    expected_outcome: str       # for the judge / verifier
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Variant:
    """One sampling strategy for the wide-scaling fan-out."""
    variant_id: str
    temperature: float = 0.7
    top_p: float = 1.0
    prompt_rephrase: Optional[str] = None        # alternate phrasing of the goal
    keyword_variant: Optional[str] = None         # alternate search keyword set
    notes: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# Per-step records
# ──────────────────────────────────────────────────────────────────────────────

ActionType = Literal[
    "click", "double_click", "right_click",
    "type", "key", "scroll", "drag",
    "navigate", "wait", "terminate",
    "approve", "block",  # AEGIS-injected actions
]


@dataclass
class Action:
    """A proposed CUA action — emitted by the executor model."""
    action_type: ActionType
    coords: Optional[tuple[int, int]] = None
    text: Optional[str] = None
    keys: Optional[list[str]] = None
    url: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict)   # full original model output


# ── Stream B verdict ─────────────────────────────────────────────────────────

DriftReason = Literal[
    "wrong_page", "stuck_loop", "modal_blocking",
    "unexpected_change", "no_change", "drift_other",
]
RetryStrategy = Literal["resample", "rephrase", "escalate", "abort", "continue"]


@dataclass
class Verdict:
    """Stream B per-step verification verdict."""
    on_track: bool
    confidence: float
    drift_reason: Optional[DriftReason] = None
    retry_strategy: Optional[RetryStrategy] = None
    reasoning: str = ""


# ── Stream C verdicts ────────────────────────────────────────────────────────

InjectionLabel = Literal["clean", "suspected", "injected"]
SecurityDecision = Literal["allow", "approve", "block"]


@dataclass
class InjectionVerdict:
    """Stream C visual prompt-injection verdict for a screenshot."""
    label: InjectionLabel
    confidence: float
    matched_patterns: list[str] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class SecurityVerdict:
    """Stream C decision on a proposed action."""
    decision: SecurityDecision
    reason: str = ""
    matched_rule: Optional[str] = None
    requires_human: bool = False


# ── A step in a trajectory ───────────────────────────────────────────────────

@dataclass
class Step:
    """One (state, action, verdicts, next_state) tuple in a trajectory."""
    step_idx: int
    ts: float = field(default_factory=time.time)
    screenshot_b64: str = ""
    dom_text: str = ""
    proposed_action: Optional[Action] = None
    executed_action: Optional[Action] = None      # may differ if AEGIS blocked
    verifier_verdict: Optional[Verdict] = None
    injection_verdict: Optional[InjectionVerdict] = None
    security_verdict: Optional[SecurityVerdict] = None
    model_reasoning: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# Trajectories and bundles
# ──────────────────────────────────────────────────────────────────────────────

Outcome = Literal["success", "failure", "blocked", "timeout", "error"]


@dataclass
class Trajectory:
    """One wide-scaling variant's full run on a task."""
    task_id: str
    variant: Variant
    browser_id: str
    live_view_url: str = ""
    steps: list[Step] = field(default_factory=list)
    outcome: Outcome = "error"
    final_url: str = ""
    final_artifacts: dict[str, Any] = field(default_factory=dict)
    judge_score: Optional[float] = None
    judge_reasoning: str = ""
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None


@dataclass
class Bundle:
    """All N trajectories produced by wide-scaling on one task."""
    task: Task
    trajectories: list[Trajectory] = field(default_factory=list)
    winner_variant_id: Optional[str] = None
    winner_score: Optional[float] = None
    judge_breakdown: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# Bargain Radar — domain types (Engineer 4)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ParsedQuery:
    item: str
    max_price: Optional[float]
    location: Optional[str]
    radius_mi: Optional[float]
    must_have: list[str] = field(default_factory=list)
    must_not_have: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class Listing:
    site: str
    listing_id: str
    title: str
    price: Optional[float]
    location: Optional[str]
    distance_mi: Optional[float]
    photos: list[str] = field(default_factory=list)
    description: str = ""
    url: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerifiedListing:
    listing: Listing
    matches_query: bool
    is_stale: bool
    is_scam_pattern: bool
    condition_score: float        # 0..1 from the verifier
    confidence: float             # verifier's overall confidence
    reasoning: str = ""
