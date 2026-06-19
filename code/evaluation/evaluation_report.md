# Operational Analysis — Multi-Modal Evidence Review

## Model Configuration

| Setting | Value |
|---------|-------|
| Model | gemini-flash-lite-latest (resolving to gemini-3.1-flash-lite) |
| Temperature | 0.1 |
| Output format | Structured JSON |
| Concurrency | 1 request at a time (sequential) |
| Pacing Delay | 4.5 seconds sleep between calls (respects 15 RPM free tier limit) |

## Model Calls

| Dataset | Claims | API Calls | Strategy |
|---------|--------|-----------|----------|
| Sample (evaluation) | 20 | 20 per strategy × 2 strategies = 40 | Both compared |
| Test (final) | 44 | 44 | Best strategy (direct) |
| Total | — | 84 | — |

> Retry calls occurred at 0% during the robust paced run (exponential backoff: 15s → 22.5s → 33.75s → 50.6s → 75.9s, max 5 retries).

## Token Usage

| Metric | Per Claim (avg) | Sample Set (20) | Test Set (44) |
|--------|----------------|-----------------|---------------|
| Input tokens (Direct) | ~2,701 | 54,029 | ~118,844 |
| Output tokens (Direct) | ~175 | 3,513 | ~7,700 |
| **Total (Direct)** | **~2,876** | **57,542** | **~126,544** |
| Input tokens (Few-Shot) | ~3,457 | 69,149 | — |
| Output tokens (Few-Shot) | ~177 | 3,549 | — |
| **Total (Few-Shot)** | **~3,634** | **72,698** | — |

> Input tokens include: system prompt (~800 for Direct, ~1,500 for Few-Shot), user prompt (~400), image tokens (~258 per image × 1-3 images).

## Images Processed

| Dataset | Total Images | Avg per Claim |
|---------|-------------|---------------|
| Sample | 30 | 1.5 |
| Test | 80 | 1.8 |

## Cost Estimate

| Item | Rate (AI Studio Free Tier) | Direct Strategy Cost | Few-Shot Strategy Cost |
|------|------|-------------|-----------|
| Input tokens | $0.075/1M | $0.004 | $0.005 |
| Output tokens | $0.30/1M | $0.001 | $0.001 |
| **Per strategy run** | — | ~$0.005 | ~$0.006 |
| **Total (Both runs)** | — | — | **~$0.011** |

> Extremely cost-efficient. Gemini 3.1 Flash-Lite is optimized for speed, low latency, and is free under the standard Google AI Studio tier.

## Latency & Runtime

| Metric | Value |
|--------|-------|
| Avg latency per claim | ~6.5 seconds (including 4.5s pacing sleep) |
| Sample set (20 claims, concurrency=1, pacing=4.5s) | ~130 seconds (~2.1 minutes) |
| Test set (44 claims, concurrency=1, pacing=4.5s) | ~286 seconds (~4.8 minutes) |
| Full pipeline (both strategies on sample + test) | ~9 minutes total |

## TPM/RPM Strategy

| Concern | Strategy |
|---------|----------|
| Rate limits | `asyncio.Semaphore(1)` with `await asyncio.sleep(4.5)` pacing between requests |
| Backoff | Exponential: 15s → 22.5s → 33.75s → 50.6s → 75.9s, max 5 retries |
| Token budget | Single call per claim (all images + context in one request) |
| Caching | Not implemented (claims are unique per run) |

## Strategies Compared

| Metric | Direct | Few-Shot | Winner |
|--------|--------|----------|--------|
| claim_status accuracy | 75.0% | 70.0% | Direct |
| issue_type accuracy | 50.0% | 60.0% | Few-Shot |
| object_part accuracy | 75.0% | 90.0% | Few-Shot |
| evidence_standard_met accuracy | 85.0% | 90.0% | Few-Shot |
| severity accuracy | 35.0% | 35.0% | Tie |
| risk_flags Jaccard | 72.8% | 79.6% | Few-Shot |
| supporting_image_ids Jaccard | 85.0% | 87.5% | Few-Shot |
| Tokens per claim (avg) | ~2,877 | ~3,635 | Direct (Cheaper) |

> **Recommendation:** While Few-Shot achieves higher accuracy across fine-grained metrics (like `object_part`, `issue_type`, and `risk_flags`), Direct is recommended by the evaluator for overall `claim_status_accuracy` (75% vs 70%) on this sample set, while using ~20% fewer tokens.

---

*Report generated after running `python evaluation/main.py --compare`*
