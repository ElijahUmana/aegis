"""Centralized config / env loading. Imported by all streams."""
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


@dataclass(frozen=True)
class Config:
    # API keys
    kernel_api_key: str = os.environ.get("KERNEL_API_KEY", "")
    tzafon_api_key: str = os.environ.get("TZAFON_API_KEY", "")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    brev_api_key: str = os.environ.get("BREV_API_KEY", "")

    # Self-hosted Northstar
    use_local_northstar: bool = _bool(os.environ.get("USE_LOCAL_NORTHSTAR"), False)
    northstar_vllm_url: str = os.environ.get("NORTHSTAR_VLLM_URL", "")

    # AEGIS knobs
    default_n: int = int(os.environ.get("AEGIS_DEFAULT_N", "4"))
    verify_every_step: bool = _bool(os.environ.get("AEGIS_VERIFY_EVERY_STEP"), True)
    security_default: str = os.environ.get("AEGIS_SECURITY_DEFAULT", "block")
    audit_log_path: str = os.environ.get("AEGIS_AUDIT_LOG_PATH", "./audit.jsonl")

    # OpenShell / NemoClaw
    openshell_policy_path: str = os.environ.get(
        "OPENSHELL_POLICY_PATH",
        "aegis_core/security/openshell_policy.yaml",
    )

    # Model IDs
    northstar_model: str = "tzafon.northstar-cua-fast-1.2"
    judge_model: str = "claude-opus-4-7"          # Opus 4.7 1M (locked default)
    verifier_model: str = "claude-haiku-4-5-20251001"

    log_level: str = os.environ.get("LOG_LEVEL", "INFO")


CONFIG = Config()
