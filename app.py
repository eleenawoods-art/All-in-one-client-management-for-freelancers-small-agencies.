import streamlit as st

from modules.database import init_db, get_dashboard_stats, get_connection

from modules.clients import render_clients_page
from modules.projects import render_projects_page
from modules.tasks import render_tasks_page
from modules.proposals import render_proposals_page
from modules.invoices import render_invoices_page
st.set_page_config(
    page_title="ClientFlow AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.15);
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .main-subtitle {
        color: #777;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# NAVIGATION
# =========================================================

NAVIGATION = [
    "📊 Dashboard",
    "👥 Clients",
    "📁 Projects",
    "✅ Tasks",
    "📄 Proposals",
    "💰 Invoices",
    "🤖 AI Assistant",
    "📈 Reports",
]

if "page" not in st.session_state:
    st.session_state.page = "📊 Dashboard"


def go_to_page(page):
    st.session_state.page = page
    st.rerun()


# =========================================================
# DASHBOARD DATA
# =========================================================

def get_dashboard_data():

    connection = get_connection()

    revenue_rows = connection.execute(
        """
        SELECT
            substr(created_at, 1, 7) AS month,
            COALESCE(SUM(total), 0) AS revenue
        FROM invoices
        WHERE status = 'Paid'
        GROUP BY substr(created_at, 1, 7)
        ORDER BY month ASC
        """
    ).fetchall()

    activity_rows = connection.execute(
        """
        SELECT type, title, created_at
        FROM (
            SELECT
                'Client' AS type,
                name AS title,
                created_at
            FROM clients

            UNION ALL

            SELECT
                'Project' AS type,
                name AS title,
                created_at
            FROM projects

            UNION ALL

            SELECT
                'Task' AS type,
                title AS title,
                created_at
            FROM tasks

            UNION ALL

            SELECT
                'Proposal' AS type,
                title AS title,
                created_at
            FROM proposals

            UNION ALL

            SELECT
                'Invoice' AS type,
                COALESCE(invoice_number, 'Invoice') AS title,
                created_at
            FROM invoices
        )
        ORDER BY datetime(created_at) DESC
        LIMIT 8
        """
    ).fetchall()

    task_rows = connection.execute(
        """
        SELECT
            tasks.title,
            COALESCE(
                NULLIF(tasks.due_date, ''),
                tasks.deadline
            ) AS due_date,
            tasks.priority,
            tasks.status,
            projects.name AS project_name
        FROM tasks
        LEFT JOIN projects
            ON tasks.project_id = projects.id
        WHERE tasks.status != 'Done'
        ORDER BY
            CASE
                WHEN COALESCE(
                    NULLIF(tasks.due_date, ''),
                    tasks.deadline
                ) IS NULL
                THEN 1
                ELSE 0
            END,
            date(
                COALESCE(
                    NULLIF(tasks.due_date, ''),
                    tasks.deadline
                )
            ) ASC
        LIMIT 6
        """
    ).fetchall()

    proposal_count = connection.execute(
        "SELECT COUNT(*) FROM proposals"
    ).fetchone()[0]

    invoice_count = connection.execute(
        "SELECT COUNT(*) FROM invoices"
    ).fetchone()[0]

    project_count = connection.execute(
        "SELECT COUNT(*) FROM projects"
    ).fetchone()[0]

    task_count = connection.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    connection.close()

    return (
        revenue_rows,
        activity_rows,
        task_rows,
        proposal_count,
        invoice_count,
        project_count,
        task_count,
    )


def format_date(value):

    if not value:
        return "No due date"

    return str(value)[:10]


def activity_icon(activity_type):

    icons = {
        "Client": "👤",
        "Project": "📁",
        "Task": "✅",
        "Proposal": "📄",
        "Invoice": "💰",
    }

    return icons.get(activity_type, "•")


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## ✨ ClientFlow AI")

    st.caption("Client Management Workspace")

    st.divider()

    selected_page = st.radio(
        "Navigation",
        NAVIGATION,
        index=NAVIGATION.index(st.session_state.page),
        label_visibility="collapsed",
    )

    st.session_state.page = selected_page

    st.divider()

    st.caption("ClientFlow AI")
    st.caption("v1.0 • Workspace")


stats = get_dashboard_stats()


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "📊 Dashboard":

    st.markdown(
        '<div class="main-title">Good morning 👋</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="main-subtitle">'
        "Here is what is happening across your client workspace."
        "</div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.metric("👥 Total Clients", stats["clients"])
            st.caption("All clients in your workspace")

    with col2:
        with st.container(border=True):
            st.metric("📁 Active Projects", stats["projects"])
            st.caption("Projects currently active")

    with col3:
        with st.container(border=True):
            st.metric("✅ Pending Tasks", stats["tasks"])
            st.caption("Tasks still requiring attention")

    with col4:
        with st.container(border=True):
            st.metric(
                "💰 Outstanding",
                f"${stats['outstanding']:,.2f}",
            )
            st.caption("Unpaid invoice balance")

    st.write("")

    (
        revenue_rows,
        activity_rows,
        task_rows,
        proposal_count,
        invoice_count,
        project_count,
        task_count,
    ) = get_dashboard_data()

    # -----------------------------------------------------
    # REVENUE + TASKS
    # -----------------------------------------------------

    left, right = st.columns([1.6, 1])

    with left:

        with st.container(border=True):

            st.subheader("Revenue Overview")

            st.caption(
                "Revenue collected from paid invoices"
            )

            if revenue_rows:

                chart_data = {
                    row["month"]: float(row["revenue"] or 0)
                    for row in revenue_rows
                }

                st.bar_chart(
                    chart_data,
                    height=280,
                )

            else:

                st.info(
                    "No paid invoices yet. "
                    "Create an invoice and mark it as Paid "
                    "to see revenue here."
                )

    with right:

        with st.container(border=True):

            st.subheader("Upcoming Tasks")

            st.caption(
                "Your next tasks requiring attention"
            )

            if task_rows:

                for task in task_rows:

                    st.markdown(
                        f"**{task['title']}**"
                    )

                    details = []

                    if task["project_name"]:
                        details.append(
                            f"📁 {task['project_name']}"
                        )

                    details.append(
                        f"📅 {format_date(task['due_date'])}"
                    )

                    details.append(
                        f"⚡ {task['priority']}"
                    )

                    st.caption(
                        " • ".join(details)
                    )

                    st.divider()

            else:

                st.info(
                    "No pending tasks right now."
                )

    st.write("")

    # -----------------------------------------------------
    # RECENT ACTIVITY + SNAPSHOT
    # -----------------------------------------------------

    left, right = st.columns([1.5, 1])

    with left:

        with st.container(border=True):

            st.subheader("Recent Activity")

            st.caption(
                "Latest activity across your workspace"
            )

            if activity_rows:

                for activity in activity_rows:

                    icon = activity_icon(
                        activity["type"]
                    )

                    st.markdown(
                        f"{icon} **{activity['type']}** — "
                        f"{activity['title']}"
                    )

                    if activity["created_at"]:

                        st.caption(
                            str(activity["created_at"])
                        )

                    st.divider()

            else:

                st.info(
                    "Your recent activity will appear here "
                    "as you add clients, projects, tasks, "
                    "proposals, and invoices."
                )

    with right:

        with st.container(border=True):

            st.subheader("Workspace Snapshot")

            st.caption(
                "Quick overview of your business"
            )

            st.metric(
                "📄 Proposals",
                proposal_count,
            )

            st.metric(
                "💰 Invoices",
                invoice_count,
            )

            st.metric(
                "📁 Projects",
                project_count,
            )

            st.metric(
                "✅ Total Tasks",
                task_count,
            )

    st.write("")

    # -----------------------------------------------------
    # QUICK ACTIONS
    # -----------------------------------------------------

    with st.container(border=True):

        st.subheader("Quick Actions")

        st.caption(
            "Jump directly to the area you want to manage."
        )

        q1, q2, q3, q4 = st.columns(4)

        with q1:

            if st.button(
                "👥 Add Client",
                use_container_width=True,
            ):
                go_to_page("👥 Clients")

        with q2:

            if st.button(
                "📁 New Project",
                use_container_width=True,
            ):
                go_to_page("📁 Projects")

        with q3:

            if st.button(
                "📄 Create Proposal",
                use_container_width=True,
            ):
                go_to_page("📄 Proposals")

        with q4:

            if st.button(
                "💰 Create Invoice",
                use_container_width=True,
            ):
                go_to_page("💰 Invoices")

    st.write("")

    # -----------------------------------------------------
    # GETTING STARTED
    # -----------------------------------------------------

    if stats["clients"] == 0:

        with st.container(border=True):

            st.subheader("🚀 Getting Started")

            st.write(
                "Welcome to ClientFlow AI. "
                "Start by adding your first client, "
                "then create projects and tasks to manage "
                "your work from one workspace."
            )

            start1, start2 = st.columns(2)

            with start1:

                if st.button(
                    "Add Your First Client",
                    use_container_width=True,
                ):
                    go_to_page("👥 Clients")

            with start2:

                if st.button(
                    "Explore Projects",
                    use_container_width=True,
                ):
                    go_to_page("📁 Projects")


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

    st.title("💰 Invoices")

    st.caption(
        "Create invoices and track outstanding payments."
    )

    st.info(
        "Invoice management module is coming next."
    )


# =========================================================
# AI ASSISTANT
# =========================================================

elif st.session_state.page == "🤖 AI Assistant":

    st.title("🤖 AI Assistant")

    st.caption(
        "Your intelligent workspace assistant."
    )

    st.info(
        "AI Assistant module is coming next."
    )


# =========================================================
# REPORTS
# =========================================================

elif st.session_state.page == "📈 Reports":

    st.title("📈 Reports")

    st.caption(
        "Business performance and client reporting."
    )

    st.info(
        "Reports module is coming next."
    )
