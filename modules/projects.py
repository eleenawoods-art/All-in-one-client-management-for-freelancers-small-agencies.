import streamlit as st

from modules.database import get_connection


PRIORITIES = ["Low", "Medium", "High", "Urgent"]
PROJECT_STATUSES = ["Active", "On Hold", "Completed"]


# =========================================================
# DATABASE HELPERS
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


def get_projects(search="", status="All"):
    connection = get_connection()

    query = """
        SELECT
            projects.*,
            clients.name AS client_name,
            clients.company AS client_company
        FROM projects
        LEFT JOIN clients
            ON projects.client_id = clients.id
        WHERE 1 = 1
    """

    params = []

    if search.strip():
        value = f"%{search.strip()}%"

        query += """
            AND (
                projects.name LIKE ?
                OR projects.description LIKE ?
                OR clients.name LIKE ?
                OR clients.company LIKE ?
            )
        """

        params.extend([value, value, value, value])

    if status != "All":
        query += " AND projects.status = ?"
        params.append(status)

    query += " ORDER BY projects.created_at DESC"

    projects = connection.execute(
        query,
        params
    ).fetchall()

    connection.close()

    return projects


def add_project(
    client_id,
    name,
    description,
    deadline,
    progress,
    priority,
    status,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO projects
        (
            client_id,
            name,
            description,
            deadline,
            progress,
            priority,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            client_id,
            name,
            description,
            deadline,
            progress,
            priority,
            status,
        ),
    )

    connection.commit()
    connection.close()


def update_project(
    project_id,
    client_id,
    name,
    description,
    deadline,
    progress,
    priority,
    status,
):
    connection = get_connection()

    connection.execute(
        """
        UPDATE projects
        SET
            client_id = ?,
            name = ?,
            description = ?,
            deadline = ?,
            progress = ?,
            priority = ?,
            status = ?
        WHERE id = ?
        """,
        (
            client_id,
            name,
            description,
            deadline,
            progress,
            priority,
            status,
            project_id,
        ),
    )

    connection.commit()
    connection.close()


def delete_project(project_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM tasks WHERE project_id = ?",
        (project_id,),
    )

    connection.execute(
        "DELETE FROM projects WHERE id = ?",
        (project_id,),
    )

    connection.commit()
    connection.close()


# =========================================================
# CLIENT LABEL
# =========================================================

def client_label(client):
    if client["company"]:
        return f"{client['name']} — {client['company']}"

    return client["name"]


# =========================================================
# ADD PROJECT FORM
# =========================================================

def render_add_project():

    clients = get_clients()

    if not clients:
        st.warning(
            "No clients found. Please create a client first."
        )
        return

    client_options = {
        client_label(client): client["id"]
        for client in clients
    }

    st.subheader("Create New Project")

    with st.form("create_project_form"):

        client_name = st.selectbox(
            "Client *",
            list(client_options.keys()),
        )

        project_name = st.text_input(
            "Project Name *",
            placeholder="e.g. Website Redesign",
        )

        description = st.text_area(
            "Description",
            placeholder="Describe the project...",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            deadline = st.date_input(
                "Deadline"
            )

        with col2:
            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=1,
            )

        with col3:
            status = st.selectbox(
                "Status",
                PROJECT_STATUSES,
            )

        progress = st.slider(
            "Progress",
            0,
            100,
            0,
            5,
        )

        submitted = st.form_submit_button(
            "Create Project",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not project_name.strip():
                st.error(
                    "Project name is required."
                )
                return

            add_project(
                client_id=client_options[client_name],
                name=project_name.strip(),
                description=description.strip(),
                deadline=str(deadline),
                progress=progress,
                priority=priority,
                status=status,
            )

            st.session_state["show_add_project"] = False

            st.success(
                f"Project '{project_name.strip()}' created successfully."
            )

            st.rerun()


# =========================================================
# EDIT PROJECT
# =========================================================

def render_edit_project(project):

    clients = get_clients()

    client_options = {
        client_label(client): client["id"]
        for client in clients
    }

    reverse_clients = {
        client["id"]: client_label(client)
        for client in clients
    }

    current_client = reverse_clients.get(
        project["client_id"]
    )

    if current_client not in client_options:
        current_client = list(
            client_options.keys()
        )[0]

    st.subheader("Edit Project")

    with st.form(
        f"edit_project_form_{project['id']}"
    ):

        client_name = st.selectbox(
            "Client",
            list(client_options.keys()),
            index=list(
                client_options.keys()
            ).index(current_client),
        )

        project_name = st.text_input(
            "Project Name",
            value=project["name"] or "",
        )

        description = st.text_area(
            "Description",
            value=project["description"] or "",
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            deadline = st.date_input(
                "Deadline",
                value=project["deadline"],
            )

        with col2:

            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=(
                    PRIORITIES.index(project["priority"])
                    if project["priority"] in PRIORITIES
                    else 1
                ),
            )

        with col3:

            status = st.selectbox(
                "Status",
                PROJECT_STATUSES,
                index=(
                    PROJECT_STATUSES.index(project["status"])
                    if project["status"] in PROJECT_STATUSES
                    else 0
                ),
            )

        progress = st.slider(
            "Progress",
            0,
            100,
            int(project["progress"] or 0),
            5,
        )

        col_save, col_cancel = st.columns(2)

        with col_save:

            save = st.form_submit_button(
                "Save Changes",
                type="primary",
                use_container_width=True,
            )

        with col_cancel:

            cancel = st.form_submit_button(
                "Cancel",
                use_container_width=True,
            )

        if save:

            if not project_name.strip():

                st.error(
                    "Project name is required."
                )
                return

            update_project(
                project_id=project["id"],
                client_id=client_options[client_name],
                name=project_name.strip(),
                description=description.strip(),
                deadline=str(deadline),
                progress=progress,
                priority=priority,
                status=status,
            )

            st.session_state.pop(
                "editing_project",
                None,
            )

            st.rerun()

        if cancel:

            st.session_state.pop(
                "editing_project",
                None,
            )

            st.rerun()


# =========================================================
# PROJECTS PAGE
# =========================================================

def render_projects_page():

    st.title("Projects")

    st.write(
        "Manage projects, deadlines, priorities, and progress."
    )

    st.divider()

    # -----------------------------------------------------
    # NEW PROJECT BUTTON
    # -----------------------------------------------------

    if st.button(
        "＋ New Project",
        type="primary",
    ):

        st.session_state["show_add_project"] = True

    # -----------------------------------------------------
    # ADD FORM
    # -----------------------------------------------------

    if st.session_state.get(
        "show_add_project",
        False,
    ):

        with st.container(border=True):

            render_add_project()

        st.divider()

    # -----------------------------------------------------
    # SEARCH + FILTER
    # -----------------------------------------------------

    search_col, filter_col = st.columns(
        [3, 1]
    )

    with search_col:

        search = st.text_input(
            "Search projects",
            placeholder="Search by project or client...",
        )

    with filter_col:

        status_filter = st.selectbox(
            "Status",
            ["All"] + PROJECT_STATUSES,
        )

    # -----------------------------------------------------
    # PROJECTS
    # -----------------------------------------------------

    projects = get_projects(
        search=search,
        status=status_filter,
    )

    st.write(
        f"**{len(projects)} project(s)**"
    )

    if not projects:

        st.info(
            "No projects found. Click "
            "**＋ New Project** above to create your first project."
        )

        return

    # -----------------------------------------------------
    # PROJECT CARDS
    # -----------------------------------------------------

    for project in projects:

        project_id = project["id"]

        with st.container(border=True):

            col_info, col_status, col_actions = st.columns(
                [3, 1.3, 1]
            )

            with col_info:

                st.subheader(
                    project["name"]
                )

                client_text = (
                    project["client_name"]
                    or "No client"
                )

                if project["client_company"]:

                    client_text += (
                        f" • {project['client_company']}"
                    )

                st.caption(
                    f"👤 {client_text}"
                )

                if project["description"]:

                    st.write(
                        project["description"]
                    )

            with col_status:

                if project["status"] == "Active":

                    st.success(
                        project["status"]
                    )

                elif project["status"] == "Completed":

                    st.info(
                        project["status"]
                    )

                else:

                    st.warning(
                        project["status"]
                    )

                st.caption(
                    f"Priority: {project['priority']}"
                )

            with col_actions:

                if st.button(
                    "Edit",
                    key=f"edit_{project_id}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "editing_project"
                    ] = project_id

                    st.rerun()

                if st.button(
                    "Delete",
                    key=f"delete_{project_id}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "deleting_project"
                    ] = project_id

                    st.rerun()

            # -------------------------------------------------
            # PROGRESS
            # -------------------------------------------------

            progress = int(
                project["progress"] or 0
            )

            st.progress(
                progress / 100
            )

            progress_col, deadline_col = st.columns(2)

            with progress_col:

                st.caption(
                    f"Progress: {progress}%"
                )

            with deadline_col:

                st.caption(
                    f"📅 Deadline: {project['deadline']}"
                )

            # -------------------------------------------------
            # EDIT
            # -------------------------------------------------

            if (
                st.session_state.get(
                    "editing_project"
                )
                == project_id
            ):

                st.divider()

                render_edit_project(
                    project
                )

            # -------------------------------------------------
            # DELETE
            # -------------------------------------------------

            if (
                st.session_state.get(
                    "deleting_project"
                )
                == project_id
            ):

                st.divider()

                st.warning(
                    "This will also delete tasks belonging "
                    "to this project."
                )

                yes_col, no_col = st.columns(2)

                with yes_col:

                    if st.button(
                        "Yes, Delete",
                        type="primary",
                        key=f"yes_{project_id}",
                        use_container_width=True,
                    ):

                        delete_project(
                            project_id
                        )

                        st.session_state.pop(
                            "deleting_project",
                            None,
                        )

                        st.rerun()

                with no_col:

                    if st.button(
                        "Cancel",
                        key=f"no_{project_id}",
                        use_container_width=True,
                    ):

                        st.session_state.pop(
                            "deleting_project",
                            None,
                        )

                        st.rerun()
