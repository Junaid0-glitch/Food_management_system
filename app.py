# Imported all the necessary libraries.
import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

# Connecting to the database.
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="juddy17",
        database="food_data"
    )

# Making functions to run quaries.
def run_query(query, params=None):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
    cursor.close()
    conn.close()
    return df

def run_execute(query, params=None):
    conn = init_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    cursor.close()
    conn.close()

st.set_page_config(page_title="Food Data Dashboard", layout="wide")
st.title("🍽 Food Data Dashboard")

menu = st.sidebar.radio(
    "Navigation",
    ["View Tables", "CRUD Operations", "SQL Queries & Visualization", "Filter Donations", "Contact Directory"]
)

# function to view all the labels.
if menu == "View Tables":
    st.header("📋 View All Tables")
    for table in ['providers', 'receivers', 'claims', 'food_listings']:
        st.subheader(table.capitalize())
        df = run_query(f"SELECT * FROM {table};")
        st.dataframe(df)

# Function For CRUD OPERATIONS.

elif menu == "CRUD Operations":
    st.header("✏️ CRUD Operations")
    table = st.selectbox("Select Table", ['providers', 'receivers', 'claims', 'food_listings'])
    operation = st.selectbox("Operation", ["Add", "Delete", "Update"])
    df_schema = run_query(f"SELECT * FROM {table} LIMIT 1;")
    columns = df_schema.columns.tolist()
    defaults = {
        'providers': [1, "Gonzales-Cochran", "Supermarket", "74347 Christopher Extensions Andreamouth, OK 91839", "New Jessica", "+1-600-220-0480"],
        'receivers': [1, "Donald Gomez", "Shelter", "Port Carlburgh", "(955)922-5295"],
        'claims': [1, 164, 908, "Pending", "3/5/2025 5:26"],
        'food_listings': [1, "Bread", 43, "3/17/2025", 110, "Grocery Store", "South Kellyville", "Non-Vegetarian", "Breakfast"]
    }
    int_columns = {'providers':[0],'receivers':[0],'claims':[0,1,2],'food_listings':[0,2,4]}
    if operation=="Add":
        values = []
        for i, col in enumerate(columns):
            default = defaults.get(table, [""]*len(columns))[i]
            if i in int_columns.get(table,[]):
                val = st.text_input(f"Enter {col}", value=str(default))
                try: val = int(val)
                except: st.warning(f"{col} should be integer.")
            else:
                val = st.text_input(f"Enter {col}", value=default)
            values.append(val)
        if st.button("Add Row"):
            placeholders = ', '.join(['%s']*len(columns))
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            run_execute(query, values)
            st.success("✅ Row Added!")
    elif operation=="Delete":
        id_col = columns[0]
        default_id = defaults.get(table,[""])[0]
        del_id = st.text_input(f"Enter {id_col} to delete", value=str(default_id))
        if 0 in int_columns.get(table,[]):
            try: del_id = int(del_id)
            except: st.warning(f"{id_col} should be integer.")
        if st.button("Delete Row"):
            query = f"DELETE FROM {table} WHERE {id_col} = %s"
            run_execute(query, (del_id,))
            st.success("🗑 Row Deleted")
    elif operation=="Update":
        id_col = columns[0]
        default_id = defaults.get(table,[""])[0]
        upd_id = st.text_input(f"Enter {id_col} to update", value=str(default_id))
        if 0 in int_columns.get(table,[]):
            try: upd_id = int(upd_id)
            except: st.warning(f"{id_col} should be integer.")
        upd_col = st.selectbox("Column to update", columns[1:])
        upd_val = st.text_input(f"New value for {upd_col}")
        upd_col_index = columns.index(upd_col)
        if upd_col_index in int_columns.get(table,[]):
            try: upd_val = int(upd_val)
            except: st.warning(f"{upd_col} should be integer.")
        if st.button("Update Row"):
            query = f"UPDATE {table} SET {upd_col} = %s WHERE {id_col} = %s"
            run_execute(query, (upd_val, upd_id))
            st.success("🔄 Row Updated")

# Function For SQL QUERIES & VISUALIZATION.
# I write all those quaries here.
elif menu == "SQL Queries & Visualization":
    st.header("📊 Predefined SQL Queries & Visualizations")
    queries = {
        "Providers by Total Quantity Donated": """
            SELECT p.Name AS provider_name, SUM(fl.Quantity) AS total_quantity_donated
            FROM providers p JOIN food_listings fl ON p.Provider_ID = fl.Provider_ID
            GROUP BY p.Provider_ID, p.Name
            ORDER BY total_quantity_donated DESC
            LIMIT 15;
        """,
        "How many food providers and receivers are there in each city?": """
            SELECT p.City AS city,
                COUNT(DISTINCT p.Provider_ID) AS num_providers,
                COUNT(DISTINCT r.Receiver_ID) AS num_receivers
            FROM providers p
            LEFT JOIN receivers r ON p.City = r.City
            GROUP BY p.City
            ORDER BY num_providers DESC
            LIMIT 15;
        """,
        "Top food items by number of claims": """
            SELECT fl.Food_Name, COUNT(c.Claim_ID) AS total_claims
            FROM food_listings fl
            JOIN claims c ON fl.Food_ID = c.Food_ID
            GROUP BY fl.Food_Name
            ORDER BY total_claims DESC
            LIMIT 15;
        """,
        "Meal type claimed the most": """
            SELECT fl.Meal_Type, COUNT(c.Claim_ID) AS total_claims
            FROM claims c
            JOIN food_listings fl ON c.Food_ID = fl.Food_ID
            GROUP BY fl.Meal_Type
            ORDER BY total_claims DESC;
        """,
        "Claims by Status": """
            SELECT Status, COUNT(*) AS count_status
            FROM claims
            GROUP BY Status;
        """,
        "Most Common Food Types": """
            SELECT Food_Type, COUNT(Food_ID) AS count_food_type
            FROM food_listings
            GROUP BY Food_Type
            ORDER BY count_food_type DESC
            LIMIT 15;
        """,
        "City with highest number of food listings": """
            SELECT Location AS city, COUNT(Food_ID) AS num_food_listings
            FROM food_listings
            GROUP BY Location
            ORDER BY num_food_listings DESC
            LIMIT 15;
        """,
        "Total quantity of food available": """
            SELECT SUM(Quantity) AS total_quantity
            FROM food_listings;
        """,
        "Providers in New Jessica with address & contact": """
            SELECT p.Address, p.Contact
            FROM providers p
            WHERE p.City = 'New Jessica';
        """,
        "Receivers with highest total quantity claimed": """
            SELECT r.Name AS receiver_name,
                SUM(f.Quantity) AS total_quantity
            FROM claims c
            JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY total_quantity DESC
            LIMIT 15;
        """
    }
    selected_query = st.selectbox("Select Query", list(queries.keys()))
    df = run_query(queries[selected_query])
    st.dataframe(df)

#   The logic to print plots.
    fig, ax = plt.subplots(figsize=(12,6))
    try:
        if "provider_name" in df.columns and "total_quantity_donated" in df.columns:
            df["total_quantity_donated"] = pd.to_numeric(df["total_quantity_donated"], errors="coerce")
            df.set_index("provider_name")["total_quantity_donated"].plot(kind="barh", ax=ax)
            ax.set_title("Providers by Total Quantity Donated")
            plt.gca().invert_yaxis()
            st.pyplot(fig)
        elif "city" in df.columns and "num_providers" in df.columns:
            df["num_providers"] = pd.to_numeric(df["num_providers"], errors="coerce")
            df["num_receivers"] = pd.to_numeric(df["num_receivers"], errors="coerce")
            df.set_index("city")[["num_providers", "num_receivers"]].plot(kind="barh", ax=ax)
            ax.set_title("Providers and Receivers per City")
            plt.gca().invert_yaxis()
            st.pyplot(fig)
        elif "Food_Name" in df.columns and "total_claims" in df.columns:
            df["total_claims"] = pd.to_numeric(df["total_claims"], errors="coerce")
            df.set_index("Food_Name")["total_claims"].plot(kind="barh", ax=ax)
            ax.set_title("Top food items by number of claims")
            plt.gca().invert_yaxis()
            st.pyplot(fig)
        elif "Meal_Type" in df.columns and "total_claims" in df.columns:
            df["total_claims"] = pd.to_numeric(df["total_claims"], errors="coerce")
            df.set_index("Meal_Type")["total_claims"].plot(kind="bar", ax=ax)
            ax.set_title("Meal Type Claimed the Most")
            st.pyplot(fig)
        elif "Status" in df.columns and "count_status" in df.columns:
            df["count_status"] = pd.to_numeric(df["count_status"], errors="coerce")
            total = df["count_status"].sum()
            df["percentage"] = (df["count_status"] / total) * 100
            df.set_index("Status")["percentage"].plot(kind="bar", ax=ax)
            ax.set_ylabel("Percentage")
            ax.set_title("Claims by Status")
            st.pyplot(fig)
        elif "Food_Type" in df.columns and "count_food_type" in df.columns:
            df["count_food_type"] = pd.to_numeric(df["count_food_type"], errors="coerce")
            df.set_index("Food_Type")["count_food_type"].plot(kind="barh", ax=ax)
            ax.set_title("Most Common Food Types")
            plt.gca().invert_yaxis()
            st.pyplot(fig)
        elif "city" in df.columns and "num_food_listings" in df.columns:
            df["num_food_listings"] = pd.to_numeric(df["num_food_listings"], errors="coerce")
            df.set_index("city")["num_food_listings"].plot(kind="barh", ax=ax)
            ax.set_title("City With Highest Number of Food Listings")
            plt.gca().invert_yaxis()
            st.pyplot(fig)
        elif "total_quantity" in df.columns:
            st.subheader(f"Total Quantity Available: {df.iloc[0,0]}")
        elif "receiver_name" in df.columns and "total_quantity" in df.columns:
            df["total_quantity"] = pd.to_numeric(df["total_quantity"], errors="coerce")
            df.set_index("receiver_name")["total_quantity"].plot(kind="barh", ax=ax)
            ax.set_title("Receivers With Highest Total Quantity Claimed")
            plt.gca().invert_yaxis()
            st.pyplot(fig)
        else:
            ax.axis("off")
            st.info("No plot available for this query. Data table is shown above.")
    except Exception as ex:
        st.error(f"Couldn't plot: {ex}")

# Function To FILTER DONATIONS
elif menu == "Filter Donations":
    st.header("🔍 Filter Food Donations")
    locations = run_query("SELECT DISTINCT Location FROM food_listings;")["Location"].dropna().tolist()
    providers = run_query("SELECT DISTINCT Name FROM providers;")["Name"].dropna().tolist()
    food_types = run_query("SELECT DISTINCT Food_Type FROM food_listings;")["Food_Type"].dropna().tolist()
    loc_choice = st.selectbox("Select Location", ["All"] + locations)
    prov_choice = st.selectbox("Select Provider", ["All"] + providers)
    food_choice = st.selectbox("Select Food Type", ["All"] + food_types)
    query = """
        SELECT fl.Food_ID, fl.Food_Name, fl.Quantity, fl.Location, fl.Food_Type, p.Name AS Provider, p.Contact
        FROM food_listings fl
        JOIN providers p ON fl.Provider_ID = p.Provider_ID
        WHERE (%s = 'All' OR fl.Location = %s)
        AND (%s = 'All' OR p.Name = %s)
        AND (%s = 'All' OR fl.Food_Type = %s);
    """
    df = run_query(query, (loc_choice, loc_choice, prov_choice, prov_choice, food_choice, food_choice))
    if not df.empty:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
        df["📞 Call"] = df["Contact"].apply(lambda x: f"[Call]({f'tel:{x}'})" if pd.notnull(x) else "")
        st.write(f"### Filtered Results ({len(df)})")
        st.dataframe(df)
        # Plot only if quantities are valid
        if df["Quantity"].notnull().any():
            fig, ax = plt.subplots(figsize=(10,5))
            df.set_index("Food_Name")["Quantity"].plot(kind="bar", ax=ax)
            ax.set_ylabel("Quantity")
            ax.set_title("Filtered Food Quantities by Food Item")
            st.pyplot(fig)
        else:
            st.info("No quantities available to plot for these filters.")
    else:
        st.warning("No results found for the selected filters.")

# Function For CONTACT.
elif menu == "Contact Directory":
    st.header("📇 Contact Food Providers & Receivers")
    contact_type = st.radio("View Contacts For:", ["Providers", "Receivers"])
    if contact_type == "Providers":
        df = run_query("SELECT Name, City, Contact FROM providers;")
    else:
        df = run_query("SELECT Name, City, Contact FROM receivers;")
    if not df.empty:
        df["📞 Call"] = df["Contact"].apply(lambda x: f"[Call]({f'tel:{x}'})" if pd.notnull(x) else "")
        st.dataframe(df)
    else:
        st.warning("No contacts available.")

# That's all i had.
