import asyncio
import httpx
import logging

# Configuration
BASE_URLS = {
    "user": "http://localhost:8004",
    "competitor": "http://localhost:8001",
    "notification": "http://localhost:8003",
    "crawler": "http://localhost:8005"
}

# Data to Seed
USER_DATA = {
    "email": "admin@astrazeneca.com",
    "password": "password123",
    "role": "ADMIN"
}

COMPETITORS = [
    {
        "name": "Roche",
        "headquarters": "Basel, Switzerland",
        "therapeuticAreas": ["Oncology", "Immunology", "Ophthalmology"],
        "activeDrugs": 85,
        "pipelineDrugs": 150
    },
    {
        "name": "Novartis",
        "headquarters": "Basel, Switzerland", 
        "therapeuticAreas": ["Cardiovascular", "Oncology", "Immunology"],
        "activeDrugs": 70,
        "pipelineDrugs": 130
    },
    {
        "name": "Pfizer",
        "headquarters": "New York, USA",
        "therapeuticAreas": ["Oncology", "Inflammation", "Vaccines"],
        "activeDrugs": 90,
        "pipelineDrugs": 110
    },
    {
        "name": "Merck & Co.",
        "headquarters": "Rahway, USA",
        "therapeuticAreas": ["Oncology", "Vaccines", "Infectious Diseases"],
        "activeDrugs": 65,
        "pipelineDrugs": 95
    }
]

JOBS = [
    {
        "source": "ClinicalTrials",
        "query": "Latest Studies",
        "schedule": "0 */12 * * *",
        "enabled": True
    },
    {
        "source": "ClinicalTrials",
        "query": "Oncology",
        "schedule": "0 */12 * * *",
        "enabled": True
    },
    {
        "source": "ClinicalTrials",
        "query": "Cardiovascular",
        "schedule": "0 */12 * * *",
        "enabled": True
    },
    {
        "source": "ResearchNews",
        "query": "General",
        "schedule": "0 */12 * * *",
        "enabled": True
    }   
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")

async def seed():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Check or Create User
        logger.info("--- Seeding User ---")
        user_id = None
        token = None
        headers = {}
        
        # Try Login First
        try:
            login_res = await client.post(f"{BASE_URLS['user']}/api/auth/login", json={
                "email": USER_DATA["email"],
                "password": USER_DATA["password"]
            })
            
            if login_res.status_code == 200:
                logger.info(f"User {USER_DATA['email']} already exists. Logged in.")
                data = login_res.json()
                token = data["accessToken"]
                user_id = data["user"]["id"]
            else:
                # Try Register
                logger.info(f"User not found, registering {USER_DATA['email']}...")
                reg_res = await client.post(f"{BASE_URLS['user']}/api/auth/register", json=USER_DATA)
                if reg_res.status_code == 201:
                    logger.info("User created successfully.")
                    # Login again to get token
                    login_res = await client.post(f"{BASE_URLS['user']}/api/auth/login", json={
                        "email": USER_DATA["email"],
                        "password": USER_DATA["password"]
                    })
                    data = login_res.json()
                    token = data["accessToken"]
                    user_id = data["user"]["id"]
                else:
                    logger.error(f"Failed to register user: {reg_res.text}")
                    return

            headers = {"Authorization": f"Bearer {token}", "X-User-Id": user_id}

        except Exception as e:
            logger.error(f"Error seeding user: {e}")
            return

        # 2. Check or Create Competitors
        logger.info("--- Seeding Competitors ---")
        competitor_ids = {}
        
        try:
            # Get existing competitors
            list_res = await client.get(f"{BASE_URLS['competitor']}/api/competitors", headers=headers)
            existing_competitors = {c["name"]: c["id"] for c in list_res.json()} if list_res.status_code == 200 else {}
            
            for comp in COMPETITORS:
                if comp["name"] in existing_competitors:
                    logger.info(f"Competitor {comp['name']} already exists.")
                    competitor_ids[comp["name"]] = existing_competitors[comp["name"]]
                else:
                    res = await client.post(f"{BASE_URLS['competitor']}/api/competitors", json=comp, headers=headers)
                    if res.status_code == 201:
                        data = res.json()
                        competitor_ids[comp["name"]] = data["id"]
                        logger.info(f"Created competitor: {comp['name']}")
                    else:
                        logger.error(f"Failed to create competitor {comp['name']}: {res.text}")
                        
        except Exception as e:
            logger.error(f"Error checking/creating competitors: {e}")

        # 3. Check or Create Subscription
        logger.info("--- Seeding Subscription ---")
        try:
            roche_id = competitor_ids.get("Roche")
            if roche_id:
                # Check existing subscriptions
                subs_res = await client.get(f"{BASE_URLS['notification']}/api/subscriptions", headers=headers)
                existing_subs = subs_res.json() if subs_res.status_code == 200 else []
                
                # Check if specific subscription exists (Oncology + Roche)
                exists = False
                for sub in existing_subs:
                    # Convert therapeuticAreas to set for comparison if order doesn't matter, 
                    # but typically checking existence in list is enough.
                    sub_areas = sub.get("therapeuticAreas", [])
                    sub_comps = sub.get("competitorIds", [])
                    
                    if "Oncology" in sub_areas and roche_id in sub_comps:
                        exists = True
                        break
                
                if exists:
                    logger.info("Subscription for Oncology and Roche already exists.")
                else:
                    sub_payload = {
                        "therapeuticAreas": ["Oncology", "General", "Cardiovascular"],
                        "competitorIds": [roche_id],
                        "channels": ["console", "email"]
                    }
                    sub_res = await client.post(f"{BASE_URLS['notification']}/api/subscriptions", json=sub_payload, headers=headers)
                    if sub_res.status_code == 201:
                        logger.info("Subscription created for Oncology and Roche.")
                    else:
                        logger.warning(f"Failed to create subscription: {sub_res.text}")
            else:
                logger.warning("Skipping subscription seeding: Roche ID not found (check if competitor created).")

        except Exception as e:
            logger.error(f"Error checking/creating subscription: {e}")

        # 4. Check or Create Crawl Jobs
        logger.info("--- Seeding Crawl Jobs ---")
        try:
            # Check existing jobs
            list_res = await client.get(f"{BASE_URLS['crawler']}/api/crawl/jobs", headers=headers)
            existing_jobs = set()
            if list_res.status_code == 200:
                for job in list_res.json():
                    existing_jobs.add(job["query"])
            
            for job in JOBS:
                if job["query"] in existing_jobs:
                    logger.info(f"Job for {job['query']} already exists.")
                else:
                    res = await client.post(f"{BASE_URLS['crawler']}/api/crawl/jobs", json=job, headers=headers)
                    if res.status_code == 201:
                        logger.info(f"Created job for: {job['query']}")
                    else:
                        logger.error(f"Failed to create job {job['query']}: {res.text}")

        except Exception as e:
            logger.error(f"Error checking/creating jobs: {e}")

    logger.info("--- Seeding Complete ---")

if __name__ == "__main__":
    asyncio.run(seed())
