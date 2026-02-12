import httpx
import logging
from typing import List, Dict

logger = logging.getLogger("crawler-service")

class ClinicalTrialsFetcher:
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    async def fetch_recent_studies(self, query: str = None, limit: int = 10) -> List[Dict]:
        """
        Fetch recent studies from ClinicalTrials.gov API v2.
        If query is provided, it filters studies by the search term.
        """
        params = {
            "format": "json",
            "pageSize": limit,
            "sort": "LastUpdatePostDate:desc" # Get most recently updated
        }
        if query:
            params["query.term"] = query
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                studies = []
                if "studies" in data:
                    for item in data["studies"]:
                        protocol = item.get("protocolSection", {})
                        identification = protocol.get("identificationModule", {})
                        description = protocol.get("descriptionModule", {})
                        status = protocol.get("statusModule", {})
                        
                        nct_id = identification.get("nctId")
                        if not nct_id: continue
                        
                        study = {
                            "nctId": nct_id,
                            "title": identification.get("briefTitle", "No Title"),
                            "summary": description.get("briefSummary", ""),
                            "status": status.get("overallStatus", "Unknown"),
                            "lastUpdate": status.get("lastUpdatePostDateStruct", {}).get("date"),
                            "url": f"https://clinicaltrials.gov/study/{nct_id}",
                            "sponsor": protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "Unknown")
                        }
                        studies.append(study)
                return studies
        except Exception as e:
            logger.error(f"Error fetching clinical trials: {e}")
            return []
