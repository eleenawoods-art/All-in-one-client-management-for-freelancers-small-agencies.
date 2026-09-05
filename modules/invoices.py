```python
import streamlit as st
from datetime import date
import sqlite3

from modules.database import get_connection


def get_clients():
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, name, company
        FROM clients
        ORDER BY name
        """
    ).fetchall()

    conn.close()

    return rows


def get_invoices():
    conn = get_connection()

    rows = conn.execute(
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

    conn.close()

    return rows


def get_invoice_items(invoice_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, service, quantity, price
        FROM invoice_items
        WHERE invoice_id = ?
        ORDER BY id
        """,
        (invoice_id,),
    ).fetchall()

    conn.close()

    return rows


def generate_invoice_number():
    conn = get_connection()

    row = conn.execute(
        """
        SELECT id
        FROM invoices
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    if row:
        next_id = int(row["id"]) + 1
    else:
        next_id = 1

    return f"INV-{date.today().year}-{next_id:04d}"


def calculate_invoice_total(items, tax_percent, discount):
    subtotal = 0.0

    for item in items:
        subtotal += (
            float(item["quantity"])
            * float(item["price"])
        )

    tax_amount = subtotal * (
        float(tax_percent) / 100
    )

    total = subtotal + tax_amount - float(discount)

    if total < 0:
        total = 0.0

    return subtotal, tax_amount, total


def create_invoice(
    client_id,
    invoice_number,
    due_date,
    tax_percent,
    discount,
    status,
    items,
):
    subtotal, tax_amount, total = (
        calculate_invoice_total(
            items,
            tax_percent,
            discount,
        )
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
                tax_amount,
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
                    item["service"],
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


def update_status(invoice_id, status):
    conn = get_connection()

    conn.execute(
        """
        UPDATE invoices
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            invoice_id,
        ),
    )

    conn.commit()
    conn.close()


def delete_invoice(invoice_id):
    conn = get_connection()

    conn.execute(
        """
        DELETE FROM invoices
        WHERE id = ?
        """,
        (invoice_id,),
    )

    conn.commit()
    conn.close()


def render_create_invoice():

    clients = get_clients()

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

    remove_index = None

    for index, item in enumerate(
        st.session_state.invoice_items
    ):

        col1, col2, col3, col4 = st.columns(
            [4, 1, 2, 0.6]
        )

        with col1:

            item["service"] = st.text_input(
                "Service",
                value=item["service"],
                key=f"invoice_service_{index}",
                placeholder="Website Design",
            )

        with col2:

            item["quantity"] = st.number_input(
                "Qty",
                min_value=1,
                value=int(item["quantity"]),
                step=1,
                key=f"invoice_qty_{index}",
            )

        with col3:

            item["price"] = st.number_input(
                "Price",
                min_value=0.0,
                value=float(item["price"]),
                step=10.0,
                format="%.2f",
                key=f"invoice_price_{index}",
            )

        with col4:

            st.write("")

            if st.button(
                "🗑️",
                key=f"invoice_remove_{index}",
            ):
                remove_index = index

    if remove_index is not None:

        if len(
            st.session_state.invoice_items
        ) > 1:

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

    valid_items = []

    for item in st.session_state.invoice_items:

        if item["service"].strip():

            valid_items.append(item)

    subtotal, tax_amount, total = (
        calculate_invoice_total(
            valid_items,
            tax_percent,
            discount,
        )
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
            f"${tax_amount:,.2f}",
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

            st.error(
                "Invoice number is required."
            )

            return

        if not valid_items:

            st.error(
                "Please add at least one service."
            )

            return

        try:

            invoice_id = create_invoice(
                client_id=client_labels[
                    selected_client
                ],
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

            st.success(
                f"Invoice {invoice_number} created successfully."
            )

            st.session_state.selected_invoice = (
                invoice_id
            )

            st.rerun()

        except sqlite3.IntegrityError:

            st.error(
                "This invoice number already exists. "
                "Please use another number."
            )

        except Exception as error:

            st.error(
                f"Could not create invoice: {error}"
            )


def render_invoice_list():

    invoices = get_invoices()

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

    for invoice in invoices:

        invoice_number = (
            invoice["invoice_number"] or ""
        )

        client_name = (
            invoice["client_name"] or ""
        )

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

                if invoice["status"] == "Paid":

                    st.success("Paid")

                elif invoice["status"] == "Overdue":

                    st.error("Overdue")

                elif invoice["status"] == "Draft":

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


def render_invoice_details(invoice_id):

    conn = get_connection()

    invoice = conn.execute(
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

    conn.close()

    if not invoice:

        st.error("Invoice not found.")

        return

    items = get_invoice_items(invoice_id)

    if st.button("← Back to Invoices"):

        st.session_state.pop(
            "selected_invoice",
            None,
        )

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

        total = (
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
                f"${total:,.2f}"
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

            update_status(
                invoice_id,
                "Paid",
            )

            st.rerun()

    with b:

        if st.button(
            "⏳ Mark Unpaid",
            use_container_width=True,
        ):

            update_status(
                invoice_id,
                "Unpaid",
            )

            st.rerun()

    with c:

        if st.button(
            "⚠️ Mark Overdue",
            use_container_width=True,
        ):

            update_status(
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
        st.session_state.get(
            "confirm_invoice_delete"
        )
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

                delete_invoice(invoice_id)

                st.session_state.pop(
                    "selected_invoice",
                    None,
                )

                st.session_state.pop(
                    "confirm_invoice_delete",
                    None,
                )

                st.success(
                    "Invoice deleted."
                )

                st.rerun()

        with y:

            if st.button(
                "Cancel",
                use_container_width=True,
            ):

                st.session_state.pop(
                    "confirm_invoice_delete",
                    None,
                )

                st.rerun()


def render_invoices_page():

    st.title("💰 Invoices")

    st.caption(
        "Create invoices, track payments, and manage "
        "outstanding balances."
    )

    if st.session_state.get("selected_invoice"):

        render_invoice_details(
            st.session_state.selected_invoice
        )

        return

    invoices = get_invoices()

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
```
