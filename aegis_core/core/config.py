"""Centralized config / env loading. Imported by all streams.

Honors the team's existing CUA_* + LIGHTCONE_* / TZAFON_* conventions and adds AEGIS_* knobs.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except Exception:
    pass


def _bool(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _first(*names: str, default: str = "") -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return default


@dataclass(frozen=True)
class Config:
    # ── API keys ────────────────────────────────────────────────────────────
    kernel_api_key: str = os.environ.get("KERNEL_API_KEY", "")
    # Tzafon's Lightcone SDK accepts either name; we expose both for the team's existing scripts
    tzafon_api_key: str = _first("TZAFON_API_KEY", "LIGHTCONE_API_KEY")
    lightcone_api_key: str = _first("LIGHTCONE_API_KEY", "TZAFON_API_KEY")
    minimax_api_key: str = os.environ.get("MINIMAX_API_KEY", "")
    minimax_base_url: str = os.environ.get(
        "MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"
    )
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    brev_api_key: str = os.environ.get("BREV_API_KEY", "")

    # ── Backend selection (matches team convention) ─────────────────────────
    browser_backend: str = os.environ.get("BROWSER_BACKEND", "kernel")

    # ── Self-hosted Northstar (Stream A stretch) ────────────────────────────
    use_local_northstar: bool = _bool(os.environ.get("USE_LOCAL_NORTHSTAR"), False)
    northstar_vllm_url: str = os.environ.get("NORTHSTAR_VLLM_URL", "")

    # ── Model IDs (env-overridable, matches team convention) ────────────────
    northstar_model: str = os.environ.get("NORTHSTAR_MODEL", "tzafon.northstar-cua-fast")
    verifier_model: str = os.environ.get("VERIFIER_MODEL", "MiniMax-M2.7-highspeed")
    # Judge: Anthropic if available, else fall back to MiniMax (cheap)
    judge_model: str = os.environ.get(
        "JUDGE_MODEL",
        "claude-opus-4-7" if os.environ.get("ANTHROPIC_API_KEY") else "MiniMax-M2.7-highspeed",
    )

    # ── CUA loop knobs (matches team convention) ────────────────────────────
    cua_display_width: int = int(os.environ.get("CUA_DISPLAY_WIDTH", "1280"))
    cua_display_height: int = int(os.environ.get("CUA_DISPLAY_HEIGHT", "720"))
    cua_max_steps: int = int(os.environ.get("CUA_MAX_STEPS", "40"))
    cua_max_attempts: int = int(os.environ.get("CUA_MAX_ATTEMPTS", "5"))
    cua_traj_dir: str = os.environ.get("CUA_TRAJ_DIR", "trajectories")

    # ── AEGIS-specific knobs ────────────────────────────────────────────────
    default_n: int = int(os.environ.get("AEGIS_DEFAULT_N", "4"))
    verify_every_step: bool = _bool(os.environ.get("AEGIS_VERIFY_EVERY_STEP"), True)
    security_default: str = os.environ.get("AEGIS_SECURITY_DEFAULT", "block")
    audit_log_path: str = os.environ.get("AEGIS_AUDIT_LOG_PATH", "./audit.jsonl")
    openshell_policy_path: str = os.environ.get(
        "OPENSHELL_POLICY_PATH",
        "aegis_core/security/openshell_policy.yaml",
    )

    log_level: str = os.environ.get("LOG_LEVEL", "INFO")


CONFIG = Config()


def health_check() -> dict[str, bool]:
    """Quick presence check for the keys we need before any stream starts."""
    return {
        "kernel": bool(CONFIG.kernel_api_key),
        "tzafon_or_lightcone": bool(CONFIG.tzafon_api_key or CONFIG.lightcone_api_key),
        "minimax": bool(CONFIG.minimax_api_key),
        "anthropic": bool(CONFIG.anthropic_api_key),
    }
