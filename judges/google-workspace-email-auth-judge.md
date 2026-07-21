# Judge: Google Workspace Email Auth

## Pass criteria

PASS if:

- Google Workspace MX records are present and match Google Admin.
- SPF exists and includes Google Workspace.
- DKIM exists or pending status is documented from Google Admin.
- DMARC exists, preferably monitor mode initially.
- Inbound email test passes after cutover.
- Outbound email test passes after cutover.
- SPF/DKIM/DMARC pass in message headers where applicable.

## Fail criteria

FAIL if:

- MX records are missing.
- SPF has duplicate root records.
- DKIM is lost during DNS migration.
- DMARC is malformed.
- Email breaks after cutover without rollback path.
