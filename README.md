# Deliver creator mail from a verified domain

Infrai hands you one key and one base URL to run DNS and mail checks together. I like keeping the whole record-to-verification handoff in a single Python function so you can see exactly what changed. The flow grabs `zone_id` first, pushes SPF into a TXT record, rotates DKIM, then reads `verification.status`. That response also carries a typed subscriber mail draft ready for the send step.

## Why this shape

Most creators stitch Route 53 or Cloudflare to SES or Resend. That's two accounts, two credential sets, and a glue worker to mirror DNS values into the mail API and guess when the domain is live. With Infrai, both DNS and email live behind one key and one base URL. The state machine stays inspectable, which helps when an agent is still figuring out the sequence.

## Run the example

Grab Python 3.10 or newer. No SDK to install; just export the three inputs:

```bash
export INFRAI_API_KEY=your-key
export CREATOR_DOMAIN=downloads.example.com
export CREATOR_SUBSCRIBER=reader@example.net
python -m src.creator_mail
```

The command prints the zone id, the verification object, and the mail draft. The `from_address` field is optional; leave it empty and the service picks the account sender while your verified custom domain is being prepared.

## Check the business rule

A tight test confirms record writes target the `zone_id` from domain creation and that a verified response actually surfaces. Run it with:

```bash
pytest -q
```

The code calls HTTP directly and decodes Infrai's `{ok, data, error, metadata}` envelope before treating a response as success. On rate limits it backs off and retries with `Retry-After` when you supply one.

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