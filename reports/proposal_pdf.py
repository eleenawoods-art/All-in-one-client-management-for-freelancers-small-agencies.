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
)


# =========================================================
# COLORS
# =========================================================

INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6B7280")
BORDER = colors.HexColor("#E5E7EB")
LIGHT = colors.HexColor("#F8FAFC")
DARK_LIGHT = colors.HexColor("#F1F5F9")
ACCENT = colors.HexColor("#4F46E5")


# =========================================================
# FOOTER
# =========================================================

def draw_footer(canvas, document):

    canvas.saveState()

    width, height = A4

    # Footer line
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        13 * mm,
        width - 18 * mm,
        13 * mm,
    )

    # Left footer
    canvas.setFont(
        "Helvetica",
        7.5,
    )

    canvas.setFillColor(MUTED)

    canvas.drawString(
        18 * mm,
        8 * mm,
        "ClientFlow AI • Client Management Workspace",
    )

    # Page number
    canvas.drawRightString(
        width - 18 * mm,
        8 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# =========================================================
# PDF BUILDER
# =========================================================

def build_proposal_pdf(
    proposal,
    items,
):
    """
    Generate a premium ClientFlow AI proposal PDF.

    Returns:
        BytesIO object containing the generated PDF.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=proposal["title"],
        author="ClientFlow AI",
        subject="Client Proposal",
    )

    styles = getSampleStyleSheet()

    # =====================================================
    # STYLES
    # =====================================================

    brand_style = ParagraphStyle(
        "Brand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=INK,
    )

    brand_subtitle = ParagraphStyle(
        "BrandSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=MUTED,
    )

    eyebrow_style = ParagraphStyle(
        "Eyebrow",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=ACCENT,
        tracking=1,
    )

    title_style = ParagraphStyle(
        "ProposalTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=25,
        leading=30,
        textColor=INK,
        spaceBefore=4,
        spaceAfter=8,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=INK,
        spaceBefore=15,
        spaceAfter=7,
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=15,
        textColor=INK,
    )

    muted_style = ParagraphStyle(
        "Muted",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=MUTED,
    )

    right_style = ParagraphStyle(
        "Right",
        parent=normal_style,
        alignment=TA_RIGHT,
    )

    right_muted = ParagraphStyle(
        "RightMuted",
        parent=muted_style,
        alignment=TA_RIGHT,
    )

    total_style = ParagraphStyle(
        "Total",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=INK,
        alignment=TA_RIGHT,
    )

    # =====================================================
    # STORY
    # =====================================================

    story = []

    # =====================================================
    # HEADER
    # =====================================================

    header = Table(
        [
            [
                Paragraph(
                    "CLIENTFLOW AI",
                    brand_style,
                ),
                Paragraph(
                    "PROPOSAL",
                    right_muted,
                ),
            ],
            [
                Paragraph(
                    "Client Management Workspace",
                    brand_subtitle,
                ),
                Paragraph(
                    datetime.now().strftime(
                        "%B %d, %Y"
                    ),
                    right_muted,
                ),
            ],
        ],
        colWidths=[
            110 * mm,
            55 * mm,
    ],
    )

    header.setStyle(
        TableStyle(
            [
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
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(header)

    story.append(
        Spacer(
            1,
            12,
        )
    )

    # Accent divider
    accent_line = Table(
        [[""]],
        colWidths=[165 * mm],
        rowHeights=[1.5 * mm],
    )

    accent_line.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    ACCENT,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    story.append(accent_line)

    story.append(
        Spacer(
            1,
            14,
        )
    )

    # =====================================================
    # PROPOSAL TITLE
    # =====================================================

    story.append(
        Paragraph(
            "PROJECT PROPOSAL",
            eyebrow_style,
        )
    )

    story.append(
        Paragraph(
            str(proposal["title"]),
            title_style,
        )
    )

    # =====================================================
    # CLIENT / STATUS CARD
    # =====================================================

    client_name = (
        proposal["client_name"]
        or "Client"
    )

    client_company = (
        proposal["client_company"]
        or ""
    )

    client_lines = (
        f"<b>{client_name}</b>"
    )

    if client_company:
        client_lines += (
            f"<br/>{client_company}"
        )

    status = (
        proposal["status"]
        or "Draft"
    )

    client_card = Table(
        [
            [
                Paragraph(
                    "<font color='#6B7280'>PREPARED FOR</font><br/>"
                    + client_lines,
                    normal_style,
                ),
                Paragraph(
                    "<font color='#6B7280'>STATUS</font><br/>"
                    f"<b>{status}</b>",
                    right_style,
                ),
            ]
        ],
        colWidths=[
            120 * mm,
            45 * mm,
        ],
    )

    client_card.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    BORDER,
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
                    11,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(client_card)

    # =====================================================
    # PROJECT OVERVIEW
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
                ).replace(
                    "\n",
                    "<br/>",
                ),
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

    rows = [
        [
            Paragraph(
                "<b>SERVICE</b>",
                muted_style,
            ),
            Paragraph(
                "<b>PRICE</b>",
                right_muted,
            ),
        ]
    ]

    total = 0.0

    for item in items:

        price = float(
            item["price"] or 0
        )

        total += price

        rows.append(
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

    rows.append(
        [
            Paragraph(
                "<b>GRAND TOTAL</b>",
                normal_style,
            ),
            Paragraph(
                f"${total:,.2f}",
                total_style,
            ),
        ]
    )

    services_table = Table(
        rows,
        colWidths=[
            120 * mm,
            45 * mm,
        ],
        repeatRows=1,
    )

    services_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    DARK_LIGHT,
                ),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, 0),
                    0.7,
                    BORDER,
                ),
                (
                    "LINEBELOW",
                    (0, 1),
                    (-1, -2),
                    0.4,
                    BORDER,
                ),
                (
                    "LINEABOVE",
                    (0, -1),
                    (-1, -1),
                    1,
                    INK,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
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

    story.append(services_table)

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
                    str(
                        proposal["timeline"]
                    ),
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
                42 * mm,
                123 * mm,
            ],
        )

        details_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        LIGHT,
                    ),
                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        BORDER,
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

        story.append(details_table)

    # =====================================================
    # CLOSING
    # =====================================================

    story.append(
        Spacer(
            1,
            20,
        )
    )

    closing = Table(
        [
            [
                Paragraph(
                    "<b>Thank you for considering this proposal.</b>"
                    "<br/>"
                    "<font color='#6B7280'>"
                    "We look forward to working with you."
                    "</font>",
                    normal_style,
                )
            ]
        ],
        colWidths=[
            165 * mm
        ],
    )

    closing.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    11,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10,
                ),
            ]
        )
    )

    story.append(closing)

    # =====================================================
    # BUILD
    # =====================================================

    document.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )

    buffer.seek(0)

    return buffer
