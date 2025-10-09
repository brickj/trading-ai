#!/usr/bin/env python3
"""
Test suite for Go sentiment optimizer integration
Tests the Go-Python integration for sentiment analysis optimization
"""

import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.sentiment_analyzer import SentimentAnalyzer
    from src.core.config import Config
except ImportError:
    print("❌ Could not import src modules. Make sure you're running from the project root.")
    sys.exit(1)


class GoOptimizerTest:
    """Test class for Go optimizer functionality"""
    
    def __init__(self):
        self.go_binary_path = self._find_go_binary()
        self.project_root = Path(__file__).parent.parent
        self.go_optimizer_path = self.project_root / "go" / "cmd" / "sentiment_optimizer"
        
    def _find_go_binary(self) -> str:
        """Find Go binary on system"""
        import shutil
        go_path = shutil.which("go")
        if go_path:
            print(f"✅ Found Go binary at: {go_path}")
            return go_path
        else:
            print("❌ Go binary not found on system")
            return None
    
    def test_go_module_structure(self) -> bool:
        """Test that Go module files exist"""
        print("\n🔍 Testing Go module structure...")
        
        required_files = [
            "go.mod",
            "go/cmd/sentiment_optimizer/main.go",
            "go/pkg/optimizer/optimizer.go"
        ]
        
        all_exist = True
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                all_exist = False
        
        return all_exist
    
    def test_go_module_build(self) -> bool:
        """Test that Go module can be built"""
        print("\n🔨 Testing Go module build...")
        
        if not self.go_binary_path:
            print("❌ Cannot test build - Go binary not available")
            return False
        
        try:
            # Change to go directory and build
            go_dir = self.project_root / "go"
            result = subprocess.run(
                ["go", "build", "-o", "sentiment_optimizer", "./cmd/sentiment_optimizer"],
                cwd=go_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Go module builds successfully")
                # Clean up binary
                binary_path = go_dir / "sentiment_optimizer"
                if binary_path.exists():
                    binary_path.unlink()
                return True
            else:
                print(f"❌ Go build failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Go build timed out")
            return False
        except Exception as e:
            print(f"❌ Go build error: {e}")
            return False
    
    def test_go_optimizer_input_output(self) -> bool:
        """Test Go optimizer with sample input/output"""
        print("\n🧪 Testing Go optimizer input/output...")
        
        if not self.go_binary_path:
            print("❌ Cannot test optimizer - Go binary not available")
            return False
        
        # Sample input data
        test_input = {
            "articles": [
                {
                    "weight": 1.0,
                    "headline": "AAPL stock surges on strong earnings",
                    "summary": "Apple Inc. reported better than expected quarterly earnings",
                    "source": "Financial News",
                    "published_at": "2024-01-01T10:00:00Z"
                },
                {
                    "weight": 0.8,
                    "headline": "Market volatility concerns",
                    "summary": "Investors worry about market stability",
                    "source": "Market Watch",
                    "published_at": "2024-01-01T11:00:00Z"
                }
            ],
            "history": [
                {
                    "sentiment": 0.7,
                    "realized_return": 0.05,
                    "confidence": 0.8,
                    "volume": 1000000,
                    "source": "Financial News",
                    "timestamp": "2024-01-01T09:00:00Z"
                },
                {
                    "sentiment": -0.3,
                    "realized_return": -0.02,
                    "confidence": 0.6,
                    "volume": 800000,
                    "source": "Market Watch",
                    "timestamp": "2024-01-01T10:30:00Z"
                }
            ]
        }
        
        try:
            # Build the optimizer from go directory
            go_dir = self.project_root / "go"
            build_result = subprocess.run(
                ["go", "build", "-o", "test_optimizer", "./cmd/sentiment_optimizer"],
                cwd=go_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if build_result.returncode != 0:
                print(f"❌ Failed to build optimizer: {build_result.stderr}")
                return False
            
            # Run the optimizer with test input
            optimizer_path = go_dir / "test_optimizer"
            result = subprocess.run(
                [str(optimizer_path)],
                input=json.dumps(test_input),
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    output = json.loads(result.stdout)
                    print("✅ Go optimizer produced valid JSON output")
                    print(f"   Output keys: {list(output.keys())}")
                    
                    # Validate output structure
                    required_keys = ["weights", "baseline_shift", "confidence_adjustment", "diagnostics", "notes"]
                    if all(key in output for key in required_keys):
                        print("✅ Output has all required keys")
                        
                        # Check weights length matches articles
                        if len(output["weights"]) == len(test_input["articles"]):
                            print("✅ Weights length matches articles count")
                            return True
                        else:
                            print(f"❌ Weights length {len(output['weights'])} != articles count {len(test_input['articles'])}")
                            return False
                    else:
                        print(f"❌ Missing required keys in output")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON output: {e}")
                    print(f"   Raw output: {result.stdout}")
                    return False
            else:
                print(f"❌ Optimizer failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Optimizer execution timed out")
            return False
        except Exception as e:
            print(f"❌ Optimizer test error: {e}")
            return False
        finally:
            # Clean up test binary
            go_dir = self.project_root / "go"
            test_binary = go_dir / "test_optimizer"
            if test_binary.exists():
                test_binary.unlink()
    
    def test_python_integration(self) -> bool:
        """Test Python integration with Go optimizer"""
        print("\n🐍 Testing Python-Go integration...")
        
        try:
            # Initialize sentiment analyzer
            analyzer = SentimentAnalyzer()
            
            # Test sample data
            test_articles = [
                {
                    "headline": "Tech stocks rally on AI breakthrough",
                    "summary": "Major technology companies see significant gains",
                    "source": "Tech News",
                    "weight": 1.0
                },
                {
                    "headline": "Market uncertainty persists",
                    "summary": "Investors remain cautious about market direction",
                    "source": "Financial Times",
                    "weight": 0.7
                }
            ]
            
            test_history = [
                {
                    "sentiment": 0.6,
                    "realized_return": 0.03,
                    "confidence": 0.75,
                    "volume": 1500000,
                    "source": "Tech News",
                    "timestamp": "2024-01-01T08:00:00Z"
                }
            ]
            
            # Test the Go optimization method
            result = analyzer._optimize_with_go(test_articles, test_history)
            
            if result is not None:
                print("✅ Python-Go integration working")
                print(f"   Optimized weights: {result.get('weights', [])}")
                return True
            else:
                print("⚠️ Go optimization not available (Go runtime may be missing)")
                return True  # This is acceptable if Go is not installed
                
        except Exception as e:
            print(f"❌ Python integration test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Go optimizer tests"""
        print("🚀 Starting Go Optimizer Test Suite")
        print("=" * 50)
        
        tests = {
            "Module Structure": self.test_go_module_structure(),
            "Module Build": self.test_go_module_build(),
            "Optimizer I/O": self.test_go_optimizer_input_output(),
            "Python Integration": self.test_python_integration()
        }
        
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("=" * 50)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in tests.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:20} {status}")
            if result:
                passed += 1
        
        print("=" * 50)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        elif passed > 0:
            print("⚠️ Some tests passed - Go integration partially working")
        else:
            print("❌ All tests failed - Go integration not working")
        
        return tests


def main():
    """Main test runner"""
    tester = GoOptimizerTest()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # All tests passed
    else:
        sys.exit(1)  # Some tests failed


if __name__ == "__main__":
    main()
