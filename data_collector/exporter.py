
import json
import pandas as pd

from config import CSV_FILE


def export_to_csv(records):

    rows = []

    for record in records:

        row = record.model_dump()

        row["additional_information"] = json.dumps(
            row["additional_information"],
            ensure_ascii=False
        )

        rows.append(row)

    columns = [
        "title",
        "summarized_data",
        "source_url",
        "additional_information"
    ]

    df = pd.DataFrame(
        rows,
        columns=columns
    )

    df.to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nCSV export completed!")
    print(f"Total records: {len(df)}")
    print(f"File: {CSV_FILE.resolve()}")
