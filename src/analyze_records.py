import os
import json
import pandas as pd
from config import JSON_DIR, OUTPUT_FILE, UIDS_FILE
from utils import ensure_dir, load_uid_map, apply_excel_styles


def analyze_to_excel(json_dir, output_file):
    if not os.path.exists(json_dir):
        print(f"Directory {json_dir} not found.")
        return

    json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]

    if not json_files:
        print("No JSON files found in the directory.")
        return

    frames = []

    # Sort files to ensure deterministic order (e.g. by UID)
    json_files.sort()

    # Load UID map
    uid_map = load_uid_map(UIDS_FILE)

    data_frames = []

    for i, json_file in enumerate(json_files):
        uid = os.path.splitext(json_file)[0]
        file_path = os.path.join(json_dir, json_file)

        # Get name from valid map, fallback to UID if not found
        user_name = uid_map.get(uid, uid)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {json_file}: {e}")
            continue

        if not data:
            continue

        # Create DataFrame from list of dicts
        df = pd.DataFrame(data)

        # Ensure correct columns exist
        desired_cols = ["problem_id", "problem_title", "status", "time"]

        # Filter and reorder columns, handle missing cols with reindex
        df = df.reindex(columns=desired_cols)

        # Deduplication logic: Keep the earliest record for each problem_id
        if not df.empty and "time" in df.columns and "problem_id" in df.columns:
            # Sort by time ascending (earliest first)
            df = df.sort_values(by="time", ascending=True)
            # Drop duplicates based on problem_id, keeping the first (earliest)
            df = df.drop_duplicates(subset=["problem_id"], keep="first")
            # Reset index
            df = df.reset_index(drop=True)

        # Handle NaNs for cleaner output
        df = df.fillna("")

        # Split time into Date and Time using vectorized string operations
        # Assuming 'time' format is "YYYY-MM-DD HH:MM:SS"
        time_split = df["time"].astype(str).str.split(" ", n=1, expand=True)
        df["AC日期"] = time_split[0]
        df["AC时间"] = time_split[1] if time_split.shape[1] > 1 else ""
        
        # Add metadata columns
        df["序号"] = range(1, len(df) + 1)
        df["UID"] = uid
        df["姓名"] = user_name
        df["题号"] = df["problem_id"]
        df["题目名称"] = df["problem_title"]
        
        # Select final columns in order
        final_df = df[["序号", "UID", "姓名", "题号", "题目名称", "AC日期", "AC时间"]]
        data_frames.append(final_df)

    if not data_frames:
        print(
            "No valid data found from JSON files. Generating empty report with summary."
        )
        result = pd.DataFrame(columns=["序号", "UID", "姓名", "题号", "题目名称", "AC日期", "AC时间"])
    else:
        # Create final DataFrame
        result = pd.concat(data_frames, ignore_index=True)

    # Ensure UID is string for consistent matching
    result["UID"] = result["UID"].astype(str)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    ensure_dir(output_dir)

    # Save to Excel with multiple sheets
    print(f"Saving to {output_file}...")
    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Sheet 1: Detailed records
            # Convert UID back to numeric for display if possible, or keep as string
            display_result = result.copy()
            try:
                display_result["UID"] = pd.to_numeric(display_result["UID"])
            except:
                pass
            display_result.to_excel(writer, index=False, sheet_name="详细记录")

            # Sheet 2: Summary
            # Optimized counting using pandas value_counts
            ac_counts = result["UID"].value_counts()

            summary_data = []
            for uid_str, name in uid_map.items():
                # uid_map keys are already strings from load_uid_map
                count = ac_counts.get(uid_str, 0)
                summary_data.append({"UID": uid_str, "姓名": name, "AC数量": count})

            summary_df = pd.DataFrame(summary_data)

            # Sort by AC count descending
            summary_df = summary_df.sort_values(by="AC数量", ascending=False)

            # Add Sequence Number column
            summary_df.insert(0, "序号", range(1, len(summary_df) + 1))

            # Convert UID to numeric for display
            try:
                summary_df["UID"] = pd.to_numeric(summary_df["UID"])
            except:
                pass

            summary_df.to_excel(writer, index=False, sheet_name="做题统计")

        print("Done.")
        apply_excel_styles(output_file)
    except PermissionError:
        print(f"Error: Permission denied. Please close {output_file} if it is open.")
    except Exception as e:
        print(f"Error saving Excel file: {e}")


if __name__ == "__main__":
    analyze_to_excel(JSON_DIR, OUTPUT_FILE)
