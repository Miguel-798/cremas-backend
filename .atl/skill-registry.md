# Skill Registry

**Orchestrator use only.** Read this registry once per session to resolve skill paths, then pass pre-resolved paths directly to each sub-agent's launch prompt. Sub-agents receive the path and load the skill directly — they do NOT read this registry.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| When user asks to build web components, pages, or applications | frontend-design | C:\Users\Miguel\Desktop\programacion 2026\gentleman\frontend-new\SKILL.md |
| When user asks to create a new skill, add agent instructions, or document patterns for AI | skill-creator | file:///C:/Users/Miguel/.config/opencode/skills/skill-creator/SKILL.md |
| When writing Go tests, using teatest, or adding test coverage | go-testing | file:///C:/Users/Miguel/.config/opencode/skills/go-testing/SKILL.md |

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| None | — | No convention files found in project root |

## SDD Workflow Skills (for Orchestrator)

| Phase | Skill | Path |
|-------|-------|------|
| sdd-init | sdd-init | file:///C:/Users/Miguel/.config/opencode/skills/sdd-init/SKILL.md |
| sdd-explore | sdd-explore | file:///C:/Users/Miguel/.config/opencode/skills/sdd-explore/SKILL.md |
| sdd-propose | sdd-propose | file:///C:/Users/Miguel/.config/opencode/skills/sdd-propose/SKILL.md |
| sdd-spec | sdd-spec | file:///C:/Users/Miguel/.config/opencode/skills/sdd-spec/SKILL.md |
| sdd-design | sdd-design | file:///C:/Users/Miguel/.config/opencode/skills/sdd-design/SKILL.md |
| sdd-tasks | sdd-tasks | file:///C:/Users/Miguel/.config/opencode/skills/sdd-tasks/SKILL.md |
| sdd-apply | sdd-apply | file:///C:/Users/Miguel/.config/opencode/skills/sdd-apply/SKILL.md |
| sdd-verify | sdd-verify | file:///C:/Users/Miguel/.config/opencode/skills/sdd-verify/SKILL.md |
| sdd-archive | sdd-archive | file:///C:/Users/Miguel/.config/opencode/skills/sdd-archive/SKILL.md |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
