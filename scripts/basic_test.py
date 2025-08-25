#!/usr/bin/env python3
"""
Basic comprehensive testing script using only standard library.
Tests all system components without external dependencies.
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Any, Tuple

class BasicTestRunner:
    def __init__(self):
        self.results = []
        self.base_url = "http://localhost:8000"
        self.ui_url = "http://localhost:3000"
        
    def test_api_health(self) -> Tuple[bool, str]:
        """Test API health endpoint."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    if data.get('status') in ['healthy', 'degraded']:
                        return True, f"API healthy: {data}"
                    else:
                        return False, f"Unexpected status: {data}"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def test_ui_accessibility(self) -> Tuple[bool, str]:
        """Test UI is accessible."""
        try:
            with urllib.request.urlopen(f"{self.ui_url}/", timeout=5) as response:
                if response.status == 200:
                    content = response.read().decode()
                    if "<!doctype html" in content.lower():
                        return True, "UI serving HTML content"
                    else:
                        return False, "Not serving HTML"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def test_ui_health(self) -> Tuple[bool, str]:
        """Test UI health endpoint."""
        try:
            with urllib.request.urlopen(f"{self.ui_url}/health", timeout=5) as response:
                if response.status == 200:
                    content = response.read().decode()
                    if "healthy" in content:
                        return True, "UI health check passed"
                    else:
                        return False, f"Unexpected response: {content}"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Health endpoint failed: {str(e)}"
    
    def test_graphrag_intent(self) -> Tuple[bool, str]:
        """Test GraphRAG intent classification."""
        try:
            data = json.dumps({"query": "SPY exposure to technology"}).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/intent/",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode())
                    if 'intent' in result and 'confidence' in result:
                        return True, f"Intent: {result['intent']} (confidence: {result['confidence']})"
                    else:
                        return False, f"Missing intent/confidence: {result}"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Request failed: {str(e)}"
    
    def test_graphrag_ask(self) -> Tuple[bool, str]:
        """Test GraphRAG ask endpoint."""
        try:
            data = json.dumps({"query": "Show me ETFs"}).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/ask/",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode())
                    if 'answer' in result and 'intent' in result:
                        return True, f"Answer: {result['answer'][:100]}..."
                    else:
                        return False, f"Missing answer/intent: {result}"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Request failed: {str(e)}"
    
    def test_api_docs(self) -> Tuple[bool, str]:
        """Test API documentation is accessible."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/docs", timeout=5) as response:
                if response.status == 200:
                    return True, "API docs accessible"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Docs not accessible: {str(e)}"
    
    def test_performance(self) -> Tuple[bool, str]:
        """Test basic performance metrics."""
        try:
            start_time = time.time()
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=5) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200 and response_time < 1000:
                    return True, f"Health check: {response_time:.2f}ms"
                elif response_time >= 1000:
                    return False, f"Slow response: {response_time:.2f}ms"
                else:
                    return False, f"HTTP {response.status}"
        except Exception as e:
            return False, f"Performance test failed: {str(e)}"
    
    def run_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        tests = [
            ("API Health Check", self.test_api_health),
            ("UI Accessibility", self.test_ui_accessibility),  
            ("UI Health Check", self.test_ui_health),
            ("GraphRAG Intent Classification", self.test_graphrag_intent),
            ("GraphRAG Ask Endpoint", self.test_graphrag_ask),
            ("API Documentation", self.test_api_docs),
            ("Basic Performance", self.test_performance),
        ]
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(tests),
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        
        print("🧪 ETF GraphRAG System - Basic Test Suite")
        print("=" * 45)
        print()
        
        for test_name, test_func in tests:
            print(f"Running: {test_name}... ", end="", flush=True)
            
            try:
                start_time = time.time()
                success, message = test_func()
                duration = (time.time() - start_time) * 1000
                
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{status} ({duration:.1f}ms)")
                
                if success:
                    results["passed"] += 1
                    print(f"   → {message}")
                else:
                    results["failed"] += 1
                    print(f"   → ERROR: {message}")
                
                results["tests"].append({
                    "name": test_name,
                    "status": "passed" if success else "failed", 
                    "message": message,
                    "duration_ms": round(duration, 2)
                })
                
            except Exception as e:
                print(f"❌ FAIL ({0:.1f}ms)")
                print(f"   → EXCEPTION: {str(e)}")
                results["failed"] += 1
                results["tests"].append({
                    "name": test_name,
                    "status": "error",
                    "message": str(e),
                    "duration_ms": 0
                })
            
            print()
        
        # Summary
        print("=" * 45)
        print(f"Test Results: {results['passed']}/{results['total_tests']} passed")
        
        if results["failed"] == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {results['failed']} tests failed")
            
        success_rate = (results["passed"] / results["total_tests"]) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        return results

def main():
    """Main test execution."""
    runner = BasicTestRunner()
    results = runner.run_tests()
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: test_results.json")
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    exit(main())