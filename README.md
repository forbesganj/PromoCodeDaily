# Daily Telegram Promo Code Bot — Setup Guide

Yeh setup daily ek fixed time pe tumhare Telegram channel me 10 apps ke promo
codes automatically post karega. Cost: **₹0** (GitHub Actions free tier ka
use karke).

---

## Step 1 — Telegram Bot banao
1. Telegram me `@BotFather` ko message karo.
2. `/newbot` bhejo, naam aur username set karo.
3. Wo tumhe ek **token** dega, kuch aisa: `123456789:ABCdefGhIJKlmNoPQRstuVWxyz`
   Isse safe rakho.
4. Apne Telegram **channel** me jao → Administrators → is bot ko admin bana do
   (kam se kam "Post Messages" permission ke saath).

## Step 2 — Chat ID pata karo
- Agar channel **public** hai (username hai jaise `@mychannel`), to `TELEGRAM_CHAT_ID`
  bas `@mychannel` rakh do.
- Agar **private** channel hai, to ek message channel me post karo, fir browser me
  ye URL kholo (apna token daal ke):
  `https://api.telegram.org/bot<TOKEN>/getUpdates`
  Response me `"chat":{"id": -1001234567890 ...}` milega — wahi id use karo.

## Step 3 — Google Sheet banao
1. Naya Google Sheet banao, pehli row me ye headers daalo:
   `App Name | Code | Redeem Link | Image URL | Expiry | Active`
2. Har row ek game app ka code (total 10 rows for 10 apps). `Active` column
   me `TRUE` rakho jab tak code valid hai, expire hone pe `FALSE` kar do.
3. **Image URL column zaroori hai** — har app ka icon/banner ka direct
   image link (jo `.jpg`/`.png` pe end hota ho, ya image hosting se direct
   link). Options:
   - App ke Play Store/App Store listing se icon image ka link (right-click
     → "Copy image address").
   - Apni khud ki banner image [imgbb.com](https://imgbb.com) (free, login
     ke bina) pe upload karke "Direct link" copy karo.
   - Company ka official press kit / media page se banner.
4. **File → Share → Publish to web** → format select karo **CSV** →
   Publish. Jo link mile wahi `SHEET_CSV_URL` hai.

   Daily codes update karna hai to bas Sheet me row edit karo — code me
   kuch touch nahi karna padega. Agar kisi row ka Image URL khali hai, wo
   post skip ho jayega us format me (digest me row drop hogi, single-post
   mode me text-only fallback chalega).

## Step 4 — Repo GitHub pe daalo
1. Ye poora folder (`post_promo_codes.py`, `.github/workflows/daily-post.yml`)
   ek naye GitHub repo me push karo.
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**
   se ye 3 secrets add karo:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `SHEET_CSV_URL`

## Step 5 — Test karo
- Repo → **Actions** tab → "Daily Promo Code Post" workflow → **Run workflow**
  (manual trigger) se turant test kar sakte ho.
- Sahi se chala to tumhare channel me formatted message aa jayega.
- Uske baad wo automatically daily fixed time (default 9:00 AM IST) pe chalega.
  Time change karna ho to `daily-digest.yml` me cron line edit karo.

---

## High-frequency mode (10-15 posts/day)

Do workflows kaam karte hain saath me:

- **`daily-digest.yml`** — din me 1 baar (9:00 AM IST), sab 10 codes ek pinned
  message me post karta hai. Isko channel me **pin** kar do — naye members ko
  sab codes ek jagah mil jayenge.
- **`high-frequency-posts.yml`** — din me ~14 baar (10 AM se 11 PM IST, roughly
  hourly), har baar **ek** rotating code post karta hai. Isse channel active
  dikhta hai aur har app ko baar-baar spotlight milta hai — bina state/database
  ke, purely time-based rotation se.

Dono milake tumhare 10-15 posts/day ka target cover ho jata hai. Dono
workflows **same 3 secrets** use karte hain, alag se kuch add nahi karna.

**Zaroori:** repo ko **public** rakhna (Settings → General → Danger Zone →
Change visibility). Public repos pe GitHub Actions minutes **unlimited free**
hain — private repo me free tier limited hai aur itni frequent runs se exhaust
ho sakta hai.

**Note:** scheduled GitHub Actions cron ka exact time thoda (1-10 min) delay
ho sakta hai peak load ke time — free tier ki limitation hai, koi paid
alternative nahi chahiye isके liye.

---

## Max reach ke liye tips
- Isi script ko copy karke ek dusra job bana lo jo **WhatsApp** (via
  WhatsApp Business API / Twilio) ya **Discord webhook** pe bhi same message
  bheje — ek hi Sheet, multiple destinations.
- Message ko daily pin karo channel me.
- Naye members ko welcome message me channel ka purpose clearly batao taaki
  wo mute na karen.
- Telegram directories (TGStat, Telegram Channels list sites) pe channel
  submit karo for organic discovery.
- Codes expire hone se pehle "last chance" reminder post add kar sakte ho
  (isi script ka ek variant, din me 2 baar chalao).
