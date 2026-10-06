import csv
from pathlib import Path


def export_to_csv(
    file_path,
    headers,
    rows
):
    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with file_path.open(
        mode="w",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)

        writer.writerow(headers)

        writer.writerows(rows)

    return file_path