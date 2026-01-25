"""
Test script for authentication system
Run this after starting the backend server: uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_register():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    
    payload = {
        "email": "test@moreach.ai",
        "password": "testpassword123",
        "full_name": "Test User",
        "company": "Moreach",
        "job_title": "Product Manager",
        "industry": "SaaS",
        "usage_type": "Personal Use"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Registration successful!")
        print(f"   User ID: {data['user']['id']}")
        print(f"   Email: {data['user']['email']}")
        print(f"   Name: {data['user']['full_name']}")
        print(f"   Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Error: {response.json()}")
        return None

def test_login():
    """Test user login"""
    print("\n=== Testing Login ===")
    
    payload = {
        "email": "test@moreach.ai",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"   User ID: {data['user']['id']}")
        print(f"   Email: {data['user']['email']}")
        print(f"   Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Error: {response.json()}")
        return None

def test_get_me(token):
    """Test getting current user"""
    print("\n=== Testing Get Current User ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Get current user successful!")
        print(f"   User ID: {data['id']}")
        print(f"   Email: {data['email']}")
        print(f"   Name: {data['full_name']}")
        print(f"   Company: {data['company']}")
        print(f"   Industry: {data['industry']}")
        print(f"   Usage Type: {data['usage_type']}")
        return True
    else:
        print(f"❌ Get current user failed: {response.status_code}")
        print(f"   Error: {response.json()}")
        return False

def test_invalid_login():
    """Test login with invalid credentials"""
    print("\n=== Testing Invalid Login ===")
    
    payload = {
        "email": "test@moreach.ai",
        "password": "wrongpassword"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    
    if response.status_code == 401:
        print("✅ Invalid login correctly rejected!")
        print(f"   Error: {response.json()['detail']}")
        return True
    else:
        print(f"❌ Invalid login should have been rejected!")
        return False

def main():
    print("=" * 60)
    print("Testing Moreach Authentication System")
    print("=" * 60)
    print("\nMake sure the backend server is running:")
    print("  cd backend && uvicorn app.main:app --reload")
    print("\nAnd that you've run the migration:")
    print("  cd backend && python scripts/migrate_add_users.py")
    
    try:
        # Test registration
        token = test_register()
        
        if token:
            # Test getting current user with token
            test_get_me(token)
        
        # Test login
        token = test_login()
        
        if token:
            # Test getting current user again
            test_get_me(token)
        
        # Test invalid login
        test_invalid_login()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend server")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

