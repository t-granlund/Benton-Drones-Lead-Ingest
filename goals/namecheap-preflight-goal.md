# Goal: Namecheap Preflight and Rollback Capture

## Objective

Capture the existing Namecheap registrar/DNS state before any Cloudflare nameserver cutover.

## Required outcomes

- Screenshot/export current nameservers.
- Screenshot/export all DNS host records.
- Capture A, CNAME, MX, TXT, SPF, DKIM, and DMARC records when present.
- Capture URL redirects and email-specific Namecheap settings.
- Document rollback notes without committing secrets.

## Non-goals

- Changing nameservers before Cloudflare is fully prepared
- Deleting records
- Editing MX records
- Automating cutover without explicit approval
