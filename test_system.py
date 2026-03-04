#!/usr/bin/env python3
"""
Test script to validate essay reviewer functionality
Run this after setup to ensure everything works
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from orchestrator import EssayReviewer
        from prompts import DIMENSION_PROMPTS, SYNTHESIS_PROMPT
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_prompts():
    """Test that prompt templates are properly formatted"""
    print("\nTesting prompt templates...")
    from prompts import DIMENSION_PROMPTS
    
    required_keys = ['name', 'priority', 'prompt']
    all_valid = True
    
    for dim_key, dim_data in DIMENSION_PROMPTS.items():
        for key in required_keys:
            if key not in dim_data:
                print(f"✗ Missing key '{key}' in dimension '{dim_key}'")
                all_valid = False
        
        # Check prompt has substantive content
        if len(dim_data['prompt']) < 200:
            print(f"✗ Dimension '{dim_key}' prompt seems too short")
            all_valid = False
    
    if all_valid:
        print(f"✓ All {len(DIMENSION_PROMPTS)} dimension prompts valid")
    
    return all_valid


def test_orchestrator():
    """Test orchestrator initialization"""
    print("\nTesting orchestrator...")
    try:
        from orchestrator import EssayReviewer
        
        # Test with dummy API key (won't make actual calls)
        reviewer = EssayReviewer(api_key="test_key")
        
        # Test cost estimation
        estimate = reviewer.estimate_cost(1500, 4)
        
        assert 'cost_gbp' in estimate
        assert 'estimated_input_tokens' in estimate
        assert estimate['cost_gbp'] > 0
        
        print("✓ Orchestrator initialization and cost estimation working")
        return True
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False


def test_sample_essay():
    """Test that sample essay exists and is readable"""
    print("\nTesting sample essay...")
    sample_path = Path(__file__).parent / 'tests' / 'sample_essays' / 'social_media_regulation.txt'
    
    if not sample_path.exists():
        print(f"✗ Sample essay not found at {sample_path}")
        return False
    
    try:
        with open(sample_path, 'r') as f:
            content = f.read()
        
        word_count = len(content.split())
        print(f"✓ Sample essay found ({word_count} words)")
        return True
    except Exception as e:
        print(f"✗ Failed to read sample essay: {e}")
        return False


def test_cli_structure():
    """Test CLI file structure"""
    print("\nTesting CLI structure...")
    cli_path = Path(__file__).parent / 'cli.py'
    
    if not cli_path.exists():
        print("✗ cli.py not found")
        return False
    
    # Check if executable
    import stat
    mode = cli_path.stat().st_mode
    is_executable = bool(mode & stat.S_IXUSR)
    
    if is_executable:
        print("✓ CLI file exists and is executable")
    else:
        print("⚠ CLI file exists but is not executable (run: chmod +x cli.py)")
    
    return True


def main():
    """Run all tests"""
    print("="*60)
    print("Essay Reviewer - System Validation")
    print("="*60)
    
    tests = [
        test_imports,
        test_prompts,
        test_orchestrator,
        test_sample_essay,
        test_cli_structure
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python cli.py setup")
        print("2. Try: python cli.py review tests/sample_essays/social_media_regulation.txt")
    else:
        print("\n⚠️ Some tests failed. Please check errors above.")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
