/**
 * Instant Promo Code Poster — Google Apps Script (Clean Version)
 * -------------------------------------------------------------
 * Runs INSIDE your Google Sheet. Fires the moment you type/edit a value in
 * the "Code" column, and immediately posts to Telegram — no scheduled wait.
 *
 * SETUP (one-time):
 *   1. Open your Sheet → Extensions → Apps Script
 *   2. Delete any placeholder code, paste this whole file in
 *   3. Replace BOT_TOKEN and CHAT_ID below with your real values
 *   4. Save (disk icon)
 *   5. Left sidebar → clock icon "Triggers" → "+ Add Trigger"
 *        - Function to run: onCodeEdited
 *        - Event source: From spreadsheet
 *        - Event type: On edit
 *        - Save → authorize when Google asks
 *   6. Done. Edit any cell in the "Code" column → posts instantly.
 *
 * Sheet columns expected (row 1 = header, exact names):
 *   App Name | Code | Code 2 | App Link | Image URL | Note | Active
 *
 * "Code 2" and "Note" are OPTIONAL — leave blank when not needed.
 */

const BOT_TOKEN = "8909843610:AAEnKorvfUslyhLitGyTtGYcXFwqbH0Vi1M";
const CHAT_ID = "@DailyVaultIN"; // your channel's @username

function onCodeEdited(e) {
  if (!e || !e.range) return;

  const sheet = e.range.getSheet();
  const editedCol = e.range.getColumn();
  const editedRow = e.range.getRow();

  if (editedRow === 1) return; // ignore header row edits

  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn())
    .getValues()[0]
    .map(h => String(h).trim());

  const codeColIndex = headers.indexOf("Code") + 1;
  if (codeColIndex === 0) return;

  if (editedCol !== codeColIndex) return; // only fire on Code column edits

  const rowValues = sheet.getRange(editedRow, 1, 1, sheet.getLastColumn()).getValues()[0];
  const row = {};
  headers.forEach((h, i) => (row[h] = String(rowValues[i] || "").trim()));

  if (!row["Code"]) return;

  const active = (row["Active"] || "TRUE").toUpperCase();
  if (active === "FALSE") return;

  const caption = buildCaption(row);
  const imageUrl = row["Image URL"];

  if (imageUrl) {
    sendPhoto(imageUrl, caption);
  } else {
    sendMessage(caption);
  }
}

function buildCaption(row) {
  let lines = [];

  lines.push(`<b>App Name:</b> ${escapeHtml(row["App Name"])}`);
  lines.push(`<b>Promo Code:</b> <code>${escapeHtml(row["Code"])}</code>`);
  if (row["Code 2"]) {
    lines.push(`<b>Promo Code 2:</b> <code>${escapeHtml(row["Code 2"])}</code>`);
  }
  if (row["App Link"]) {
    lines.push(`<b>App Link:</b> ${row["App Link"]}`);
  }
  if (row["Note"]) {
    lines.push(`<b>Note:</b> ${escapeHtml(row["Note"])}`);
  }

  return lines.join("\n");
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function sendPhoto(imageUrl, caption) {
  const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto`;
  const payload = {
    chat_id: CHAT_ID,
    photo: imageUrl,
    caption: caption,
    parse_mode: "HTML",
  };
  callTelegram(url, payload);
}

function sendMessage(caption) {
  const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;
  const payload = {
    chat_id: CHAT_ID,
    text: caption,
    parse_mode: "HTML",
  };
  callTelegram(url, payload);
}

function callTelegram(url, payload) {
  const options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  };
  const response = UrlFetchApp.fetch(url, options);
  Logger.log(response.getContentText());
}

/* ============================================================
 * SOURCE CHANNEL AUTO-MONITOR
 * ------------------------------------------------------------
 * Checks a public Telegram channel's preview page (t.me/s/...)
 * every few minutes for new posts matching the template:
 *
 *   <emoji> APPNAME New PromoCode
 *   Claim > claimlink.com
 *   App Link 👉
 *   https://applink.com/?code=XXXX&t=...
 *
 * When a new matching post is found, it auto-extracts App Name,
 * Code (from the ?code= in the App Link) and App Link, then
 * posts it to YOUR channel automatically — no manual step.
 *
 * SETUP:
 *   1. Set SOURCE_CHANNEL below (just the @username, no t.me/)
 *   2. Triggers → + Add Trigger → function: checkSourceChannel
 *      Event source: Time-driven → Minutes timer → Every 10 minutes
 *   3. Save. Done — it now runs automatically forever.
 * ============================================================ */

const SOURCE_CHANNEL = "allyonocodewala"; // no @, no t.me/

function checkSourceChannel() {
  const url = `https://t.me/s/${SOURCE_CHANNEL}`;
  const response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
  const html = response.getContentText();

  const props = PropertiesService.getScriptProperties();
  const lastId = parseInt(props.getProperty("LAST_SOURCE_ID_" + SOURCE_CHANNEL) || "0", 10);

  // Find each message block: data-post="channel/12345" ... message text div
  const blockRegex = new RegExp(
    `data-post="${SOURCE_CHANNEL}\\/(\\d+)"[\\s\\S]*?class="tgme_widget_message_text[^"]*"[^>]*>([\\s\\S]*?)<\\/div>`,
    "g"
  );

  let match;
  let maxIdSeen = lastId;
  const newPosts = [];

  while ((match = blockRegex.exec(html)) !== null) {
    const postId = parseInt(match[1], 10);
    if (postId <= lastId) continue;

    const rawHtml = match[2];
    const text = rawHtml
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<[^>]+>/g, "")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .trim();

    newPosts.push({ id: postId, text: text });
    if (postId > maxIdSeen) maxIdSeen = postId;
  }

  // Process oldest-first so channel order stays correct
  newPosts.sort((a, b) => a.id - b.id);

  newPosts.forEach(post => {
    const parsed = parseSourceMessage(post.text);
    if (parsed) {
      const caption = buildCaption({
        "App Name": parsed.appName,
        "Code": parsed.code,
        "App Link": parsed.appLink,
      });
      sendMessage(caption);
    } else {
      Logger.log("Skipped (did not match template): " + post.text.substring(0, 80));
    }
  });

  if (maxIdSeen > lastId) {
    props.setProperty("LAST_SOURCE_ID_" + SOURCE_CHANNEL, String(maxIdSeen));
  }
}

function parseSourceMessage(text) {
  // Expected shape:
  //   <emoji> APPNAME New PromoCode
  //   Claim > something
  //   App Link 👉
  //   https://.../?code=XXXX&t=...
  const appNameMatch = text.match(/([A-Za-z0-9\-\.]+)\s+New\s*PromoCode/i);
  const appLinkMatch = text.match(/(https?:\/\/\S+)/i);

  if (!appNameMatch || !appLinkMatch) return null;

  const appLink = appLinkMatch[1];
  const codeMatch = appLink.match(/[?&]code=([^&\s]+)/i);
  if (!codeMatch) return null;

  return {
    appName: appNameMatch[1],
    code: decodeURIComponent(codeMatch[1]),
    appLink: appLink,
  };
}
