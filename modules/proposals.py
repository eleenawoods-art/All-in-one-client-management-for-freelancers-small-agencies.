import streamlit as st

from modules.database import get_connection


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
        return f"{client['name']} — {client['company']}"

    return client["name"]


# =========================================================
# PROPOSALS
# =========================================================

def get_proposals(search="", status="All"):

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


def get_proposal_items(proposal_id):

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
# CREATE PROPOSAL
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
# DELETE PROPOSAL
# =========================================================

def delete_proposal(proposal_id):

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
# ADD PROPOSAL FORM
# =========================================================

def render_add_proposal():

    clients = get_clients()

    if not clients:

        st.warning(
            "Please create a client before creating a proposal."
        )

        return

    client_options = {
        client_label(client): client["id"]
        for client in clients
    }

    st.subheader("Create New Proposal")

    with st.form("create_proposal_form"):

        client_name = st.selectbox(
            "Client *",
            list(client_options.keys()),
        )

        title = st.text_input(
            "Proposal Title *",
            placeholder="e.g. Website Redesign Proposal",
        )

        description = st.text_area(
            "Project Description",
            placeholder="Describe the work and expected outcome...",
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
            placeholder="e.g. 50% upfront, 50% on completion",
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

        for index in range(int(item_count)):

            col_service, col_price = st.columns(
                [3, 1]
            )

            with col_service:

                service = st.text_input(
                    f"Service {index + 1}",
                    key=f"proposal_service_{index}",
                    placeholder="e.g. Website Design",
                )

            with col_price:

                price = st.number_input(
                    f"Price {index + 1}",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    key=f"proposal_price_{index}",
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
                payment_terms=payment_terms.strip(),
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
# PROPOSAL PAGE
# =========================================================

def render_proposals_page():

    st.title("Proposals")

    st.write(
        "Create professional proposals for your clients."
    )

    st.divider()

    # -----------------------------------------------------
    # NEW PROPOSAL
    # -----------------------------------------------------

    if st.button(
        "＋ New Proposal",
        type="primary",
    ):

        st.session_state[
            "show_add_proposal"
        ] = True

    # -----------------------------------------------------
    # FORM
    # -----------------------------------------------------

    if st.session_state.get(
        "show_add_proposal",
        False,
    ):

        with st.container(border=True):

            render_add_proposal()

        st.divider()

    # -----------------------------------------------------
    # SEARCH / FILTER
    # -----------------------------------------------------

    search_col, filter_col = st.columns(
        [3, 1]
    )

    with search_col:

        search = st.text_input(
            "Search proposals",
            placeholder="Search proposals or clients...",
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
            "No proposals found. Click **＋ New Proposal** "
            "to create your first proposal."
        )

        return

    # -----------------------------------------------------
    # PROPOSAL CARDS
    # -----------------------------------------------------

    for proposal in proposals:

        with st.container(border=True):

            col_info, col_status, col_actions = st.columns(
                [3, 1.2, 1]
            )

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
                        f" • {proposal['client_company']}"
                    )

                st.caption(
                    f"👤 {client_text}"
                )

                if proposal["description"]:

                    st.write(
                        proposal["description"]
                    )

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

            with col_actions:

                if st.button(
                    "Delete",
                    key=f"delete_proposal_{proposal['id']}",
                    use_container_width=True,
                ):

                    delete_proposal(
                        proposal["id"]
                    )

                    st.rerun()

            # -------------------------------------------------
            # ITEMS
            # -------------------------------------------------

            items = get_proposal_items(
                proposal["id"]
            )

            if items:

                st.markdown("**Services**")

                total = 0.0

                for item in items:

                    service_col, price_col = st.columns(
                        [4, 1]
                    )

                    with service_col:

                        st.write(
                            item["service"]
                        )

                    with price_col:

                        st.write(
                            f"${item['price']:,.2f}"
                        )

                    total += item["price"]

                st.divider()

                total_col, amount_col = st.columns(
                    [4, 1]
                )

                with total_col:

                    st.markdown("**Total**")

                with amount_col:

                    st.markdown(
                        f"**${total:,.2f}**"
                    )

            # -------------------------------------------------
            # EXTRA DETAILS
            # -------------------------------------------------

            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:

                if proposal["timeline"]:

                    st.caption(
                        f"⏱ Timeline: {proposal['timeline']}"
                    )

            with detail_col2:

                if proposal["payment_terms"]:

                    st.caption(
                        f"💳 Payment: {proposal['payment_terms']}"
                    )
