# AEGIS

**Reliability + safety middleware that wraps any computer-use agent.**

Wide-scaling parallel sampling on KERNEL Pools, per-step verification, and visual prompt-injection defense. Doubles open-model performance (Northstar 37% → ~72% on OSWorld-class tasks) at sub-Claude cost.

> Built for the Open Source Computer Use Hackathon (May 9, 2026) — Tzafon, KERNEL, SF Compute, Nvidia.

---

## What it is

Three composable layers you can stack on any CUA model (Northstar, Claude Computer Use, OpenAI CUA, Browser Use, Stagehand, etc.):

| Layer | Job | Inspiration |
|---|---|---|
| **Wide-Scaling Engine** | Run the same task across N parallel KERNEL browsers with sampling diversity. An LLM judge picks the best trajectory. | BJudge (37%→72% on OSWorld) |
| **Verification Loop** | After every action, a small verifier checks: did the screen change as expected? Is the agent on track? Trigger retry on drift. | VLAA-GUI (Completeness Verifier + Loop Breaker) |
| **Security Guardrails** | Visual prompt-injection scanner on every screenshot. Block dangerous actions (purchase, send-money, contact, file delete) without explicit human approval. Full audit trail. | OS-Harm / WASP defense literature |

Inference-time only. No training. Wraps any model. Apache 2.0.

## Why it works economically

Northstar CUA Fast costs **$0.30/M input tokens** vs Claude Opus 4.6 at **~$15/M**. Wide-scaling at N=8 across Northstar still costs **less than one Claude call** — and the judge picks the best of 8 trajectories, recovering performance the small model loses on its own.

Result: **frontier-class CUA reliability on open 4B weights**, self-hostable on a single Brev GPU.

## Reference application: Bargain Radar

A real, demo-able CUA app built on AEGIS. Lives in [`examples/bargain_radar/`](examples/bargain_radar/).

Type *"Used Eames lounge chair, real leather, under $1500, within 50 miles"*. AEGIS-wrapped Northstar fans out across **Facebook Marketplace, Craigslist, OfferUp, Mercari, eBay, Reverb** simultaneously, verifies every listing (matches the query? not stale? not a known scam pattern?), ranks the survivors, and never messages a seller without your explicit approval.

The same system without AEGIS is unusable on these sites. With AEGIS, it ships.

## Architecture

```
       ┌──────────────────────────────────────────────────────────┐
       │                   USER QUERY (CLI / web)                 │
       └──────────────────────────────┬───────────────────────────┘
                                      │
                          ┌───────────▼────────────┐
                          │  AEGIS Orchestrator    │
                          └───────────┬────────────┘
                                      │
       ┌──────────────────────────────┴──────────────────────────┐
       │                  WIDE-SCALING ENGINE  (Stream A)        │
       │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
       │   │ KERNEL  │  │ KERNEL  │  │ KERNEL  │  │ KERNEL  │   │
       │   │ browser │  │ browser │  │ browser │  │ browser │   │
       │   │   +     │  │   +     │  │   +     │  │   +     │   │
       │   │Northstar│  │Northstar│  │Northstar│  │Northstar│   │
       │   │ (temp1) │  │ (temp2) │  │ (temp3) │  │ (temp4) │   │
       │   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
       │        └───────┬────┴────────────┴────────────┘         │
       │     each step  │                                        │
       │       ╔════════▼═══════════════════════════════╗        │
       │       ║  VERIFICATION LOOP   (Stream B)        ║        │
       │       ║  • screen-change predictor             ║        │
       │       ║  • on-track classifier                 ║        │
       │       ║  • retry policy / loop-breaker         ║        │
       │       ╚════════╤═══════════════════════════════╝        │
       │     each frame │                                        │
       │       ╔════════▼═══════════════════════════════╗        │
       │       ║  SECURITY GUARDRAILS (Stream C)        ║        │
       │       ║  • visual prompt-injection scanner     ║        │
       │       ║  • dangerous-action policy engine      ║        │
       │       ║  • OpenShell sandbox enforcement       ║        │
       │       ║  • audit log                           ║        │
       │       ╚════════╤═══════════════════════════════╝        │
       └────────────────┼────────────────────────────────────────┘
                        │
              ┌─────────▼──────────┐
              │  Trajectory Judge  │   ← Claude Opus 4.6 picks best of N
              └─────────┬──────────┘
                        │
              ┌─────────▼──────────┐
              │ LIVE DASHBOARD     │   (Stream D)
              │ KERNEL live-views  │
              │ + verdict stream   │
              │ + success-rate UI  │
              └────────────────────┘
```

## The sponsor stack used

- **KERNEL** — Browser Pools (10-50 pre-warmed browsers per query × N=8 sampling), Computer Controls API, Managed Auth (1Password) for the FB Marketplace login flow, live-view iframes for the dashboard.
- **Tzafon Northstar CUA Fast 4B** — the executor model, accessed via Lightcone SDK or self-hosted on Brev via vLLM.
- **Nvidia Brev + NemoClaw + OpenShell** — Northstar served on H100 behind OpenShell's `inference.local` proxy. NemoClaw's policy YAML enforces the dangerous-action gates at the sandbox boundary.
- **Anthropic Claude Opus 4.6** — trajectory judge for wide-scaling; secondary verifier model.

## Quickstart

```bash
git clone https://github.com/<team>/aegis.git
cd aegis
uv venv && uv sync
cp .env.example .env  # fill in keys

# Single-shot demo (wraps Northstar with N=4 sampling on a real query)
python -m aegis.demo \
    --query "vintage Polaroid camera under $200 within 50mi of San Francisco" \
    --sites craigslist,offerup,mercari,ebay \
    --n 4

# Full Bargain Radar dashboard
python -m examples.bargain_radar.server
# → http://localhost:3000
```

## Evaluation

We measure AEGIS on:
- **Bargain Radar held-out set**: 50 hand-curated queries with verified ground-truth listings. Pass rate with N=1 vs N=8.
- **WebVoyager subset**: 100 tasks. Pass rate with raw Northstar vs AEGIS-wrapped Northstar vs AEGIS-wrapped Northstar with verification + security on.
- **Injection defense**: 30 adversarial pages from OS-Harm/WASP. Detection rate.

Numbers in [`BUILD_PLAN.md`](BUILD_PLAN.md#evaluation--what-we-measure).

## License

Apache 2.0. See [LICENSE](LICENSE).

## Built by

Team @ Open Source Computer Use Hackathon, San Francisco, 2026-05-09.

---

For the full execution plan (per-engineer assignments, timeline, demo script, fallback paths) see [`BUILD_PLAN.md`](BUILD_PLAN.md).
