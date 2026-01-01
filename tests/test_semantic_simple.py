"""Simple test for semantic chunking system"""

from utils.knowledge.semantic_extractor import PythonASTExtractor

# Test code
test_code = """
import os
import sys

def function_one():
    '''First function'''
    return 'one'

def function_two():
    '''Second function'''
    return 'two'

class MyClass:
    '''Test class'''
    def method_one(self):
        return 1

    def method_two(self):
        return 2
"""


def test_ast_extraction():
    """Test AST extraction"""
    extractor = PythonASTExtractor()
    structure = extractor.extract(test_code, "test.py")

    print(f"Functions found: {len(structure.functions)}")
    for func in structure.functions:
        print(f"  - {func['name']}: lines {func['start']}-{func['end']}")

    print(f"Classes found: {len(structure.classes)}")
    for cls in structure.classes:
        print(f"  - {cls['name']}: lines {cls['start']}-{cls['end']}")
        print(f"    Methods: {cls['methods']}")

    assert len(structure.functions) >= 2, "Should find at least 2 functions"
    assert len(structure.classes) >= 1, "Should find at least 1 class"
    print("\n✓ AST extraction test passed!")


if __name__ == "__main__":
    test_ast_extraction()
