import requests
import json
import time
import urllib.parse
import os
import sys
import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from config import JSON_DIR, LUOGU_BASE_URL, UIDS_FILE
from utils import ensure_dir, load_uid_map


def get_records(user_id, cookies=None, min_date=None):
    base_url = LUOGU_BASE_URL
    params = {"user": user_id, "page": 1}

    # Convert min_date (YYYY-MM-DD) to timestamp
    min_timestamp = 0
    if min_date:
        try:
            dt = datetime.datetime.strptime(min_date, "%Y-%m-%d")
            min_timestamp = dt.timestamp()
            print(f"Filtering records after: {min_date}")
        except ValueError:
            print("Invalid date format. Ignoring min_date.")

    # Use a session for connection pooling and cookie persistence
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": UserAgent().random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": f"https://www.luogu.com.cn/record/list?user={user_id}",
        }
    )

    if cookies:
        print("Using provided cookies.")
        session.cookies.update(cookies)

    all_records = []

    while True:
        print(f"Fetching page {params['page']}...")
        try:
            response = session.get(base_url, params=params)

            if response.status_code != 200:
                print(f"Failed to retrieve page: Status code {response.status_code}")
                if len(response.text) < 500:
                    print(response.text)
                break

            data = None
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Fallback to HTML parsing
                try:
                    soup = BeautifulSoup(response.text, "html.parser")
                    for script in soup.find_all("script"):
                        if script.text and "window._feInjection" in script.text:
                            start = script.text.find('decodeURIComponent("')
                            if start != -1:
                                start += len('decodeURIComponent("')
                                end = script.text.find('")', start)
                                if end != -1:
                                    data = json.loads(
                                        urllib.parse.unquote(script.text[start:end])
                                    )
                            break
                except Exception as e:
                    print(f"HTML parsing attempts failed: {e}")

            if not data:
                print("Could not retrieve data (neither JSON nor HTML injection).")
                if "登录" in response.text:
                    print(
                        "Redirected to login page. Cookie might be invalid or expired."
                    )
                else:
                    print("Unknown page content.")
                    try:
                        print(response.text[:200])
                    except:
                        pass
                break

            if (
                isinstance(data, dict)
                and data.get("code") != 200
                and "currentData" not in data
            ):
                # Check if it's the standard Luogu API response structure
                if "currentData" not in data:
                    print(f"API Error or unexpected structure: {str(data)[:100]}")
                    break

            current_data = data.get("currentData", {})
            if not current_data:
                # Sometimes data is directly the struct in some APIs, but usually _contentOnly returns standard structure
                print("No currentData found in JSON response.")
                current_data = data  # Try this?

            records_data = current_data.get("records", {})
            records = records_data.get("result", [])

            if not records:
                print("No records found on this page.")
                break

            for record in records:
                problem = record.get("problem", {})
                status = record.get("status")
                score = record.get("score")
                submit_time = record.get("submitTime")

                # Filter by date
                if min_timestamp and submit_time < min_timestamp:
                    print("Found record older than cutoff date. Stopping.")
                    # Assuming records are returned in descending order (newest first)
                    # We can stop here.
                    return all_records

                # Only accepted records (Status 12)
                # If you want to include others, remove the check.
                # User asked for "Accepted status's problem and id"
                if status != 12:
                    continue

                submit_time_str = datetime.datetime.fromtimestamp(submit_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                rec = {
                    "problem_id": problem.get("pid"),
                    "problem_title": problem.get("title"),
                    "status": "Accepted",  # We only keep status 12
                    "time": submit_time_str,
                }
                all_records.append(rec)
                print(
                    f"Found AC: {rec['time']} - {rec['problem_id']} - {rec['problem_title']}"
                )

            count = records_data.get("count", 0)
            per_page = records_data.get("perPage", 20)

            if params["page"] * per_page >= count:
                print("Reached end of records.")
                break

            params["page"] += 1
            time.sleep(1)

        except Exception as e:
            print(f"Request error: {e}")
            break

    return all_records


if __name__ == "__main__":
    print("Please manually enter your Luogu cookies (Current session only).")
    print(
        "You can find them in your browser developer tools (F12) -> Application -> Cookies."
    )

    client_id_input = input("Enter __client_id: ").strip()
    uid_input = input("Enter _uid: ").strip()

    if client_id_input and uid_input:
        cookies = {"__client_id": client_id_input, "_uid": uid_input}
    else:
        print("Cookies not provided. Exiting.")
        sys.exit(1)

    target_users = []

    # Try to load users from uids.xlsx using shared utility
    uid_map = load_uid_map(UIDS_FILE)
    if uid_map:
        target_users = list(uid_map.keys())
        print(f"Loaded {len(target_users)} users from {UIDS_FILE}")

    if not target_users:
        if len(sys.argv) > 1:
            target_users = sys.argv[1:]
        else:
            print("No users found in uids.xlsx and no arguments provided.")
            print("No users to scrape. Exiting.")
            sys.exit(0)

    # Simple input for date
    min_date_input = input(
        "Enter earliest date (YYYY-MM-DD) or press Enter for all: "
    ).strip()

    for user_id in target_users:
        print(f"\n{'='*30}")
        print(f"Starting scrape for user {user_id}...")
        records = get_records(
            user_id,
            cookies=cookies,
            min_date=min_date_input if min_date_input else None,
        )

        print(f"Total AC records collected for {user_id}: {len(records)}")

        if records:
            # Ensure json directory exists
            ensure_dir(JSON_DIR)

            filename = os.path.join(JSON_DIR, f"{user_id}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            print(f"Saved to {filename}")
        print(f"{'='*30}\n")

    input("Scraping completed. Press Enter to exit...")
