# Roblox release monitor (Discord)

Monitors **Egg Farm Simulator Remastered**, place ID `85419519353403`, using Roblox's playability-status endpoint. Runs on a GitHub Actions schedule every 10 minutes (best effort; GitHub schedules may be delayed). Sends a Discord webhook alert once and commits `release_state.json` to remember it.

## Setup

1. Create a **private GitHub repository** and upload `monitor.py` and the `.github/workflows/check-release.yml` file, preserving the folders.
2. In Discord: **Server Settings → Integrations → Webhooks → New Webhook**, select the channel and copy the webhook URL. You need permission to manage webhooks.
3. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**. Name it `DISCORD_WEBHOOK_URL` and paste the URL. Never put it in source code.
4. In GitHub: **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions** and save. The workflow must be able to commit the one-time notification state.
5. Go to **Actions → Check Roblox game release → Run workflow** for a manual test. If the game isn't playable yet, the workflow should succeed without a Discord message. Read the logs for the result.
6. The workflow will then run on GitHub's approximately 10-minute schedule. The default branch must contain the workflow, and GitHub Actions must be enabled.

## Notes

- The monitor requires an explicit `isPlayable: true` from Roblox. It does **not** infer release from visits or player count.
- If Roblox blocks the public API, changes the response, or requires login, the job fails without sending a false notification. Check Actions logs. An authenticated account's playability can differ from public access.
- GitHub scheduled workflows may be delayed or dropped during heavy load. This is not guaranteed to check exactly every 10 minutes.
- After a successful Discord response, the workflow commits `release_state.json` with `notified: true`; subsequent checks do nothing.
- If Discord accepts a notification but the subsequent GitHub commit fails, a later run may send it again. Check repository workflow permissions if this happens.
- Do not commit Roblox authentication cookies or the Discord webhook URL.
- If you want to reset it, delete `release_state.json` and commit that deletion.
