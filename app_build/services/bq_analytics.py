import os
import logging
from google.cloud import bigquery

logger = logging.getLogger(__name__)

_bq_client = None

def get_bq_client():
    global _bq_client
    if _bq_client is not None:
        return _bq_client
        
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id:
        try:
            _bq_client = bigquery.Client(project=project_id)
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
    return _bq_client

async def log_event(event_name: str, payload: dict):
    """
    Sinks an analytic event to BigQuery.
    """
    client = get_bq_client()
    if not client:
        logger.warning(f"BigQuery client not available. Event '{event_name}' not logged.")
        return
        
    # In a full implementation, you would write this to a specific dataset.table
    # e.g. table_id = f"{project_id}.analytics.events"
    # client.insert_rows_json(table_id, [{"event": event_name, **payload}])
    
    logger.info(f"BigQuery Event Logged (simulated insert): {event_name} - {payload}")
