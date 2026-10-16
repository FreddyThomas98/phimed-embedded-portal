import os
import msal
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import requests

try:
    import pyodbc
except ImportError:
    pyodbc = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env from backend directory first, or fallback to root
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

app = FastAPI(title="Phimed Embedded POC")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQL Server configuration (used when DB_TYPE=mssql)
SERVER = os.getenv("DB_SERVER", r"localhost\SQLEXPRESS")
DATABASE = os.getenv("DB_NAME", "Phimed_Embedded_POC")
USERNAME = os.getenv("DB_USER", "sa")
PASSWORD = os.getenv("DB_PASSWORD", "Manavalan@123")

# SQLite configuration (default for hosting)
SQLITE_DB_PATH = os.path.join(BASE_DIR, "phimed.db")
SQLITE_SEED_PATH = os.path.join(BASE_DIR, "seed.sql")


class AttrRow:
    """Row factory enabling dot-notation attribute access (e.g. row.ClientID) and indexing."""
    def __init__(self, cursor, row):
        for idx, col in enumerate(cursor.description):
            setattr(self, col[0], row[idx])
    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.__dict__.values())[item]
        return getattr(self, item)


class SQLiteCursorWrapper:
    """Cursor wrapper allowing pyodbc-style multiple arguments: execute(sql, arg1, arg2)."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, sql, *args):
        if not args:
            return self._cursor.execute(sql)
        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            params = args[0]
        else:
            params = args
        return self._cursor.execute(sql, params)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class SQLiteConnWrapper:
    """Connection wrapper returning SQLiteCursorWrapper."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())

    def close(self):
        self._conn.close()


def ensure_sqlite_db():
    """Ensure phimed.db exists; if not, initialize it from seed.sql automatically."""
    if not os.path.exists(SQLITE_DB_PATH) and os.path.exists(SQLITE_SEED_PATH):
        print(f"Initializing SQLite database at {SQLITE_DB_PATH} from seed.sql...")
        conn = sqlite3.connect(SQLITE_DB_PATH)
        with open(SQLITE_SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("SQLite database successfully initialized.")


def get_db_connection():
    if DB_TYPE == "mssql":
        if pyodbc is None:
            raise RuntimeError("pyodbc is not installed. Please install pyodbc or set DB_TYPE=sqlite.")
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={SERVER};"
            f"DATABASE={DATABASE};"
            f"UID={USERNAME};"
            f"PWD={PASSWORD};"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(connection_string)

    # Default: SQLite
    ensure_sqlite_db()
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = AttrRow
    return SQLiteConnWrapper(conn)


# Login request
class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/api/health")
def health():
    return {
        "message": "Phimed Embedded POC Backend is running",
        "database_type": DB_TYPE
    }


@app.get("/test-db")
def test_database():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        if DB_TYPE == "sqlite":
            cursor.execute("SELECT 'phimed.db (SQLite)'")
        else:
            cursor.execute("SELECT DB_NAME()")

        database_name = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "database": database_name
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/login")
def login(request: LoginRequest):

    connection = get_db_connection()
    cursor = connection.cursor()

    # =========================================================
    # FIND CLIENT
    # =========================================================

    cursor.execute(
        """
        SELECT
            c.ClientID,
            c.ClientName,
            c.Username,
            c.PasswordHash,
            c.GroupID,
            g.GroupName,
            g.RLSRole,
            g.AppID,
            a.AppName
        FROM Clients c

        INNER JOIN Groups g
            ON c.GroupID = g.GroupID

        INNER JOIN Apps a
            ON g.AppID = a.AppID

        WHERE c.Username = ?
          AND c.IsActive = 1
          AND g.IsActive = 1
          AND a.IsActive = 1
        """,
        request.email
    )

    client = cursor.fetchone()

    # =========================================================
    # CLIENT NOT FOUND
    # =========================================================

    if not client:
        cursor.close()
        connection.close()

        return {
            "status": "error",
            "message": "Invalid email or password"
        }

    # =========================================================
    # CLIENT INFORMATION
    # =========================================================

    client_id = client.ClientID
    client_name = client.ClientName
    username = client.Username
    stored_password = client.PasswordHash
    group_id = client.GroupID
    group_name = client.GroupName
    rls_role = client.RLSRole
    app_id = client.AppID
    app_name = client.AppName

    # =========================================================
    # CHECK PASSWORD
    # =========================================================

    if request.password != stored_password:

        cursor.close()
        connection.close()

        return {
            "status": "error",
            "message": "Invalid email or password"
        }

    # =========================================================
    # GET REPORTS FOR THIS CLIENT'S APP
    # =========================================================

    cursor.execute(
        """
        SELECT
            r.ReportID,
            r.ReportName,
            r.PowerBIReportID,
            r.WorkspaceID,
            r.IsRLS

        FROM AppReportAccess ara

        INNER JOIN Reports r
            ON ara.ReportID = r.ReportID

        WHERE ara.AppID = ?
          AND r.IsActive = 1

        ORDER BY r.ReportID
        """,
        app_id
    )

    reports = cursor.fetchall()

    # =========================================================
    # BUILD REPORT LIST
    # =========================================================

    report_list = []

    for report in reports:

        report_list.append({
            "report_id": report.ReportID,
            "report_name": report.ReportName,
            "powerbi_report_id": str(report.PowerBIReportID),
            "workspace_id": str(report.WorkspaceID),
            "is_rls": bool(report.IsRLS)
        })

    cursor.close()
    connection.close()

    # =========================================================
    # LOGIN SUCCESS
    # =========================================================

    return {
        "status": "success",

        "user": {
            "user_id": client_id,
            "name": client_name,
            "email": username,
            "client_id": client_id,

            "group_id": group_id,
            "group_name": group_name,

            "app_id": app_id,
            "app_name": app_name,

            "rls_role": rls_role
        },

        "reports": report_list
    }

@app.get("/test-entra")
def test_entra():
    try:
        result = msal_app.acquire_token_for_client(
            scopes=["https://analysis.windows.net/powerbi/api/.default"]
        )

        if "access_token" in result:
            return {
                "status": "success",
                "message": "Microsoft Entra authentication successful"
            }

        return {
            "status": "error",
            "error": result.get("error"),
            "error_description": result.get("error_description")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/test-powerbi")
def test_powerbi():
    try:
        # Get Microsoft Entra access token
        token_result = msal_app.acquire_token_for_client(
            scopes=["https://analysis.windows.net/powerbi/api/.default"]
        )

        if "access_token" not in token_result:
            return {
                "status": "error",
                "message": "Could not get Microsoft Entra access token",
                "error": token_result.get("error_description")
            }

        access_token = token_result["access_token"]

        # Your Power BI workspace
        workspace_id = "067b608f-823f-4b49-b2ad-db8a23b7734d"

        # Call Power BI REST API
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            return {
                "status": "success",
                "message": "Power BI workspace access successful",
                "reports": [
                    {
                        "id": report["id"],
                        "name": report["name"]
                    }
                    for report in data.get("value", [])
                ]
            }

        return {
            "status": "error",
            "status_code": response.status_code,
            "message": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/generate-embed-token")
def generate_embed_token():
    try:
        # Get Microsoft Entra access token
        token_result = msal_app.acquire_token_for_client(
            scopes=["https://analysis.windows.net/powerbi/api/.default"]
        )

        if "access_token" not in token_result:
            return {
                "status": "error",
                "message": "Could not get Microsoft Entra access token",
                "error": token_result.get("error_description")
            }

        access_token = token_result["access_token"]

        # KPI report and semantic model
        report_id = "304622c8-04b3-44b4-a37d-253faa49a319"
        dataset_id = "4af3acd5-3320-477b-a57c-ea15d7a413ad"

        url = "https://api.powerbi.com/v1.0/myorg/GenerateToken"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        body = {
            "reports": [
                {
                    "id": report_id
                }
            ],
            "datasets": [
                {
                    "id": dataset_id
                }
            ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=body
        )

        if response.status_code == 200:
            data = response.json()

            return {
                "status": "success",
                "message": "Embed token generated successfully",
                "expiration": data.get("expiration"),
                "token_generated": True
            }

        return {
            "status": "error",
            "status_code": response.status_code,
            "message": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/get-kpi-dataset")
def get_kpi_dataset():
    try:
        token_result = msal_app.acquire_token_for_client(
            scopes=["https://analysis.windows.net/powerbi/api/.default"]
        )

        if "access_token" not in token_result:
            return {
                "status": "error",
                "message": "Could not get Microsoft Entra access token",
                "error": token_result.get("error_description")
            }

        access_token = token_result["access_token"]

        workspace_id = "067b608f-823f-4b49-b2ad-db8a23b7734d"

        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            return {
                "status": "success",
                "datasets": [
                    {
                        "id": dataset["id"],
                        "name": dataset["name"]
                    }
                    for dataset in data.get("value", [])
                ]
            }

        return {
            "status": "error",
            "status_code": response.status_code,
            "message": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/report-pages/{report_id}")
def get_report_pages(report_id: str):
    try:
        # Get Microsoft Entra access token
        token_result = msal_app.acquire_token_for_client(
            scopes=["https://analysis.windows.net/powerbi/api/.default"]
        )

        if "access_token" not in token_result:
            return {
                "status": "error",
                "message": "Could not get Microsoft Entra access token",
                "error": token_result.get("error_description")
            }

        access_token = token_result["access_token"]

        workspace_id = "067b608f-823f-4b49-b2ad-db8a23b7734d"

        url = (
            f"https://api.powerbi.com/v1.0/myorg/"
            f"groups/{workspace_id}/reports/{report_id}/pages"
        )

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()

            return {
                "status": "success",
                "pages": [
                    {
                        "name": page["name"],
                        "display_name": page["displayName"],
                        "order": page["order"]
                    }
                    for page in data.get("value", [])
                ]
            }

        return {
            "status": "error",
            "status_code": response.status_code,
            "message": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/embed-token/{report_id}")
def get_embed_token(report_id: str, user_id: int):

    try:

        # =========================================================
        # CHECK CLIENT -> GROUP -> APP -> REPORT ACCESS
        # ALSO GET RLS INFORMATION
        # =========================================================

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                c.ClientID,
                c.Username,
                c.IsActive AS ClientIsActive,

                g.GroupID,
                g.GroupName,
                g.RLSRole,

                a.AppID,
                a.AppName,

                r.ReportID,
                r.IsRLS,
                r.PowerBIReportID,
                r.WorkspaceID

            FROM Clients c

            INNER JOIN Groups g
                ON c.GroupID = g.GroupID

            INNER JOIN Apps a
                ON g.AppID = a.AppID

            INNER JOIN AppReportAccess ara
                ON a.AppID = ara.AppID

            INNER JOIN Reports r
                ON ara.ReportID = r.ReportID

            WHERE c.ClientID = ?
              AND c.IsActive = 1
              AND g.IsActive = 1
              AND a.IsActive = 1
              AND r.PowerBIReportID = ?
              AND r.IsActive = 1
            """,
            user_id,
            report_id
        )

        access = cursor.fetchone()

        # =========================================================
        # CLIENT DOES NOT HAVE ACCESS
        # =========================================================

        if not access:

            cursor.close()
            connection.close()

            return {
                "status": "error",
                "message": "You do not have access to this report"
            }

        client_id = access.ClientID
        user_email = access.Username
        group_id = access.GroupID
        group_name = access.GroupName
        rls_role = access.RLSRole
        is_rls = access.IsRLS

        # =========================================================
        # RLS REPORT
        # =========================================================

        if is_rls:

            if not rls_role:

                cursor.close()
                connection.close()

                return {
                    "status": "error",
                    "message": (
                        "This report requires RLS, "
                        "but no RLS role is assigned to the client's group"
                    )
                }

        cursor.close()
        connection.close()

        # =========================================================
        # GET MICROSOFT ENTRA ACCESS TOKEN
        # =========================================================

        token_result = msal_app.acquire_token_for_client(
            scopes=[
                "https://analysis.windows.net/powerbi/api/.default"
            ]
        )

        if "access_token" not in token_result:

            return {
                "status": "error",
                "message": "Could not get Microsoft Entra access token",
                "error": token_result.get("error_description")
            }

        access_token = token_result["access_token"]

        # =========================================================
        # POWER BI WORKSPACE
        # =========================================================

        workspace_id = str(access.WorkspaceID)

        # =========================================================
        # FIND SEMANTIC MODEL ASSOCIATED WITH REPORT
        # =========================================================

        dataset_url = (
            f"https://api.powerbi.com/v1.0/myorg/"
            f"groups/{workspace_id}/reports/{report_id}"
        )

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        report_response = requests.get(
            dataset_url,
            headers=headers
        )

        if report_response.status_code != 200:

            return {
                "status": "error",
                "message": "Could not find Power BI report",
                "details": report_response.text
            }

        report_data = report_response.json()

        dataset_id = report_data.get("datasetId")

        if not dataset_id:

            return {
                "status": "error",
                "message": "No semantic model found for this report"
            }

        # =========================================================
        # GENERATE EMBED TOKEN
        # =========================================================

        generate_url = (
            "https://api.powerbi.com/v1.0/myorg/"
            "GenerateToken"
        )

        body = {
            "reports": [
                {
                    "id": report_id
                }
            ],
            "datasets": [
                {
                    "id": dataset_id
                }
            ]
        }

        # =========================================================
        # DYNAMIC RLS
        #
        # Client
        #   -> Group
        #       -> RLSRole
        #
        # Only RLS reports receive an identity.
        # =========================================================

        if is_rls:

            body["identities"] = [
                {
                    "username": user_email,
                    "roles": [
                        rls_role
                    ],
                    "datasets": [
                        dataset_id
                    ]
                }
            ]

        # =========================================================
        # CALL POWER BI GENERATE TOKEN API
        # =========================================================

        token_response = requests.post(
            generate_url,

            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },

            json=body
        )

        if token_response.status_code != 200:

            return {
                "status": "error",
                "status_code": token_response.status_code,
                "message": token_response.text
            }

        token_data = token_response.json()

        # =========================================================
        # SUCCESS
        # =========================================================

        return {
            "status": "success",

            "report_id": report_id,

            "dataset_id": dataset_id,

            "embed_url": report_data.get("embedUrl"),

            "embed_token": token_data.get("token"),

            "expiration": token_data.get("expiration"),

            "client_id": client_id,

            "group_id": group_id,

            "group_name": group_name,

            "rls_enabled": bool(is_rls),

            "rls_role": rls_role
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# MOUNT FRONTEND STATIC FILES (FOR CLOUD HOSTING)
# =========================================================
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def home():
        return {
            "message": "Phimed Embedded POC Backend is running",
            "database_type": DB_TYPE
        }