import streamlit as st

from modules.database import init_db, get_dashboard_stats


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
# INITIALIZE DATABASE
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
        border-right: 1px solid rgba(128, 128, 128, 0.18);
    }

    .brand {
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 1.5rem;
    }

    .subtitle {
        color: #777;
        margin-top: -0.8rem;
        margin-bottom: 2rem;
    }

    .metric-card {
        padding: 1.2rem;
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 16px;
        background: rgba(128, 128, 128, 0.035);
        min-height: 115px;
    }

    .metric-label {
        font-size: 0.86rem;
        color: #777;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 750;
        margin-top: 0.3rem;
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin: 1.6rem 0 0.8rem;
    }

    .info-card {
        padding: 1.3rem;
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 16px;
        background: rgba(128, 128, 128, 0.035);
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

    st.caption("CLIENT MANAGEMENT")

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
        "All-in-one client management for freelancers "
        "and small agencies."
    )

    st.divider()

    st.caption("ClientFlow AI v1.0")


# =========================================================
# DASHBOARD DATA
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

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Clients</div>
                <div class="metric-value">{stats["clients"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Active Projects</div>
                <div class="metric-value">{stats["projects"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Pending Tasks</div>
                <div class="metric-value">{stats["tasks"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Outstanding</div>
                <div class="metric-value">
                    ${stats["outstanding"]:,.0f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # MAIN DASHBOARD
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Business Overview</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1])

    with left:

        st.markdown("### Revenue Overview")

        st.info(
            "Revenue analytics will appear here as invoices "
            "and payments are added."
        )

        st.markdown("### Recent Activity")

        st.empty()

        st.caption(
            "No activity yet. Add your first client or project "
            "to get started."
        )

    with right:

        st.markdown("### Quick Actions")

        if st.button(
            "＋ Add Client",
            use_container_width=True,
        ):
            st.session_state["quick_action"] = "Clients"

        if st.button(
            "＋ Create Project",
            use_container_width=True,
        ):
            st.session_state["quick_action"] = "Projects"

        if st.button(
            "＋ Create Proposal",
            use_container_width=True,
        ):
            st.session_state["quick_action"] = "Proposals"

        if st.button(
            "＋ Create Invoice",
            use_container_width=True,
        ):
            st.session_state["quick_action"] = "Invoices"

    # -----------------------------------------------------
    # GETTING STARTED
    # -----------------------------------------------------

    st.markdown(
        '<div class="section-title">Getting Started</div>',
        unsafe_allow_html=True,
    )

    st.success(
        "Your ClientFlow AI workspace is ready. "
        "Next we’ll add the complete client, project, "
        "task, proposal, invoice, AI and reporting workflows."
    )


# =========================================================
# OTHER MODULES
# =========================================================

else:

    module_info = {

        "👥 Clients": (
            "Clients",
            "Manage leads, active clients, and completed relationships.",
        ),

        "📁 Projects": (
            "Projects",
            "Track projects, deadlines, priorities, and progress.",
        ),

        "✅ Tasks": (
            "Tasks",
            "Organize work across your projects.",
        ),

        "📄 Proposals": (
            "Proposals",
            "Create professional proposals and export them as PDF.",
        ),

        "💰 Invoices": (
            "Invoices",
            "Create invoices, manage due dates, and export PDF invoices.",
        ),

        "🤖 AI Assistant": (
            "AI Assistant",
            "Generate proposals, emails, follow-ups, "
            "project descriptions, and meeting summaries.",
        ),

        "📈 Reports": (
            "Reports",
            "Track revenue, clients, projects, "
            "and outstanding invoices.",
        ),
    }

    title, description = module_info[page]

    st.title(title)

    st.markdown(
        f'<div class="subtitle">{description}</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "This module is part of the ClientFlow AI foundation. "
        "The full workflow will be added in the next development phase."
    )
