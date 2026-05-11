# RAG Prompt Template

```
Here are the most relevant code chunks from the repository (ordered by relevance):

{chunks_formatted}

---

Question: {question}

Answer based only on the code above. Cite file paths and line numbers when relevant.
```

## Chunk format

Each chunk is presented as:

```
[Chunk N] path/to/file.py (lines START-END) [similarity: 0.87]
```python
<code content>
```
```

The LLM must reference chunks by file path and line range, never by chunk number alone.
