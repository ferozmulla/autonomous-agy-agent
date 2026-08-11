# Agent-Built Demos

**Automated company-specific Agentic AI demos for Google Cloud Sales Engineers.**

Type a company name → get a live, deployed demo dashboard with synthetic data and an AI-powered analytics chatbot — all built by AI agents in under 10 minutes.

```bash
python src/launch_demo.py --company "SiriusXM"
```

## What It Does

Agent-Built Demos spawns two Managed Agents in parallel via the Gemini API:

1. **Page Builder Agent** — Researches the company via web search, builds a React "Pastel Terminal" dashboard with financial data, and deploys it to Cloud Run. In Phase 2, it also builds and deploys a Conversational Analytics (CA) backend agent.

2. **Data Generator Agent** — Determines the company's industry, selects an analytics use-case, generates a synthetic BigQuery dataset following the `analytics-data-generator` skill methodology, and verifies data quality.

The result is a live URL with a polished dashboard showing company financials, growth drivers, market challenges, and a working AI chat interface.

## Architecture

```
Sales Engineer (CLI)
    │
    ├── launch_demo.py ──┬── Managed Agent 1: Page Builder
    │                    │      ├── Web Search (company research)
    │                    │      ├── React App (Pastel Terminal)
    │                    │      ├── CA Backend (ADK Agent)
    │                    │      └── Cloud Run Deploy
    │                    │
    │                    └── Managed Agent 2: Data Generator
    │                           ├── Industry Detection
    │                           ├── BigQuery SQL Generation
    │                           └── Dataset Verification
    │
    └── Output: ✅ Demo ready: https://{company}-frontend-xxx.run.app
```

## Prerequisites

- Python 3.11+
- Node.js 20+ (for local frontend development)
- Google Cloud SDK (`gcloud`) installed and authenticated
- A GCP project with BigQuery API and Cloud Run API enabled
- A Gemini API key

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd agent-built-demos
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY

# 3. Set up GCP project (one-time)
bash scripts/setup_project.sh

# 4. Run a demo
python src/launch_demo.py --company "Apple"
```

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `--company` | *(required)* | Company name to build the demo for |
| `--ticker` | *(auto-detected)* | Stock ticker symbol (optional override) |
| `--project` | `firstargolisproject-338816` | GCP project ID |
| `--region` | `us-central1` | GCP region for Cloud Run |

## Project Structure

```
agent-built-demos/
├── src/                          # CLI orchestrator
│   ├── launch_demo.py            # Main entry point
│   ├── config.py                 # Configuration & slugify
│   ├── output.py                 # Rich terminal formatting
│   ├── result_parser.py          # Agent output parsing
│   └── agents/                   # Agent invocation modules
│       ├── data_generator.py     # Data Generator agent
│       └── page_builder.py       # Page Builder agent
├── prompts/                      # Managed Agent system instructions
│   ├── data_generator_system.md  # Data Generator prompt
│   ├── page_builder_system.md    # Page Builder prompt
│   └── ca_agent_system_template.md # CA agent prompt template
├── templates/page-builder/       # Files mounted into Page Builder sandbox
│   ├── frontend/                 # React + Vite application
│   └── ca-backend/               # ADK agent backend
├── skills/analytics-data-generator/ # Data Generator skill
│   ├── SKILL.md                  # Skill instructions
│   └── examples/                 # Reference SQL scripts
├── scripts/                      # Infrastructure scripts
├── tests/                        # Test suite
├── docs/                         # Documentation
└── web-page-design/              # Design system reference (read-only)
```

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) — Detailed installation and configuration
- [Customization Guide](docs/CUSTOMIZATION_GUIDE.md) — Extending the system
- [Prompt Engineering Guide](docs/PROMPT_ENGINEERING.md) — Iterating on agent prompts
- [PRD](docs/PRD.md) — Product Requirements Document
- [Design Doc](docs/DESIGN_DOC.md) — Technical Design Document

## Troubleshooting

| Problem | Solution |
|---|---|
| `GOOGLE_API_KEY not set` | Copy `.env.example` to `.env` and add your API key |
| `gcloud auth error` | Run `gcloud auth login` and `gcloud auth application-default login` |
| BigQuery permission denied | Ensure BigQuery API is enabled: `gcloud services enable bigquery.googleapis.com` |
| Cloud Run deploy fails | Ensure Cloud Run API is enabled: `gcloud services enable run.googleapis.com` |
| Agent timeout | The company may have insufficient public data. Try a well-known public company. |

## License

Apache 2.0 — see [LICENSE](LICENSE).
