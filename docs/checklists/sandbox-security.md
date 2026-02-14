
# Sandbox Security Checklist

Runner container must enforce:
- [ ] non-root user
- [ ] read-only filesystem
- [ ] no network (`network_mode: none`)
- [ ] resource limits (CPU/mem/pids)
- [ ] dropped capabilities (`cap_drop: ALL`)
- [ ] `no-new-privileges:true`
- [ ] allowlist + arg validation still enforced in code
