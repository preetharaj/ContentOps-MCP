# ContentOps MCP Server Registry

`registry.contentops.dev` is a curated MCP server registry for content operations stacks. The prototype is intentionally simple: a static registry UI plus a machine-readable `servers.json` catalog that agents, local CLIs, and the ContentOps orchestrator can consume.

## Scope

This registry focuses on content-stack integrations only:

- CMS and publishing: Ghost, WordPress, Webflow, Substack via scrape
- Newsletter and email: Beehiiv, Resend, Loops, Mailchimp
- Editorial operations: Linear, Notion, Coda
- Workflow quality: `qa_gate::run_check`

The goal is not to list every MCP server on the internet. The goal is to own a reliable content-vertical namespace where servers are tested, versioned, and documented for draft-to-publish workflows.

## Curation rules

A server is listed only when it includes:

1. A stable MCP-compatible tool surface.
2. Clear authentication requirements.
3. Versioned compatibility notes.
4. A documented install extra such as `contentops-mcp[ghost]`.
5. A basic health-check or fallback behavior.
6. Tool names that map to content workflows, not generic SaaS automation only.

Servers are grouped by maintenance tier:

- `core`: free and open-source registry entries maintained by the ContentOps project.
- `community`: free entries that may depend on community-maintained adapters.
- `premium`: optional paid add-ons such as Salesforce CRM sync and HubSpot tagging.

## Install examples

Install only the Ghost adapter:

```bash
pip install contentops-mcp[ghost]
```

Install WordPress and Resend support:

```bash
pip install contentops-mcp[wordpress,resend]
```

Install the common content stack:

```bash
pip install contentops-mcp[cms,email,collab]
```

Install everything published by the OSS registry:

```bash
pip install contentops-mcp[all]
```

## Example usage

Use the registry from Python:

```python
import json
from pathlib import Path

catalog = json.loads(Path("registry/servers.json").read_text())
wordpress = next(server for server in catalog["servers"] if server["id"] == "wordpress")

print(wordpress["name"])
print(wordpress["tools"])
```

Use a registered server in a workflow:

```yaml
workflow: draft-to-publish-with-qa
trigger:
  server: notion-mcp
  tool: get_pages
  params:
    database_id: $NOTION_EDITORIAL_DB
steps:
  - server: wordpress-mcp
    tool: create_draft
    input_map:
      title: "{trigger.pages[0].title}"
      content: "{trigger.pages[0].body}"
  - server: qa-gate
    tool: run_check
    input_map:
      title: "{trigger.pages[0].title}"
      content: "{trigger.pages[0].body}"
      meta_description: "A practical guide for content teams adopting MCP-native workflows."
      target_audience: "technical content operators and product engineers"
      brand_rubric: "Clear, practical, non-hype, specific examples, no vague AI claims."
      mode: "manual_approval"
  - server: wordpress-mcp
    tool: publish_post
    input_map:
      post_id: "{steps[0].post_id}"
      qa_passed: "{steps[1].passed}"
```

## Static prototype

The static UI lives at:

```text
registry/index.html
```

When the FastAPI app is running, open:

```text
http://localhost:8000/registry
```

The UI reads `registry/servers.json`, lists each server, and lets you filter by category.

## Monetization boundary

The registry catalog, schema, static UI, and core content-stack server entries remain free and OSS. Premium entries are optional and never required for the default orchestrator path. Examples:

- `salesforce-crm-sync`: sync publication leads and campaign attribution.
- `hubspot-contact-tagging`: tag contacts by content engagement and lifecycle stage.
