# Anima skills

Optional abilities the being can learn during onboarding or via `/capabilities grant`.

| Skill | Capability | Command |
|-------|------------|---------|
| Web fetch | `web_fetch` | `/fetch <url>` |
| Web crawl | `web_crawl` | `/crawl <url>` |
| Explore | `explore` | `/explore <url>` |

Natural language also works when skills are enabled:

- "fetch https://example.com"
- "explore https://news.ycombinator.com"
- "crawl https://docs.example.com"

Enable at any time:

```bash
anima onboard
# or
/capabilities grant web_fetch
```
