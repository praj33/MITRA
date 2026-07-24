#!/usr/bin/env python3
"""
Comprehensive Test Matrix Runner
Runs all 72 tests from edge_test_matrix.json against the canonical validator
"""

import json
import sys
from datetime import datetime
from behavior_validator import validate_behavior

def load_test_matrix():
    """Load test cases from edge_test_matrix.json"""
    try:
        with open('edge_test_matrix.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: edge_test_matrix.json not found")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in edge_test_matrix.json: {e}")
        return None

def map_expected_decision(expected):
    """Map test matrix decisions to validator decisions"""
    mapping = {
        "block": "hard_deny",
        "flag": "soft_rewrite", 
        "pass": "allow"
    }
    return mapping.get(expected, expected)

def run_comprehensive_tests():
    """Run all 72 test cases from the matrix"""
    
    print("COMPREHENSIVE TEST SUITE - 72 TESTS")
    print("=" * 60)
    
    matrix = load_test_matrix()
    if not matrix:
        return False
    
    test_categories = matrix["edge_test_matrix"]["test_categories"]
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Run tests by category
    for category_name, category_data in test_categories.items():
        print(f"\nCATEGORY: {category_name.upper()}")
        print("-" * 40)
        
        tests = category_data.get("tests", [])
        category_passed = 0
        
        print(f"Found {len(tests)} tests in {category_name}")
        
        for test in tests:
            total_tests += 1
            test_id = test["test_id"]
            content = test["content"]
            expected_decision = map_expected_decision(test["expected_decision"])
            
            # Run validation
            result = validate_behavior("auto", content)
            actual_decision = result["decision"]
            
            # Check if test passed
            test_passed = actual_decision == expected_decision
            status = "PASS" if test_passed else "FAIL"
            
            print(f"  {test_id}: {status}")
            print(f"    Content: {content[:50]}...")
            print(f"    Expected: {expected_decision}, Got: {actual_decision}")
            
            if test_passed:
                passed_tests += 1
                category_passed += 1
            else:
                failed_tests.append({
                    "test_id": test_id,
                    "category": category_name,
                    "content": content,
                    "expected": expected_decision,
                    "actual": actual_decision,
                    "trace_id": result["trace_id"]
                })
            
            print(f"    Trace: {result['trace_id']}")
            print()
        
        print(f"Category Result: {category_passed}/{len(tests)} passed")
    
    # Final results
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests:
        print(f"\nFAILED TESTS ({len(failed_tests)}):")
        print("-" * 30)
        for failure in failed_tests:
            print(f"  {failure['test_id']} ({failure['category']})")
            print(f"    Expected: {failure['expected']}, Got: {failure['actual']}")
            print(f"    Content: {failure['content'][:60]}...")
            print()
    
    # Save results
    results = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": len(failed_tests),
        "success_rate": (passed_tests/total_tests)*100,
        "failed_tests": failed_tests
    }
    
    with open('comprehensive_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: comprehensive_test_results.json")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    print("Starting comprehensive test suite...")
    success = run_comprehensive_tests()
    
    if success:
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)