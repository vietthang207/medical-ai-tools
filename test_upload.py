#!/usr/bin/env python3
"""
Test script to verify DICOM viewer functionality
"""

import requests
import os
import sys

def test_server_running(base_url="http://localhost:5000"):
    """Test if server is running"""
    print("🔍 Testing server connection...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("\nMake sure the server is running:")
        print("  python app.py")
        return False

def test_upload(zip_file_path, base_url="http://localhost:5000"):
    """Test file upload functionality"""
    if not os.path.exists(zip_file_path):
        print(f"❌ File not found: {zip_file_path}")
        return False
    
    print(f"\n📤 Testing upload with: {zip_file_path}")
    
    try:
        with open(zip_file_path, 'rb') as f:
            files = {'file': (os.path.basename(zip_file_path), f, 'application/zip')}
            response = requests.post(f"{base_url}/upload", files=files, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Upload successful!")
                print(f"\n📋 Metadata:")
                metadata = data.get('metadata', {})
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
                
                # Test slice retrieval
                session_id = data.get('session_id')
                print(f"\n🔍 Testing slice retrieval...")
                slice_response = requests.get(f"{base_url}/slice/{session_id}/0")
                if slice_response.status_code == 200:
                    print("✅ Slice retrieval works!")
                else:
                    print(f"❌ Slice retrieval failed: {slice_response.status_code}")
                
                # Test multiplanar views
                print(f"\n🔍 Testing multiplanar views...")
                views_response = requests.get(f"{base_url}/views/{session_id}")
                if views_response.status_code == 200:
                    print("✅ Multiplanar views work!")
                else:
                    print(f"❌ Multiplanar views failed: {views_response.status_code}")
                
                return True
            else:
                print(f"❌ Upload failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Upload failed with status code: {response.status_code}")
            try:
                print(f"   Error: {response.json().get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🏥 DICOM Viewer Test Script")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test server
    if not test_server_running(base_url):
        sys.exit(1)
    
    # Test upload if file provided
    if len(sys.argv) > 1:
        zip_file = sys.argv[1]
        if test_upload(zip_file, base_url):
            print("\n✅ All tests passed!")
            print(f"\n🌐 Open your browser: {base_url}")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    else:
        print("\n✅ Server test passed!")
        print(f"\n🌐 Open your browser: {base_url}")
        print("\nTo test upload, run:")
        print("  python test_upload.py /path/to/dicom.zip")

if __name__ == "__main__":
    main()

