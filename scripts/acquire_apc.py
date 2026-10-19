import argparse
import os

import pandas as pd
from huggingface_hub import hf_hub_download


REPO = "somemone/ac-transit-apc"


def main():
    parser = argparse.ArgumentParser(
        description="Download real AC Transit APC data from Hugging Face."
    )

    parser.add_argument(
        "--year",
        default="2019",
        help="Dataset year partition, e.g. 2019",
    )

    parser.add_argument(
        "--month",
        default="02",
        help="Dataset month partition, e.g. 02",
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=100000,
        help="Number of rows to keep from the downloaded partition.",
    )

    parser.add_argument(
        "--out",
        default="backend/data/raw/ac_transit_apc.csv",
        help="Output CSV path.",
    )

    args = parser.parse_args()

    # Hugging Face dataset uses month=2, not month=02.
    month = str(int(args.month))

    filename = (
        f"year={args.year}/"
        f"month={month}/"
        f"data_0.parquet"
    )

    print("=" * 70)
    print("SAFE-BUS AI — AC TRANSIT APC DATA ACQUISITION")
    print("=" * 70)
    print(f"Dataset : {REPO}")
    print(f"Partition: {filename}")
    print(f"Rows     : {args.rows:,}")
    print()

    print("Downloading real APC dataset partition...")

    try:
        parquet_path = hf_hub_download(
            repo_id=REPO,
            filename=filename,
            repo_type="dataset",
        )
    except Exception as error:
        print()
        print("ERROR: Could not download the APC dataset.")
        print(error)
        raise SystemExit(1)

    print("Download completed.")
    print(f"Cached file: {parquet_path}")
    print()

    print("Reading Parquet data...")

    try:
        df = pd.read_parquet(parquet_path)
    except Exception as error:
        print()
        print("ERROR: Could not read the Parquet file.")
        print(error)
        raise SystemExit(1)

    print(f"Available rows: {len(df):,}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Keep only the requested number of rows.
    df = df.head(args.rows).copy()

    # Expected fields for SAFE-BUS AI.
    required_columns = [
        "route_id",
        "stop_id",
        "event_timestamp",
        "boardings",
        "alightings",
        "passenger_load",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("ERROR: Required APC columns are missing:")
        for column in missing_columns:
            print(f"  - {column}")

        print()
        print("Available columns:")
        for column in df.columns:
            print(f"  - {column}")

        raise SystemExit(1)

    # Create output directory.
    output_directory = os.path.dirname(args.out)

    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    # Save real APC data.
    df.to_csv(args.out, index=False)

    print("=" * 70)
    print("SUCCESS")
    print("=" * 70)
    print(f"Real APC rows written : {len(df):,}")
    print(f"Output file           : {args.out}")
    print()

    print("SAFE-BUS AI APC columns:")
    print()

    for column in required_columns:
        print(f"  ✓ {column}")

    print()
    print("Dataset acquisition completed successfully.")


if __name__ == "__main__":
    main()
