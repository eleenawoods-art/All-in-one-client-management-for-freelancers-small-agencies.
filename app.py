import streamlit as st

from modules.database import init_db, get_dashboard_stats
from modules.clients import render_clients_page
from modules.projects import render_projects_page
from modules.tasks import render_tasks_page


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
        border-right: 1px solid rgba(128,128,128,.18);
    }

    .brand {
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.3rem;
    }

    .brand-subtitle {
        font-size: 0.78rem;
        color: #888;
        margin-bottom: 1.5rem;
    }

    .subtitle {
        color: #777;
        margin-top: -0.7rem;
        margin-bottom: 2rem;
        font-size: 1rem;
    }

    .metric-card {
        padding: 1.25rem;
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 16px;
        background: rgba(128,128,128,.035);
        min-height: 120px;
    }

    .metric-label {
        font-size: .85rem;
        color: #777;
    }

    .metric-value {
        font-size: 1.85rem;
        font-weight: 750;
        margin-top: .35rem;
    }

    .metric-description {
        font-size: .75rem;
        color: #888;
        margin-top: .3rem;
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin: 1.7rem 0 .8rem;
    }

    .dashboard-card {
        padding: 1.35rem;
        border: 1px solid rgba(128,128,128,.18);
        border-radius: 16px;
        min-height: 180px;
        background: rgba(128,128,128,.025);
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
        "Client Management Workspace"
        "</div>",
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

    st.markdown(
        """
        <div style="
            font-size:0.82rem;
            line-height:1.5;
            color:#777;
        ">
        All-in-one client management for
        freelancers & small agencies.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.caption("ClientFlow AI • v1.0")


# =========================================================
# DASHBOARD STATS
# =========================================================

stats = get_dashboard_stats()


# =========================================================
# DASHBOARD
# =========================================================

if page == "📊 Dashboard":

    st.title("Good morning 👋")

    st.markdown(
        '<div class="subtitle">'
        "Here’s what’s happening with your business today."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Total Clients
                </div>
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

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Active Projects
                </div>
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

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Pending Tasks
                </div>
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

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">
                    Outstanding
                </div>
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

    st.markdown(
        '<div class="section-title">'
        "Business Overview"
        "</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown(
            """
            <div class="dashboard-card">

                <h3>Revenue Overview</h3>

                <p style="color:#777;">
                    Revenue analytics will appear here
                    as invoices and payments are added.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="dashboard-card">

                <h3>Recent Activity</h3>

                <p style="color:#777;">
                    Your latest client and project activity
                    will appear here.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:

        st.markdown(
            """
            <div class="dashboard-card">

                <h3>Quick Actions</h3>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "＋ Add Client",
            use_container_width=True,
        ):
            st.info(
                "Open **👥 Clients** from the sidebar."
            )

        if st.button(
            "＋ Create Project",
            use_container_width=True,
        ):
            st.info(
                "Open **📁 Projects** from the sidebar."
            )

        if st.button(
            "＋ Create Task",
            use_container_width=True,
        ):
            st.info(
                "Open **✅ Tasks** from the sidebar."
            )

        if st.button(
            "＋ Create Proposal",
            use_container_width=True,
        ):
            st.info(
                "Proposal Builder will be added soon."
            )

        if st.button(
            "＋ Create Invoice",
            use_container_width=True,
        ):
            st.info(
                "Invoice Generator will be added soon."
            )

    st.markdown(
        '<div class="section-title">'
        "Getting Started"
        "</div>",
        unsafe_allow_html=True,
    )

    if stats["clients"] == 0:

        st.info(
            "👋 Welcome to ClientFlow AI! "
            "Start by adding your first client."
        )

    else:

        st.success(
            f"You currently have "
            f"{stats['clients']} client(s) in your workspace."
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

    st.title("Proposals")

    st.write(
        "Create professional proposals for your clients."
    )

    st.info(
        "🚧 Proposal Builder is coming soon."
    )


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
        "🚧 AI Assistant will be added after the core CRM workflows."
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
