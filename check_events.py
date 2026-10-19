import os
import smtplib
import sys
from email.header import Header
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

MVTD_URL = "https://events.microsoft.com/en-us/mvtd"
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

TARGET_KEYWORDS = ["Data Fundamentals", "データの基礎"]


def send_email(matched_events: list[dict]) -> None:
    """検知したイベントをGmail経由で送信する"""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("Error: GMAIL_USER or GMAIL_APP_PASSWORD is not set.", file=sys.stderr)
        sys.exit(1)

    subject = "【DP-900 割引検知】Microsoft Virtual Training Day が見つかりました"

    body_lines = [
        "DP-900 割引対象の可能性が高いセッションが検知されました。",
        "",
        f"■ カタログ一覧: {MVTD_URL}",
        "-" * 50,
    ]

    for i, ev in enumerate(matched_events, 1):
        body_lines.extend(
            [
                f"[{i}] {ev['title']}",
                f"URL: {ev['link']}",
                f"テキスト抜粋: {ev['snippet'][:150]}...",
                "-" * 50,
            ]
        )

    body_text = "\n".join(body_lines)

    msg = MIMEText(body_text, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER

    try:
        # GmailのSMTPサーバー（ポート587 / TLS）に接続
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        print("Notification email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    matched_events = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})

        print(f"Navigating to {MVTD_URL}...")
        page.goto(MVTD_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        links = page.locator("a").all()
        print(f"Total links found: {len(links)}")

        seen_hrefs = set()

        for link in links:
            text = link.inner_text().strip()
            href = link.get_attribute("href") or ""

            if any(kw.lower() in text.lower() for kw in TARGET_KEYWORDS):
                full_url = href if href.startswith("http") else f"https://events.microsoft.com{href}"
                if full_url in seen_hrefs:
                    continue
                seen_hrefs.add(full_url)

                title_line = text.split("\n")[0] if text else "Azure Data Fundamentals Session"
                matched_events.append(
                    {
                        "title": title_line,
                        "link": full_url,
                        "snippet": " ".join(text.split()),
                    }
                )

        browser.close()

    # テスト用にダミーデータを作成して強制送信
    test_events = matched_events if matched_events else [
        {
            "title": "【テスト送信】DP-900 監視通知テスト",
            "link": MVTD_URL,
            "snippet": "これはメール疎通テストです。GitHub Actionsからの通知が正常に届いています。",
        }
    ]
    print("Sending test email...")
    send_email(test_events)


if __name__ == "__main__":
    main()