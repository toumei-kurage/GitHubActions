import sys
from playwright.sync_api import sync_playwright

MVTD_URL = "https://events.microsoft.com/en-us/mvtd"
TARGET_KEYWORDS = ["Data Fundamentals", "データの基礎"]


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

    if matched_events:
        print(f"Found {len(matched_events)} matching event(s). Generating report...")
        with open("result.md", "w", encoding="utf-8") as f:
            f.write("@toumei-kurage\n\n")  # メンション通知用
            f.write("## 🔔 DP-900 割引対象の可能性があるトレーニングが見つかりました\n\n")
            f.write(f"- カタログ一覧: {MVTD_URL}\n\n")
            f.write("---\n\n")
            for ev in matched_events:
                f.write(f"### [{ev['title']}]({ev['link']})\n")
                f.write(f"- 抜粋: {ev['snippet'][:150]}...\n\n")
    else:
        print("No matching DP-900 events found today.")


if __name__ == "__main__":
    main()