# Setting up the workspace (one time, about 20 minutes)

For the person creating the organisation. Nothing here costs money.

1. **Create the organisation** on GitHub (for example `commonhold`; check the name is free). Add at least two more
   owners later (GOVERNANCE.md: continuity).
2. **Create a public repository** `commonhold` in it, empty, then push this folder:
   `git remote add origin git@github.com:<org>/commonhold.git && git push -u origin main`
3. **Settings → General:** enable **Allow auto-merge** and **Automatically delete head branches**; enable **Wiki**
   and create its first page by hand (the wiki repository doesn't exist until then).
4. **Settings → Pages:** Source: **GitHub Actions**.
5. **Deploy key for the living README:** create a key pair (`ssh-keygen -t ed25519 -f render_key -N ""`).
   Settings → Deploy keys → add `render_key.pub` with **write access**. Settings → Secrets → Actions → new secret
   `RENDER_DEPLOY_KEY` with the contents of `render_key`. Delete both files afterwards.
6. **Settings → Rules → New branch ruleset** for `main`:
   - Enforcement: Active. Bypass list: **Deploy keys** (so only the render job can write the generated files).
   - Restrict deletions; Block force pushes.
   - Require a pull request before merging: 0 approvals, **Require review from Code Owners** on.
   - Require status checks to pass: **guard** (and **tests**).
7. **Invite members** as collaborators with **Write** access, and ask each to fill in `github:` in their
   `member.yml` (in their own folder, so it ships by itself).
8. **Optional, Codeberg mirror:** create the same org and repo on Codeberg, make an access token, add it as secret
   `CODEBERG_TOKEN` and add a variable `CODEBERG_REPO` = `<org>/commonhold`.
9. **Optional, Discord:** create a server and lay it out from `community/discord-layout.yml`. Add a webhook to #ships
   if you want merged pull requests posted there.

Then edit `commonhold.yml` (`repo:`) and the console link in README.md, and run the **render** workflow once.

## Why a guard check instead of GitHub's push rules
GitHub's "restrict file paths" push rules aren't available for free public repositories, and CODEOWNERS can't let
you approve your own folder. The guard check gives each member a folder only they control, at no cost.
It runs from the base branch, so a pull request can't change how it's judged. A pull request that edits `.github/`
always needs a steward's code-owner review as well.
