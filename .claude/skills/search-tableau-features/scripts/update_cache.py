"""
Tableau Desktop機能キャッシュ更新スクリプト

Tableau公式サイトからDesktop向け新機能を取得し、
.claude/skills/search-tableau-features/features-cache.md に書き出す。

サーバーサイドフィルタ (?field_products_target_id=37) を使い、
Desktop機能のみを取得する。

Usage:
    python scripts/search-tableau-features/update_cache.py
    python scripts/search-tableau-features/update_cache.py --dry-run   # 画面出力のみ
"""

import re
import html
import urllib.request
import urllib.error
import argparse
import os
import sys
from datetime import datetime, timedelta

# --- Config ---
ALL_FEATURES_URL = "https://www.tableau.com/products/all-features"
NEW_FEATURES_URL = "https://www.tableau.com/products/new-features"
DESKTOP_FILTER = "?field_products_target_id=37"  # Tableau Desktop
CACHE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "features-cache.md",
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
LOOKBACK_DAYS = 450  # 約15ヶ月（四半期ずれを吸収）


def fetch(url: str) -> str:
    """URLからHTMLを取得する"""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"  [WARN] HTTP {e.code} for {url}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"  [WARN] Failed to fetch {url}: {e}", file=sys.stderr)
        return ""


def get_major_release_urls(all_features_html: str) -> list[tuple[str, str]]:
    """
    all-features ページから過去1年分のメジャーリリースURLを抽出する。
    Returns: [(release_name, url), ...] 新しい順
    """
    # パターン: /2025-3-features（月次リリースは除外: 2025-2-november-features 等）
    url_pattern = re.compile(
        r'href="(https://www\.tableau\.com/(\d{4})-(\d)-features)"', re.IGNORECASE
    )

    cutoff = datetime.now() - timedelta(days=LOOKBACK_DAYS)
    releases = []

    for match in url_pattern.finditer(all_features_html):
        url = match.group(1)
        year, quarter = int(match.group(2)), int(match.group(3))
        # Q1=1月, Q2=4月, Q3=7月, Q4=10月（リリースは四半期初め頃）
        approx_month = {1: 1, 2: 4, 3: 7, 4: 10}.get(quarter, 1)

        if datetime(year, approx_month, 1) >= cutoff:
            name = f"Tableau {year}.{quarter}"
            if (name, url) not in releases:
                releases.append((name, url))

    # 重複排除（同一リリース名は最初の出現を採用）
    seen = set()
    unique = []
    for name, url in releases:
        if name not in seen:
            seen.add(name)
            unique.append((name, url))
    releases = unique

    releases.sort(key=lambda r: r[0], reverse=True)

    # 最新リリース（new-features）を先頭に追加
    latest_name = detect_latest_release_name(all_features_html)
    releases = [(n, u) for n, u in releases if n != latest_name]
    releases.insert(0, (latest_name, NEW_FEATURES_URL))

    return releases


def detect_latest_release_name(html_text: str) -> str:
    """new-features に対応するリリース名を推定する"""
    match = re.search(r"Tableau\s+(\d{4}\.\d)", html_text)
    if match:
        return f"Tableau {match.group(1)}"
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"Tableau {now.year}.{quarter}"


def extract_desktop_features(release_html: str) -> list[tuple[str, str, str]]:
    """
    Desktop機能フィルタ済みページから機能を抽出する。
    Returns: [(feature_name, description), ...]
    """
    features = []
    item_ids = re.findall(r'id="(item-\d+)"', release_html)

    for i, item_id in enumerate(item_ids):
        start_pos = release_html.find(f'id="{item_id}"')
        if start_pos == -1:
            continue

        if i + 1 < len(item_ids):
            end_pos = release_html.find(f'id="{item_ids[i + 1]}"', start_pos + 1)
        else:
            end_pos = len(release_html)

        block = release_html[start_pos:end_pos]

        # タイトル
        title_match = re.search(
            r'<h3[^>]*class="[^"]*teaser-item__title[^"]*"[^>]*>(.*?)</h3>',
            block, re.DOTALL,
        )
        if not title_match:
            continue
        title = clean_html(title_match.group(1))
        if not title:
            continue

        # 説明
        desc_match = re.search(
            r'field--name-field-teaser-text[^>]*><p>(.*?)</p>',
            block, re.DOTALL,
        )
        description = clean_html(desc_match.group(1)) if desc_match else ""

        # 詳細テキスト（feature-highlight__copy 内）
        detail_match = re.search(
            r'<div class="feature-highlight__copy">([\s\S]*?)</div>',
            block,
        )
        detail = clean_html(detail_match.group(1)) if detail_match else ""

        features.append((title, description, detail))

    return features


def clean_html(text: str) -> str:
    """HTMLタグを除去してプレーンテキストにする"""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("|", "-")  # Markdownテーブル対策
    return text.strip()


def build_cache_markdown(
    releases: list[tuple[str, str, list[tuple[str, str, str]]]]
) -> str:
    """キャッシュ用Markdownを生成する"""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"<!-- Last updated: {today} -->", ""]

    for name, url, features in releases:
        lines.append(f"## {name} ({url})")
        lines.append("")
        lines.append("| Feature | Description | Detail |")
        lines.append("|---------|-------------|--------|")
        for title, desc, detail in features:
            lines.append(f"| {title} | {desc} | {detail} |")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Tableau機能キャッシュ更新")
    parser.add_argument(
        "--dry-run", action="store_true", help="ファイルに書き込まず画面出力のみ"
    )
    args = parser.parse_args()

    print("=== Tableau Desktop機能キャッシュ更新 ===\n")

    # Step 1: リリース一覧を取得
    print(f"[1/3] リリース一覧を取得中... ({ALL_FEATURES_URL})")
    all_html = fetch(ALL_FEATURES_URL)
    if not all_html:
        print("[ERROR] all-features ページの取得に失敗しました", file=sys.stderr)
        sys.exit(1)

    releases = get_major_release_urls(all_html)
    print(f"  -> {len(releases)} 件のメジャーリリースを検出\n")
    for name, url in releases:
        print(f"  - {name}: {url}")
    print()

    # Step 2: 各リリースからDesktop機能を抽出（フィルタ付きURL）
    print("[2/3] 各リリースからDesktop機能を抽出中...")
    results = []
    for name, url in releases:
        filtered_url = url + DESKTOP_FILTER
        print(f"  -> {name} ...", end=" ", flush=True)
        release_html = fetch(filtered_url)
        if not release_html:
            print("SKIP (fetch failed)")
            continue
        features = extract_desktop_features(release_html)
        print(f"{len(features)} 件")
        results.append((name, url, features))

    print()

    # Step 3: キャッシュファイル生成
    md = build_cache_markdown(results)
    total = sum(len(f) for _, _, f in results)

    if args.dry_run:
        print("[3/3] --dry-run: 画面出力のみ\n")
        print("=" * 60)
        print(md)
        print("=" * 60)
    else:
        cache_path = os.path.normpath(CACHE_PATH)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[3/3] キャッシュを保存しました: {cache_path}")

    print(f"\n合計: {len(results)} リリース / {total} 機能")


if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    main()
