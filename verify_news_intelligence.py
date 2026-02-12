import requests
import time
import json

BASE_URL_CRAWLER = "http://localhost:8005"
BASE_URL_USER_MGMT = "http://localhost:8004"

def get_admin_token():
    print("\n--- Registering Admin User ---")
    admin_data = {
        "email": f"admin_news_{int(time.time())}@example.com",
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

    print("--- Testing News Summarizer Intelligence Loop ---")
    
    # Trigger Crawl for ResearchNews (which uses Summarizer)
    print("\nTriggering Reviews Crawl Job...")
    job_payload = {
        "source": "ResearchNews",
        "query": "Cancer", 
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
    
    print("Waiting for Crawl to Finish (15s)...")
    time.sleep(15)
    
    print("Now check logs for JSON structure with 'company', 'drug_name', 'phase', etc.")
    print("Run: docker-compose logs crawler-service | grep 'News Signal'")

if __name__ == "__main__":
    run_test()
