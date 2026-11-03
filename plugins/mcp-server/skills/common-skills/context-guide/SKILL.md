# Context Guide

How to read and write company and personal context. Read this before every
`write_context` call. The system prompt's "Company and personal context"
section says *when* to read and write; this skill says *what* a good file
looks like and *where* it goes.

---

## 1. Context, skill, or guidance

| It is… | Test | Where it goes |
|---|---|---|
| **Context** — what is true | A plain sentence that is simply true ("Amazon is reported under `amazon_us` and `amazon_ca`") | `context/<topic>.md` |
| **Skill** — how to do one job | Starts with "When asked to…"; has steps, queries, and an output format | `skills/<name>/SKILL.md` |
| **Guidance** — a standing rule | "Always…" / "Never…" ("Report net revenue, not gross") | `guidance.md` (company) or `preferences.md` (personal) |
| **Security** — what must not be shown or done | "Never show salaries", "Do not share supplier costs" | `security.md` (company admins only) |

A "skill" that only lists facts about the company is context. Save it as
context.

## 2. Company or personal

**If it is true no matter who asks, it is company. If it changes with who is
asking, it is personal.**

| Company | Personal |
|---|---|
| Business model, brands, channels, stack | The user's role and what they own ("I run DTC") |
| Fiscal calendar, which plan is live, plan naming | Their default plan, channel, period, currency |
| Metric definitions; GL, channel, and segment mappings | Format and length preferences |
| Product hierarchy and SKU quirks | Questions they ask every week |
| Known data issues and workarounds | Their working notes and drafts |
| Team roster and who owns what | Their own skills |
| Company guidance and security rules | |

- Personal files set style and defaults only. They never override a company
  fact or a security rule.
- Only a company admin can write company context. If a regular user teaches
  you a company fact, save it as a personal note and tell them an admin can
  promote it.

## 3. Layout

```
organization/
  profile.md               always in the prompt; at most 2,000 characters
  guidance.md              always in the prompt
  security.md              always in the prompt
  context/business.md      in the index; read on demand
  context/data-sources.md
  context/model.md
  context/metrics.md
  context/glossary.md
  context/team.md
  skills/<name>/SKILL.md
personal/<email>/
  preferences.md           always in the prompt; at most 2,000 characters
  context/<topic>.md
  skills/<name>/SKILL.md
```

Add to the existing file for a topic before creating a new one. Create a new
`context/<topic>.md` only when no existing file fits.

## 4. Every file

1. **Frontmatter** with flat `key: value` lines:
   - Context files: `title`, `description`, `owner`, `updated`, `source`,
     and optionally `review_by`.
   - Skills: `name`, `description`, `owner`, `updated`.
2. **`description` is the only thing the model sees in the index.** One line,
   at most 150 characters, starting with "Use when…".
3. **One topic per file.** Context files are at most 8,000 characters and
   skills at most 6,000. `profile.md` and `preferences.md` are at most 2,000.
   If a file grows past its limit, split it by heading.
4. **Definitions, not numbers.** "Net revenue = net sales + shipping, before
   marketplace fees" belongs in context. "Q2 revenue was $4.1M" does not — it
   goes stale and the data tools already answer it. If a number must appear,
   date it ("as of 2026-07-06").
5. **Cite the source** for anything non-obvious: the conversation, a ticket,
   a table name, or a person.
6. **Use real identifiers exactly**: table, column, `metric_id`, `plan_id`,
   and channel values as they appear in the warehouse.
7. **Never save** credentials, raw personal data, customer addresses, or
   anything the user asked you not to keep.
8. **Short, plain bullets.** No marketing tone, no hedging.
9. **Agents write like people.** Set `owner` to the user who asked, set
   `source` to the conversation, and set `updated` to today's date from a
   query (`SELECT CURRENT_DATE()`), not from memory.

## 5. Before you call `write_context`

- Read the current file with `read_context` first and edit it; never replace
  a file you have not read.
- Show the user the exact lines you will add or change, and where they go.
- Write only after the user confirms.
- If the new fact contradicts an existing line, replace the old line and say
  so. Do not keep both.

## 6. Skill files

```
---
name: company:<kebab-case-name>
description: Use when <the trigger, in the user's words>.
owner: <email>
updated: <YYYY-MM-DD>
---

# <Title>

## Steps
1. …

## Queries and tools
…

## Output
…
```

- Name the exact tools and tables to use.
- Personal skills use the `me:` prefix.
- A company or personal skill can never reuse the name of a Drivepoint skill.
