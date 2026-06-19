# Multi-Modal Evidence Review — Solution

## Quick Start

### 1. Install Dependencies

```bash
cd code/
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your Gemini API key
# GOOGLE_API_KEY=your_key_here
```

Or set it as an environment variable:
```bash
export GOOGLE_API_KEY=your_key_here        # macOS/Linux
set GOOGLE_API_KEY=your_key_here           # Windows CMD
$env:GOOGLE_API_KEY="your_key_here"        # PowerShell
```

### 3. Run on Test Data

```bash
cd code/
python main.py
```

This reads `dataset/claims.csv`, processes 45 claims, and writes `output.csv` to the repo root.

### 4. Run Evaluation

```bash
# Evaluate with the default strategy (few_shot)
cd code/
python evaluation/main.py

# Compare both strategies
python evaluation/main.py --compare
```

---

## Architecture

```
claims.csv ──► Parser ──► Pipeline Orchestrator ──► Output Writer ──► output.csv
                              │
                    ┌─────────┼──────────┐
                    ▼         ▼          ▼
              Image       Gemini      Post-
              Validator   Vision      Processor
                          Analyzer    (guardrails)
```

### Pipeline Flow (per claim)

1. **Parse** claim, look up user history and evidence requirements
2. **Validate** images locally with Pillow (saves tokens on bad inputs)
3. **Analyze** with Gemini 2.5 Flash — single multimodal call with all images + context
4. **Post-process** — merge risk flags from Gemini + history, apply decision guardrails
5. **Write** structured output row

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **1 API call per claim** | Cost-efficient: all images + context in one request |
| **Structured JSON output** | Eliminates parsing errors, enforced by Gemini |
| **Pydantic validation** | Catches and clamps any invalid values from Gemini |
| **Two prompt strategies** | "Direct" (no examples) vs "Few-Shot" (4 representative examples) — compared on sample data |
| **Async with semaphore** | 5 concurrent requests balances speed vs rate limits |
| **Low temperature (0.1)** | More deterministic outputs for consistent evaluations |

---

## File Structure

```
code/
├── main.py                    # CLI entry point
├── config.py                  # Settings and paths
├── models.py                  # Pydantic models + enums for all allowed values
├── parsers.py                 # CSV parsers (claims, history, requirements)
├── image_validator.py         # Pre-flight image checks with Pillow
├── gemini_client.py           # Gemini API wrapper (retry, backoff, tokens)
├── vision_analyzer.py         # Prompt builder + Gemini call + response validation
├── post_processor.py          # Evidence check, risk flag merge, decision guardrails
├── output_writer.py           # CSV output with exact schema
├── pipeline.py                # Orchestrator (async, progress, ordering)
├── prompts.py                 # System/user prompt templates (2 strategies)
├── requirements.txt           # Dependencies
├── .env.example               # API key template
└── evaluation/
    ├── main.py                # Evaluation runner + strategy comparison
    ├── metrics.py             # Accuracy, Jaccard, per-object breakdown
    └── evaluation_report.md   # Operational analysis
```

---

## CLI Options

```bash
python main.py [OPTIONS]

Options:
  --sample           Run on sample_claims.csv (for evaluation)
  --input PATH       Custom input CSV path
  --output PATH      Custom output CSV path
  --strategy TYPE    "direct" or "few_shot" (default: few_shot)
  --concurrency N    Max parallel API calls (default: 5)
  --api-key KEY      Override GOOGLE_API_KEY env var
  --model NAME       Override Gemini model (default: gemini-2.5-flash)
```

---

## Model & Cost

- **Model:** Google Gemini 2.5 Flash
- **Cost per claim:** ~$0.0005
- **Total cost (85 API calls):** ~$0.04
- **Avg latency:** 3-5 seconds per claim

See `evaluation/evaluation_report.md` for full operational analysis.
