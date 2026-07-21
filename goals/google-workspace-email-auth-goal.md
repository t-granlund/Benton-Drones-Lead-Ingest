# Goal: Google Workspace Email Authentication Preservation

## Objective

Ensure DNS changes do not interrupt Benton Drones email.

## Required outcomes

- Preserve Google Workspace MX records exactly as confirmed in Google Admin.
- Preserve or create SPF with Google Workspace included.
- Preserve or create Google DKIM TXT record.
- Add or verify DMARC, preferably monitor mode first.
- Verify inbound and outbound mail after cutover.
- Verify SPF/DKIM/DMARC pass from message headers where applicable.

## Required checks

```txt
MX bentondrones.com
TXT bentondrones.com
TXT google._domainkey.bentondrones.com
TXT _dmarc.bentondrones.com
```

## Non-goals

- Google Admin write automation
- Mailbox migration
- Changing email provider
