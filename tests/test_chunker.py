from app.services.chunker import chunk_python, chunk_markdown, chunk_sliding_window


def test_chunk_python_simple_function():
    code = '''
def hello(name: str) -> str:
    """Return greeting."""
    return f"Hello, {name}"
'''
    chunks = chunk_python(code, "test.py")
    assert len(chunks) >= 1
    assert "hello" in chunks[0].text
    assert chunks[0].language == "python"
    assert chunks[0].chunk_type == "function"


def test_chunk_python_invalid_syntax_fallback():
    code = "def broken(: invalid syntax"
    chunks = chunk_python(code, "test.py")
    assert isinstance(chunks, list)


def test_chunk_markdown_by_heading():
    md = """# Title
Intro text here that is long enough

## Section 1
Content 1 with enough text to pass the minimum size filter

## Section 2
Content 2 with enough text to pass the minimum size filter"""
    chunks = chunk_markdown(md, "README.md")
    assert len(chunks) >= 2


def test_chunk_sliding_window_respects_size():
    content = "x " * 1000  # 2000 chars
    chunks = chunk_sliding_window(content, "test.ts", "typescript")
    assert len(chunks) >= 1
    for chunk in chunks:
        assert len(chunk.text) <= 2200
