import os
import asyncio
import logging
from typing import Optional, Any
from google.cloud import bigquery

logger = logging.getLogger(__name__)

_bq_client: Optional[bigquery.Client] = None

def get_bq_client() -> Optional[bigquery.Client]:
    """
    Retrieves or initializes the Google Cloud BigQuery client singleton securely.
    
    Returns:
        Optional[bigquery.Client]: The BigQuery client, or None if the project ID is missing.
    """
    global _bq_client
    if _bq_client is not None:
        return _bq_client
        
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id and project_id != "your-project-id":
        try:
            _bq_client = bigquery.Client(project=project_id)
            logger.info("BigQuery client successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
    else:
         logger.warning("GOOGLE_CLOUD_PROJECT empty or invalid. Analytics will be locally simulated.")
         
    return _bq_client

async def log_event(event_name: str, payload: dict[str, Any]) -> None:
    """
    Sinks an analytic event asynchronously via thread-offload to Google BigQuery.
    
    Args:
        event_name (str): The logical name of the event (e.g., 'chat_interaction').
        payload (dict): Structured event telemetry metadata.
    """
    client = get_bq_client()
    if not client:
        return
        
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-project-id")
    table_id = f"{project_id}.analytics.events"
    
    def _insert() -> None:
        if not client:
            return
        try:
            errors = client.insert_rows_json(table_id, [{"event": event_name, **payload}])
            if errors:
                logger.error(f"BigQuery Insert Errors: {errors}")
            else:
                logger.info(f"BigQuery Event Logged (insert): {event_name}")
        except Exception as e:
            logger.error(f"Failed to insert to BigQuery: {e}")

    await asyncio.to_thread(_insert)
