"""Test semantic chunking for multiple file formats"""

from utils.knowledge.json_extractor import JSONExtractor
from utils.knowledge.markdown_extractor import MarkdownExtractor


def test_markdown_extraction():
    """Test Markdown header extraction"""
    md_content = """# Main Title

Some intro text.

## Section 1

Content for section 1.

### Subsection 1.1

More content.

## Section 2

```python
def example():
    return "code"
```

Final content.
"""

    extractor = MarkdownExtractor()
    structure = extractor.extract(md_content, "test.md")

    print(f"Headers found: {len(structure.headers)}")
    for header in structure.headers:
        print(f"  Level {header['level']}: {header['text']} (line {header['line']})")

    print(f"\nCode blocks found: {len(structure.code_blocks)}")
    for block in structure.code_blocks:
        print(f"  {block['language']}: lines {block['start']}-{block['end']}")

    # Test chunking
    chunks = extractor.chunk_by_sections(md_content, structure, target_size=200)
    print(f"\nChunks created: {len(chunks)}")

    assert len(structure.headers) == 4, f"Expected 4 headers, got {len(structure.headers)}"
    assert len(structure.code_blocks) == 1, (
        f"Expected 1 code block, got {len(structure.code_blocks)}"
    )
    print("✓ Markdown extraction test passed!")


def test_json_extraction():
    """Test JSON structure extraction"""
    json_content = """
{
  "name": "test",
  "version": "1.0.0",
  "dependencies": {
    "package1": "1.0.0",
    "package2": "2.0.0"
  },
  "scripts": {
    "test": "pytest",
    "build": "ruff check"
  }
}
"""

    extractor = JSONExtractor()
    structure = extractor.extract(json_content, "test.json")

    print(f"\nTop-level keys: {structure.top_level_keys}")
    print(f"Is array: {structure.is_array}")
    print(f"Total items: {structure.total_items}")

    # Test chunking
    chunks = extractor.chunk_by_keys(json_content, structure, target_size=100)
    print(f"\nChunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i} size: {len(chunk)} chars")

    assert not structure.is_array, "Should not be an array"
    assert len(structure.top_level_keys) == 4, (
        f"Expected 4 keys, got {len(structure.top_level_keys)}"
    )
    print("✓ JSON extraction test passed!")


def test_empty_file_handling():
    """Test that empty/small files are handled gracefully"""
    from utils.knowledge.semantic_chunker import SemanticChunker

    chunker = SemanticChunker()

    # Empty file
    chunks = chunker.chunk("", "empty.py")
    assert chunks == [], f"Expected empty list, got {chunks}"

    # Very small file
    chunks = chunker.chunk("# Just a comment", "tiny.py")
    assert len(chunks) <= 1, f"Small file should produce 0-1 chunks, got {len(chunks)}"

    print("✓ Empty file handling test passed!")


if __name__ == "__main__":
    test_markdown_extraction()
    test_json_extraction()
    test_empty_file_handling()
    print("\n✅ All multi-format chunking tests passed!")
