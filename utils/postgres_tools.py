import pandas as pd
import psycopg2
import csv
import os
import subprocess
import filtered_stream as fs
from sqlalchemy import create_engine
from dotenv import load_dotenv
load_dotenv()

POSTGRES_ADMIN_USER = "postgres"
POSTGRES_USER = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# POSTGRES CONNECTION CURSOR VERSION
# def check_postgres():
#     try:
#         conn = psycopg2.connect(
#             host="localhost",
#             database="test",
#             user=POSTGRES_USER,
#             password=POSTGRES_PASSWORD)
#         print("Postgres is running and configured correctly")
#         cur = conn.cursor()
#         cur.execute(
#             f"SELECT 1 FROM pg_roles WHERE rolname='{POSTGRES_USER}'")
#         if cur.fetchone():
#             print(f"Role {POSTGRES_USER} exists")
#             return True
#         else:
#             print(f"Role {POSTGRES_USER} does not exist")
#             return False
#     except psycopg2.OperationalError as e:
#         print(f"PostgreSQL is not running or configured: {e}")
#         return False


# def start_postgres():
#     print("\nStarting PostgreSQL...")

#     # subprocess.run(["pg_ctl", "start"])
#     subprocess.run(
#         ["pg_ctl", "-D", "/opt/homebrew/var/postgresql@14", "start"])
#     conn = psycopg2.connect(
#         host="localhost",
#         database="test",
#         user=POSTGRES_USER,
#         password=POSTGRES_PASSWORD)
#     print("PostgreSQL started")


# def create_role_and_grant_admin_privileges(user, password):
#     try:
#         print("Starting connection to PostgreSQL...")
#         conn = psycopg2.connect(
#             host="localhost",
#             database="test",
#             user=user,
#             password=password)
#         cur = conn.cursor()
#         print("Connection to PostgreSQL successful")

#         cur.execute(f"CREATE ROLE {user} WITH LOGIN PASSWORD '{password}';")
#         cur.execute(f"ALTER ROLE {user} CREATEDB")
#         cur.execute(f"ALTER ROLE {user} CREATEROLE")
#         cur.execute(f"ALTER ROLE {user} INHERIT")
#         cur.execute(f"ALTER ROLE {user} LOGIN")
#         cur.execute(f"ALTER ROLE {user} REPLICATION")

#         cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE test TO {user};")
#         cur.execute(
#             f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {user};")
#         cur.execute(
#             f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {user};")
#         cur.execute(
#             f"GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {user};")

#         conn.commit()
#         print(f"Role {user} created and privileges granted")

#     except (Exception, psycopg2.DatabaseError) as error:
#         print(f"Error: {error}")

#     finally:
#         if conn is not None:
#             cur.close()
#             conn.close()

# POSTGRES SUBPROCESS VERSION

# CSV FUNCTIONS
def write_csv(df, csv_path):
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL)


def read_csv(csv_path):
    df = pd.read_csv(
        csv_path, index_col=0, on_bad_lines="skip")
    return df

# DATABASE ADMIN FUNCTIONS


def create_db(db_name, user):
    try:
        print("\nCreating database...")
        subprocess.run(["createdb", "-U", POSTGRES_ADMIN_USER,
                        "-O", user, db_name], check=True)
        print("Database created")
    except subprocess.CalledProcessError:
        print("Database '{}' already exists".format(db_name))


def create_role(user, password):
    try:
        subprocess.run(
            ["createuser", "-U", POSTGRES_ADMIN_USER, user], check=True)
        print("Role '{}' created.".format(user))
        subprocess.run(["psql", "-U", POSTGRES_ADMIN_USER, "-c",
                        f"ALTER USER {user} WITH PASSWORD '{password}'"], check=True)

    except subprocess.CalledProcessError:
        print("Role '{}' already exists.".format(user))

# DATABASE INTERACTION FUNCTIONS


def start_db(db_name):
    engine = create_engine(
        'postgresql://'+POSTGRES_USER+':'+POSTGRES_PASSWORD+'@localhost:5433/'+db_name)
    return engine


def write_to_db(engine, df, table_name):
    df.to_sql(table_name, engine, if_exists='append', index=True)


def get_admin_user(database_name):
    conn = psycopg2.connect(
        host="localhost",
        database=database_name,
        user="postgres",
        password=POSTGRES_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pg_user")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

# MAIN FUNCTION FOR COMPARING AND UPDATING DATABASE


def main():
    # Assuming database and roles aren't created yet
    # create_role(POSTGRES_USER, POSTGRES_PASSWORD)
    # create_db("test", POSTGRES_ADMIN_USER)

    # TODO: fix logic for getting export_df from fs to write to database
    # we will either call this in a listener that triggers with each new twitter listener trigger
    # or we will call this in a while loop that refreshes every x minutes and pushes DF updates to database

    # Assuming database and roles already exist
    engine = start_db("test")
    df = fs.get_export_df()
    print(df)

    # TODO: rework so that write_to_db() is called from filtered_stream.py()
    # deals with conncurrent get_stream never setting export_df proprely
    # this way we have the df and can inherit the engine from start here

    # TODO: add logic to compare metrics for author and included/parent author
    # aggregate stats for participating author + stats for included/parent author
    # compare to current dataabase and push changes? or overwrite?

    # write_to_db(engine, df, "df_table") # currently an empty frame for some reason


if __name__ == "__main__":
    main()
