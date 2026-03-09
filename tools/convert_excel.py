"""Utility to convert the original Excel dataset into JSON for use as test data."""
import pandas as pd
import json
import sys


def excel_to_json(xlsx_path: str, out_json: str):
    df = pd.read_excel(xlsx_path)
    # Drop unnamed index cols
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    records = df.to_dict(orient='records')
    with open(out_json, 'w') as f:
        json.dump(records, f, indent=2, default=str)
    print(f"wrote {len(records)} records to {out_json}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("usage: python convert_excel.py INPUT.xlsx OUTPUT.json")
        sys.exit(1)
    excel_to_json(sys.argv[1], sys.argv[2])
