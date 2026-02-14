/**
 * About page — project overview and architecture.
 */
export function AboutPage() {
  return (
    <div className="page about-page">
      <h1>About</h1>
      <p>
        The <strong>AI-Powered Enterprise Operations Assistant</strong> is an AI-driven operations
        tool for IBM Z / mainframe infrastructure. It uses GPT-4 with a Model Context Protocol
        (MCP) tool layer to plan and execute operations safely.
      </p>

      <h2>Architecture</h2>
      <ul>
        <li><strong>Frontend:</strong> React + Vite + TypeScript</li>
        <li><strong>Backend:</strong> FastAPI + Pydantic v2 + uvicorn</li>
        <li><strong>LLM:</strong> OpenAI GPT-4 (stub for testing)</li>
        <li><strong>Security:</strong> CommandPolicy with allowlist, blocklist, path jail</li>
        <li><strong>Observability:</strong> Langfuse tracing</li>
        <li><strong>Sandbox:</strong> Docker runner container</li>
      </ul>

      <h2>Security Model</h2>
      <p>
        Every command is validated through a multi-layer security policy before execution:
        allowlist check, blocklist check, metacharacter blocking, and path jail enforcement
        (restricted to <code>/sim/**</code>).
      </p>
      <p>
        In the public demo, only <strong>plan_only</strong> mode is available — no commands are
        ever executed on the server.
      </p>
    </div>
  );
}
