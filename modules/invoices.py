```python
import sqlite3
from datetime import date, datetime

import streamlit as st

from modules.database import get_connection


# =========================================================
# HELPERS
# =========================================================

def get_clients():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT id, name, company, email
        FROM clients
        ORDER BY name ASC
        """
    ).fetchall()

    connection.close()

    return rows


def get_invoices():
    connection = get_connection()

    rows = connection.execute(
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

    connection.close()

    return rows


def get_invoice_items(invoice_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            service,
            quantity,
            price
        FROM invoice_items
        WHERE invoice_id = ?
        ORDER BY id ASC
        """,
        (invoice_id,),
    ).fetchall()

    connection.close()

    return rows


def generate_invoice_number():
    connection = get_connection()

    row = connection.execute(
        """
        SELECT id
        FROM invoices
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    next_id = 1 if row is None else int(row["id"]) + 1

    return f"INV-{datetime.now().year}-{next_id:04d}"


def calculate_total(subtotal, tax_percent, discount):
    tax_amount = subtotal * (tax_percent / 100)

    total = subtotal + tax_amount - discount

    if total < 0:
        total = 0

    return tax_amount, total


def delete_invoice(invoice_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM invoices WHERE id = ?",
        (invoice_id,),
    )

    connection.commit()
    connection.close()


def update_invoice_status(invoice_id, status):
    connection = get_connection()

    connection.execute(
        """
        UPDATE invoices
        SET status = ?
        WHERE id = ?
        """,
        (status, invoice_id),
    )

    connection.commit()
    connection.close()


def save_invoice(
    client_id,
    invoice_number,
    due_date,
    tax_percent,
    discount,
    items,
    status,
):
    connection = get_connection()

    subtotal = sum(
        float(item["quantity"]) * float(item["price"])
        for item in items
    )

    tax_amount, total = calculate_total(
        subtotal,
        tax_percent,
        discount,
    )

    cursor = connection.cursor()

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
            due_date,
            subtotal,
            tax_amount,
            discount,
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
                item["service"],
                int(item["quantity"]),
                float(item["price"]),
            ),
        )

    connection.commit()
    connection.close()

    return invoice_id


# =========================================================
# INVOICE PREVIEW
# =========================================================

def render_invoice_preview(invoice, items):

    st.markdown("---")

    st.subheader(
        f"Invoice {invoice['invoice_number']}"
    )

    left, right = st.columns(2)

    with left:

        st.markdown("### Bill To")

        st.write(
            f"**{invoice['client_name'] or 'Unknown Client'}**"
        )

        if invoice["company"]:
            st.caption(invoice["company"])

    with right:

        st.markdown("### Invoice Details")

        st.write(
            f"**Invoice:** {invoice['invoice_number']}"
        )

        st.write(
            f"**Due Date:** {invoice['due_date'] or 'Not set'}"
        )

        st.write(
            f"**Status:** {invoice['status']}"
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

    summary1, summary2 = st.columns(2)

    with summary2:

        st.write(
            f"**Subtotal:** "
            f"${float(invoice['subtotal']):,.2f}"
        )

        st.write(
            f"**Tax:** "
            f"${float(invoice['tax']):,.2f}"
        )

        st.write(
            f"**Discount:** "
            f"${float(invoice['discount']):,.2f}"
        )

        st.markdown(
            f"### Total: ${float(invoice['total']):,.2f}"
        )


# =========================================================
# CREATE INVOICE
# =========================================================

def render_create_invoice():

    clients = get_clients()

    if not clients:

        st.warning(
            "You need at least one client before "
            "creating an invoice."
        )

        if st.button(
            "👥 Go to Clients",
            use_container_width=True,
        ):
            st.session_state.page = "👥 Clients"
            st.rerun()

        return

    st.subheader("Create New Invoice")

    client_options = {}

    for client in clients:

        label = client["name"]

        if client["company"]:
            label += f" — {client['company']}"

        client_options[label] = client["id"]

    selected_client = st.selectbox(
        "Client",
        list(client_options.keys()),
    )

    invoice_number = st.text_input(
        "Invoice Number",
        value=generate_invoice_number(),
    )

    due_date = st.date_input(
        "Due Date",
        value=date.today(),
    )

    st.markdown("### Invoice Items")

    if "invoice_items" not in st.session_state:
        st.session_state.invoice_items = [
            {
                "service": "",
                "quantity": 1,
                "price": 0.0,
            }
        ]

    items_to_remove = []

    for index, item in enumerate(
        st.session_state.invoice_items
    ):

        c1, c2, c3, c4 = st.columns(
            [4, 1.2, 2, 0.7]
        )

        with c1:

            item["service"] = st.text_input(
                "Service",
                value=item["service"],
                key=f"service_{index}",
                placeholder="Website design",
            )

        with c2:

            item["quantity"] = st.number_input(
                "Qty",
                min_value=1,
                value=int(item["quantity"]),
                step=1,
                key=f"quantity_{index}",
            )

        with c3:

            item["price"] = st.number_input(
                "Price",
                min_value=0.0,
                value=float(item["price"]),
                step=10.0,
                format="%.2f",
                key=f"price_{index}",
            )

        with c4:

            st.write("")

            if st.button(
                "🗑️",
                key=f"remove_{index}",
            ):

                items_to_remove.append(index)

    for index in reversed(items_to_remove):

        if len(
            st.session_state.invoice_items
        ) > 1:

            st.session_state.invoice_items.pop(index)

            st.rerun()

    if st.button(
        "➕ Add Another Item",
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
            "Unpaid",
            "Paid",
            "Overdue",
            "Draft",
        ],
    )

    # -----------------------------------------------------
    # TOTAL PREVIEW
    # -----------------------------------------------------

    subtotal = sum(
        float(item["quantity"])
        * float(item["price"])
        for item in st.session_state.invoice_items
    )

    tax_amount, total = calculate_total(
        subtotal,
        tax_percent,
        discount,
    )

    st.divider()

    a, b, c = st.columns(3)

    with a:
        st.metric(
            "Subtotal",
            f"${subtotal:,.2f}",
        )

    with b:
        st.metric(
            "Tax",
            f"${tax_amount:,.2f}",
        )

    with c:
        st.metric(
            "Total",
            f"${total:,.2f}",
        )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    if st.button(
        "💾 Create Invoice",
        type="primary",
        use_container_width=True,
    ):

        valid_items = []

        for item in st.session_state.invoice_items:

            service = str(
                item["service"]
            ).strip()

            quantity = int(
                item["quantity"]
            )

            price = float(
                item["price"]
            )

            if service:

                valid_items.append(
                    {
                        "service": service,
                        "quantity": quantity,
                        "price": price,
                    }
                )

        if not valid_items:

            st.error(
                "Please add at least one service."
            )

            return

        try:

            invoice_id = save_invoice(
                client_id=client_options[
                    selected_client
                ],
                invoice_number=invoice_number.strip(),
                due_date=str(due_date),
                tax_percent=tax_percent,
                discount=discount,
                items=valid_items,
                status=status,
            )

            st.session_state.invoice_items = [
                {
                    "service": "",
                    "quantity": 1,
                    "price": 0.0,
                }
            ]

            st.success(
                f"Invoice {invoice_number} created successfully."
            )

            st.session_state.selected_invoice = invoice_id

            st.rerun()

        except sqlite3.IntegrityError:

            st.error(
                "That invoice number already exists. "
                "Please use a different invoice number."
            )

        except Exception as error:

            st.error(
                f"Unable to create invoice: {error}"
            )


# =========================================================
# INVOICE LIST
# =========================================================

def render_invoice_list():

    invoices = get_invoices()

    if not invoices:

        st.info(
            "No invoices yet. "
            "Create your first invoice above."
        )

        return

    st.subheader("All Invoices")

    search = st.text_input(
        "🔎 Search invoices",
        placeholder="Search by invoice number or client...",
    )

    status_filter = st.selectbox(
        "Filter by status",
        [
            "All",
            "Paid",
            "Unpaid",
            "Overdue",
            "Draft",
        ],
    )

    filtered = []

    for invoice in invoices:

        search_text = (
            f"{invoice['invoice_number'] or ''} "
            f"{invoice['client_name'] or ''} "
            f"{invoice['company'] or ''}"
        ).lower()

        if search.strip().lower() not in search_text:
            continue

        if (
            status_filter != "All"
            and invoice["status"] != status_filter
        ):
            continue

        filtered.append(invoice)

    if not filtered:

        st.info(
            "No invoices match your filters."
        )

        return

    for invoice in filtered:

        with st.container(border=True):

            c1, c2, c3, c4, c5 = st.columns(
                [2, 2.5, 1.2, 1.5, 1.5]
            )

            with c1:

                st.markdown(
                    f"**{invoice['invoice_number']}**"
                )

                st.caption(
                    invoice["created_at"] or ""
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
                    st.success(status)

                elif status == "Overdue":
                    st.error(status)

                elif status == "Draft":
                    st.info(status)

                else:
                    st.warning(status)

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
                    key=f"view_{invoice['id']}",
                    use_container_width=True,
                ):

                    st.session_state.selected_invoice = (
                        invoice["id"]
                    )

                    st.rerun()


# =========================================================
# INVOICE DETAILS
# =========================================================

def render_invoice_details(invoice_id):

    connection = get_connection()

    invoice = connection.execute(
        """
        SELECT
            invoices.*,
            clients.name AS client_name,
            clients.company,
            clients.email,
            clients.phone,
            clients.website
        FROM invoices
        LEFT JOIN clients
            ON invoices.client_id = clients.id
        WHERE invoices.id = ?
        """,
        (invoice_id,),
    ).fetchone()

    connection.close()

    if not invoice:

        st.error("Invoice not found.")

        return

    items = get_invoice_items(invoice_id)

    if st.button("← Back to Invoices"):

        del st.session_state.selected_invoice

        st.rerun()

    render_invoice_preview(
        invoice,
        items,
    )

    st.markdown("---")

    st.subheader("Invoice Actions")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        if st.button(
            "✅ Mark Paid",
            use_container_width=True,
        ):

            update_invoice_status(
                invoice_id,
                "Paid",
            )

            st.success(
                "Invoice marked as paid."
            )

            st.rerun()

    with c2:

        if st.button(
            "⏳ Mark Unpaid",
            use_container_width=True,
        ):

            update_invoice_status(
                invoice_id,
                "Unpaid",
            )

            st.success(
                "Invoice marked as unpaid."
            )

            st.rerun()

    with c3:

        if st.button(
            "⚠️ Mark Overdue",
            use_container_width=True,
        ):

            update_invoice_status(
                invoice_id,
                "Overdue",
            )

            st.warning(
                "Invoice marked as overdue."
            )

            st.rerun()

    with c4:

        if st.button(
            "🗑️ Delete Invoice",
            use_container_width=True,
        ):

            st.session_state.confirm_delete_invoice = (
                invoice_id
            )

            st.rerun()

    if (
        st.session_state.get(
            "confirm_delete_invoice"
        )
        == invoice_id
    ):

        st.warning(
            "Are you sure you want to permanently "
            "delete this invoice?"
        )

        d1, d2 = st.columns(2)

        with d1:

            if st.button(
                "Yes, Delete",
                type="primary",
                use_container_width=True,
            ):

                delete_invoice(invoice_id)

                del st.session_state[
                    "confirm_delete_invoice"
                ]

                del st.session_state[
                    "selected_invoice"
                ]

                st.success(
                    "Invoice deleted successfully."
                )

                st.rerun()

        with d2:

            if st.button(
                "Cancel",
                use_container_width=True,
            ):

                del st.session_state[
                    "confirm_delete_invoice"
                ]

                st.rerun()


# =========================================================
# MAIN INVOICE PAGE
# =========================================================

def render_invoices_page():

    st.title("💰 Invoices")

    st.caption(
        "Create invoices, track payments, and manage "
        "your outstanding client balances."
    )

    # -----------------------------------------------------
    # SELECTED INVOICE
    # -----------------------------------------------------

    selected_invoice = st.session_state.get(
        "selected_invoice"
    )

    if selected_invoice:

        render_invoice_details(
            selected_invoice
        )

        return

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    invoices = get_invoices()

    total_invoices = len(invoices)

    paid_amount = sum(
        float(invoice["total"] or 0)
        for invoice in invoices
        if invoice["status"] == "Paid"
    )

    outstanding_amount = sum(
        float(invoice["total"] or 0)
        for invoice in invoices
        if invoice["status"] != "Paid"
    )

    overdue_count = sum(
        1
        for invoice in invoices
        if invoice["status"] == "Overdue"
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        with st.container(border=True):

            st.metric(
                "📄 Total Invoices",
                total_invoices,
            )

    with s2:

        with st.container(border=True):

            st.metric(
                "✅ Paid",
                f"${paid_amount:,.2f}",
            )

    with s3:

        with st.container(border=True):

            st.metric(
                "💰 Outstanding",
                f"${outstanding_amount:,.2f}",
            )

    with s4:

        with st.container(border=True):

            st.metric(
                "⚠️ Overdue",
                overdue_count,
            )

    st.write("")

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    with st.expander(
        "➕ Create New Invoice",
        expanded=not bool(invoices),
    ):

        render_create_invoice()

    st.write("")

    # -----------------------------------------------------
    # LIST
    # -----------------------------------------------------

    render_invoice_list()
```
