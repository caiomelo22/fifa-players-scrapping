import os
import numpy as np
import mysql.connector


class MySQLService:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_DATABASE")
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            self.cursor = self.conn.cursor()
            print("Connected to MySQL database")
        except mysql.connector.Error as e:
            print(f"Error connecting to MySQL database: {e}")
            raise

    def create_table(self, table_name, columns):
        try:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            self.cursor.execute(query)
            self.conn.commit()
            print(f"Table '{table_name}' created successfully.")
        except mysql.connector.Error as e:
            print(f"Error creating table: {e}")
            self.conn.rollback()

    def create_table_from_df(self, table_name, df):
        try:
            columns = []

            # Mapping data types for table creation
            type_mapping = {
                "int64": "INT",
                "float64": "FLOAT",
                "datetime64[ns]": "DATETIME",
                "object": "VARCHAR(255)",
            }

            # Iterate over DataFrame columns to determine data types for table creation
            for col, dtype in df.dtypes.items():
                col_type = type_mapping.get(str(dtype), "VARCHAR(255)")
                columns.append(f"{col} {col_type}")

            # Find the position of "id" column and set it as the primary key
            id_index = df.columns.get_loc("id") if "id" in df.columns else None
            if id_index is not None:
                columns[id_index] = f"{columns[id_index]} PRIMARY KEY"

            # Create the table
            self.create_table(table_name=table_name, columns=columns)
        except Exception as e:
            print(f"Error creating table: {e}")

    def insert_multiple_rows_from_dataframe(self, table_name, df):
        try:
            # Convert DataFrame to a list of dicts
            data_list = df.to_dict(orient='records')
            
            # Check if the "id" exists in any of the rows in the DataFrame
            existing_ids = set()
            for data in data_list:
                id_value = data.get("id")
                if id_value is not None:
                    existing_ids.add(id_value)

            # Query the database to see if any of the IDs already exist in the table
            if existing_ids:
                self.cursor.execute(f"SELECT id FROM {table_name} WHERE id IN ({', '.join(map(str, existing_ids))})")
                existing_id_results = self.cursor.fetchall()
                existing_ids_in_table = {result[0] for result in existing_id_results}

                # Filter out rows with existing IDs to skip insertion
                data_list = [data for data in data_list if data.get("id") not in existing_ids_in_table]

            if not data_list:
                print("There were not rows to insert.")
                return

            # Extract columns and values from the data_list
            columns = data_list[0].keys()
            values = [tuple(row.values()) for row in data_list]
            
            # Generate the query
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
            
            # Execute the query and commit the changes
            self.cursor.executemany(query, values)
            self.conn.commit()
            
            print("Multiple rows inserted successfully.")
        except mysql.connector.Error as e:
            print(f"Error inserting multiple rows: {e}")
            self.conn.rollback()

    def close(self):
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print("Connection to MySQL database closed.")
