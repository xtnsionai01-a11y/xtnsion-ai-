# Agents

Project subagents available to Claude Code in this repo. Invoke one with the
`Agent` tool, or let Claude pick it by matching the task to the agent's
`description`.

## claude-code-ui-agents (frontend UI/UX pack)

Nine frontend design and implementation agents, vendored flat from
[mustafakendiguzel/claude-code-ui-agents](https://github.com/mustafakendiguzel/claude-code-ui-agents)
at commit `e224ca0` (2025-08-08), MIT licensed — see
[LICENSE-claude-code-ui-agents](LICENSE-claude-code-ui-agents).

| Agent | Category | Upstream source |
| --- | --- | --- |
| `aria-implementation` | accessibility | `prompts/accessibility/aria-implementation.md` |
| `micro-interactions` | animation | `prompts/animation/micro-interactions.md` |
| `react-component-generator` | components | `prompts/components/react-component-generator.md` |
| `mobile-first-layout` | responsive | `prompts/responsive/mobile-first-layout.md` |
| `design-system-generator` | ui-design | `prompts/ui-design/design-system-generator.md` |
| `mobile-design-philosophy` | ui-design | `prompts/ui-design/mobile-design-philosophy.md` |
| `ui-design-expert` | ui-design | `prompts/ui-design/universal-ui-design-methodology.md` |
| `user-persona-generator` | ux-research | `prompts/ux-research/user-persona-generator.md` |
| `css-architecture` | web-development | `prompts/web-development/css-architecture.md` |

### Changes made while vendoring

Upstream ships these as a prompt library, not as loadable agents, so three
things were normalized:

1. **Quoted `description` values.** Every upstream description contains a bare
   `Examples:` — a colon followed by a space, which is not legal in a YAML
   plain scalar. All nine files failed to parse as frontmatter; the
   descriptions are now double-quoted.
2. **Slugified `name` values.** Upstream names are prose ("React Component
   Architect"). Agent names must be kebab-case identifiers, so each file uses
   its upstream filename stem, except `ui-design-expert`, whose upstream name
   was already a valid slug.
3. **Added frontmatter to `mobile-design-philosophy`.** It shipped with none;
   its `description` was written from the file's own Description section.

Prompt bodies are otherwise verbatim. Each file carries an HTML comment
pointing at its upstream path.
