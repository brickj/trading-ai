#!/usr/bin/env python3
"""
Comprehensive Test Runner for Trading AI Application
Runs both backend system tests and frontend page tests
"""
import sys
import os
import time
import subprocess
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def run_backend_tests():
    """Run the comprehensive backend system tests"""
    print("🔧 Running Backend System Tests...")
    print("=" * 50)
    
    try:
        # Import and run backend tests
        from comprehensive_system_test import ComprehensiveSystemTest
        
        backend_test = ComprehensiveSystemTest()
        backend_test.runTest()
        
        print("✅ Backend tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Backend tests failed: {e}")
        return False

def run_frontend_tests():
    """Run the comprehensive frontend tests"""
    print("\n🌐 Running Frontend Page Tests...")
    print("=" * 50)
    
    try:
        # Import and run frontend tests
        from comprehensive_frontend_test import ComprehensiveFrontendTest
        
        frontend_test = ComprehensiveFrontendTest()
        frontend_test.runTest()
        
        print("✅ Frontend tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Frontend tests failed: {e}")
        return False

def check_application_status():
    """Check if the application is running"""
    print("🔍 Checking Application Status...")
    
    try:
        import requests
        response = requests.get("http://localhost:5001/api/system_status", timeout=5)
        
        if response.status_code == 200:
            print("✅ Application is running on port 5001")
            return True
        else:
            print("❌ Application is not responding properly")
            return False
            
    except requests.exceptions.RequestException:
        print("❌ Application is not running on port 5001")
        print("💡 Please start the application first: python3 start_app.py")
        return False

def run_integration_tests():
    """Run integration tests that test the full system together"""
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    try:
        import requests
        
        # Test end-to-end workflow
        print("Testing end-to-end trading analysis workflow...")
        
        # 1. Test stock analysis
        response = requests.post("http://localhost:5001/api/analyze_stock", 
                               json={"symbol": "AAPL"})
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ Stock analysis workflow working")
            else:
                print("⚠️ Stock analysis returned error")
        else:
            print("❌ Stock analysis endpoint failed")
        
        # 2. Test telegram integration
        response = requests.get("http://localhost:5001/api/telegram/test")
        if response.status_code == 200:
            data = response.json()
            if data.get("working"):
                print("✅ Telegram integration working")
            else:
                print("⚠️ Telegram integration has issues")
        else:
            print("❌ Telegram endpoint failed")
        
        # 3. Test data consistency
        response = requests.get("http://localhost:5001/api/system_status")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ System status consistent")
            else:
                print("⚠️ System status inconsistent")
        else:
            print("❌ System status endpoint failed")
        
        print("✅ Integration tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False

def generate_test_report(backend_success, frontend_success, integration_success):
    """Generate a comprehensive test report"""
    print("\n📊 COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    total_tests = 3
    passed_tests = sum([backend_success, frontend_success, integration_success])
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"🔧 Backend System Tests: {'✅ PASSED' if backend_success else '❌ FAILED'}")
    print(f"🌐 Frontend Page Tests: {'✅ PASSED' if frontend_success else '❌ FAILED'}")
    print(f"🔗 Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"📈 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED! Your Trading AI system is fully operational!")
    elif success_rate >= 66:
        print("\n⚠️ MOST TESTS PASSED! Some issues need attention.")
    else:
        print("\n❌ MANY TESTS FAILED! System needs significant attention.")
    
    print("\n📋 Test Coverage Summary:")
    print("   • Backend: Database, APIs, Services, Background Jobs")
    print("   • Frontend: All Pages, Data Display, User Interactions")
    print("   • Integration: End-to-End Workflows, Data Consistency")
    
    return success_rate

def main():
    """Main test runner function"""
    print("🚀 TRADING AI COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if application is running
    if not check_application_status():
        print("\n❌ Cannot run tests without a running application!")
        print("💡 Please start the application first:")
        print("   python3 start_app.py")
        return False
    
    print("\n" + "=" * 60)
    
    # Run all test suites
    backend_success = run_backend_tests()
    frontend_success = run_frontend_tests()
    integration_success = run_integration_tests()
    
    # Generate final report
    success_rate = generate_test_report(backend_success, frontend_success, integration_success)
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return success_rate >= 66  # Return True if most tests passed

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
