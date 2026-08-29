from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


def build_proposal_pdf(
    proposal,
    items,
):
    """
    Generate a professional PDF proposal.

    Returns:
        BytesIO containing the PDF.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=proposal["title"],
        author="ClientFlow AI",
    )

    styles = getSampleStyleSheet()

    brand_style = ParagraphStyle(
        "Brand",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#777777"),
    )

    title_style = ParagraphStyle(
        "ProposalTitle",
        parent=styles["Heading1"],
        fontSize=22,
        leading=28,
        spaceBefore=8,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        spaceBefore=12,
        spaceAfter=7,
        fontName="Helvetica-Bold",
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=15,
    )

    right_style = ParagraphStyle(
        "Right",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    story = []

    # =====================================================
    # HEADER
    # =====================================================

    story.append(
        Paragraph(
            "CLIENTFLOW AI",
            brand_style,
        )
    )

    story.append(
        Paragraph(
            "Client Management Workspace",
            small_style,
        )
    )

    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "PROPOSAL",
            small_style,
        )
    )

    story.append(
        Paragraph(
            proposal["title"],
            title_style,
        )
    )

    # =====================================================
    # CLIENT INFORMATION
    # =====================================================

    client_name = (
        proposal["client_name"]
        or "Client"
    )

    client_company = (
        proposal["client_company"]
        or ""
    )

    client_text = client_name

    if client_company:
        client_text += f"<br/>{client_company}"

    client_table = Table(
        [
            [
                Paragraph(
                    "<b>PREPARED FOR</b><br/>"
                    + client_text,
                    normal_style,
                ),
                Paragraph(
                    "<b>STATUS</b><br/>"
                    + str(proposal["status"]),
                    right_style,
                ),
            ]
        ],
        colWidths=[
            120 * mm,
            45 * mm,
        ],
    )

    client_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F5F7FA"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D9DEE5"),
                ),
                (
                    "INNERPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    story.append(client_table)

    # =====================================================
    # DESCRIPTION
    # =====================================================

    if proposal["description"]:

        story.append(
            Paragraph(
                "PROJECT OVERVIEW",
                section_style,
            )
        )

        story.append(
            Paragraph(
                str(
                    proposal["description"]
                ).replace("\n", "<br/>"),
                normal_style,
            )
        )

    # =====================================================
    # SERVICES
    # =====================================================

    story.append(
        Paragraph(
            "SERVICES & PRICING",
            section_style,
        )
    )

    service_rows = [
        [
            Paragraph(
                "<b>Service</b>",
                normal_style,
            ),
            Paragraph(
                "<b>Price</b>",
                right_style,
            ),
        ]
    ]

    total = 0.0

    for item in items:

        price = float(
            item["price"] or 0
        )

        total += price

        service_rows.append(
            [
                Paragraph(
                    str(item["service"]),
                    normal_style,
                ),
                Paragraph(
                    f"${price:,.2f}",
                    right_style,
                ),
            ]
        )

    service_rows.append(
        [
            Paragraph(
                "<b>TOTAL</b>",
                normal_style,
            ),
            Paragraph(
                f"<b>${total:,.2f}</b>",
                right_style,
            ),
        ]
    )

    service_table = Table(
        service_rows,
        colWidths=[
            120 * mm,
            45 * mm,
    ],
    )

    service_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#F1F3F6"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -2),
                    0.4,
                    colors.HexColor("#D9DEE5"),
                ),
                (
                    "LINEABOVE",
                    (0, -1),
                    (-1, -1),
                    1,
                    colors.HexColor("#222222"),
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(service_table)

    # =====================================================
    # PROJECT DETAILS
    # =====================================================

    details = []

    if proposal["timeline"]:

        details.append(
            [
                Paragraph(
                    "<b>Timeline</b>",
                    normal_style,
                ),
                Paragraph(
                    str(proposal["timeline"]),
                    normal_style,
                ),
            ]
        )

    if proposal["payment_terms"]:

        details.append(
            [
                Paragraph(
                    "<b>Payment Terms</b>",
                    normal_style,
                ),
                Paragraph(
                    str(
                        proposal["payment_terms"]
                    ),
                    normal_style,
                ),
            ]
        )

    if details:

        story.append(
            Paragraph(
                "PROJECT DETAILS",
                section_style,
            )
        )

        details_table = Table(
            details,
            colWidths=[
                40 * mm,
                125 * mm,
            ],
        )

        details_table.setStyle(
            TableStyle(
                [
                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#E0E3E7"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        story.append(details_table)

    # =====================================================
    # FOOTER CONTENT
    # =====================================================

    story.append(Spacer(1, 22))

    story.append(
        Paragraph(
            "Thank you for considering this proposal.",
            normal_style,
        )
    )

    story.append(Spacer(1, 20))

    generated = datetime.now().strftime(
        "%B %d, %Y"
    )

    story.append(
        Paragraph(
            f"Generated by ClientFlow AI • {generated}",
            small_style,
        )
    )

    # =====================================================
    # BUILD
    # =====================================================

    document.build(story)

    buffer.seek(0)

    return buffer
