import streamlit as st

from modules.database import get_connection


# =========================================================
# OPTIONS
# =========================================================

PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent",
]

PROJECT_STATUSES = [
    "Active",
    "On Hold",
    "Completed",
]


# =========================================================
# GET CLIENTS
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


# =========================================================
# GET PROJECTS
# =========================================================

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

        search_value = f"%{search.strip()}%"

        query += """
            AND (
                projects.name LIKE ?
                OR projects.description LIKE ?
                OR clients.name LIKE ?
                OR clients.company LIKE ?
            )
        """

        params.extend(
            [
                search_value,
                search_value,
                search_value,
                search_value,
            ]
        )

    if status != "All":

        query += """
            AND projects.status = ?
        """

        params.append(status)

    query += """
        ORDER BY projects.created_at DESC
    """

    projects = connection.execute(
        query,
        params,
    ).fetchall()

    connection.close()

    return projects


# =========================================================
# ADD PROJECT
# =========================================================

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
        INSERT INTO projects (
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


# =========================================================
# UPDATE PROJECT
# =========================================================

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


# =========================================================
# DELETE PROJECT
# =========================================================

def delete_project(project_id):

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM tasks
        WHERE project_id = ?
        """,
        (project_id,),
    )

    connection.execute(
        """
        DELETE FROM projects
        WHERE id = ?
        """,
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
            "You need to create a client before creating a project."
        )

        return

    client_options = {
        client_label(client): client["id"]
        for client in clients
    }

    with st.form(
        "add_project_form",
        clear_on_submit=True,
    ):

        st.markdown("### Create New Project")

        col1, col2 = st.columns(2)

        with col1:

            selected_client = st.selectbox(
                "Client *",
                list(client_options.keys()),
            )

            project_name = st.text_input(
                "Project Name *",
                placeholder="Website Redesign",
            )

            deadline = st.date_input(
                "Deadline",
            )

            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=1,
            )

        with col2:

            status = st.selectbox(
                "Status",
                PROJECT_STATUSES,
            )

            progress = st.slider(
                "Progress",
                min_value=0,
                max_value=100,
                value=0,
                step=5,
            )

            description = st.text_area(
                "Description",
                placeholder="Describe the project...",
                height=150,
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
                client_id=client_options[
                    selected_client
                ],
                name=project_name.strip(),
                description=description.strip(),
                deadline=str(deadline),
                progress=progress,
                priority=priority,
                status=status,
            )

            st.session_state[
                "show_add_project"
            ] = False

            st.success(
                f"Project '{project_name.strip()}' created successfully."
            )

            st.rerun()


# =========================================================
# EDIT PROJECT FORM
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

    with st.form(
        f"edit_project_{project['id']}"
    ):

        st.markdown("### Edit Project")

        col1, col2 = st.columns(2)

        with col1:

            selected_client = st.selectbox(
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

            deadline = st.date_input(
                "Deadline",
                value=(
                    project["deadline"]
                    if project["deadline"]
                    else None
                ),
            )

            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=(
                    PRIORITIES.index(
                        project["priority"]
                    )
                    if project["priority"] in PRIORITIES
                    else 1
                ),
            )

        with col2:

            status = st.selectbox(
                "Status",
                PROJECT_STATUSES,
                index=(
                    PROJECT_STATUSES.index(
                        project["status"]
                    )
                    if project["status"] in PROJECT_STATUSES
                    else 0
                ),
            )

            progress = st.slider(
                "Progress",
                min_value=0,
                max_value=100,
                value=int(
                    project["progress"] or 0
                ),
                step=5,
            )

            description = st.text_area(
                "Description",
                value=project["description"] or "",
                height=150,
            )

        save = st.form_submit_button(
            "Save Changes",
            type="primary",
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
                client_id=client_options[
                    selected_client
                ],
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

            st.success(
                "Project updated successfully."
            )

            st.rerun()


# =========================================================
# PROJECTS PAGE
# =========================================================

def render_projects_page():

    st.title("Projects")

    st.markdown(
        '<div class="subtitle">'
        "Manage projects, deadlines, priorities, and progress."
        "</div>",
        unsafe_allow_html=True,
    )

    # =====================================================
    # TOP BAR
    # =====================================================

    search_col, button_col = st.columns(
        [4, 1]
    )

    with search_col:

        search = st.text_input(
            "Search projects",
            placeholder="Search projects or clients...",
            label_visibility="collapsed",
        )

    with button_col:

        if st.button(
            "＋ New Project",
            type="primary",
            use_container_width=True,
        ):

            st.session_state[
                "show_add_project"
            ] = not st.session_state.get(
                "show_add_project",
                False,
            )

            st.rerun()

    # =====================================================
    # ADD PROJECT
    # =====================================================

    if st.session_state.get(
        "show_add_project",
        False,
    ):

        with st.container(
            border=True
        ):

            render_add_project()

    # =====================================================
    # STATUS FILTER
    # =====================================================

    filter_col, spacer = st.columns(
        [1, 4]
    )

    with filter_col:

        status_filter = st.selectbox(
            "Status",
            ["All"] + PROJECT_STATUSES,
        )

    # =====================================================
    # PROJECTS
    # =====================================================

    projects = get_projects(
        search=search,
        status=status_filter,
    )

    st.markdown(
        f"**{len(projects)} project(s)**"
    )

    if not projects:

        st.info(
            "No projects found. Click "
            "**＋ New Project** to create your first project."
        )

        return

    # =====================================================
    # PROJECT CARDS
    # =====================================================

    for project in projects:

        project_id = project["id"]

        with st.container(
            border=True
        ):

            info_col, status_col, action_col = st.columns(
                [3.4, 1.4, 1]
            )

            with info_col:

                st.markdown(
                    f"### {project['name']}"
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

                    st.caption(
                        project["description"]
                    )

            with status_col:

                if project["status"] == "Completed":

                    st.success(
                        project["status"]
                    )

                elif project["status"] == "On Hold":

                    st.warning(
                        project["status"]
                    )

                else:

                    st.info(
                        project["status"]
                    )

                st.caption(
                    f"Priority: {project['priority']}"
                )

            with action_col:

                if st.button(
                    "Edit",
                    key=f"edit_project_{project_id}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "editing_project"
                    ] = project_id

                    st.session_state.pop(
                        "deleting_project",
                        None,
                    )

                    st.rerun()

                if st.button(
                    "Delete",
                    key=f"delete_project_{project_id}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "deleting_project"
                    ] = project_id

                    st.session_state.pop(
                        "editing_project",
                        None,
                    )

                    st.rerun()

            # =================================================
            # PROGRESS
            # =================================================

            progress_value = int(
                project["progress"] or 0
            )

            st.progress(
                progress_value / 100
            )

            progress_col, deadline_col = st.columns(2)

            with progress_col:

                st.caption(
                    f"Progress: {progress_value}%"
                )

            with deadline_col:

                if project["deadline"]:

                    st.caption(
                        f"📅 Deadline: {project['deadline']}"
                    )

            # =================================================
            # EDIT
            # =================================================

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

            # =================================================
            # DELETE
            # =================================================

            if (
                st.session_state.get(
                    "deleting_project"
                )
                == project_id
            ):

                st.divider()

                st.warning(
                    "Deleting this project will also "
                    "delete all tasks belonging to it."
                )

                confirm_col, cancel_col = st.columns(2)

                with confirm_col:

                    if st.button(
                        "Yes, Delete Project",
                        type="primary",
                        key=f"confirm_project_{project_id}",
                        use_container_width=True,
                    ):

                        delete_project(
                            project_id
                        )

                        st.session_state.pop(
                            "deleting_project",
                            None,
                        )

                        st.success(
                            "Project deleted successfully."
                        )

                        st.rerun()

                with cancel_col:

                    if st.button(
                        "Cancel",
                        key=f"cancel_project_{project_id}",
                        use_container_width=True,
                    ):

                        st.session_state.pop(
                            "deleting_project",
                            None,
                        )

                        st.rerun()
