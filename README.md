# Bluejay Docs

[![Mintlify](https://img.shields.io/badge/docs-Mintlify-brightgreen)](https://mintlify.com)
[![Platform](https://img.shields.io/badge/platform-getbluejay.ai-blue)](https://app.getbluejay.ai)

Official documentation for **Bluejay** — an end-to-end testing and observability platform for AI voice agents.

---

## What is Bluejay?

Bluejay helps teams build reliable AI voice agents by providing two core capabilities:

- **Simulations** — Test your voice agents with realistic customer interactions powered by AI-driven "Digital Humans". Run automated, repeatable scenarios before deploying to production.
- **Observability** — Monitor and evaluate your production calls at scale. Get actionable insights, anomaly detection, and detailed analytics on every real-world interaction.

Whether you're a developer building voice agents, a QA engineer creating test scenarios, or an ops team monitoring live performance, Bluejay gives you full visibility across the entire agent lifecycle.

---

## Documentation Sections

### Get Started
- **[Introduction](./index.mdx)** — Overview of the Bluejay platform
- **[Quickstart](./quickstart.mdx)** — Connect your first voice agent and run a simulation

### Core Concepts
| Concept | Description |
|---|---|
| [Agents](./core-concepts/agents.mdx) | Entities representing the voice agents you test and monitor |
| [Digital Humans](./core-concepts/digital-humans.mdx) | AI-powered virtual customers that simulate realistic conversations |
| [Communities](./core-concepts/communities.mdx) | Groups of Digital Humans for organizing test personas |
| [Simulations](./core-concepts/simulations.mdx) | Structured test scenarios run against your agents |
| [Simulation Runs](./core-concepts/simulation-runs.mdx) | Individual execution results with detailed metrics |
| [Observability](./core-concepts/observability.mdx) | Production call monitoring and evaluation |
| [Tool Calls](./core-concepts/tool-calls.mdx) | Track API and database calls made during agent interactions |
| [Traces](./core-concepts/traces.mdx) | Deep call tracing and analysis |
| [Webhooks](./core-concepts/webhook.mdx) | Real-time event notifications |

### Simulation Integrations
Connect Bluejay to your existing voice infrastructure:
- **Telephony / SIP** — Phone-based testing via PSTN or SIP
- **LiveKit** — Video/audio real-time communication
- **WebSockets** — Custom real-time bidirectional protocols
- **HTTP Webhooks** — Flexible webhook-based integration
- **Pipecat** — Open-source voice AI infrastructure
- **Miro** — Collaborative whiteboarding for visual workflows

### Observability Integrations
Monitor production calls from your existing providers:
- **Retell AI**, **VAPI**, **Bland AI**, **ElevenLabs**

### Cookbook
Practical how-to guides:
- [Observability](./cookbook/observability.mdx) — Evaluate calls programmatically via the Skywatch API
- [Workflows](./cookbook/workflows.mdx) — Automate and orchestrate simulation workflows
- [GitHub Actions](./cookbook/github-actions.mdx) — Integrate Bluejay into your CI/CD pipeline

### API Reference
Bluejay exposes two REST APIs with full OpenAPI specs:
- **Mimic** — Simulation API (agents, digital humans, simulations, runs, and more)
- **Skywatch** — Observability API (production call monitoring, custom metrics, labeling)

Comprehensive endpoint coverage across multiple resource groups, plus webhook event documentation.

---

## Local Development

This documentation site is built with [Mintlify](https://mintlify.com). To run it locally:

```bash
# Install the Mintlify CLI (requires Node.js v19+)
npm i -g mintlify

# Start the local dev server (available at http://localhost:3000)
mintlify dev

# Check for broken links
mintlify broken-links
```

Changes committed to the `main` branch are automatically deployed via the Mintlify GitHub App.

---

## Contributing

1. Fork or branch from `main`
2. Edit or add `.mdx` files in the relevant section
3. Test locally with `mintlify dev`
4. Open a pull request — the Mintlify preview will be generated automatically

For API reference changes, update `api-reference/openapi.json` (OpenAPI 3.1 format).

---

## Links

- **Platform**: [app.getbluejay.ai](https://app.getbluejay.ai)
- **Twitter/X**: [@getbluejay](https://x.com/getbluejay)
- **LinkedIn**: [Bluejay on LinkedIn](https://linkedin.com/company/getbluejay)
