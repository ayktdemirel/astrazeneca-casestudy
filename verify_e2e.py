
import requests
import json
import time

BASE_URL_COMPETITOR = "http://localhost:8001"
BASE_URL_INSIGHTS = "http://localhost:8002"
BASE_URL_NOTIFICATION = "http://localhost:8003"

def wait_for_services():
    print("Waiting for services to be ready...")
    for url in [BASE_URL_COMPETITOR, BASE_URL_INSIGHTS, BASE_URL_NOTIFICATION]:
        for i in range(30):
            try:
                resp = requests.get(f"{url}/health")
                if resp.status_code == 200:
                    print(f"{url} is ready")
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        else:
            print(f"Failed to connect to {url}")
            return False
    return True

def test_competitor_flow():
    print("\n--- Testing Competitor Flow ---")
    # Create Competitor
    comp_data = {
        "name": "AstraZeneca",
        "headquarters": "Cambridge, UK",
        "therapeuticAreas": ["Oncology", "Cardiovascular"],
        "activeDrugs": 50,
        "pipelineDrugs": 100
    }
    resp = requests.post(f"{BASE_URL_COMPETITOR}/api/competitors", json=comp_data)
    assert resp.status_code == 201, f"Create competitor failed: {resp.text}"
    comp = resp.json()
    print(f"Created Competitor: {comp['id']}")
    
    # Add Trial
    trial_data = {
        "trialId": "NCT00000001",
        "drugName": "Tagrisso",
        "phase": "Phase 3",
        "indication": "NSCLC",
        "status": "Active",
        "enrollmentTarget": 500
    }
    resp = requests.post(f"{BASE_URL_COMPETITOR}/api/competitors/{comp['id']}/trials", json=trial_data)
    assert resp.status_code == 201, f"Add trial failed: {resp.text}"
    print(f"Added Trial: {resp.json()['id']}")
    
    return comp['id']

def test_insights_flow(competitor_id):
    print("\n--- Testing Insights Flow ---")
    # Create Insight with implicit scoring
    insight_data = {
        "title": "New Approval in Oncology",
        "description": "FDA approves drug X",
        "category": "Regulatory",
        "therapeuticArea": "Oncology",
        "competitorId": competitor_id,
        "impactLevel": "High",
        "relevanceScore": None # Should become 9.0
    }
    resp = requests.post(f"{BASE_URL_INSIGHTS}/api/insights", json=insight_data)
    assert resp.status_code == 201, f"Create insight failed: {resp.text}"
    insight = resp.json()
    assert insight['relevanceScore'] == 9.0, f"Relevance score incorrect: {insight['relevanceScore']}"
    print(f"Created Insight: {insight['id']} with score {insight['relevanceScore']}")
    
    return insight['id']

def test_notification_flow(insight_id, competitor_id):
    print("\n--- Testing Notification Flow ---")
    # Create Subscription
    sub_data = {
        "therapeuticAreas": ["Oncology"],
        "competitorIds": [competitor_id],
        "channels": ["console"]
    }
    # Pass user ID header
    headers = {"X-User-Id": "user-test-01"}
    resp = requests.post(f"{BASE_URL_NOTIFICATION}/api/subscriptions", json=sub_data, headers=headers)
    assert resp.status_code == 201, f"Create subscription failed: {resp.text}"
    sub = resp.json()
    print(f"Created Subscription: {sub['id']}")
    
    # Send Notification
    send_data = {
        "insightId": insight_id,
        "subscriptionId": sub['id']
    }
    resp = requests.post(f"{BASE_URL_NOTIFICATION}/api/notifications/send", json=send_data)
    assert resp.status_code == 200, f"Send notification failed: {resp.text}"
    print(f"Notification Sent: {resp.json()}")
    
    # Check History
    resp = requests.get(f"{BASE_URL_NOTIFICATION}/api/notifications", headers=headers)
    history = resp.json()
    assert len(history) > 0, "History empty"
    print(f"Notification History verified. Count: {len(history)}")

if __name__ == "__main__":
    if wait_for_services():
        try:
            comp_id = test_competitor_flow()
            insight_id = test_insights_flow(comp_id)
            test_notification_flow(insight_id, comp_id)
            print("\n✅ E2E Verification Passed!")
        except Exception as e:
            print(f"\n❌ E2E Verification Failed: {e}")
            exit(1)
    else:
        print("\n❌ Services not ready.")
        exit(1)
