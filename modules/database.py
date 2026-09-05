```python
import sqlite3
from pathlib import Path


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "clientflow.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 30000")

    return connection


# =========================================================
# DATABASE MIGRATIONS
# =========================================================

def add_column_if_missing(
    connection,
    table_name,
    column_name,
    column_definition,
):
    columns = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = {
        column["name"] for column in columns
    }

    if column_name not in existing_columns:
        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


def migrate_database(connection):

    # Tasks migrations
    add_column_if_missing(
        connection,
        "tasks",
        "description",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "tasks",
        "due_date",
        "TEXT",
    )

    add_column_if_missing(
        connection,
        "tasks",
        "assignee",
        "TEXT",
    )

    # Keep old deadline values compatible
    connection.execute(
        """
        UPDATE tasks
        SET due_date = deadline
        WHERE
            (due_date IS NULL OR due_date = '')
            AND deadline IS NOT NULL
            AND deadline != ''
        """
    )

    connection.commit()


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    connection = get_connection()

    connection.executescript(
        """

        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            email TEXT,
            phone TEXT,
            website TEXT,
            status TEXT NOT NULL DEFAULT 'Lead',
            notes TEXT,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        );


        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            deadline TEXT,
            progress INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (client_id)
                REFERENCES clients(id)
                ON DELETE SET NULL
        );


        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            deadline TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'To Do',
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (project_id)
                REFERENCES projects(id)
                ON DELETE SET NULL
        );


        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            timeline TEXT,
            payment_terms TEXT,
            status TEXT DEFAULT 'Draft',
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (client_id)
                REFERENCES clients(id)
                ON DELETE SET NULL
        );


        CREATE TABLE IF NOT EXISTS proposal_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER,
            service TEXT NOT NULL,
            price REAL DEFAULT 0,

            FOREIGN KEY (proposal_id)
                REFERENCES proposals(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            invoice_number TEXT UNIQUE,
            due_date TEXT,
            subtotal REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            total REAL DEFAULT 0,
            status TEXT DEFAULT 'Unpaid',
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (client_id)
                REFERENCES clients(id)
                ON DELETE SET NULL
        );


        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            service TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            price REAL DEFAULT 0,

            FOREIGN KEY (invoice_id)
                REFERENCES invoices(id)
                ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        """
    )

    connection.commit()

    migrate_database(connection)

    connection.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_projects_client_id
            ON projects(client_id);

        CREATE INDEX IF NOT EXISTS idx_tasks_project_id
            ON tasks(project_id);

        CREATE INDEX IF NOT EXISTS idx_proposals_client_id
            ON proposals(client_id);

        CREATE INDEX IF NOT EXISTS idx_proposal_items_proposal_id
            ON proposal_items(proposal_id);

        CREATE INDEX IF NOT EXISTS idx_invoices_client_id
            ON invoices(client_id);

        CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id
            ON invoice_items(invoice_id);
        """
    )

    connection.commit()
    connection.close()


# =========================================================
# DASHBOARD STATS
# =========================================================

def get_dashboard_stats():

    connection = get_connection()

    clients = connection.execute(
        """
        SELECT COUNT(*)
        FROM clients
        """
    ).fetchone()[0]

    projects = connection.execute(
        """
        SELECT COUNT(*)
        FROM projects
        WHERE status = 'Active'
        """
    ).fetchone()[0]

    tasks = connection.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE status != 'Done'
        """
    ).fetchone()[0]

    outstanding = connection.execute(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM invoices
        WHERE status != 'Paid'
        """
    ).fetchone()[0]

    paid_revenue = connection.execute(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM invoices
        WHERE status = 'Paid'
        """
    ).fetchone()[0]

    total_invoices = connection.execute(
        """
        SELECT COUNT(*)
        FROM invoices
        """
    ).fetchone()[0]

    paid_invoices = connection.execute(
        """
        SELECT COUNT(*)
        FROM invoices
        WHERE status = 'Paid'
        """
    ).fetchone()[0]

    proposals = connection.execute(
        """
        SELECT COUNT(*)
        FROM proposals
        """
    ).fetchone()[0]

    connection.close()

    return {
        "clients": clients,
        "projects": projects,
        "tasks": tasks,
        "outstanding": float(outstanding or 0),
        "paid_revenue": float(paid_revenue or 0),
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "proposals": proposals,
    }


# =========================================================
# REVENUE DATA
# =========================================================

def get_revenue_overview():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            substr(created_at, 1, 7) AS month,
            COALESCE(SUM(total), 0) AS revenue
        FROM invoices
        WHERE status = 'Paid'
        GROUP BY substr(created_at, 1, 7)
        ORDER BY month ASC
        LIMIT 12
        """
    ).fetchall()

    connection.close()

    return [
        {
            "month": row["month"],
            "revenue": float(row["revenue"] or 0),
        }
        for row in rows
    ]


# =========================================================
# RECENT ACTIVITY
# =========================================================

def get_recent_activity(limit=8):

    connection = get_connection()

    activities = []

    rows = connection.execute(
        """
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

        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    for row in rows:

        if row["type"] == "Client":
            title = f"New client: {row['title']}"

        elif row["type"] == "Project":
            title = f"Project created: {row['title']}"

        elif row["type"] == "Proposal":
            title = f"Proposal created: {row['title']}"

        else:
            title = f"Invoice created: {row['title']}"

        activities.append(
            {
                "type": row["type"],
                "title": title,
                "created_at": row["created_at"],
            }
        )

    return activities


# =========================================================
# UPCOMING TASKS
# =========================================================

def get_upcoming_tasks(limit=5):

    connection = get_connection()

    rows = connection.execute(
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
            COALESCE(
                NULLIF(tasks.due_date, ''),
                tasks.deadline
            ) ASC

        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    return [
        {
            "title": row["title"],
            "due_date": row["due_date"],
            "priority": row["priority"] or "Medium",
            "status": row["status"] or "To Do",
            "project_name": row["project_name"],
        }
        for row in rows
    ]
```
