"""
Local Testing Script for CivicFix AI Service
Tests the API endpoints without deploying to cloud
"""

import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://localhost:8080"
API_KEY = "8209d737eb28d61c61026a61ee96326a96ebbc67ccc89ac04a8b6495f63d011b0f1053467bd9970399e7ad5e598115f1489265d916868dc55d1d687a06b33562"

def print_test(name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} - {name}")
    if message:
        print(f"  {message}")

def test_health_endpoint():
    """Test /health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            print_test("Health Endpoint", True, f"Status: {data.get('status')}")
            return True
        else:
            print_test("Health Endpoint", False, f"Status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_test("Health Endpoint", False, "Cannot connect - is the service running?")
        return False
    except Exception as e:
        print_test("Health Endpoint", False, f"Error: {str(e)}")
        return False

def test_root_endpoint():
    """Test / endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            print_test("Root Endpoint", True, f"Service: {data.get('service')}")
            return True
        else:
            print_test("Root Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Root Endpoint", False, f"Error: {str(e)}")
        return False

def test_stats_endpoint():
    """Test /api/v1/stats endpoint (requires API key)"""
    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(f"{BASE_URL}/api/v1/stats", headers=headers, timeout=5)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            print_test("Stats Endpoint", True, f"Total verifications: {data.get('total_verifications', 0)}")
            return True
        else:
            print_test("Stats Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        print_test("Stats Endpoint", False, f"Error: {str(e)}")
        return False

def test_stats_without_api_key():
    """Test /api/v1/stats without API key (should fail)"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/stats", timeout=5)
        passed = response.status_code == 401  # Should be unauthorized
        
        if passed:
            print_test("Stats Auth Check", True, "Correctly requires API key")
            return True
        else:
            print_test("Stats Auth Check", False, f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print_test("Stats Auth Check", False, f"Error: {str(e)}")
        return False

def test_initial_verification():
    """Test /api/v1/verify/initial endpoint"""
    try:
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "issue_id": 1,
            "image_urls": ["https://example.com/image1.jpg"],
            "category": "pothole",
            "location": {"latitude": 13.0827, "longitude": 80.2707},
            "description": "Large pothole on main road"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/verify/initial",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            print_test("Initial Verification", True, f"Status: {data.get('status')}, Confidence: {data.get('confidence_score', 0):.2f}")
            return True
        else:
            print_test("Initial Verification", False, f"Status code: {response.status_code}")
            if response.text:
                print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_test("Initial Verification", False, f"Error: {str(e)}")
        return False

def test_cors():
    """Test CORS headers"""
    try:
        headers = {"Origin": "http://localhost:3000"}
        response = requests.options(f"{BASE_URL}/health", headers=headers, timeout=5)
        
        has_cors = "access-control-allow-origin" in response.headers
        print_test("CORS Headers", has_cors, "CORS enabled" if has_cors else "CORS not configured")
        return has_cors
    except Exception as e:
        print_test("CORS Headers", False, f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("CivicFix AI Service - Local Testing")
    print("=" * 60)
    print(f"Testing service at: {BASE_URL}")
    print()
    
    # Wait for service to be ready
    print("Waiting for service to start...")
    max_retries = 10
    for i in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("Service is ready!")
            break
        except:
            if i < max_retries - 1:
                time.sleep(2)
            else:
                print("\n✗ Service did not start in time")
                print("\nMake sure the service is running:")
                print("  docker-compose up")
                print("  or")
                print("  uvicorn app.main:app --host 0.0.0.0 --port 8080")
                sys.exit(1)
    
    print()
    print("Running tests...")
    print("-" * 60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_endpoint()))
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("CORS", test_cors()))
    results.append(("Stats (with auth)", test_stats_endpoint()))
    results.append(("Stats (without auth)", test_stats_without_api_key()))
    results.append(("Initial Verification", test_initial_verification()))
    
    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Service is working correctly.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
