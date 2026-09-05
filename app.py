```python
import streamlit as st

from modules.database import (
    init_db,
    get_dashboard_stats,
    get_revenue_overview,
    get_recent_activity,
    get_upcoming_tasks,
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
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE
# =========================================================

init_db()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.16);
    }

    .brand {
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.04em;
    }

    .brand-subtitle {
        font-size: .78rem;
        color: #888;
        margin-top: .15rem;
        margin-bottom: 1.4rem;
    }

    .hero-title {
        font-size: 2.35rem;
        font-weight: 800;
        letter-spacing: -.055em;
        margin-bottom: .2rem;
    }

    .subtitle {
        color: #777;
        font-size: 1rem;
        margin-bottom: 1.8rem;
    }

    .metric-card {
        border: 1px solid rgba(128,128,128,.16);
        border-radius: 18px;
        padding: 1.25rem;
        min-height: 135px;
        background: rgba(128,128,128,.025);
    }

    .metric-icon {
        font-size: 1.25rem;
        margin-bottom: .5rem;
    }

    .metric-label {
        font-size: .82rem;
        color: #777;
    }

    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -.04em;
        margin-top: .2rem;
    }

    .metric-description {
        font-size: .72rem;
        color: #888;
        margin-top: .3rem;
    }

    .section-title {
        font-size: 1.08rem;
        font-weight: 750;
        margin: 1.8rem 0 .8rem;
    }

    .dashboard-card {
        border: 1px solid rgba(128,128,128,.16);
        border-radius: 18px;
        padding: 1.3rem;
        background: rgba(128,128,128,.02);
    }

    .card-heading {
        font-size: 1.05rem;
        font-weight: 750;
    }

    .card-subheading {
        font-size: .78rem;
        color: #888;
        margin-top: .15rem;
        margin-bottom: 1rem;
    }

    .empty-state {
        text-align: center;
        padding: 2rem 1rem;
        color: #888;
    }

    .empty-icon {
        font-size: 2rem;
        margin-bottom: .35rem;
    }

    .empty-title {
        font-weight: 700;
        color: #777;
        margin-bottom: .25rem;
    }

    .activity-row {
        padding: .72rem 0;
        border-bottom: 1px solid rgba(128,128,128,.11);
    }

    .activity-row:last-child {
        border-bottom: none;
    }

    .activity-title {
        font-size: .84rem;
        font-weight: 600;
    }

    .activity-date {
        font-size: .7rem;
        color: #888;
        margin-top: .15rem;
    }

    .task-row {
        padding: .75rem;
        margin-bottom: .55rem;
        border: 1px solid rgba(128,128,128,.12);
        border-radius: 12px;
    }

    .task-name {
        font-size: .84rem;
        font-weight: 650;
    }

    .task-meta {
        font-size: .7rem;
        color: #888;
        margin-top: .25rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        '<div class="brand">✨ ClientFlow AI</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="brand-subtitle">'
        'Client Management Workspace'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption("NAVIGATION")

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "👥 Clients",
            "📁 Projects",
            "✅ Tasks",
            "📄 Proposals",
            "💰 Invoices",
            "🤖 AI Assistant",
            "📈 Reports",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.caption("WORKSPACE")

    st.caption(
        "All-in-one client management for "
        "freelancers & small agencies."
    )

    st.divider()

    st.caption("ClientFlow AI • v1.0")


# =========================================================
# DASHBOARD DATA
# =========================================================

stats = get_dashboard_stats()


# =========================================================
# DASHBOARD
# =========================================================

if page == "📊 Dashboard":

    st.markdown(
        '<div class="hero-title">Good morning 👋</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        "Here’s what’s happening with your business today."
        "</div>",
        unsafe_allow_html=True,
    )


    # =====================================================
    # METRICS
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">👥</div>
                <div class="metric-label">Total Clients</div>
                <div class="metric-value">
                    {stats["clients"]}
                </div>
                <div class="metric-description">
                    All clients in your workspace
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">📁</div>
                <div class="metric-label">Active Projects</div>
                <div class="metric-value">
                    {stats["projects"]}
                </div>
                <div class="metric-description">
                    Projects currently active
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">✅</div>
                <div class="metric-label">Pending Tasks</div>
                <div class="metric-value">
                    {stats["tasks"]}
                </div>
                <div class="metric-description">
                    Tasks waiting for completion
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-icon">💰</div>
                <div class="metric-label">Outstanding</div>
                <div class="metric-value">
                    ${stats["outstanding"]:,.0f}
                </div>
                <div class="metric-description">
                    Unpaid invoice balance
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    # =====================================================
    # BUSINESS OVERVIEW
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        'Business Overview'
        '</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1])


    # =====================================================
    # REVENUE
    # =====================================================

    with left:

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-heading">
                Revenue Overview
            </div>

            <div class="card-subheading">
                Revenue from paid invoices
            </div>
            """,
            unsafe_allow_html=True,
        )

        revenue = get_revenue_overview()

        if revenue:

            chart = {
                item["month"]: item["revenue"]
                for item in revenue
            }

            st.bar_chart(
                chart,
                height=250,
            )

            st.caption(
                f"Total paid revenue: "
                f"${stats['paid_revenue']:,.2f}"
            )

        else:

            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-icon">📊</div>
                    <div class="empty-title">
                        No revenue data yet
                    </div>
                    <div>
                        Revenue analytics will appear
                        when invoices are marked as paid.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        st.markdown("<br>", unsafe_allow_html=True)


        # =================================================
        # UPCOMING TASKS
        # =================================================

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-heading">
                Upcoming Tasks
            </div>

            <div class="card-subheading">
                Tasks that still need attention
            </div>
            """,
            unsafe_allow_html=True,
        )

        tasks = get_upcoming_tasks()

        if tasks:

            for task in tasks:

                due = task["due_date"] or "No due date"
                project = task["project_name"] or "No project"

                st.markdown(
                    f"""
                    <div class="task-row">

                        <div class="task-name">
                            {task["title"]}
                        </div>

                        <div class="task-meta">
                            📁 {project}
                            &nbsp; • &nbsp;
                            📅 {due}
                            &nbsp; • &nbsp;
                            {task["priority"]}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-icon">🎉</div>
                    <div class="empty-title">
                        You're all caught up
                    </div>
                    <div>
                        No pending tasks right now.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    # =====================================================
    # RIGHT COLUMN
    # =====================================================

    with right:

        # =================================================
        # QUICK ACTIONS
        # =================================================

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-heading">
                Quick Actions
            </div>

            <div class="card-subheading">
                Jump directly into your workflow
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "＋ Add Client",
            use_container_width=True,
            key="quick_client",
        ):
            st.session_state["page"] = "👥 Clients"
            st.rerun()

        if st.button(
            "＋ Create Project",
            use_container_width=True,
            key="quick_project",
        ):
            st.session_state["page"] = "📁 Projects"
            st.rerun()

        if st.button(
            "＋ Create Task",
            use_container_width=True,
            key="quick_task",
        ):
            st.session_state["page"] = "✅ Tasks"
            st.rerun()

        if st.button(
            "＋ Create Proposal",
            use_container_width=True,
            key="quick_proposal",
        ):
            st.session_state["page"] = "📄 Proposals"
            st.rerun()

        if st.button(
            "＋ Create Invoice",
            use_container_width=True,
            key="quick_invoice",
        ):
            st.session_state["page"] = "💰 Invoices"
            st.rerun()

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        st.markdown("<br>", unsafe_allow_html=True)


        # =================================================
        # SNAPSHOT
        # =================================================

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-heading">
                Workspace Snapshot
            </div>

            <div class="card-subheading">
                Your current business pipeline
            </div>
            """,
            unsafe_allow_html=True,
        )

        s1, s2 = st.columns(2)

        with s1:
            st.metric(
                "Proposals",
                stats["proposals"],
            )

        with s2:
            st.metric(
                "Invoices",
                stats["total_invoices"],
            )

        st.divider()

        if stats["total_invoices"] > 0:

            payment_rate = (
                stats["paid_invoices"]
                / stats["total_invoices"]
            ) * 100

            st.write(
                f"**Invoice payment rate:** "
                f"{payment_rate:.0f}%"
            )

            st.progress(
                int(payment_rate)
            )

        else:

            st.caption(
                "Invoice payment insights will appear "
                "as invoices are added."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    # =====================================================
    # RECENT ACTIVITY
    # =====================================================

    st.markdown(
        '<div class="section-title">'
        'Recent Activity'
        '</div>',
        unsafe_allow_html=True,
    )

    activity_left, activity_right = st.columns(
        [1.45, 1]
    )


    with activity_left:

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-heading">
                Latest Activity
            </div>

            <div class="card-subheading">
                Recent changes across your workspace
            </div>
            """,
            unsafe_allow_html=True,
        )

        activities = get_recent_activity()

        if activities:

            icons = {
                "Client": "👤",
                "Project": "📁",
                "Proposal": "📄",
                "Invoice": "💰",
            }

            for activity in activities:

                icon = icons.get(
                    activity["type"],
                    "•",
                )

                st.markdown(
                    f"""
                    <div class="activity-row">

                        <div class="activity-title">
                            {icon} {activity["title"]}
                        </div>

                        <div class="activity-date">
                            {activity["created_at"] or "Recently"}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-icon">✨</div>
                    <div class="empty-title">
                        No activity yet
                    </div>
                    <div>
                        Your latest workspace activity
                        will appear here.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    # =====================================================
    # GETTING STARTED
    # =====================================================

    with activity_right:

        st.markdown(
            """
            <div class="dashboard-card">

            <div class="card-heading">
                Getting Started
            </div>

            <div class="card-subheading">
                Build your workspace step by step
            </div>
            """,
            unsafe_allow_html=True,
        )

        if stats["clients"] == 0:

            st.markdown(
                """
                ### 👋 Welcome!

                Start by adding your first client.

                Once you add clients, you can create
                projects, tasks, proposals and invoices.
                """
            )

            if st.button(
                "Add your first client →",
                use_container_width=True,
                key="getting_started_client",
            ):
                st.session_state["page"] = "👥 Clients"
                st.rerun()

        elif stats["projects"] == 0:

            st.success(
                f"You have {stats['clients']} client(s)."
            )

            st.info(
                "Next step: create your first project."
            )

            if st.button(
                "Create a project →",
                use_container_width=True,
                key="getting_started_project",
            ):
                st.session_state["page"] = "📁 Projects"
                st.rerun()

        elif stats["tasks"] == 0:

            st.success(
                "Your client and project workspace is ready."
            )

            st.info(
                "Next step: create your first task."
            )

            if st.button(
                "Create a task →",
                use_container_width=True,
                key="getting_started_task",
            ):
                st.session_state["page"] = "✅ Tasks"
                st.rerun()

        else:

            st.success(
                "Your ClientFlow workspace is up and running."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# CLIENTS
# =========================================================

elif page == "👥 Clients":

    render_clients_page()


# =========================================================
# PROJECTS
# =========================================================

elif page == "📁 Projects":

    render_projects_page()


# =========================================================
# TASKS
# =========================================================

elif page == "✅ Tasks":

    render_tasks_page()


# =========================================================
# PROPOSALS
# =========================================================

elif page == "📄 Proposals":

    render_proposals_page()


# =========================================================
# INVOICES
# =========================================================

elif page == "💰 Invoices":

    st.title("Invoices")

    st.write(
        "Create invoices and manage outstanding payments."
    )

    st.info(
        "🚧 Invoice Generator is coming soon."
    )


# =========================================================
# AI ASSISTANT
# =========================================================

elif page == "🤖 AI Assistant":

    st.title("AI Assistant 🤖")

    st.write(
        "Your AI-powered client management assistant."
    )

    st.info(
        "🚧 AI Assistant will be added after the core "
        "CRM workflows are complete."
    )


# =========================================================
# REPORTS
# =========================================================

elif page == "📈 Reports":

    st.title("Reports")

    st.write(
        "Track business performance and client activity."
    )

    st.info(
        "🚧 Reports & analytics are coming soon."
    )
```
