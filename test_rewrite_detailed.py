"""
Test rewrite endpoint with detailed error information
"""
import requests
import json

def test_rewrite_detailed():
    base_url = "http://localhost:8001"
    
    print("🧪 Testing AI Rewrite Endpoint with Detailed Error Info...")
    
    # Test 1: Check if service is running
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test 2: Test rewrite endpoint with detailed error info
    try:
        payload = {
            "field": "title",
            "current_content": "Test post",
            "platform": "instagram",
            "content_type": "post"
        }
        
        print(f"\n📝 Testing rewrite with payload: {payload}")
        response = requests.post(
            f"{base_url}/ai/rewrite",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Rewrite endpoint working!")
            print(f"Response JSON: {response.json()}")
        else:
            print("❌ Rewrite endpoint failed")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Test with different endpoint path
    try:
        print(f"\n📝 Testing rewrite with /ai/rewrite/ path...")
        response = requests.post(
            f"{base_url}/ai/rewrite/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        
    except Exception as e:
        print(f"❌ Alternative path failed: {e}")

if __name__ == "__main__":
    test_rewrite_detailed()

