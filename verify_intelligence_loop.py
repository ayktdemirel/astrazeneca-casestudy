import requests
import time
import json

BASE_URL_CRAWLER = "http://localhost:8005"
BASE_URL_COMPETITOR = "http://localhost:8001"
BASE_URL_USER_MGMT = "http://localhost:8004"

def get_admin_token():
    print("\n--- Registering Admin User ---")
    admin_data = {
        "email": f"admin_intel_{int(time.time())}@example.com",
        "password": "adminsecret",
        "role": "ADMIN"
    }
    requests.post(f"{BASE_URL_USER_MGMT}/api/auth/register", json=admin_data)
    
    # Login
    resp = requests.post(f"{BASE_URL_USER_MGMT}/api/auth/login", json={"email": admin_data['email'], "password": admin_data['password']})
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    token = resp.json()['accessToken']
    print(f"Got Admin Token: {token[:10]}...")
    return token

def run_test():
    try:
        token = get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"Skipping test - Authentication failed: {e}")
        return

    print("--- Testing Crawler -> Competitor Intelligence Loop ---")
    
    # 1. Create a Competitor that we know appears in current ClinicalTrials.gov feeds
    # Based on logs: "abbvie" appears in recent trials
    target_sponsor = "AbbVie"
    print(f"1. Creating Competitor: {target_sponsor}")
    
    comp_payload = {
        "name": target_sponsor, 
        "headquarters": "Spain",
        "therapeuticAreas": ["Stress", "VR"],
        "activeDrugs": 0,
        "pipelineDrugs": 0
    }
    
    try:
        r = requests.post(f"{BASE_URL_COMPETITOR}/api/competitors", json=comp_payload, headers=headers)
        if r.status_code == 201:
            comp_data = r.json()
            comp_id = comp_data["id"]
            print(f"✅ Created Competitor: {comp_id}")
        else:
            print(f"⚠️ Failed to create competitor (maybe exists): {r.status_code}")
            # Try to find it
            r = requests.get(f"{BASE_URL_COMPETITOR}/api/competitors", headers=headers)
            comps = r.json()
            found = next((c for c in comps if c['name'] == target_sponsor), None)
            if found:
                comp_id = found['id']
                print(f"✅ Found Existing Competitor: {comp_id}")
            else:
                print("❌ Could not find or create competitor. Aborting.")
                return
    except Exception as e:
        print(f"❌ Error connecting to Competitor Service: {e}")
        return

    # 2. Trigger Crawl
    print("\n2. Triggering Crawl Job...")
    job_payload = {
        "source": "ClinicalTrials",
        "query": "VR", 
        "schedule": "0 0 * * *",
        "enabled": True
    }
    r = requests.post(f"{BASE_URL_CRAWLER}/api/crawl/jobs", json=job_payload, headers=headers)
    if r.status_code != 201:
        print(f"❌ Failed to create crawl job: {r.text}")
        return
    job_id = r.json()["id"]
    
    r = requests.post(f"{BASE_URL_CRAWLER}/api/crawl/run", params={"job_id": job_id}, headers=headers)
    run_id = r.json()["id"]
    print(f"✅ Triggered Crawl Run: {run_id}")
    
    print("3. Waiting for Crawl to Finish (10s)...")
    time.sleep(10)
    
    print("4. Test Complete (Check logs for 'Successfully added trial')")

if __name__ == "__main__":
    run_test()
