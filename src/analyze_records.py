import json
import logging
from typing import Dict, List, Any, cast
import pandas as pd
from pathlib import Path
from config import JSON_DIR, OUTPUT_FILE, UIDS_FILE
from utils import ensure_dir, load_uid_map, apply_excel_styles

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def process_user_data(file_path: Path, uid: str, user_name: str) -> pd.DataFrame:
    """Read JSON file and process it into a cleaned DataFrame."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path.name}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error reading {file_path.name}: {e}")
        return pd.DataFrame()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Ensure correct columns exist
    desired_cols = ["problem_id", "problem_title", "status", "time"]
    df = df.reindex(columns=desired_cols)

    # Deduplication: Keep the earliest record for each problem_id
    if not df.empty and "time" in df.columns and "problem_id" in df.columns:
        df = df.sort_values(by="time", ascending=True)
        df = df.drop_duplicates(subset=["problem_id"], keep="first")
        df = df.reset_index(drop=True)

    # Handle NaNs
    # Pylance Strict mode may warn about unknown types from fillna
    df = cast(pd.DataFrame, df.fillna(""))  # type: ignore

    # Split time into Date and Time
    if not df.empty and "time" in df.columns:
        time_split = df["time"].astype(str).str.split(" ", n=1, expand=True)
        df["AC日期"] = time_split[0]
        df["AC时间"] = time_split[1] if time_split.shape[1] > 1 else ""
    else:
        df["AC日期"] = ""
        df["AC时间"] = ""

    # Add metadata
    df["序号"] = range(1, len(df) + 1)
    df["UID"] = uid
    df["姓名"] = user_name
    df["题号"] = df["problem_id"]
    df["题目名称"] = df["problem_title"]

    return df[["序号", "UID", "姓名", "题号", "题目名称", "AC日期", "AC时间"]]


def analyze_to_excel(json_dir: str, output_file: str) -> None:
    """
    Main function to analyze records and save to Excel.
    """
    json_path = Path(json_dir)
    if not json_path.exists():
        logger.warning(f"Directory {json_dir} not found.")
        return

    # Use pathlib for iteration
    json_files = sorted([f for f in json_path.iterdir() if f.name.endswith(".json")])

    if not json_files:
        logger.warning("No JSON files found in the directory.")
        return

    # Load UID map
    uid_map: Dict[str, str] = load_uid_map(UIDS_FILE)

    data_frames: List[pd.DataFrame] = []

    for json_file in json_files:
        uid = json_file.stem  # safer than os.path.splitext
        user_name = uid_map.get(uid, uid)

        df = process_user_data(json_file, uid, user_name)
        if not df.empty:
            data_frames.append(df)

    # Initialize result variable
    result: pd.DataFrame

    if not data_frames:
        logger.warning("No valid data found. Generating empty report.")
        result = pd.DataFrame(
            columns=["序号", "UID", "姓名", "题号", "题目名称", "AC日期", "AC时间"]
        )
    else:
        result = pd.concat(data_frames, ignore_index=True)

    # Ensure UID is string
    result["UID"] = result["UID"].astype(str)

    # Ensure output directory exists
    output_path = Path(output_file)
    ensure_dir(str(output_path.parent))

    logger.info(f"Saving to {output_file}...")
    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Sheet 1: Detailed records
            result.to_excel(writer, index=False, sheet_name="详细记录")  # type: ignore

            # Sheet 2: Summary
            # Count ACs per UID (using string UIDs for grouping)
            ac_counts: pd.Series = result["UID"].value_counts()

            summary_data: List[Dict[str, Any]] = []
            for uid_str, name in uid_map.items():
                count = ac_counts.get(uid_str, 0)
                summary_data.append({"UID": uid_str, "姓名": name, "AC数量": count})

            summary_df: pd.DataFrame = pd.DataFrame(summary_data)
            summary_df = summary_df.sort_values(by="AC数量", ascending=False)

            # Numeric index for Summary
            # Use 'Any' cast for the value argument to bypass strict checks if necessary, or just ignore
            row_indices: List[int] = list(range(1, len(summary_df) + 1))
            summary_df.insert(0, "序号", cast(Any, row_indices))  # type: ignore

            summary_df.to_excel(writer, index=False, sheet_name="做题统计")  # type: ignore

        logger.info("Done.")
        apply_excel_styles(output_file)

    except PermissionError:
        logger.error(f"Permission denied: Please close {output_file} if it is open.")
    except Exception as e:
        logger.error(f"Error saving Excel file: {e}")


if __name__ == "__main__":
    analyze_to_excel(JSON_DIR, OUTPUT_FILE)
