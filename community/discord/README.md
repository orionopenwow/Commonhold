# Commonhold Discord setup (you run it, once, about 5 minutes)

Sets the server up for developers: two categories, seven channels, two roles, each channel named `<emoji>︱<name>`
like the Leyline Discord, and one short pinned post in each channel saying what it's for. It deletes nothing and never
touches the server's name, icon or banner. Running it twice changes nothing the second time.

| Category | Channel | For |
|---|---|---|
| 🧭︱start here | 👋︱welcome (read-only) | What Commonhold is, how to join |
| | 📢︱announcements (read-only) | Milestones only |
| 🛠️︱build | 💬︱general | Talk, introductions, ideas |
| | 📜︱spec | The protocol; decisions go to the repo |
| | ⚙️︱dev | Code, adapters, launchers, tools |
| | 🐞︱help | Stuck? Ask here |
| | 🚀︱ships (read-only) | Merged changes, posted automatically |
| | 🎙️︱dev call (voice) | Calls |

Roles: **Steward** (approves a spec section), **Builder** (has a folder in the repo).

## Steps
1. **Make a bot:** <https://discord.com/developers/applications> → New Application (`Commonhold setup`) → Bot →
   Reset Token → Copy. That token is the bot's password: don't share it. Paste it when the script asks (hidden), or
   save it as `token.txt` next to the script (git-ignored).
2. **Invite it:** OAuth2 → URL Generator → tick **bot**, then **Administrator** → open the URL → pick the Commonhold
   server → Authorize. In Server Settings → Roles, drag the bot's role to the top.
3. **Preview:** double-click `Commonhold Discord - preview.bat`. It prints the plan and changes nothing.
4. **Do it:** double-click `Commonhold Discord - do it.bat`, and paste the repo link when asked (or press Enter).
5. **Kick the bot** (Server Settings → Members → the bot → Kick), and delete `token.txt` if you made one.

**#ships feed:** in #ships → Edit Channel → Integrations → Webhooks → New Webhook → Copy URL. Then in the GitHub
repo: Settings → Webhooks → Add webhook, paste the URL with `/github` on the end, content type `application/json`,
"Let me select individual events" → **Pull requests** only.
