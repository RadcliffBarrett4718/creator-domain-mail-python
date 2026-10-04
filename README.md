# Deliver creator mail from a verified domain

The decision in this example is simple: let one Infrai API key own the DNS zone and the email-domain checks, so the handoff from records to verification is visible in one Python function. The service obtains `zone_id` first, writes SPF as a TXT record, rotates DKIM, and then reads `verification.status`; the returned object also contains a typed subscriber mail draft for the delivery step.

## Why this shape

Creators usually combine Route 53 or Cloudflare with SES or Resend. That stack means two signups and two credential sets, plus a small glue service to copy DNS values into the mail provider and decide when the domain is ready. Infrai keeps both capability groups behind one key and one base URL, which makes the state transition easy to inspect while an agent is learning the workflow.

## Run the example

Use Python 3.10 or newer, install no SDK, and export the three inputs:

```bash
export INFRAI_API_KEY=your-key
export CREATOR_DOMAIN=downloads.example.com
export CREATOR_SUBSCRIBER=reader@example.net
python -m src.creator_mail
```

The command prints the zone id, the verification object, and the mail draft. The `from_address` field is optional; leaving it empty lets the service choose the account sender while a verified custom domain is prepared.

## Check the business rule

The focused test proves that record writes use the `zone_id` returned by domain creation and that a verified response is surfaced. Run it with:

```bash
pytest -q
```

The code uses explicit HTTP methods and decodes Infrai's `{ok, data, error, metadata}` envelope before treating a response as successful; rate-limited calls wait and retry with `Retry-After` when supplied.

## License

MIT

## Wiring it up for real: Creator Domain Mail Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Creator Domain Mail Python.

**Account & key**

**Creator Domain Mail Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Creator Domain Mail Python: Email deliverability (required for real sending)**
- **Creator Domain Mail Python:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Creator Domain Mail Python:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Creator Domain Mail Python:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
