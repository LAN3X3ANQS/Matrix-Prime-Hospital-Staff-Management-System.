from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)


def export_to_pdf(
    file_path,
    title,
    headers,
    rows
):
    file_path = Path(file_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=landscape(A4)
    )

    data = [
        headers
    ]

    data.extend(rows)

    table = Table(
        data,
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.grey
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.black
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "LEFT"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                8
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, 0),
                8
            )
        ])
    )

    document.build([
        Table(
            [[title]],
            colWidths=[700]
        ),
        table
    ])

    return file_path