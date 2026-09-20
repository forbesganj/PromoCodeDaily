# DailyVaultIN Promo Automation

A starter GitHub Actions project that checks configured public Telegram preview pages,
filters for selected app names, extracts promo codes, maps them to your referral links,
and publishes premium posts to your Telegram channel.

## Setup

1. Create a GitHub repository and upload all files.
2. Edit `config.json`:
   - Add more source channel usernames to `source_channels`.
   - Replace every `PASTE_YOUR_...` value with your authorized referral URL.
   - Add or remove app names in `allowed_apps`.
3. Add repository secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID` (for example: `@DailyVaultIN`)
4. Ensure your Telegram bot is an administrator of the destination channel with permission to post.
5. Run **Actions → DailyVaultIN Promo Monitor → Run workflow** for a manual test.
6. Review the first runs and logs before relying on scheduled publishing.

## Important limitations

- This uses the public `t.me/s/<channel>` preview page, not Telegram's private message API.
- Public preview HTML can change, and some posts may not be visible.
- GitHub scheduled workflows may be delayed; this is not real-time delivery.
- The parser is intentionally conservative and skips apps without a configured referral link.
- The workflow commits `data/state.json` to prevent repeated processing. Avoid running multiple copies concurrently.
- Use only public channels and referral links you are authorized to promote.
- Check applicable platform terms, affiliate terms, and local legal requirements before publishing.

## Adding a source

```json
"source_channels": [
  "Slots_567slots",
  "another_public_channel"
]
```

## Adding an app

Add the exact app display name to `allowed_apps`, then add the same key to `referral_links`.
For different spellings, extend `find_app()` in `src/parser.py` with explicit aliases.
