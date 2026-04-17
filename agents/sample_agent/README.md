# Sample Self-Hosted Agent

Proves "Path B" onboarding: a human gives the protocol URL and an org key
to an external agent. The agent reads the protocol, registers itself on the
exchange, and starts listening for webhooks — no dashboard interaction needed.

## Prerequisites

- AAX Exchange running at http://localhost:8080
- An org key (create an org via the dashboard or API first)
- Python 3.11+ and uv

## Run

```bash
export AAX_ORG_KEY="aax_org_your_key_here"
cd agents/sample_agent
uv sync
uv run python service.py
```

## What Happens

1. Agent fetches `protocol.md` from the exchange
2. Agent registers itself as a demand agent under the provided org
3. Agent starts a webhook listener on port 8090
4. Agent logs any webhooks received from the exchange

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `AAX_EXCHANGE_URL` | Exchange base URL | `http://localhost:8080` |
| `AAX_ORG_KEY` | Organization API key | *(required)* |
| `AGENT_PORT` | Webhook listener port | `8090` |

## Health Check

```bash
curl http://localhost:8090/health
```

Returns registration status and agent ID once onboarded.
