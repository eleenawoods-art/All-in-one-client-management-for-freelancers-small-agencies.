```python
import streamlit as st
from datetime import date

from modules.database import (
    init_db,
    get_dashboard_stats,
    get_connection,
)
from modules.clients import render_clients_page
from modules.projects import render_projects_page
from modules.tasks import render_tasks_page
from modules.proposals import render_proposals_page


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="ClientFlow AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE
# =========================================================

init_db()


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "📊 Dashboard"

if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = [
        {
            "service": "",
            "quantity": 1,
            "price": 0.0,
        }
    ]

if "selected_invoice" not in st.session_state:
    st.session_state.selected_invoice = None

if "confirm_invoice_delete" not in st.session_state:
    st.session_state.confirm_invoice_delete = None


# =========================================================
# INVOICE DATABASE FUNCTIONS
# =========================================================

def invoice_get_clients():
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT id, name, company
            FROM clients
            ORDER BY name
            """
        ).fetchall()
    finally:
        conn.close()


def invoice_get_all():
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT
                invoices.id,
                invoices.invoice_number,
                invoices.due_date,
                invoices.subtotal,
                invoices.tax,
                invoices.discount,
                invoices.total,
                invoices.status,
                invoices.created_at,
                clients.name AS client_name,
                clients.company AS company
            FROM invoices
            LEFT JOIN clients
                ON invoices.client_id = clients.id
            ORDER BY invoices.id DESC
            """
        ).fetchall()
    finally:
        conn.close()


def invoice_get_items(invoice_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT id, service, quantity, price
            FROM invoice_items
            WHERE invoice_id = ?
            ORDER BY id
            """,
            (invoice_id,),
        ).fetchall()
    finally:
        conn.close()


def invoice_get_one(invoice_id):
    conn = get_connection()

    try:
        return conn.execute(
            """
            SELECT
                invoices.*,
                clients.name AS client_name,
                clients.company,
                clients.email,
                clients.phone
            FROM invoices
            LEFT JOIN clients
                ON invoices.client_id = clients.id
            WHERE invoices.id = ?
            """,
            (invoice_id,),
        ).fetchone()
    finally:
        conn.close()


def invoice_generate_number():
    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT id
            FROM invoices
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    finally:
        conn.close()

    if row:
        next_id = int(row["id"]) + 1
    else:
        next_id = 1

    return f"INV-{date.today().year}-{next_id:04d}"


def invoice_calculate(items, tax_percent, discount):
    subtotal = 0.0

    for item in items:
        subtotal += (
            float(item["quantity"])
            * float(item["price"])
        )

    tax = subtotal * (
        float(tax_percent) / 100
    )

    total = subtotal + tax - float(discount)

    if total < 0:
        total = 0.0

    return subtotal, tax, total


def invoice_create(
    client_id,
    invoice_number,
    due_date,
    tax_percent,
    discount,
    status,
    items,
):
    subtotal, tax, total = invoice_calculate(
        items,
        tax_percent,
        discount,
    )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO invoices (
                client_id,
                invoice_number,
                due_date,
                subtotal,
                tax,
                discount,
                total,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client_id,
                invoice_number,
                str(due_date),
                subtotal,
                tax,
                float(discount),
                total,
                status,
            ),
        )

        invoice_id = cursor.lastrowid

        for item in items:
            cursor.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id,
                    service,
                    quantity,
                    price
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item["service"].strip(),
                    int(item["quantity"]),
                    float(item["price"]),
                ),
            )

        conn.commit()

        return invoice_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def invoice_update_status(invoice_id, status):
    conn = get_connection()

    try:
        conn.execute(
            """
            UPDATE invoices
            SET status = ?
            WHERE id = ?
            """,
            (status, invoice_id),
        )

        conn.commit()

    finally:
        conn.close()


def invoice_delete(invoice_id):
    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM invoices
            WHERE id = ?
            """,
            (invoice_id,),
        )

        conn.commit()

    finally:
        conn.close()


# =========================================================
# CREATE INVOICE
# =========================================================

def render_create_invoice():
    clients = invoice_get_clients()

    if not clients:
        st.warning(
            "Please add a client before creating an invoice."
        )

        if st.button(
            "👥 Go to Clients",
            use_container_width=True,
        ):
            st.session_state.page = "👥 Clients"
            st.rerun()

        return

    st.subheader("Create New Invoice")

    client_labels = {}

    for client in clients:
        label = client["name"]

        if client["company"]:
            label += f" — {client['company']}"

        client_labels[label] = client["id"]

    selected_client = st.selectbox(
        "Client",
        list(client_labels.keys()),
    )

    invoice_number = st.text_input(
        "Invoice Number",
        value=invoice_generate_number(),
    )

    due_date = st.date_input(
        "Due Date",
        value=date.today(),
    )

    st.markdown("### Invoice Items")

    remove_index = None

    for index, item in enumerate(
        st.session_state.invoice_items
    ):
        col1, col2, col3, col4 = st.columns(
            [4, 1, 2, 0.7]
        )

        with col1:
            service = st.text_input(
                "Service",
                value=item["service"],
                key=f"invoice_service_{index}",
                placeholder="Website Design",
            )

            item["service"] = service

        with col2:
            quantity = st.number_input(
                "Qty",
                min_value=1,
                value=int(item["quantity"]),
                step=1,
                key=f"invoice_qty_{index}",
            )

            item["quantity"] = quantity

        with col3:
            price = st.number_input(
                "Price",
                min_value=0.0,
                value=float(item["price"]),
                step=10.0,
                format="%.2f",
                key=f"invoice_price_{index}",
            )

            item["price"] = price

        with col4:
            st.write("")

            if st.button(
                "🗑️",
                key=f"invoice_remove_{index}",
            ):
                remove_index = index

    if remove_index is not None:
        if len(st.session_state.invoice_items) > 1:
            st.session_state.invoice_items.pop(
                remove_index
            )
            st.rerun()

    if st.button(
        "➕ Add Item",
        use_container_width=True,
    ):
        st.session_state.invoice_items.append(
            {
                "service": "",
                "quantity": 1,
                "price": 0.0,
            }
        )

        st.rerun()

    st.markdown("### Payment")

    tax_percent = st.number_input(
        "Tax (%)",
        min_value=0.0,
        value=0.0,
        step=1.0,
    )

    discount = st.number_input(
        "Discount",
        min_value=0.0,
        value=0.0,
        step=10.0,
    )

    status = st.selectbox(
        "Status",
        [
            "Draft",
            "Unpaid",
            "Paid",
            "Overdue",
        ],
    )

    valid_items = [
        item
        for item in st.session_state.invoice_items
        if item["service"].strip()
    ]

    subtotal, tax, total = invoice_calculate(
        valid_items,
        tax_percent,
        discount,
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Subtotal",
            f"${subtotal:,.2f}",
        )

    with c2:
        st.metric(
            "Tax",
            f"${tax:,.2f}",
        )

    with c3:
        st.metric(
            "Total",
            f"${total:,.2f}",
        )

    if st.button(
        "💾 Create Invoice",
        type="primary",
        use_container_width=True,
    ):
        if not invoice_number.strip():
            st.error("Invoice number is required.")
            return

        if not valid_items:
            st.error(
                "Please add at least one service."
            )
            return

        try:
            invoice_id = invoice_create(
                client_id=client_labels[selected_client],
                invoice_number=invoice_number.strip(),
                due_date=due_date,
                tax_percent=tax_percent,
                discount=discount,
                status=status,
                items=valid_items,
            )

            st.session_state.invoice_items = [
                {
                    "service": "",
                    "quantity": 1,
                    "price": 0.0,
                }
            ]

            st.session_state.selected_invoice = (
                invoice_id
            )

            st.rerun()

        except Exception as error:
            if "UNIQUE constraint failed" in str(error):
                st.error(
                    "This invoice number already exists. "
                    "Please use another number."
                )
            else:
                st.error(
                    f"Could not create invoice: {error}"
                )


# =========================================================
# INVOICE LIST
# =========================================================

def render_invoice_list():
    invoices = invoice_get_all()

    if not invoices:
        st.info(
            "No invoices yet. Create your first invoice above."
        )
        return

    st.subheader("All Invoices")

    search = st.text_input(
        "🔎 Search",
        placeholder="Search invoice or client...",
    )

    status_filter = st.selectbox(
        "Status",
        [
            "All",
            "Draft",
            "Unpaid",
            "Paid",
            "Overdue",
        ],
    )

    visible = 0

    for invoice in invoices:
        invoice_number = invoice["invoice_number"] or ""
        client_name = invoice["client_name"] or ""

        search_text = (
            invoice_number
            + " "
            + client_name
        ).lower()

        if search.strip().lower() not in search_text:
            continue

        if (
            status_filter != "All"
            and invoice["status"] != status_filter
        ):
            continue

        visible += 1

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns(
                [2, 2.5, 1.3, 1.5, 1]
            )

            with c1:
                st.markdown(
                    f"**{invoice_number}**"
                )
                st.caption(
                    str(invoice["created_at"] or "")
                )

            with c2:
                st.write(
                    invoice["client_name"]
                    or "Unknown Client"
                )

                if invoice["company"]:
                    st.caption(
                        invoice["company"]
                    )

            with c3:
                status = invoice["status"]

                if status == "Paid":
                    st.success("Paid")
                elif status == "Overdue":
                    st.error("Overdue")
                elif status == "Draft":
                    st.info("Draft")
                else:
                    st.warning("Unpaid")

            with c4:
                st.markdown(
                    f"**${float(invoice['total']):,.2f}**"
                )

                st.caption(
                    f"Due: {invoice['due_date'] or 'N/A'}"
                )

            with c5:
                if st.button(
                    "View",
                    key=f"invoice_view_{invoice['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_invoice = (
                        invoice["id"]
                    )
                    st.rerun()

    if visible == 0:
        st.info("No invoices match your search/filter.")


# =========================================================
# INVOICE DETAILS
# =========================================================

def render_invoice_details(invoice_id):
    invoice = invoice_get_one(invoice_id)

    if not invoice:
        st.error("Invoice not found.")

        if st.button("← Back to Invoices"):
            st.session_state.selected_invoice = None
            st.rerun()

        return

    items = invoice_get_items(invoice_id)

    if st.button("← Back to Invoices"):
        st.session_state.selected_invoice = None
        st.session_state.confirm_invoice_delete = None
        st.rerun()

    st.subheader(
        f"Invoice {invoice['invoice_number']}"
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Bill To")

        st.write(
            f"**{invoice['client_name'] or 'Unknown Client'}**"
        )

        if invoice["company"]:
            st.caption(invoice["company"])

        if invoice["email"]:
            st.caption(invoice["email"])

        if invoice["phone"]:
            st.caption(invoice["phone"])

    with c2:
        st.markdown("### Invoice Details")

        st.write(
            f"Invoice: **{invoice['invoice_number']}**"
        )

        st.write(
            f"Due Date: **{invoice['due_date'] or 'N/A'}**"
        )

        st.write(
            f"Status: **{invoice['status']}**"
        )

    st.markdown("### Services")

    for item in items:
        item_total = (
            float(item["quantity"])
            * float(item["price"])
        )

        c1, c2, c3, c4 = st.columns(
            [4, 1, 2, 2]
        )

        with c1:
            st.write(item["service"])

        with c2:
            st.write(item["quantity"])

        with c3:
            st.write(
                f"${float(item['price']):,.2f}"
            )

        with c4:
            st.write(
                f"${item_total:,.2f}"
            )

    st.divider()

    c1, c2 = st.columns(2)

    with c2:
        st.write(
            f"Subtotal: "
            f"${float(invoice['subtotal']):,.2f}"
        )

        st.write(
            f"Tax: "
            f"${float(invoice['tax']):,.2f}"
        )

        st.write(
            f"Discount: "
            f"${float(invoice['discount']):,.2f}"
        )

        st.markdown(
            f"### Total: ${float(invoice['total']):,.2f}"
        )

    st.divider()

    st.subheader("Invoice Actions")

    a, b, c, d = st.columns(4)

    with a:
        if st.button(
            "✅ Mark Paid",
            use_container_width=True,
        ):
            invoice_update_status(
                invoice_id,
                "Paid",
            )
            st.rerun()

    with b:
        if st.button(
            "⏳ Mark Unpaid",
            use_container_width=True,
        ):
            invoice_update_status(
                invoice_id,
                "Unpaid",
            )
            st.rerun()

    with c:
        if st.button(
            "⚠️ Mark Overdue",
            use_container_width=True,
        ):
            invoice_update_status(
                invoice_id,
                "Overdue",
            )
            st.rerun()

    with d:
        if st.button(
            "🗑️ Delete",
            use_container_width=True,
        ):
            st.session_state.confirm_invoice_delete = (
                invoice_id
            )
            st.rerun()

    if (
        st.session_state.confirm_invoice_delete
        == invoice_id
    ):
        st.warning(
            "This will permanently delete the invoice."
        )

        x, y = st.columns(2)

        with x:
            if st.button(
                "Yes, Delete",
                type="primary",
                use_container_width=True,
            ):
                invoice_delete(invoice_id)

                st.session_state.selected_invoice = None
                st.session_state.confirm_invoice_delete = None

                st.rerun()

        with y:
            if st.button(
                "Cancel",
                use_container_width=True,
            ):
                st.session_state.confirm_invoice_delete = None
                st.rerun()


# =========================================================
# INVOICES PAGE
# =========================================================

def render_invoices_page():
    st.title("💰 Invoices")

    st.caption(
        "Create invoices, track payments, and manage "
        "outstanding balances."
    )

    selected_invoice = st.session_state.get(
        "selected_invoice"
    )

    if selected_invoice:
        render_invoice_details(selected_invoice)
        return

    invoices = invoice_get_all()

    paid_total = sum(
        float(invoice["total"] or 0)
        for invoice in invoices
        if invoice["status"] == "Paid"
    )

    outstanding_total = sum(
        float(invoice["total"] or 0)
        for invoice in invoices
        if invoice["status"] != "Paid"
    )

    overdue_count = sum(
        1
        for invoice in invoices
        if invoice["status"] == "Overdue"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        with st.container(border=True):
            st.metric(
                "📄 Total Invoices",
                len(invoices),
            )

    with c2:
        with st.container(border=True):
            st.metric(
                "✅ Paid",
                f"${paid_total:,.2f}",
            )

    with c3:
        with st.container(border=True):
            st.metric(
                "💰 Outstanding",
                f"${outstanding_total:,.2f}",
            )

    with c4:
        with st.container(border=True):
            st.metric(
                "⚠️ Overdue",
                overdue_count,
            )

    st.write("")

    with st.expander(
        "➕ Create New Invoice",
        expanded=len(invoices) == 0,
    ):
        render_create_invoice()

    st.write("")

    render_invoice_list()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🚀 ClientFlow AI")
st.sidebar.caption(
    "Client management workspace"
)

st.sidebar.divider()

pages = [
    "📊 Dashboard",
    "👥 Clients",
    "📁 Projects",
    "✅ Tasks",
    "📄 Proposals",
    "💰 Invoices",
    "🤖 AI Assistant",
    "📈 Reports",
]

selected_page = st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(st.session_state.page),
)

st.session_state.page = selected_page


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "📊 Dashboard":

    st.title("📊 Dashboard")

    st.caption(
        "Overview of your clients, projects, tasks, "
        "proposals, and invoices."
    )

    stats = get_dashboard_stats()

    conn = get_connection()

    try:
        paid_revenue = conn.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM invoices
            WHERE status = 'Paid'
            """
        ).fetchone()[0]

        proposal_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM proposals
            """
        ).fetchone()[0]

        recent_clients = conn.execute(
            """
            SELECT name, company, created_at
            FROM clients
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        upcoming_tasks = conn.execute(
            """
            SELECT
                tasks.title,
                tasks.deadline,
                tasks.priority,
                projects.name AS project_name
            FROM tasks
            LEFT JOIN projects
                ON tasks.project_id = projects.id
            WHERE tasks.status != 'Done'
            ORDER BY
                CASE
                    WHEN tasks.deadline IS NULL
                    OR tasks.deadline = ''
                    THEN 1
                    ELSE 0
                END,
                tasks.deadline ASC
            LIMIT 5
            """
        ).fetchall()

    finally:
        conn.close()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        with st.container(border=True):
            st.metric(
                "👥 Clients",
                stats["clients"],
            )

    with c2:
        with st.container(border=True):
            st.metric(
                "📁 Active Projects",
                stats["projects"],
            )

    with c3:
        with st.container(border=True):
            st.metric(
                "✅ Pending Tasks",
                stats["tasks"],
            )

    with c4:
        with st.container(border=True):
            st.metric(
                "💰 Outstanding",
                f"${float(stats['outstanding']):,.2f}",
            )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.subheader("💵 Revenue Overview")

            st.metric(
                "Paid Revenue",
                f"${float(paid_revenue):,.2f}",
            )

            st.caption(
                "Total value of invoices marked as paid."
            )

    with c2:
        with st.container(border=True):
            st.subheader("📄 Proposals")

            st.metric(
                "Total Proposals",
                proposal_count,
            )

            st.caption(
                "Proposals currently stored in your workspace."
            )

    st.write("")

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.subheader("⏰ Upcoming Tasks")

            if upcoming_tasks:
                for task in upcoming_tasks:
                    task_title = task["title"] or "Untitled Task"
                    deadline = task["deadline"] or "No deadline"
                    project = task["project_name"] or "No project"

                    st.markdown(
                        f"**{task_title}**"
                    )

                    st.caption(
                        f"{project} • Due: {deadline} • "
                        f"Priority: {task['priority'] or 'Medium'}"
                    )

                    st.divider()
            else:
                st.info("No pending tasks.")

    with c2:
        with st.container(border=True):
            st.subheader("👥 Recent Clients")

            if recent_clients:
                for client in recent_clients:
                    name = client["name"] or "Unnamed Client"
                    company = client["company"] or "No company"

                    st.markdown(
                        f"**{name}**"
                    )

                    st.caption(company)

                    st.divider()
            else:
                st.info(
                    "No clients yet. Add your first client."
                )

    st.write("")

    with st.container(border=True):
        st.subheader("⚡ Quick Actions")

        q1, q2, q3, q4 = st.columns(4)

        with q1:
            if st.button(
                "👥 Add Client",
                use_container_width=True,
            ):
                st.session_state.page = "👥 Clients"
                st.rerun()

        with q2:
            if st.button(
                "📁 Projects",
                use_container_width=True,
            ):
                st.session_state.page = "📁 Projects"
                st.rerun()

        with q3:
            if st.button(
                "📄 Proposals",
                use_container_width=True,
            ):
                st.session_state.page = "📄 Proposals"
                st.rerun()

        with q4:
            if st.button(
                "💰 New Invoice",
                use_container_width=True,
            ):
                st.session_state.page = "💰 Invoices"
                st.rerun()


# =========================================================
# CLIENTS
# =========================================================

elif st.session_state.page == "👥 Clients":
    render_clients_page()


# =========================================================
# PROJECTS
# =========================================================

elif st.session_state.page == "📁 Projects":
    render_projects_page()


# =========================================================
# TASKS
# =========================================================

elif st.session_state.page == "✅ Tasks":
    render_tasks_page()


# =========================================================
# PROPOSALS
# =========================================================

elif st.session_state.page == "📄 Proposals":
    render_proposals_page()


# =========================================================
# INVOICES
# =========================================================

elif st.session_state.page == "💰 Invoices":
    render_invoices_page()


# =========================================================
# AI ASSISTANT
# =========================================================

elif st.session_state.page == "🤖 AI Assistant":

    st.title("🤖 AI Assistant")

    st.caption(
        "Use AI to help manage your client workspace."
    )

    with st.container(border=True):
        st.subheader("AI Workspace Assistant")

        prompt = st.text_area(
            "What would you like help with?",
            placeholder=(
                "Example: Write a follow-up message "
                "for a client who has not replied."
            ),
            height=150,
        )

        if st.button(
            "✨ Generate",
            type="primary",
            use_container_width=True,
        ):
            if prompt.strip():
                st.info(
                    "AI Assistant is ready for integration. "
                    "Connect your preferred AI provider to "
                    "generate live responses."
                )
            else:
                st.warning(
                    "Please enter a request first."
                )


# =========================================================
# REPORTS
# =========================================================

elif st.session_state.page == "📈 Reports":

    st.title("📈 Reports")

    st.caption(
        "Workspace performance and financial overview."
    )

    stats = get_dashboard_stats()

    conn = get_connection()

    try:
        total_invoices = conn.execute(
            "SELECT COUNT(*) FROM invoices"
        ).fetchone()[0]

        paid_invoices = conn.execute(
            """
            SELECT COUNT(*)
            FROM invoices
            WHERE status = 'Paid'
            """
        ).fetchone()[0]

        unpaid_invoices = conn.execute(
            """
            SELECT COUNT(*)
            FROM invoices
            WHERE status = 'Unpaid'
            """
        ).fetchone()[0]

        overdue_invoices = conn.execute(
            """
            SELECT COUNT(*)
            FROM invoices
            WHERE status = 'Overdue'
            """
        ).fetchone()[0]

        paid_revenue = conn.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM invoices
            WHERE status = 'Paid'
            """
        ).fetchone()[0]

    finally:
        conn.close()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        with st.container(border=True):
            st.metric(
                "Clients",
                stats["clients"],
            )

    with c2:
        with st.container(border=True):
            st.metric(
                "Active Projects",
                stats["projects"],
            )

    with c3:
        with st.container(border=True):
            st.metric(
                "Pending Tasks",
                stats["tasks"],
            )

    with c4:
        with st.container(border=True):
            st.metric(
                "Paid Revenue",
                f"${float(paid_revenue):,.2f}",
            )

    st.write("")

    with st.container(border=True):
        st.subheader("💰 Invoice Summary")

        r1, r2, r3, r4 = st.columns(4)

        with r1:
            st.metric(
                "Total Invoices",
                total_invoices,
            )

        with r2:
            st.metric(
                "Paid",
                paid_invoices,
            )

        with r3:
            st.metric(
                "Unpaid",
                unpaid_invoices,
            )

        with r4:
            st.metric(
                "Overdue",
                overdue_invoices,
            )

    st.write("")

    with st.container(border=True):
        st.subheader("📊 Workspace Summary")

        st.write(
            f"**Clients:** {stats['clients']}"
        )

        st.write(
            f"**Active Projects:** {stats['projects']}"
        )

        st.write(
            f"**Pending Tasks:** {stats['tasks']}"
        )

        st.write(
            f"**Outstanding Balance:** "
            f"${float(stats['outstanding']):,.2f}"
        )

        st.write(
            f"**Paid Revenue:** "
            f"${float(paid_revenue):,.2f}"
        )
```
