# Governance

## Members
A member is anyone with a folder in `members/`. Joining takes a pull request adding `members/<handle>/member.yml`,
approved by 2 members. Members get write access and one equal vote.

## Stewards
Each spec section has a steward (see `commonhold.yml`), who must approve changes to it. Stewards rotate or change by
decision.

## How decisions are made
| Change | Needs |
|---|---|
| Your own folder | Nothing: the guard checks it and it merges itself |
| Someone else's folder | That person's approval |
| `joint/`, `wiki/`, README text, a new member | 2 other members |
| `spec/` | 3 other members, including the section steward |
| How the workspace works (`.github/`, `tools/`, this file, the charter) | 2 other members plus a steward code-owner review |

Bigger questions go in `joint/decisions/` as a proposal. If nobody objects within 72 hours and the approvals above are
met, it's accepted. If someone objects, talk first; if it's still split, a simple majority of members decides, and
the proposal and the vote stay in the record either way.

## Blocks and safety
Delisting a world or relay takes a block record signed by 2 of the 3 council members, with a reason and an expiry,
published in the open. The affected host may appeal once; a different 2 of 3 decide the appeal.
TODO(group): name the first council of 3.

## Continuity
- The GitHub organisation has at least three owners, each with recovery codes stored safely.
- If a member leaves, their folder stays as they left it (with its licence) unless they ask for it to be removed.
- The repository is mirrored to Codeberg; signed records and releases keep working if either host disappears.
- Renaming the project or moving the organisation needs a decision with approval from every active member.

## Code of conduct
We follow the [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Reports go to the council (see SECURITY.md for contacts).
