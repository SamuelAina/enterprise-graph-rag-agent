# AI Governance Notes

- Data minimisation: retrieval truncates context to MAX_CONTEXT_CHARS
- Redaction: basic sensitive keyword redaction (placeholder for real DLP)
- Audit: trace events capture routing and retrieval decisions
- Upgrade path:
  - PII detection
  - policy-based access control per document classification
  - signed prompts, prompt versioning, approval workflow
