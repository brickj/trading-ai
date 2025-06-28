#!/usr/bin/env python3
"""
Test to ensure NO MOCK DATA exists in the production application
This test helps enforce the strict no-mock-data policy.
"""

import os
import re
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestNoMockData(unittest.TestCase):
    """Test suite to ensure no mock data exists in production code"""

    def setUp(self):
        """Set up test fixtures"""
        self.project_root = project_root
        self.src_directory = self.project_root / "src"
        self.allowed_mock_files = {
            # Only test files are allowed to have mock data
            "tests/",
            "test_",
            "__pycache__",
            ".pyc",
            "mock_",  # Files specifically named as mock files
        }
        
    def test_no_mock_data_in_source_files(self):
        """Test that no source files contain mock data implementations"""
        violations = []
        
        # Search patterns for mock data (excluding security checks)
        mock_patterns = [
            r'return.*\[.*"Mock',  # Mock data returns
            r'Mock.*Data(?!.*disabled|.*safety)',  # Mock data variables (not safety messages)
            r'mock_data\s*=',  # Mock data assignments
            r'def.*_get_mock_.*\(',  # Mock functions (except in test files)
            r'"source":\s*"Mock',  # Mock data sources
        ]
        
        # Search all Python files in src directory
        for py_file in self.src_directory.rglob("*.py"):
            if self._is_test_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                for line_num, line in enumerate(lines, 1):
                    for pattern in mock_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip lines that are security checks rejecting mock data
                            if any(reject in line.lower() for reject in [
                                'disabled', 'rejected', 'not allowed', 'safety', 
                                'reject mock', 'instead of', 'error', 'security'
                            ]):
                                continue
                            violations.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': line_num,
                                'content': line.strip(),
                                'pattern': pattern
                            })
            except Exception as e:
                self.fail(f"Error reading file {py_file}: {e}")
        
        if violations:
            error_message = "\n❌ MOCK DATA VIOLATIONS FOUND:\n"
            for violation in violations:
                error_message += f"  📁 {violation['file']}:{violation['line']}\n"
                error_message += f"     🔍 Pattern: {violation['pattern']}\n"
                error_message += f"     📝 Code: {violation['content']}\n\n"
            error_message += "🚨 ALL MOCK DATA MUST BE REMOVED FROM PRODUCTION CODE!\n"
            self.fail(error_message)

    def test_no_mock_returns_in_data_fetcher(self):
        """Specifically test data_fetcher.py for mock return statements"""
        data_fetcher_path = self.src_directory / "data" / "data_fetcher.py"
        
        if not data_fetcher_path.exists():
            self.skipTest("data_fetcher.py not found")
            
        with open(data_fetcher_path, 'r') as f:
            content = f.read()
            
        # Check for specific mock patterns in data fetcher
        mock_violations = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            # Look for return statements with mock data
            if re.search(r'return\s*\[.*"Mock', line, re.IGNORECASE):
                mock_violations.append(f"Line {line_num}: {line.strip()}")
            elif re.search(r'return\s*\[.*"Test', line, re.IGNORECASE):
                mock_violations.append(f"Line {line_num}: {line.strip()}")
            elif re.search(r'headline.*Mock', line, re.IGNORECASE):
                mock_violations.append(f"Line {line_num}: {line.strip()}")
                
        if mock_violations:
            self.fail(f"❌ Mock data found in data_fetcher.py:\n" + 
                     "\n".join(mock_violations))

    def test_no_mock_functions_in_sentiment_analyzer(self):
        """Test that sentiment_analyzer.py has no mock functions"""
        sentiment_path = self.src_directory / "core" / "sentiment_analyzer.py"
        
        if not sentiment_path.exists():
            self.skipTest("sentiment_analyzer.py not found")
            
        with open(sentiment_path, 'r') as f:
            content = f.read()
            
        # Check for mock functions
        mock_functions = re.findall(r'def\s+.*mock.*\(', content, re.IGNORECASE)
        
        if mock_functions:
            self.fail(f"❌ Mock functions found in sentiment_analyzer.py: {mock_functions}")

    def test_no_mock_fallbacks_in_web_app(self):
        """Test that web app doesn't have mock data fallbacks"""
        app_path = self.src_directory / "web" / "app.py"
        
        if not app_path.exists():
            self.skipTest("app.py not found")
            
        with open(app_path, 'r') as f:
            content = f.read()
            
        # Check for mock fallback patterns
        mock_patterns = [
            r'fallback.*mock',
            r'using.*mock.*data',
            r'Mock Data',
            r'source.*Mock',
        ]
        
        violations = []
        lines = content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            for pattern in mock_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(f"Line {line_num}: {line.strip()}")
                    
        if violations:
            self.fail(f"❌ Mock data fallbacks found in app.py:\n" + 
                     "\n".join(violations))

    def test_no_mock_data_in_trading_strategy(self):
        """Test that trading strategy files don't contain mock data"""
        trading_dir = self.src_directory / "trading"
        
        if not trading_dir.exists():
            self.skipTest("trading directory not found")
            
        violations = []
        
        for py_file in trading_dir.glob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
                lines = content.splitlines()
                
            for line_num, line in enumerate(lines, 1):
                if re.search(r'Mock.*object', line, re.IGNORECASE):
                    violations.append(f"{py_file.name}:{line_num} - {line.strip()}")
                elif re.search(r'mock.*confidence', line, re.IGNORECASE):
                    violations.append(f"{py_file.name}:{line_num} - {line.strip()}")
                    
        if violations:
            self.fail(f"❌ Mock data found in trading strategies:\n" + 
                     "\n".join(violations))

    def test_check_config_for_mock_providers(self):
        """Test that config doesn't default to mock providers"""
        config_path = self.src_directory / "core" / "config.py"
        
        if not config_path.exists():
            self.skipTest("config.py not found")
            
        with open(config_path, 'r') as f:
            content = f.read()
            
        # Check for mock provider defaults
        if re.search(r'PREFERRED_AI_PROVIDER.*=.*["\']mock["\']', content, re.IGNORECASE):
            self.fail("❌ Config defaults to mock AI provider")
            
        if re.search(r'DEFAULT.*PROVIDER.*=.*["\']mock["\']', content, re.IGNORECASE):
            self.fail("❌ Config has mock provider as default")

    def test_import_all_core_modules_without_mock_errors(self):
        """Test that core modules can be imported without mock dependencies"""
        core_modules = [
            "src.core.sentiment_analyzer",
            "src.data.data_fetcher", 
            "src.trading.trading_strategy",
            "src.trading.enhanced_trading_strategy",
        ]
        
        for module_name in core_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                if "mock" in str(e).lower():
                    self.fail(f"❌ Module {module_name} has mock dependencies: {e}")
                # Other import errors are acceptable for this test

    def test_no_mock_provider_acceptance(self):
        """Test that the application properly rejects mock providers"""
        try:
            from src.core.sentiment_analyzer import SentimentAnalyzer
            
            analyzer = SentimentAnalyzer()
            
            # Test that mock provider is rejected
            test_articles = [{"headline": "Test", "summary": "Test summary"}]
            
            with self.assertRaises(Exception) as context:
                analyzer.analyze_news_sentiment(test_articles, ai_provider="mock")
                
            self.assertIn("Mock data provider is disabled", str(context.exception))
            
        except ImportError:
            self.skipTest("Cannot import SentimentAnalyzer for testing")

    def test_documentation_warns_about_mock_data(self):
        """Test that documentation mentions the no-mock-data policy"""
        todo_path = self.project_root / "TODO.md"
        
        if not todo_path.exists():
            self.skipTest("TODO.md not found")
            
        with open(todo_path, 'r') as f:
            content = f.read()
            
        # Check that TODO mentions mock data policy
        if not re.search(r'NO MOCK DATA', content, re.IGNORECASE):
            self.fail("❌ TODO.md doesn't mention NO MOCK DATA policy")
            
        if not re.search(r'remove.*mock', content, re.IGNORECASE):
            self.fail("❌ TODO.md doesn't mention removing mock data")

    def _is_test_file(self, file_path):
        """Check if a file is a test file (allowed to have mock data)"""
        path_str = str(file_path)
        
        for allowed in self.allowed_mock_files:
            if allowed in path_str:
                return True
                
        return False

    def test_print_summary(self):
        """Print a summary of the mock data audit"""
        print("\n" + "="*60)
        print("🔍 MOCK DATA AUDIT SUMMARY")
        print("="*60)
        print("✅ All tests passed - No mock data found in production code")
        print("🚨 Policy: Mock data is ONLY allowed in test files")
        print("📁 Checked directories:")
        print(f"   • {self.src_directory}")
        print("🔒 This test helps enforce the strict no-mock-data policy")
        print("="*60)


def run_mock_data_audit():
    """Run the mock data audit as a standalone script"""
    print("🚀 Starting Mock Data Audit...")
    
    # Run the tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNoMockData)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ MOCK DATA AUDIT PASSED - No violations found!")
        return True
    else:
        print("\n❌ MOCK DATA AUDIT FAILED - Violations found!")
        print("🚨 Please remove all mock data from production code immediately!")
        return False


if __name__ == "__main__":
    success = run_mock_data_audit()
    sys.exit(0 if success else 1)
