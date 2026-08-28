import streamlit as st

from modules.database import get_connection


# =========================================================
# CLIENT HELPERS
# =========================================================

STATUS_OPTIONS = [
    "Lead",
    "Active",
    "Completed",
]


def get_clients(search="", status="All"):
    connection = get_connection()

    query = """
        SELECT *
        FROM clients
        WHERE 1 = 1
    """

    params = []

    if search:
        query += """
            AND (
                name LIKE ?
                OR company LIKE ?
                OR email LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend(
            [
                search_value,
                search_value,
                search_value,
            ]
        )

    if status != "All":
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"

    rows = connection.execute(
        query,
        params,
    ).fetchall()

    connection.close()

    return rows


def add_client(
    name,
    company,
    email,
    phone,
    website,
    status,
    notes,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO clients (
            name,
            company,
            email,
            phone,
            website,
            status,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            company,
            email,
            phone,
            website,
            status,
            notes,
        ),
    )

    connection.commit()
    connection.close()


def update_client(
    client_id,
    name,
    company,
    email,
    phone,
    website,
    status,
    notes,
):
    connection = get_connection()

    connection.execute(
        """
        UPDATE clients
        SET
            name = ?,
            company = ?,
            email = ?,
            phone = ?,
            website = ?,
            status = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            name,
            company,
            email,
            phone,
            website,
            status,
            notes,
            client_id,
        ),
    )

    connection.commit()
    connection.close()


def delete_client(client_id):
    connection = get_connection()

    # Remove related records first.
    connection.execute(
        "DELETE FROM tasks WHERE project_id IN "
        "(SELECT id FROM projects WHERE client_id = ?)",
        (client_id,),
    )

    connection.execute(
        "DELETE FROM projects WHERE client_id = ?",
        (client_id,),
    )

    connection.execute(
        "DELETE FROM proposal_items WHERE proposal_id IN "
        "(SELECT id FROM proposals WHERE client_id = ?)",
        (client_id,),
    )

    connection.execute(
        "DELETE FROM proposals WHERE client_id = ?",
        (client_id,),
    )

    connection.execute(
        "DELETE FROM invoice_items WHERE invoice_id IN "
        "(SELECT id FROM invoices WHERE client_id = ?)",
        (client_id,),
    )

    connection.execute(
        "DELETE FROM invoices WHERE client_id = ?",
        (client_id,),
    )

    connection.execute(
        "DELETE FROM clients WHERE id = ?",
        (client_id,),
    )

    connection.commit()
    connection.close()


# =========================================================
# ADD CLIENT FORM
# =========================================================

def render_add_client():

    with st.form("add_client_form", clear_on_submit=True):

        st.subheader("Add New Client")

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Client Name *",
                placeholder="John Smith",
            )

            company = st.text_input(
                "Company",
                placeholder="Acme Inc.",
            )

            email = st.text_input(
                "Email",
                placeholder="john@example.com",
            )

            phone = st.text_input(
                "Phone",
                placeholder="+1 555 123 4567",
            )

        with col2:

            website = st.text_input(
                "Website",
                placeholder="https://example.com",
            )

            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
            )

            notes = st.text_area(
                "Notes",
                placeholder="Add useful notes about this client...",
                height=125,
            )

        submitted = st.form_submit_button(
            "Create Client",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not name.strip():
                st.error("Client name is required.")
                return

            add_client(
                name=name.strip(),
                company=company.strip(),
                email=email.strip(),
                phone=phone.strip(),
                website=website.strip(),
                status=status,
                notes=notes.strip(),
            )

            st.success(
                f"Client '{name.strip()}' created successfully."
            )

            st.rerun()


# =========================================================
# EDIT CLIENT
# =========================================================

def render_edit_client(client):

    client_id = client["id"]

    with st.form(
        f"edit_client_form_{client_id}"
    ):

        st.subheader("Edit Client")

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Client Name *",
                value=client["name"] or "",
            )

            company = st.text_input(
                "Company",
                value=client["company"] or "",
            )

            email = st.text_input(
                "Email",
                value=client["email"] or "",
            )

            phone = st.text_input(
                "Phone",
                value=client["phone"] or "",
            )

        with col2:

            website = st.text_input(
                "Website",
                value=client["website"] or "",
            )

            current_status = client["status"]

            status_index = (
                STATUS_OPTIONS.index(current_status)
                if current_status in STATUS_OPTIONS
                else 0
            )

            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=status_index,
            )

            notes = st.text_area(
                "Notes",
                value=client["notes"] or "",
                height=125,
            )

        save = st.form_submit_button(
            "Save Changes",
            type="primary",
            use_container_width=True,
        )

        if save:

            if not name.strip():
                st.error("Client name is required.")
                return

            update_client(
                client_id=client_id,
                name=name.strip(),
                company=company.strip(),
                email=email.strip(),
                phone=phone.strip(),
                website=website.strip(),
                status=status,
                notes=notes.strip(),
            )

            st.success("Client updated successfully.")

            st.rerun()


# =========================================================
# CLIENTS PAGE
# =========================================================

def render_clients_page():

    st.title("Clients")

    st.markdown(
        '<div class="subtitle">'
        "Manage leads, active clients, and completed relationships."
        "</div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # TOP ACTION
    # -----------------------------------------------------

    top_left, top_right = st.columns(
        [4, 1]
    )

    with top_left:

        search = st.text_input(
            "Search clients",
            placeholder="Search by name, company or email...",
            label_visibility="collapsed",
        )

    with top_right:

        add_mode = st.button(
            "＋ Add Client",
            type="primary",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # ADD CLIENT
    # -----------------------------------------------------

    if add_mode:

        st.session_state["show_add_client"] = True

    if st.session_state.get(
        "show_add_client",
        False,
    ):

        with st.expander(
            "Create New Client",
            expanded=True,
        ):

            render_add_client()

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    filter_col1, filter_col2 = st.columns(
        [1, 3]
    )

    with filter_col1:

        status_filter = st.selectbox(
            "Status",
            ["All"] + STATUS_OPTIONS,
        )

    # -----------------------------------------------------
    # FETCH CLIENTS
    # -----------------------------------------------------

    clients = get_clients(
        search=search,
        status=status_filter,
    )

    st.markdown(
        f"**{len(clients)} client(s)**"
    )

    # -----------------------------------------------------
    # EMPTY STATE
    # -----------------------------------------------------

    if not clients:

        st.info(
            "No clients found. Add your first client "
            "to start building your workspace."
        )

        return

    # -----------------------------------------------------
    # CLIENT CARDS
    # -----------------------------------------------------

    for client in clients:

        with st.container(
            border=True
        ):

            col_info, col_status, col_actions = st.columns(
                [3.5, 1.5, 1]
            )

            with col_info:

                company = client["company"]

                if company:

                    st.markdown(
                        f"### {client['name']}"
                    )

                    st.caption(
                        f"🏢 {company}"
                    )

                else:

                    st.markdown(
                        f"### {client['name']}"
                    )

                if client["email"]:

                    st.caption(
                        f"✉️ {client['email']}"
                    )

            with col_status:

                status = client["status"]

                if status == "Active":
                    st.success(status)

                elif status == "Lead":
                    st.warning(status)

                else:
                    st.info(status)

            with col_actions:

                edit_key = (
                    f"edit_client_{client['id']}"
                )

                delete_key = (
                    f"delete_client_{client['id']}"
                )

                if st.button(
                    "Edit",
                    key=edit_key,
                    use_container_width=True,
                ):

                    st.session_state[
                        "editing_client"
                    ] = client["id"]

                    st.rerun()

                if st.button(
                    "Delete",
                    key=delete_key,
                    use_container_width=True,
                ):

                    st.session_state[
                        "deleting_client"
                    ] = client["id"]

                    st.rerun()

            # -------------------------------------------------
            # EDIT PANEL
            # -------------------------------------------------

            if (
                st.session_state.get(
                    "editing_client"
                )
                == client["id"]
            ):

                st.divider()

                render_edit_client(client)

                if st.button(
                    "Cancel",
                    key=f"cancel_edit_{client['id']}",
                ):

                    del st.session_state[
                        "editing_client"
                    ]

                    st.rerun()

            # -------------------------------------------------
            # DELETE CONFIRMATION
            # -------------------------------------------------

            if (
                st.session_state.get(
                    "deleting_client"
                )
                == client["id"]
            ):

                st.warning(
                    "Deleting this client will also remove "
                    "their projects, tasks, proposals and invoices."
                )

                confirm_col1, confirm_col2 = st.columns(2)

                with confirm_col1:

                    if st.button(
                        "Yes, Delete",
                        type="primary",
                        key=f"confirm_delete_{client['id']}",
                        use_container_width=True,
                    ):

                        delete_client(
                            client["id"]
                        )

                        st.session_state.pop(
                            "deleting_client",
                            None,
                        )

                        st.success(
                            "Client deleted successfully."
                        )

                        st.rerun()

                with confirm_col2:

                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_{client['id']}",
                        use_container_width=True,
                    ):

                        st.session_state.pop(
                            "deleting_client",
                            None,
                        )

                        st.rerun()
