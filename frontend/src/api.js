const BASE_URL =
  import.meta.env.VITE_API_URL || "https://yanou16-gitgub-rag.hf.space";

export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`, { signal: AbortSignal.timeout(8000) });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function ingestRepo({ repoUrl, branch = "main", forceReingest = false }) {
  const res = await fetch(`${BASE_URL}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_url: repoUrl,
      branch,
      force_reingest: forceReingest,
    }),
    signal: AbortSignal.timeout(300_000), // 5 min — cloning can be slow
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail?.error || data?.detail || `Ingest failed: ${res.status}`);
  return data;
}

export async function queryRepo({
  repoUrl,
  question,
  k = 5,
  useHybrid = true,
  useReranking = true,
  language = null,
  temperature = 0.1,
}) {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      repo_url: repoUrl,
      question,
      k,
      use_hybrid: useHybrid,
      use_reranking: useReranking,
      language: language || null,
      temperature,
    }),
    signal: AbortSignal.timeout(60_000),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.detail?.error || data?.detail || `Query failed: ${res.status}`);
  return data;
}
