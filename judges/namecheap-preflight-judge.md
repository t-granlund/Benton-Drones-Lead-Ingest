# Judge: Namecheap Preflight

## Pass criteria

PASS if:

- Current nameservers are captured.
- Current host records are captured.
- Current redirects are captured or confirmed absent.
- Current email/MX settings are captured.
- Rollback instructions are documented.
- No Namecheap changes were made during preflight.

## Fail criteria

FAIL if:

- Nameserver history is unknown.
- DNS state is not captured before Cloudflare cutover.
- Email-related records are assumed absent without verification.
- Any destructive action occurs during preflight.
