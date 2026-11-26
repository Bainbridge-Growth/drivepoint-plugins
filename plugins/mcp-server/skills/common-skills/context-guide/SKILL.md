# Context Guide

How to read and write company and personal context. Read this before every
`write_context`, `validate_context_file`, or `create_context_file` call. The
system prompt's "Company and personal context" section says *when* to read
and write; this skill says *what* a good file looks like and *where* it goes.
The server enforces the hard limits below and rejects a write that breaks
them, so treat the error message as the source of truth.

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

Use the paths `list_context` returns. They look like this:

```
organization/
  profile.md               always in the prompt
  guidance.md              always in the prompt
  security.md              always in the prompt
  context/<topic>.md       in the index; read on demand
  context/<folder>/<topic>.md   folders are allowed, up to 3 deep
  skills/<name>/SKILL.md
personal/
  preferences.md           always in the prompt
  context/<topic>.md
  skills/<name>/SKILL.md
```

Personal paths always mean the signed-in user's own files. File and folder
names use lowercase letters, numbers, and hyphens.

Add to the existing file for a topic before creating a new one. Create a new
file only when no existing file fits.

## 4. Every file

1. **Frontmatter** is optional on write and uses flat `key: value` lines.
   Write only `title` and `description` (skills may also have `name`, the
   kebab-case skill name, which is also the folder name). Do not write `owner`, `updated`, or `source`:
   the server stamps them on every save and ignores any you send. Do not
   write a `company:` or `me:` prefix in `name`; the catalog adds that prefix
   when it lists the skill.
2. **`description` is the only thing the model sees in the index.** One line,
   at most 150 characters, starting with "Use when…". `title` is at most 120.
3. **One topic per file.** Limits apply to the body, after the frontmatter:
   context files at most 8,000 characters, skills at most 6,000,
   `guidance.md` and `security.md` at most 4,000, and `profile.md` and
   `preferences.md` at most 2,000. If a file grows past its limit, split it
   by heading.
4. **Definitions, not numbers.** "Net revenue = net sales + shipping, before
   marketplace fees" belongs in context. "Q2 revenue was $4.1M" does not — it
   goes stale and the data tools already answer it. If a number must appear,
   date it ("as of 2026-07-06").
5. **Cite the source** for anything non-obvious in the body: the conversation,
   a ticket, a table name, or a person.
6. **Use real identifiers exactly**: table, column, `metric_id`, `plan_id`,
   and channel values as they appear in the warehouse.
7. **Never save** credentials, raw personal data, customer addresses, or
   anything the user asked you not to keep.
8. **Save only what every reader could already see.** Everyone who can read
   company context can read what you write, so never copy in data from
   outside this company's marts, another company's data, benchmarks, or
   Drivepoint-internal notes — even if your session can reach them.
9. **Short, plain bullets.** No marketing tone, no hedging.

## 5. Before you save

- **Changing an existing file:** call `read_context` first and edit what it
  returned; never replace a file you have not read. Pass the `generation`
  from `read_context` to `write_context`. If someone changed the file since,
  the write fails: read it again and redo the edit.
- **Adding a new file or skill:** call `validate_context_file` to check it
  without saving, show the user the result, then call `create_context_file`.
  New files go through a safety review; `read_context` shows the
  `reviewStatus`, and the file is usable only once it is `active`.
- Show the user the exact lines you will add or change, and where they go.
- Save only after the user confirms.
- If the new fact contradicts an existing line, replace the old line and say
  so. Do not keep both.

## 6. Skill files

```
---
name: <kebab-case-name>
description: Use when <the trigger, in the user's words>.
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
- The skill appears in `list_skills` as `company:<name>` or `me:<name>`,
  depending on where it is saved.
- A company or personal skill can never reuse the name of a Drivepoint skill.
