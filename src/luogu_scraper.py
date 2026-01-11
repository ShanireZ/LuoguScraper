import requests
import json
import time
import urllib.parse
import os
import sys
import datetime
import getpass
from typing import List, Dict, Any, Optional, cast
from bs4 import BeautifulSoup, Tag
from fake_useragent import UserAgent

from config import JSON_DIR, LUOGU_BASE_URL, UIDS_FILE
from utils import ensure_dir, load_uid_map


def get_records(
    user_id: str,
    cookies: Optional[Dict[str, str]] = None,
    min_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    获取用户的所有提交记录。

    参数:
        user_id (str): 用户ID。
        cookies (dict): 登录 cookies。
        min_date (str): 最早日期（格式为 YYYY-MM-DD）。

    返回:
        list: 包含所有 Accepted 提交的记录列表。
    """
    base_url = LUOGU_BASE_URL
    params: Dict[str, Any] = {"user": user_id, "page": 1}

    # Convert min_date (YYYY-MM-DD) to timestamp
    min_timestamp: Optional[float] = None
    if min_date:
        try:
            dt = datetime.datetime.strptime(min_date, "%Y-%m-%d")
            min_timestamp = dt.timestamp()
            print(f"Filtering records after: {min_date}")
        except ValueError:
            print("Invalid date format. Ignoring min_date.")

    # Use a session for connection pooling and cookie persistence
    session = requests.Session()
    # Use cached UserAgent to avoid potential network issues
    try:
        # UserAgent might not have type stubs for use_cache_server
        ua = UserAgent(use_cache_server=False).random  # type: ignore
    except Exception:
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    session.headers.update(
        {
            "User-Agent": ua,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/webp,*/*;q=0.8"
            ),
            "Referer": f"https://www.luogu.com.cn/record/list?user={user_id}",
        }
    )

    if cookies:
        print("Using provided cookies.")
        # requests Cookies update expects dict or CookieJar, strict check might fail on Optional
        session.cookies.update(cookies)  # type: ignore

    all_records: List[Dict[str, Any]] = []

    while True:
        print(f"Fetching page {params['page']}...")
        try:
            response = session.get(base_url, params=params, timeout=15)

            if response.status_code != 200:
                print(f"Failed to retrieve page: Status code {response.status_code}")
                if len(response.text) < 500:
                    print(response.text)
                break

            data: Any = None
            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback to HTML parsing
                try:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Try to find specific script containing the data
                    def _fe_injection_filter(t: Any) -> bool:
                        return t is not None and "window._feInjection" in str(t)

                    # By pass bs4 overloaded find checking for callable
                    script: Any = soup.find("script", string=_fe_injection_filter)  # type: ignore
                    if script:
                        # Cast to Tag to access .text property safely
                        script_tag = cast(Tag, script)
                        start: int = script_tag.text.find('decodeURIComponent("')
                        if start != -1:
                            start += len('decodeURIComponent("')
                            end: int = script_tag.text.find('")', start)
                            if end != -1:
                                encoded_str: str = script_tag.text[start:end]
                                data = json.loads(urllib.parse.unquote(encoded_str))
                except Exception as inner_e:
                    print(f"HTML parsing attempts failed: {inner_e}")

            if not isinstance(data, dict):
                print("Could not retrieve valid data dictionary.")
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

            # At this point, data is guaranteed to be a dict
            data_dict = cast(Dict[str, Any], data)

            if data_dict.get("code") != 200 and "currentData" not in data_dict:
                # Check if it's the standard Luogu API response structure
                if "currentData" not in data_dict:
                    print(f"API Error or unexpected structure: {str(data_dict)[:100]}")
                    break

            current_data: Dict[str, Any] = data_dict.get("currentData", {})

            if not current_data:
                # Sometimes data is directly the struct in some APIs
                print("No currentData found in JSON response.")
                current_data = data_dict

            records_data = current_data.get("records", {})
            records = cast(List[Dict[str, Any]], records_data.get("result", []))

            if not records:
                print("No records found on this page.")
                break

            for record in records:
                problem: Dict[str, Any] = record.get("problem", {})
                status: Any = record.get("status")
                # score variable is likely int, default to 0
                score: int = record.get("score", 0)
                submit_time: int = record.get("submitTime", 0)

                # Filter by date
                if min_timestamp is not None and submit_time < min_timestamp:
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

                rec: Dict[str, Any] = {
                    "problem_id": problem.get("pid"),
                    "problem_title": problem.get("title"),
                    "status": "Accepted",  # We only keep status 12
                    "score": score,
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

        except requests.exceptions.Timeout:
            print(f"Request timed out while fetching page {params['page']}.")
            break
        except requests.exceptions.RequestException as e:
            print(f"Network request error on page {params['page']}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error on page {params['page']}: {e}")
            # Optionally import traceback and print_exc() for debugging
            # import traceback; traceback.print_exc()
            break

    return all_records


if __name__ == "__main__":
    print("Please manually enter your Luogu cookies (Current session only).")
    print(
        "You can find them in your browser developer tools (F12) -> Application -> Cookies."
    )
    print("Alternatively, set LUOGU_CLIENT_ID and LUOGU_UID environment variables.")

    client_id_input: Optional[str] = os.environ.get("LUOGU_CLIENT_ID")
    if not client_id_input:
        client_id_input = getpass.getpass("Enter __client_id (hidden input): ").strip()

    if not client_id_input:
        print("Invalid __client_id. Exiting.")
        sys.exit(1)

    uid_input: Optional[str] = os.environ.get("LUOGU_UID")
    if not uid_input:
        uid_input = input("Enter _uid: ").strip()

    if not uid_input:
        print("Invalid _uid. Exiting.")
        sys.exit(1)

    cookies: Dict[str, str] = {"__client_id": client_id_input, "_uid": uid_input}

    target_users: List[str] = []

    # Try to load users from uids.xlsx using shared utility
    uid_map: Dict[str, str] = load_uid_map(UIDS_FILE)
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
