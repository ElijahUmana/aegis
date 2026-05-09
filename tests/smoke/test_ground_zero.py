"""Ground-zero connectivity smoke tests. Run before any stream starts.

    uv run python -m tests.smoke.test_ground_zero
"""
from __future__ import annotations

import asyncio
import json
import sys
import time

from rich.console import Console
from rich.table import Table

from aegis_core.core.config import CONFIG, health_check

console = Console()


def banner(title: str) -> None:
    console.rule(f"[bold cyan]{title}[/bold cyan]")


def check_keys() -> dict[str, bool]:
    banner("1/4  env / keys")
    h = health_check()
    table = Table(show_header=True, header_style="bold")
    table.add_column("provider")
    table.add_column("present")
    for k, v in h.items():
        table.add_row(k, "✅" if v else "❌")
    console.print(table)
    if not h["kernel"] or not h["tzafon_or_lightcone"]:
        console.print("[red]missing required keys; aborting.[/red]")
        sys.exit(1)
    return h


def check_kernel() -> str:
    banner("2/4  KERNEL connectivity")
    try:
        from kernel import Kernel
    except Exception as e:
        console.print(f"[red]import kernel failed: {e}[/red]")
        sys.exit(1)
    k = Kernel(api_key=CONFIG.kernel_api_key)
    t0 = time.time()
    browsers = k.browsers.list()
    dt = (time.time() - t0) * 1000
    n = len(list(browsers)) if hasattr(browsers, "__iter__") else 0
    console.print(f"  ✅ list_browsers OK in {dt:.0f}ms ({n} active)")
    return f"kernel ok ({dt:.0f}ms)"


def check_tzafon() -> str:
    banner("3/4  Tzafon Lightcone connectivity")
    try:
        from tzafon import Lightcone
    except Exception as e:
        console.print(f"[red]import tzafon failed: {e}[/red]")
        sys.exit(1)
    lc = Lightcone(api_key=CONFIG.tzafon_api_key or CONFIG.lightcone_api_key)
    t0 = time.time()
    try:
        models = lc.models.list()
        dt = (time.time() - t0) * 1000
        ids = [m.id for m in models.data] if hasattr(models, "data") else []
        console.print(f"  ✅ list_models OK in {dt:.0f}ms")
        if ids:
            console.print(f"  available: {', '.join(ids[:6])}{'...' if len(ids) > 6 else ''}")
        return f"tzafon ok ({dt:.0f}ms)"
    except Exception as e:
        console.print(f"[yellow]list_models failed ({e}); trying minimal completion...[/yellow]")
        t0 = time.time()
        resp = lc.responses.create(
            model=CONFIG.northstar_model,
            input=[{"role": "user", "content": "ping"}],
            max_output_tokens=8,
        )
        dt = (time.time() - t0) * 1000
        console.print(f"  ✅ responses.create OK in {dt:.0f}ms")
        return f"tzafon ok ({dt:.0f}ms)"


def check_minimax() -> str:
    banner("4/4  MiniMax connectivity (verifier)")
    if not CONFIG.minimax_api_key:
        console.print("[yellow]  no MINIMAX_API_KEY; skipping[/yellow]")
        return "minimax skipped"
    import httpx
    headers = {
        "Authorization": f"Bearer {CONFIG.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": CONFIG.verifier_model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 4,
        "stream": False,
    }
    for base in (
        "https://api.minimaxi.com/v1/chat/completions",
        "https://api.minimax.io/v1/chat/completions",
        "https://api.minimax.chat/v1/chat/completions",
    ):
        try:
            t0 = time.time()
            r = httpx.post(base, headers=headers, json=payload, timeout=15.0)
            dt = (time.time() - t0) * 1000
            if r.status_code == 200:
                console.print(f"  ✅ {base} → 200 in {dt:.0f}ms")
                return f"minimax ok via {base}"
            console.print(f"  [dim]{base} → {r.status_code} ({r.text[:120]})[/dim]")
        except Exception as e:
            console.print(f"  [dim]{base} → {e}[/dim]")
    console.print("[yellow]  could not reach MiniMax; verifier needs manual setup[/yellow]")
    return "minimax unreachable (non-blocking)"


def main() -> int:
    console.print("[bold]AEGIS ground-zero smoke[/bold]")
    console.print(f"  cfg: backend={CONFIG.browser_backend} ns={CONFIG.northstar_model} "
                  f"verifier={CONFIG.verifier_model} judge={CONFIG.judge_model}")
    console.print(f"       display={CONFIG.cua_display_width}x{CONFIG.cua_display_height} "
                  f"max_steps={CONFIG.cua_max_steps} N={CONFIG.default_n}")

    h = check_keys()
    results = {
        "kernel": check_kernel(),
        "tzafon": check_tzafon(),
        "minimax": check_minimax(),
    }
    banner("summary")
    for k, v in results.items():
        console.print(f"  • {k}: {v}")
    console.print("\n[bold green]GROUND ZERO READY ✓[/bold green]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
