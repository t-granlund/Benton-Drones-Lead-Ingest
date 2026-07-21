# Benton Drones Lead-Ingest Judges

This directory defines acceptance criteria for each project goal.

A judge returns one of:

```txt
PASS
FAIL
BLOCKED
DEFERRED
```

Each judge should record:

- what was inspected
- commands run
- evidence collected
- passing criteria
- failing criteria
- remaining gaps
- recommended next action

## Judge files

| Judge | File |
|---|---|
| Local MVP | `local-mvp-judge.md` |
| Domains/DNS/Cloudflare | `domain-dns-cloudflare-judge.md` |
| Namecheap preflight | `namecheap-preflight-judge.md` |
| Google Workspace email auth | `google-workspace-email-auth-judge.md` |
| Shopify landing page | `shopify-landing-page-judge.md` |
| Future Shopify App Proxy | `shopify-app-proxy-future-judge.md` |
| Backend deployment | `backend-deployment-judge.md` |
| Design system capture | `design-system-capture-judge.md` |
| Production hardening | `production-hardening-judge.md` |
| Browser QA | `browser-qa-judge.md` |
| Read-only preflight scripts | `readonly-preflight-scripts-judge.md` |
| BDS/Dolt-style tracking | `bds-dolt-tracking-judge.md` |

## Evidence rule

A PASS without evidence is just optimism wearing a fake mustache. Link every PASS to commands, screenshots, exports, or docs.
