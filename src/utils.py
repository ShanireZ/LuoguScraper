import os
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter


def ensure_dir(directory):
    """Ensures that a directory exists, creating it if necessary."""
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
            print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")


def load_uid_map(file_path):
    """Loads UID to Name mapping from an Excel file."""
    uid_map = {}
    if not os.path.exists(file_path):
        print(f"Warning: UID map file not found at {file_path}")
        return uid_map

    try:
        uid_df = pd.read_excel(file_path)
        # Normalize column names
        uid_df.columns = [c.lower() for c in uid_df.columns]
        if "uid" in uid_df.columns and "name" in uid_df.columns:
            # Ensure strings for matching
            uid_df["uid"] = uid_df["uid"].astype(str)
            uid_map = dict(zip(uid_df["uid"], uid_df["name"]))
        else:
            print(f"Warning: Columns 'uid' and 'name' not found in {file_path}")
    except Exception as e:
        print(f"Error reading UID map from {file_path}: {e}")
    
    return uid_map


def apply_excel_styles(filename):
    """
    Applies custom styles to the Excel file:
    - Font: Microsoft YaHei, 12pt
    - Alignment: Center
    - Borders: All sides thin for cells with content
    - Header: Bold
    - Fixed row height (18)
    - Auto-fit column width
    """
    try:
        wb = load_workbook(filename)

        for ws in wb.worksheets:
            # Define styles
            font_normal = Font(name="Microsoft YaHei", size=12)
            font_bold = Font(name="Microsoft YaHei", size=12, bold=True)
            alignment_style = Alignment(horizontal="center", vertical="center")
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )

            # Iterate over all cells
            for row in ws.iter_rows():
                for cell in row:
                    cell.alignment = alignment_style
                    cell.border = thin_border

                    if cell.row == 1:
                        cell.font = font_bold
                    else:
                        cell.font = font_normal

            # Set row height
            for i in range(1, ws.max_row + 1):
                ws.row_dimensions[i].height = 18

            # Auto-fit columns
            for column_cells in ws.columns:
                length = 0
                for cell in column_cells:
                    if cell.value:
                        try:
                            # Handle CJK characters being wider
                            cell_str = str(cell.value)
                            cell_len = 0
                            for char in cell_str:
                                if ord(char) > 127:
                                    cell_len += 1.8  # Adjusted for CJK width
                                else:
                                    cell_len += 1.1  # Adjusted for Latin width with 12pt font
                            length = max(length, cell_len)
                        except:
                            length = max(length, len(str(cell.value)) * 1.1)

                col_letter = get_column_letter(column_cells[0].column)
                
                # Special handling for "题目名称" (Problem Title)
                # Ensure we have enough buffer and prevent it from being too narrow
                if str(column_cells[0].value) == "题目名称":
                     # Increase buffer specifically for titles
                     # Cap at 80 to prevent massive width
                     ws.column_dimensions[col_letter].width = min(length + 8, 80)
                else:
                     ws.column_dimensions[col_letter].width = length + 4

        wb.save(filename)
        print("Styles applied successfully.")

    except Exception as e:
        print(f"Error applying styles: {e}")
