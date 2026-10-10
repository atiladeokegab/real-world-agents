# Real-World Agents Hackathon (Dwelly, London, Sat 10 Oct 2026)

Our team's entry for the Real-World Agents Hackathon hosted by Dwelly in London on Saturday 10 October 2026. The track and the agent we build are chosen together at 10:00 on the day; IDEA.md and this page are updated then.

Official rules: [docs/rules/RULES.md](docs/rules/RULES.md), the organisers' guide word for word, with their PDF beside it. It wins over every other page in this repo, this one included: if anything here disagrees with it, open a `question` issue.

Smoke: `uv run --with pytest pytest -q`

The product that ships is `main`: the last commit that passed the smoke check.

Board: https://github.com/users/atiladeokegab/projects/10

## Deadlines

Your agent checks these every session against the UTC column. GitHub milestones keep only the
date, so this UTC column is the clock, never the milestone.

| Deadline | Event time | UTC |
|---|---|---|
| build start | 2026-10-10T10:00+01:00 | 2026-10-10T09:00Z |
| code freeze | 2026-10-10T16:30+01:00 | 2026-10-10T15:30Z |
| reality test | 2026-10-10T16:30+01:00 | 2026-10-10T15:30Z |
| demo video | 2026-10-10T16:30+01:00 | 2026-10-10T15:30Z |
| submit | 2026-10-10T17:00+01:00 | 2026-10-10T16:00Z |

## Judging criteria

- Overall: 70% technical evaluation + 30% demo video and presentation
- Technical, correct outcomes and coverage: 38.5 points (35% outcomes, 20% coverage of the technical score)
- Technical, judgement and safety (ambiguity, conflicts, escalation; doing nothing can be right): 14 points
- Technical, engineering quality (autonomous, robust, reproducible): 10.5 points
- Technical, real-world applicability: 7 points
- Demo, 30 points: a working product, clarity (problem, solution, key workflow, outcome), product insight
- Technical scoring is mostly the unseen Reality Test, judged by Claude-based agents; manipulating them scores zero

## Team

| Name | GitHub | Role |
|---|---|---|
| Atilade | @atiladeokegab | lead, voice (ElevenLabs), demo video, pitch |
| Abdussalam | @Abdussalam-popsy | designer, designer |
| Faisal | @FHL-08 | PhD in control theory (Manchester); Python, C++, ROS, full-stack web |
| Jack | @Drastixs | backend / agent logic |

The lead's agents: Zeus, Prometheus, Hermes. When this page or a review says "the lead", it may be one of them acting for the lead.
