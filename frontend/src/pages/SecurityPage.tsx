/**
 * Security page — documents the security model and safeguards.
 */
export function SecurityPage() {
  return (
    <div className="page security-page">
      <h1>Security</h1>

      <h2>Defense in Depth</h2>
      <p>The system implements 7 layers of security:</p>
      <ol>
        <li><strong>Network:</strong> CORS, rate limiting, request size limits</li>
        <li><strong>API:</strong> Demo mode gate — execute_safe rejected in public mode</li>
        <li><strong>Validation:</strong> Pydantic models, enum validation, whitespace checks</li>
        <li><strong>Policy:</strong> CommandPolicy — allowlist, blocklist, metacharacters, path jail</li>
        <li><strong>Sandbox:</strong> Docker runner container (local development only)</li>
        <li><strong>Data:</strong> All simulator data is synthetic / fictional</li>
        <li><strong>Observability:</strong> Langfuse traces for full audit trail</li>
      </ol>

      <h2>Command Policy</h2>
      <table>
        <thead>
          <tr><th>Layer</th><th>What it does</th></tr>
        </thead>
        <tbody>
          <tr><td>Allowlist</td><td>Only safe read-only commands: cat, head, tail, grep, ls, etc.</td></tr>
          <tr><td>Blocklist</td><td>Explicit deny: rm, curl, sudo, python, bash, etc.</td></tr>
          <tr><td>Metacharacters</td><td>Blocks: ; | &amp; ` $() &gt; &lt; and more</td></tr>
          <tr><td>Path Jail</td><td>All file paths must be within /sim/**</td></tr>
          <tr><td>Traversal</td><td>".." rejected in all paths</td></tr>
        </tbody>
      </table>

      <h2>Public Demo Safety</h2>
      <ul>
        <li>Public demo uses <strong>plan_only</strong> mode — no commands ever execute</li>
        <li>execute_safe requests return <strong>403 Forbidden</strong></li>
        <li>Rate limited to 10 requests/minute per IP</li>
        <li>Request body size limited to 2KB</li>
        <li>All data is synthetic — no real systems are accessed</li>
      </ul>

      <h2>Threat Model</h2>
      <ul>
        <li><strong>Prompt Injection:</strong> Policy validates every command regardless of LLM output</li>
        <li><strong>Tool Misuse:</strong> Public mode blocks execute_safe at API layer</li>
        <li><strong>DoS:</strong> Rate limiting + request size limits</li>
        <li><strong>Data Leakage:</strong> Synthetic data only, no stack traces in responses</li>
      </ul>
    </div>
  );
}
