# Fullstack AI Assistant - Google Antigravity Challenge

## Chosen Vertical
**Fullstack**

## Approach and Logic
The architecture is designed with an "agent-first" and proactive security mindset. Rather than passing user queries blindly to Google services, the backend (built with Python FastAPI) stands as a protective reasoning layer.
1. **Input Validation:** User prompts are intercepted and strictly validated (length bounds, content checks) via Pydantic models to prevent DoS or injection overloads.
2. **Context-Aware Routing:** Once validated, the prompt is safely handed off to the `vertex_llm.py` service.
3. **Graceful Degradation (Mock Mode):** A strict security guardrail ensures that if Application Default Credentials (ADC) or environmental GCP configs are not present, the agent falls back to a safe "Mock Mode". It gracefully alerts the user instead of outright crashing or exposing hardcoded credentials.

## How the Solution Works
The project follows a robust modular execution pipeline located entirely in the `app_build/` directory:
- **Frontend (`app_build/static`):** A sleek, dark-themed responsive vanilla HTML/CSS/JS frontend provides the user interface. It securely pipes inputs to the backend API via asynchronous JavaScript `fetch`.
- **Backend API (`app_build/main.py`):** An asynchronous FastAPI instance processes incoming JSON data streams. 
- **Google Cloud Services Integration:** 
  - **Vertex AI (`vertex_llm.py`):** Acts as the primary brain processing the user interactions dynamically.
  - **Cloud SQL (`db_client.py`):** Leverages SQLAlchemy async engines to securely commit chat histories to a relational database for persistance.
  - **BigQuery (`bq_analytics.py`):** Sinks usage event telemetry for real-time traffic analysis.

## Any Assumptions Made
- **Environment Context:** Assumes the terminal executing the server has been actively exported with the required GCP environment variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`).
- **Application Default Credentials:** Assumes `gcloud auth application-default login` has been executed locally. 
- **Database Architecture:** Currently abstracted with a local SQLite fallback if `DB_URL` isn't fully provided, guaranteeing zero-downtime local development.