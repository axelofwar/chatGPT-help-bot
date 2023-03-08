import pandas as pd
import psycopg2
import yaml
import csv
import os
import subprocess
# import filtered_stream as fs
from sqlalchemy import create_engine, Table, Column, Integer, Text, MetaData, select
from dotenv import load_dotenv
if 'GITHUB_ACTION' not in os.environ:
    load_dotenv()

'''
Tools for interacting with postgresql databases - contains functions for:
    - Connecting and creating a database
    - Creating a role
    - Writing a dataframe to a csv
    - Reading a dataframe from a csv
    - Starting our connection to the database
    - Writing a dataframe to the database
    - Getting the admin user of the database

TODO: add functions for adding columns to the table if they don't exist:
    - index
    - author
    - favorites
    - retweets
    - replies
    - tweet_id
'''

# POSTGRES CONFIG
POSTGRES_ADMIN_USER = "postgres"
# POSTGRES_USER = os.getenv("POSTGRES_USERNAME")  # github actions
# POSTGRES_USER = os.environ["POSTGRES_USERNAME"] # for local testing
POSTGRES_USER = os.getenv("RENDER_USERNAME")  # render database

# POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")  # github actions
# POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"] # for local testing
POSTGRES_PASSWORD = os.getenv("RENDER_PASSWORD")  # render database

# POSTGRES_HOST = os.getenv("POSTGRESQL_HOST")  # github actions
# POSTGRES_HOST = os.environ["POSTGRESQL_HOST"] # for local testing
POSTGRES_HOST = os.getenv("RENDER_HOST")  # render database

# POSTGRES_PORT = os.getenv("POSTGRESQL_PORT")  # github actions
# POSTGRES_PORT = os.environ["POSTGRESQL_PORT"] # for local testing
POSTGRES_PORT = os.getenv("RENDER_PORT")  # render database

with open("utils/yamls/config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

table_name = config["metrics_table_name"]

# POSTGRES SUBPROCESS FUNCTIONS
# CSV FUNCTIONS


def write_df_to_csv(df, csv_path):
    df.to_csv(csv_path, index=False, quoting=csv.QUOTE_ALL)


def read_df_to_csv(csv_path):
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
        # 'postgresql://'+POSTGRES_USER+':'+POSTGRES_PASSWORD+'@localhost:5433/'+db_name)
        'postgresql://'+POSTGRES_USER+':'+POSTGRES_PASSWORD+'@'+POSTGRES_HOST+':'+POSTGRES_PORT+'/'+db_name)

    return engine


def check_metrics_table(engine, table_name):

    metadata = MetaData(bind=engine)

    if not engine.has_table(table_name):
        print("Creating table...")
        Table(table_name, metadata,
              Column('index', Text),
              Column('Author', Text),
              Column('Favorites', Integer),
              Column('Retweets', Integer),
              Column('Replies', Integer),
              Column('Impressions', Integer),
              Column('Tweet ID', Text),
              )
        metadata.create_all()
        print("Metrics Table created")
    else:
        print(f"{table_name} Table already exists")


def check_users_table(engine, table_name):
    metadata = MetaData(bind=engine)

    if not engine.has_table(table_name):
        print("Creating table...")
        Table(table_name, metadata,
              Column('index', Text),
              Column('Name', Text),
              Column('Favorites', Integer),
              Column("Retweets", Integer),
              Column("Replies", Integer),
              Column("Impressions", Integer),
              )
        metadata.create_all()
        print("Table created")
    else:
        print(f"{table_name} Table already exists")


def check_pfp_table(engine, table_name):
    metadata = MetaData(bind=engine)

    if not engine.has_table(table_name):
        print("Creating table...")
        Table(table_name, metadata,
              Column('index', Text),
              Column('Name', Text),
              Column("Favorites", Integer),
              Column("Retweets", Integer),
              Column("Replies", Integer),
              Column("Impressions", Integer),
              )
        metadata.create_all()
        print("Table created")
    else:
        print(f"{table_name} Table already exists")


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


def get_all_user_metric_rows(engine, table_name, username):
    metadata = MetaData(bind=engine)
    table = Table(table_name, metadata, autoload=True)
    query = select([table]).where(table.columns.index == username)
    result = engine.execute(query)
    rows = result.fetchall()
    return rows


# MAIN FUNCTION FOR STANDALONE DB FUNCTIONS
# def main():
    # Assuming database and roles aren't created yet
    # create_role(POSTGRES_USER, POSTGRES_PASSWORD)
    # create_db("test", POSTGRES_ADMIN_USER)

    # with open("utils/yamls/config.yml", "r") as file:
    #     config = yaml.load(file, Loader=yaml.FullLoader)
    # Assuming database and roles already exist
    # engine = start_db(config["db_name"])
    # df = fs.get_export_df()
    # print(df)

    # write_to_db(engine, df, table_name'') # currently an empty frame for some reason


# if __name__ == "__main__":
#     main()
