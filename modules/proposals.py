import streamlit as st

from modules.database import get_connection
from reports.proposal_pdf import build_proposal_pdf


PROPOSAL_STATUSES = [
    "Draft",
    "Sent",
    "Accepted",
    "Rejected",
]


# =========================================================
# CLIENTS
# =========================================================

def get_clients():

    connection = get_connection()

    clients = connection.execute(
        """
        SELECT id, name, company
        FROM clients
        ORDER BY name ASC
        """
    ).fetchall()

    connection.close()

    return clients


def client_label(client):

    if client["company"]:
        return (
            f"{client['name']} — "
            f"{client['company']}"
        )

    return client["name"]


# =========================================================
# PROPOSALS
# =========================================================

def get_proposals(
    search="",
    status="All",
):

    connection = get_connection()

    query = """
        SELECT
            proposals.*,
            clients.name AS client_name,
            clients.company AS client_company
        FROM proposals
        LEFT JOIN clients
            ON proposals.client_id = clients.id
        WHERE 1 = 1
    """

    params = []

    if search.strip():

        value = f"%{search.strip()}%"

        query += """
            AND (
                proposals.title LIKE ?
                OR proposals.description LIKE ?
                OR clients.name LIKE ?
                OR clients.company LIKE ?
            )
        """

        params.extend(
            [
                value,
                value,
                value,
                value,
            ]
        )

    if status != "All":

        query += """
            AND proposals.status = ?
        """

        params.append(status)

    query += """
        ORDER BY proposals.created_at DESC
    """

    proposals = connection.execute(
        query,
        params,
    ).fetchall()

    connection.close()

    return proposals


def get_proposal(
    proposal_id,
):

    connection = get_connection()

    proposal = connection.execute(
        """
        SELECT
            proposals.*,
            clients.name AS client_name,
            clients.company AS client_company
        FROM proposals
        LEFT JOIN clients
            ON proposals.client_id = clients.id
        WHERE proposals.id = ?
        """,
        (proposal_id,),
    ).fetchone()

    connection.close()

    return proposal


def get_proposal_items(
    proposal_id,
):

    connection = get_connection()

    items = connection.execute(
        """
        SELECT *
        FROM proposal_items
        WHERE proposal_id = ?
        ORDER BY id ASC
        """,
        (proposal_id,),
    ).fetchall()

    connection.close()

    return items


# =========================================================
# CREATE
# =========================================================

def create_proposal(
    client_id,
    title,
    description,
    timeline,
    payment_terms,
    status,
    items,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO proposals
        (
            client_id,
            title,
            description,
            timeline,
            payment_terms,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            client_id,
            title,
            description,
            timeline,
            payment_terms,
            status,
        ),
    )

    proposal_id = cursor.lastrowid

    for item in items:

        cursor.execute(
            """
            INSERT INTO proposal_items
            (
                proposal_id,
                service,
                price
            )
            VALUES (?, ?, ?)
            """,
            (
                proposal_id,
                item["service"],
                item["price"],
            ),
        )

    connection.commit()
    connection.close()


# =========================================================
# UPDATE
# =========================================================

def update_proposal(
    proposal_id,
    client_id,
    title,
    description,
    timeline,
    payment_terms,
    status,
    items,
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE proposals
        SET
            client_id = ?,
            title = ?,
            description = ?,
            timeline = ?,
            payment_terms = ?,
            status = ?
        WHERE id = ?
        """,
        (
            client_id,
            title,
            description,
            timeline,
            payment_terms,
            status,
            proposal_id,
        ),
    )

    cursor.execute(
        """
        DELETE FROM proposal_items
        WHERE proposal_id = ?
        """,
        (proposal_id,),
    )

    for item in items:

        cursor.execute(
            """
            INSERT INTO proposal_items
            (
                proposal_id,
                service,
                price
            )
            VALUES (?, ?, ?)
            """,
            (
                proposal_id,
                item["service"],
                item["price"],
            ),
        )

    connection.commit()
    connection.close()


# =========================================================
# DUPLICATE
# =========================================================

def duplicate_proposal(
    proposal_id,
):

    connection = get_connection()

    cursor = connection.cursor()

    proposal = cursor.execute(
        """
        SELECT
            client_id,
            title,
            description,
            timeline,
            payment_terms,
            status
        FROM proposals
        WHERE id = ?
        """,
        (proposal_id,),
    ).fetchone()

    if not proposal:

        connection.close()
        return None

    new_title = (
        f"{proposal['title']} "
        "(Copy)"
    )

    cursor.execute(
        """
        INSERT INTO proposals
        (
            client_id,
            title,
            description,
            timeline,
            payment_terms,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            proposal["client_id"],
            new_title,
            proposal["description"],
            proposal["timeline"],
            proposal["payment_terms"],
            "Draft",
        ),
    )

    new_proposal_id = cursor.lastrowid

    items = cursor.execute(
        """
        SELECT service, price
        FROM proposal_items
        WHERE proposal_id = ?
        ORDER BY id ASC
        """,
        (proposal_id,),
    ).fetchall()

    for item in items:

        cursor.execute(
            """
            INSERT INTO proposal_items
            (
                proposal_id,
                service,
                price
            )
            VALUES (?, ?, ?)
            """,
            (
                new_proposal_id,
                item["service"],
                item["price"],
            ),
        )

    connection.commit()
    connection.close()

    return new_proposal_id


# =========================================================
# DELETE
# =========================================================

def delete_proposal(
    proposal_id,
):

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM proposal_items
        WHERE proposal_id = ?
        """,
        (proposal_id,),
    )

    connection.execute(
        """
        DELETE FROM proposals
        WHERE id = ?
        """,
        (proposal_id,),
    )

    connection.commit()
    connection.close()



# =========================================================
# STATUS UPDATE
# =========================================================

def update_proposal_status(proposal_id, status):
    """Update only the proposal status."""
    if status not in PROPOSAL_STATUSES:
        return

    connection = get_connection()
    connection.execute(
        """
        UPDATE proposals
        SET status = ?
        WHERE id = ?
        """,
        (status, proposal_id),
    )
    connection.commit()
    connection.close()


# =========================================================
# ADD PROPOSAL
# =========================================================

def render_add_proposal():

    clients = get_clients()

    if not clients:

        st.warning(
            "Please create a client before "
            "creating a proposal."
        )

        return

    client_options = {
        client_label(client): client["id"]
        for client in clients
    }

    st.subheader(
        "Create New Proposal"
    )

    with st.form(
        "create_proposal_form"
    ):

        client_name = st.selectbox(
            "Client *",
            list(client_options.keys()),
        )

        title = st.text_input(
            "Proposal Title *",
            placeholder=(
                "e.g. Website Redesign Proposal"
            ),
        )

        description = st.text_area(
            "Project Description",
            placeholder=(
                "Describe the work and "
                "expected outcome..."
            ),
        )

        col1, col2 = st.columns(2)

        with col1:

            timeline = st.text_input(
                "Timeline",
                placeholder="e.g. 3 weeks",
            )

        with col2:

            status = st.selectbox(
                "Status",
                PROPOSAL_STATUSES,
            )

        payment_terms = st.text_input(
            "Payment Terms",
            placeholder=(
                "e.g. 50% upfront, "
                "50% on completion"
            ),
        )

        st.markdown("### Services")

        item_count = st.number_input(
            "Number of Services",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )

        items = []

        total = 0.0

        for index in range(
            int(item_count)
        ):

            col_service, col_price = (
                st.columns([3, 1])
            )

            with col_service:

                service = st.text_input(
                    f"Service {index + 1}",
                    key=(
                        f"proposal_service_"
                        f"{index}"
                    ),
                    placeholder=(
                        "e.g. Website Design"
                    ),
                )

            with col_price:

                price = st.number_input(
                    f"Price {index + 1}",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    key=(
                        f"proposal_price_"
                        f"{index}"
                    ),
                )

            if service.strip():

                items.append(
                    {
                        "service": service.strip(),
                        "price": price,
                    }
                )

                total += price

        st.markdown(
            f"### Total: ${total:,.2f}"
        )

        submitted = st.form_submit_button(
            "Create Proposal",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not title.strip():

                st.error(
                    "Proposal title is required."
                )

                return

            if not items:

                st.error(
                    "Add at least one service."
                )

                return

            create_proposal(
                client_id=client_options[
                    client_name
                ],
                title=title.strip(),
                description=description.strip(),
                timeline=timeline.strip(),
                payment_terms=(
                    payment_terms.strip()
                ),
                status=status,
                items=items,
            )

            st.session_state[
                "show_add_proposal"
            ] = False

            st.success(
                "Proposal created successfully."
            )

            st.rerun()


# =========================================================
# EDIT PROPOSAL
# =========================================================

def render_edit_proposal(
    proposal_id,
):

    proposal = get_proposal(
        proposal_id
    )

    if not proposal:

        st.error(
            "Proposal not found."
        )

        return

    clients = get_clients()

    if not clients:

        st.warning(
            "No clients available."
        )

        return

    client_options = {
        client_label(client): client["id"]
        for client in clients
    }

    current_client_label = None

    for label, client_id in client_options.items():

        if client_id == proposal["client_id"]:

            current_client_label = label
            break

    if current_client_label is None:

        current_client_label = list(
            client_options.keys()
        )[0]

    existing_items = get_proposal_items(
        proposal_id
    )

    st.subheader(
        "Edit Proposal"
    )

    with st.form(
        f"edit_proposal_form_{proposal_id}"
    ):

        client_name = st.selectbox(
            "Client *",
            list(client_options.keys()),
            index=list(
                client_options.keys()
            ).index(
                current_client_label
            ),
        )

        title = st.text_input(
            "Proposal Title *",
            value=proposal["title"] or "",
        )

        description = st.text_area(
            "Project Description",
            value=proposal["description"] or "",
        )

        col1, col2 = st.columns(2)

        with col1:

            timeline = st.text_input(
                "Timeline",
                value=proposal["timeline"] or "",
            )

        with col2:

            current_status = (
                proposal["status"]
                if proposal["status"]
                in PROPOSAL_STATUSES
                else "Draft"
            )

            status = st.selectbox(
                "Status",
                PROPOSAL_STATUSES,
                index=PROPOSAL_STATUSES.index(
                    current_status
                ),
            )

        payment_terms = st.text_input(
            "Payment Terms",
            value=(
                proposal["payment_terms"]
                or ""
            ),
        )

        st.markdown("### Services")

        default_count = max(
            1,
            min(
                10,
                len(existing_items),
            ),
        )

        item_count = st.number_input(
            "Number of Services",
            min_value=1,
            max_value=10,
            value=default_count,
            step=1,
            key=f"edit_item_count_{proposal_id}",
        )

        items = []

        total = 0.0

        for index in range(
            int(item_count)
        ):

            existing = (
                existing_items[index]
                if index < len(existing_items)
                else None
            )

            default_service = (
                existing["service"]
                if existing
                else ""
            )

            default_price = float(
                existing["price"]
                if existing
                else 0
            )

            col_service, col_price = (
                st.columns([3, 1])
            )

            with col_service:

                service = st.text_input(
                    f"Service {index + 1}",
                    value=default_service,
                    key=(
                        f"edit_service_"
                        f"{proposal_id}_"
                        f"{index}"
                    ),
                )

            with col_price:

                price = st.number_input(
                    f"Price {index + 1}",
                    min_value=0.0,
                    value=default_price,
                    step=50.0,
                    key=(
                        f"edit_price_"
                        f"{proposal_id}_"
                        f"{index}"
                    ),
                )

            if service.strip():

                items.append(
                    {
                        "service": service.strip(),
                        "price": price,
                    }
                )

                total += price

        st.markdown(
            f"### Total: ${total:,.2f}"
        )

        col_save, col_cancel = st.columns(2)

        with col_save:

            submitted = st.form_submit_button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True,
            )

        with col_cancel:

            cancelled = st.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

        if cancelled:

            st.session_state[
                "editing_proposal"
            ] = None

            st.rerun()

        if submitted:

            if not title.strip():

                st.error(
                    "Proposal title is required."
                )

                return

            if not items:

                st.error(
                    "Add at least one service."
                )

                return

            update_proposal(
                proposal_id=proposal_id,
                client_id=client_options[
                    client_name
                ],
                title=title.strip(),
                description=description.strip(),
                timeline=timeline.strip(),
                payment_terms=(
                    payment_terms.strip()
                ),
                status=status,
                items=items,
            )

            st.session_state[
                "editing_proposal"
            ] = None

            st.success(
                "Proposal updated successfully."
            )

            st.rerun()


# =========================================================
# PAGE
# =========================================================

def render_proposals_page():

    st.title("Proposals")

    st.write(
        "Create professional proposals "
        "for your clients."
    )

    st.divider()

    # -----------------------------------------------------
    # EDIT MODE
    # -----------------------------------------------------

    editing_id = st.session_state.get(
        "editing_proposal"
    )

    if editing_id:

        with st.container(
            border=True
        ):

            render_edit_proposal(
                editing_id
            )

        st.divider()

    else:

        # -------------------------------------------------
        # NEW
        # -------------------------------------------------

        if st.button(
            "＋ New Proposal",
            type="primary",
        ):

            st.session_state[
                "show_add_proposal"
            ] = True

        # -------------------------------------------------
        # FORM
        # -------------------------------------------------

        if st.session_state.get(
            "show_add_proposal",
            False,
        ):

            with st.container(
                border=True
            ):

                render_add_proposal()

            st.divider()

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    search_col, filter_col = (
        st.columns([3, 1])
    )

    with search_col:

        search = st.text_input(
            "Search proposals",
            placeholder=(
                "Search proposals or clients..."
            ),
        )

    with filter_col:

        status_filter = st.selectbox(
            "Status",
            ["All"] + PROPOSAL_STATUSES,
        )

    # -----------------------------------------------------
    # RESULTS
    # -----------------------------------------------------

    proposals = get_proposals(
        search=search,
        status=status_filter,
    )

    st.write(
        f"**{len(proposals)} proposal(s)**"
    )

    if not proposals:

        st.info(
            "No proposals found. Click "
            "**＋ New Proposal** to create "
            "your first proposal."
        )

        return

    # -----------------------------------------------------
    # CARDS
    # -----------------------------------------------------

    for proposal in proposals:

        with st.container(
            border=True
        ):

            col_info, col_status, col_actions = (
                st.columns([3, 1.2, 1.4])
            )

            # ---------------------------------------------
            # INFO
            # ---------------------------------------------

            with col_info:

                st.subheader(
                    proposal["title"]
                )

                client_text = (
                    proposal["client_name"]
                    or "No client"
                )

                if proposal["client_company"]:

                    client_text += (
                        f" • "
                        f"{proposal['client_company']}"
                    )

                st.caption(
                    f"👤 {client_text}"
                )

                if proposal["description"]:

                    st.write(
                        proposal["description"]
                    )

            # ---------------------------------------------
            # STATUS
            # ---------------------------------------------

            with col_status:

                if proposal["status"] == "Accepted":

                    st.success(
                        proposal["status"]
                    )

                elif proposal["status"] == "Rejected":

                    st.error(
                        proposal["status"]
                    )

                elif proposal["status"] == "Sent":

                    st.warning(
                        proposal["status"]
                    )

                else:

                    st.info(
                        proposal["status"]
                    )

            # ---------------------------------------------
            # ACTIONS
            # ---------------------------------------------

            with col_actions:

                if st.button(
                    "✏️ Edit",
                    key=f"edit_proposal_{proposal['id']}",
                    use_container_width=True,
                ):
                    st.session_state["editing_proposal"] = proposal["id"]
                    st.rerun()

                view_key = f"view_proposal_{proposal['id']}"
                if st.button(
                    "👁️ View",
                    key=view_key,
                    use_container_width=True,
                ):
                    st.session_state["viewing_proposal"] = (
                        None
                        if st.session_state.get("viewing_proposal") == proposal["id"]
                        else proposal["id"]
                    )
                    st.rerun()

                # Quick status workflow
                status_options = {
                    "Draft": ["Sent"],
                    "Sent": ["Accepted", "Rejected", "Draft"],
                    "Accepted": ["Sent"],
                    "Rejected": ["Draft", "Sent"],
                }
                current_status = proposal["status"] or "Draft"
                next_statuses = status_options.get(current_status, PROPOSAL_STATUSES)

                if next_statuses:
                    status_label = (
                        "📤 Mark as Sent"
                        if current_status == "Draft"
                        else "🔄 Change Status"
                    )

                    selected_status = st.selectbox(
                        status_label,
                        next_statuses,
                        key=f"status_select_{proposal['id']}",
                        label_visibility="collapsed",
                    )

                    if st.button(
                        f"Set: {selected_status}",
                        key=f"set_status_{proposal['id']}",
                        use_container_width=True,
                    ):
                        update_proposal_status(
                            proposal["id"],
                            selected_status,
                        )
                        st.success(
                            f"Proposal marked as {selected_status}."
                        )
                        st.rerun()

                if st.button(
                    "📋 Duplicate",
                    key=f"duplicate_proposal_{proposal['id']}",
                    use_container_width=True,
                ):
                    duplicate_proposal(proposal["id"])
                    st.success("Proposal duplicated.")
                    st.rerun()

                delete_key = f"confirm_delete_{proposal['id']}"

                if not st.session_state.get(delete_key, False):
                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_proposal_{proposal['id']}",
                        use_container_width=True,
                    ):
                        st.session_state[delete_key] = True
                        st.rerun()
                else:
                    st.warning("Delete this proposal?")

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:
                        if st.button(
                            "Yes",
                            key=f"confirm_yes_{proposal['id']}",
                            use_container_width=True,
                        ):
                            delete_proposal(proposal["id"])
                            st.session_state[delete_key] = False
                            if st.session_state.get("viewing_proposal") == proposal["id"]:
                                st.session_state["viewing_proposal"] = None
                            st.rerun()

                    with cancel_col:
                        if st.button(
                            "No",
                            key=f"confirm_no_{proposal['id']}",
                            use_container_width=True,
                        ):
                            st.session_state[delete_key] = False
                            st.rerun()

            # ---------------------------------------------
            # SERVICES
            # ---------------------------------------------

            items = get_proposal_items(
                proposal["id"]
            )

            total = 0.0

            if items:

                st.markdown(
                    "**Services**"
                )

                for item in items:

                    service_col, price_col = (
                        st.columns([4, 1])
                    )

                    with service_col:

                        st.write(
                            item["service"]
                        )

                    with price_col:

                        price = float(
                            item["price"] or 0
                        )

                        st.write(
                            f"${price:,.2f}"
                        )

                        total += price

                st.divider()

                total_col, amount_col = (
                    st.columns([4, 1])
                )

                with total_col:

                    st.markdown(
                        "**Total**"
                    )

                with amount_col:

                    st.markdown(
                        f"**${total:,.2f}**"
                    )

            # ---------------------------------------------
            # DETAILS
            # ---------------------------------------------

            detail_col1, detail_col2 = (
                st.columns(2)
            )

            with detail_col1:

                if proposal["timeline"]:

                    st.caption(
                        "⏱ Timeline: "
                        + str(
                            proposal["timeline"]
                        )
                    )

            with detail_col2:

                if proposal["payment_terms"]:

                    st.caption(
                        "💳 Payment: "
                        + str(
                            proposal["payment_terms"]
                        )
                    )

            # ---------------------------------------------
            # PDF
            # ---------------------------------------------

            st.divider()

            pdf_col, spacer = st.columns(
                [1.2, 3]
            )

            with pdf_col:

                pdf_data = build_proposal_pdf(
                    proposal,
                    items,
                )

                safe_title = (
                    proposal["title"]
                    .strip()
                    .replace(" ", "_")
                )

                st.download_button(
                    label="📄 Download PDF",
                    data=pdf_data,
                    file_name=(
                        f"{safe_title}_Proposal.pdf"
                    ),
                    mime="application/pdf",
                    key=(
                        f"download_proposal_"
                        f"{proposal['id']}"
                    ),
                    use_container_width=True,
                )
