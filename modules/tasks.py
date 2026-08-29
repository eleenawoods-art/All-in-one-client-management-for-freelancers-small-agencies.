import streamlit as st
from modules.database import get_connection


TASK_STATUSES = [
    "To Do",
    "In Progress",
    "Done",
]

TASK_PRIORITIES = [
    "Low",
    "Medium",
    "High",
    "Urgent",
]


# =========================================================
# PROJECTS
# =========================================================

def get_projects():

    connection = get_connection()

    projects = connection.execute(
        """
        SELECT
            id,
            name
        FROM projects
        ORDER BY name ASC
        """
    ).fetchall()

    connection.close()

    return projects


# =========================================================
# TASKS
# =========================================================

def get_tasks(search="", status="All"):

    connection = get_connection()

    query = """
        SELECT
            tasks.*,
            projects.name AS project_name,
            clients.name AS client_name
        FROM tasks
        LEFT JOIN projects
            ON tasks.project_id = projects.id
        LEFT JOIN clients
            ON projects.client_id = clients.id
        WHERE 1 = 1
    """

    params = []

    if search.strip():

        value = f"%{search.strip()}%"

        query += """
            AND (
                tasks.title LIKE ?
                OR tasks.description LIKE ?
                OR projects.name LIKE ?
                OR clients.name LIKE ?
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
            AND tasks.status = ?
        """

        params.append(status)

    query += """
        ORDER BY tasks.created_at DESC
    """

    tasks = connection.execute(
        query,
        params,
    ).fetchall()

    connection.close()

    return tasks


# =========================================================
# ADD TASK
# =========================================================

def add_task(
    project_id,
    title,
    description,
    due_date,
    priority,
    status,
    assignee,
):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO tasks
        (
            project_id,
            title,
            description,
            due_date,
            priority,
            status,
            assignee
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            title,
            description,
            due_date,
            priority,
            status,
            assignee,
        ),
    )

    connection.commit()
    connection.close()


# =========================================================
# UPDATE TASK
# =========================================================

def update_task(
    task_id,
    project_id,
    title,
    description,
    due_date,
    priority,
    status,
    assignee,
):

    connection = get_connection()

    connection.execute(
        """
        UPDATE tasks
        SET
            project_id = ?,
            title = ?,
            description = ?,
            due_date = ?,
            priority = ?,
            status = ?,
            assignee = ?
        WHERE id = ?
        """,
        (
            project_id,
            title,
            description,
            due_date,
            priority,
            status,
            assignee,
            task_id,
        ),
    )

    connection.commit()
    connection.close()


# =========================================================
# DELETE TASK
# =========================================================

def delete_task(task_id):

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM tasks
        WHERE id = ?
        """,
        (task_id,),
    )

    connection.commit()
    connection.close()


# =========================================================
# ADD TASK FORM
# =========================================================

def render_add_task():

    projects = get_projects()

    if not projects:

        st.warning(
            "Please create a project before creating a task."
        )

        return

    project_options = {
        project["name"]: project["id"]
        for project in projects
    }

    st.subheader("Create New Task")

    with st.form(
        "create_task_form"
    ):

        project_name = st.selectbox(
            "Project *",
            list(project_options.keys()),
        )

        title = st.text_input(
            "Task Title *",
            placeholder="e.g. Design homepage",
        )

        description = st.text_area(
            "Description",
            placeholder="Describe what needs to be done...",
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            due_date = st.date_input(
                "Due Date"
            )

        with col2:

            priority = st.selectbox(
                "Priority",
                TASK_PRIORITIES,
                index=1,
            )

        with col3:

            status = st.selectbox(
                "Status",
                TASK_STATUSES,
            )

        assignee = st.text_input(
            "Assignee",
            placeholder="e.g. Rohan",
        )

        submitted = st.form_submit_button(
            "Create Task",
            type="primary",
            use_container_width=True,
        )

        if submitted:

            if not title.strip():

                st.error(
                    "Task title is required."
                )

                return

            add_task(
                project_id=project_options[
                    project_name
                ],
                title=title.strip(),
                description=description.strip(),
                due_date=str(due_date),
                priority=priority,
                status=status,
                assignee=assignee.strip(),
            )

            st.session_state[
                "show_add_task"
            ] = False

            st.success(
                f"Task '{title.strip()}' created successfully."
            )

            st.rerun()


# =========================================================
# EDIT TASK
# =========================================================

def render_edit_task(task):

    projects = get_projects()

    project_options = {
        project["name"]: project["id"]
        for project in projects
    }

    reverse_projects = {
        project["id"]: project["name"]
        for project in projects
    }

    current_project = reverse_projects.get(
        task["project_id"]
    )

    if current_project not in project_options:

        current_project = list(
            project_options.keys()
        )[0]

    st.subheader("Edit Task")

    with st.form(
        f"edit_task_form_{task['id']}"
    ):

        project_name = st.selectbox(
            "Project",
            list(project_options.keys()),
            index=list(
                project_options.keys()
            ).index(current_project),
        )

        title = st.text_input(
            "Task Title",
            value=task["title"] or "",
        )

        description = st.text_area(
            "Description",
            value=task["description"] or "",
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            due_date = st.date_input(
                "Due Date",
                value=task["due_date"],
            )

        with col2:

            priority = st.selectbox(
                "Priority",
                TASK_PRIORITIES,
                index=(
                    TASK_PRIORITIES.index(
                        task["priority"]
                    )
                    if task["priority"] in TASK_PRIORITIES
                    else 1
                ),
            )

        with col3:

            status = st.selectbox(
                "Status",
                TASK_STATUSES,
                index=(
                    TASK_STATUSES.index(
                        task["status"]
                    )
                    if task["status"] in TASK_STATUSES
                    else 0
                ),
            )

        assignee = st.text_input(
            "Assignee",
            value=task["assignee"] or "",
        )

        save = st.form_submit_button(
            "Save Changes",
            type="primary",
            use_container_width=True,
        )

        if save:

            if not title.strip():

                st.error(
                    "Task title is required."
                )

                return

            update_task(
                task_id=task["id"],
                project_id=project_options[
                    project_name
                ],
                title=title.strip(),
                description=description.strip(),
                due_date=str(due_date),
                priority=priority,
                status=status,
                assignee=assignee.strip(),
            )

            st.session_state.pop(
                "editing_task",
                None,
            )

            st.rerun()


# =========================================================
# TASKS PAGE
# =========================================================

def render_tasks_page():

    st.title("Tasks")

    st.write(
        "Organize tasks across your projects."
    )

    st.divider()

    # =====================================================
    # NEW TASK
    # =====================================================

    if st.button(
        "＋ New Task",
        type="primary",
    ):

        st.session_state[
            "show_add_task"
        ] = True

    # =====================================================
    # ADD FORM
    # =====================================================

    if st.session_state.get(
        "show_add_task",
        False,
    ):

        with st.container(border=True):

            render_add_task()

        st.divider()

    # =====================================================
    # SEARCH / FILTER
    # =====================================================

    search_col, filter_col = st.columns(
        [3, 1]
    )

    with search_col:

        search = st.text_input(
            "Search tasks",
            placeholder="Search tasks, projects or clients...",
        )

    with filter_col:

        status_filter = st.selectbox(
            "Status",
            ["All"] + TASK_STATUSES,
        )

    # =====================================================
    # TASKS
    # =====================================================

    tasks = get_tasks(
        search=search,
        status=status_filter,
    )

    st.write(
        f"**{len(tasks)} task(s)**"
    )

    if not tasks:

        st.info(
            "No tasks found. Click **＋ New Task** "
            "to create your first task."
        )

        return

    # =====================================================
    # TASK CARDS
    # =====================================================

    for task in tasks:

        task_id = task["id"]

        with st.container(border=True):

            info_col, status_col, actions_col = st.columns(
                [3.2, 1.3, 1]
            )

            with info_col:

                st.subheader(
                    task["title"]
                )

                st.caption(
                    f"📁 {task['project_name'] or 'No project'}"
                )

                if task["client_name"]:

                    st.caption(
                        f"👤 {task['client_name']}"
                    )

                if task["description"]:

                    st.write(
                        task["description"]
                    )

            with status_col:

                if task["status"] == "Done":

                    st.success(
                        task["status"]
                    )

                elif task["status"] == "In Progress":

                    st.warning(
                        task["status"]
                    )

                else:

                    st.info(
                        task["status"]
                    )

                st.caption(
                    f"Priority: {task['priority']}"
                )

                if task["due_date"]:

                    st.caption(
                        f"📅 {task['due_date']}"
                    )

            with actions_col:

                if st.button(
                    "Edit",
                    key=f"edit_task_{task_id}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "editing_task"
                    ] = task_id

                    st.rerun()

                if st.button(
                    "Delete",
                    key=f"delete_task_{task_id}",
                    use_container_width=True,
                ):

                    delete_task(
                        task_id
                    )

                    st.rerun()

            # -------------------------------------------------
            # ASSIGNEE
            # -------------------------------------------------

            if task["assignee"]:

                st.caption(
                    f"👨‍💻 Assigned to: {task['assignee']}"
                )

            # -------------------------------------------------
            # EDIT
            # -------------------------------------------------

            if (
                st.session_state.get(
                    "editing_task"
                )
                == task_id
            ):

                st.divider()

                render_edit_task(
                    task
                )
