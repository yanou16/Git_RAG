import ast
import re
from dataclasses import dataclass
from app.config import get_settings

settings = get_settings()


@dataclass
class Chunk:
    text: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str  # "function" | "class" | "window" | "section"


def chunk_file(content: str, file_path: str, language: str) -> list[Chunk]:
    if not content or len(content.strip()) < settings.MIN_CHUNK_SIZE_CHARS:
        return []

    if language == "python":
        return chunk_python(content, file_path)
    elif language == "markdown":
        return chunk_markdown(content, file_path)
    else:
        return chunk_sliding_window(content, file_path, language)


def chunk_python(content: str, file_path: str) -> list[Chunk]:
    chunks = []
    try:
        tree = ast.parse(content)
        lines = content.split("\n")

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue

            start = node.lineno - 1
            end = node.end_lineno

            chunk_text = "\n".join(lines[start:end])

            if len(chunk_text.strip()) < settings.MIN_CHUNK_SIZE_CHARS:
                continue

            if len(chunk_text) > 2000:
                chunk_text = chunk_text[:2000] + "\n# ... [truncated]"

            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append(Chunk(
                text=f"# File: {file_path}\n{chunk_text}",
                file_path=file_path,
                language="python",
                start_line=node.lineno,
                end_line=node.end_lineno,
                chunk_type=chunk_type
            ))

    except SyntaxError:
        return chunk_sliding_window(content, file_path, "python")

    if not chunks:
        return chunk_sliding_window(content, file_path, "python")

    return chunks


def chunk_markdown(content: str, file_path: str) -> list[Chunk]:
    chunks = []
    sections = re.split(r'\n(?=#{1,3} )', content)
    current_line = 1

    for section in sections:
        section = section.strip()
        if len(section) < settings.MIN_CHUNK_SIZE_CHARS:
            current_line += section.count("\n") + 1
            continue

        if len(section) > 2000:
            section = section[:2000] + "\n... [truncated]"

        end_line = current_line + section.count("\n")
        chunks.append(Chunk(
            text=f"# File: {file_path}\n{section}",
            file_path=file_path,
            language="markdown",
            start_line=current_line,
            end_line=end_line,
            chunk_type="section"
        ))
        current_line = end_line + 1

    return chunks


def chunk_sliding_window(
    content: str,
    file_path: str,
    language: str,
    chunk_size: int = 512,
    overlap: int = 64
) -> list[Chunk]:
    chunks = []
    char_chunk = chunk_size * 4
    char_overlap = overlap * 4

    start = 0
    chunk_idx = 0

    while start < len(content):
        end = min(start + char_chunk, len(content))
        chunk_text = content[start:end]

        if len(chunk_text.strip()) >= settings.MIN_CHUNK_SIZE_CHARS:
            chars_before = content[:start]
            start_line = chars_before.count("\n") + 1
            end_line = start_line + chunk_text.count("\n")

            chunks.append(Chunk(
                text=f"# File: {file_path}\n{chunk_text}",
                file_path=file_path,
                language=language,
                start_line=start_line,
                end_line=end_line,
                chunk_type="window"
            ))

        start = end - char_overlap
        chunk_idx += 1

        if chunk_idx >= settings.MAX_CHUNKS_PER_FILE:
            break

    return chunks
