import httpx
import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger("orchestrator")

class CompetitorClient:
    def __init__(self):
        self.base_url = os.getenv("COMPETITOR_SERVICE_URL", "http://competitor-service:8000")

    async def get_competitors(self, headers: Optional[Dict] = None) -> List[Dict]:
        """Fetch all competitors from the Competitor Service."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/competitors", headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch competitors: {e}")
            return []

    async def add_trial(self, competitor_id: str, trial_data: Dict, headers: Optional[Dict] = None) -> Optional[Dict]:
        """Add a clinical trial to a competitor."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/api/competitors/{competitor_id}/trials",
                    json=trial_data,
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"Successfully added trial {trial_data.get('trialId')} to competitor {competitor_id}")
                return response.json()
        except httpx.HTTPStatusError as e:
             logger.error(f"Failed to add trial: {e.response.text}")
             return None
        except Exception as e:
            logger.error(f"Error adding trial: {e}")
            return None
