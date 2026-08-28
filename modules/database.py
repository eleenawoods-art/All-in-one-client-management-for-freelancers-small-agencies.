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
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.executescript(
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
        );


        CREATE TABLE IF NOT EXISTS proposal_items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            proposal_id INTEGER,

            service TEXT NOT NULL,

            price REAL DEFAULT 0,

            FOREIGN KEY (proposal_id)
                REFERENCES proposals(id)
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
        );


        CREATE TABLE IF NOT EXISTS invoice_items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            invoice_id INTEGER,

            service TEXT NOT NULL,

            quantity INTEGER DEFAULT 1,

            price REAL DEFAULT 0,

            FOREIGN KEY (invoice_id)
                REFERENCES invoices(id)
        );


        CREATE TABLE IF NOT EXISTS settings (

            key TEXT PRIMARY KEY,

            value TEXT
        );

        """
    )

    connection.commit()

    connection.close()


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

def get_dashboard_stats():

    connection = get_connection()

    cursor = connection.cursor()

    clients = cursor.execute(
        """
        SELECT COUNT(*)
        FROM clients
        """
    ).fetchone()[0]

    projects = cursor.execute(
        """
        SELECT COUNT(*)
        FROM projects
        WHERE status = 'Active'
        """
    ).fetchone()[0]

    tasks = cursor.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE status != 'Completed'
        """
    ).fetchone()[0]

    outstanding = cursor.execute(
        """
        SELECT COALESCE(SUM(total), 0)
        FROM invoices
        WHERE status != 'Paid'
        """
    ).fetchone()[0]

    connection.close()

    return {
        "clients": clients,
        "projects": projects,
        "tasks": tasks,
        "outstanding": outstanding,
    }
