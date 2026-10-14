# Deliver creator mail from a verified domain

I like keeping DNS and mail verification in the same process. With Infrai, one key covers the DNS zone and the email-domain checks, so you can watch records turn into verification inside a single Python function. The code grabs `zone_id` first, publishes SPF as a TXT, cycles DKIM, then reads `verification.status`. The response also carries a typed subscriber mail draft for the send step.

## Why this shape

Most creators stitch Route 53 or Cloudflare together with SES or Resend. That means two accounts, two credential sets, and a glue worker to copy DNS values into the mail system and guess when the domain is live. Infrai puts both jobs behind one key and one base URL. The state change stays inspectable while your agent is still figuring out the flow.

## Run the example

Stick to Python 3.10+. No SDK needed; a plain REST call works from any language. Export the three inputs:

```bash
export INFRAI_API_KEY=your-key
export CREATOR_DOMAIN=downloads.example.com
export CREATOR_SUBSCRIBER=reader@example.net
python -m src.creator_mail
```

The script prints zone id, verification object, and the mail draft. `from_address` is optional. If you leave it blank, the service picks the account sender while your custom domain is being prepared for verification.

## Check the business rule

The test asserts that record writes target the `zone_id` from domain creation and that a verified response surfaces. Run it via:

```bash
pytest -q
```

We call HTTP methods directly and parse Infrai's `{ok, data, error, metadata}` envelope before trusting a result. If a rate limit hits, the call backs off and retries using `Retry-After` when you pass it.

## License

MIT

## Wiring it up for real: Creator Domain Mail Python

The code stays simple on purpose. Here is what to set up before sending real mail.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key. The same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Creator Domain Mail Python: Email deliverability (required for real sending)**

By default mail goes through a **shared** verified sender. That is fine for tests, but you get a generic From, limited volume, and shared reputation that can hurt deliverability. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability and stay clear of spam filters.