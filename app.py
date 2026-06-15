import streamlit as st
from datetime import datetime

st.set_page_config(page_title="TableTap", layout="centered")

conn = st.connection("snowflake")

st.title("🍽️ TableTap")

params = st.query_params
table_number = params.get("table", None)

def insert_request(table_number, request_type):
    sql = """
        INSERT INTO RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        (TABLE_NUMBER, REQUEST_TYPE, STATUS, CREATED_AT)
        VALUES (?, ?, 'WAITING', CURRENT_TIMESTAMP())
    """
    with conn.raw_connection().cursor() as cur:
        cur.execute(sql, (str(table_number), request_type))

def update_request(request_id):
    sql = """
        UPDATE RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        SET STATUS = 'COMPLETED'
        WHERE REQUEST_ID = ?
    """
    with conn.raw_connection().cursor() as cur:
        cur.execute(sql, (request_id,))

if table_number:
    st.subheader(f"Table {table_number}")

    st.write("How can we assist you?")

    if st.button("🔔 Call Waiter"):
        insert_request(table_number, "Call Waiter")
        st.success("Waiter has been called.")

    if st.button("💳 Request Bill"):
        insert_request(table_number, "Request Bill")
        st.success("Bill request sent.")

    if st.button("🥤 Order Drinks"):
        insert_request(table_number, "Order Drinks")
        st.success("Drinks request sent.")

    if st.button("🍽️ Request Menu"):
        insert_request(table_number, "Request Menu")
        st.success("Menu request sent.")

else:
    st.subheader("Waiter Dashboard")

    if st.button("Refresh"):
        st.rerun()

    df = conn.query("""
        SELECT
            REQUEST_ID,
            TABLE_NUMBER,
            REQUEST_TYPE,
            STATUS,
            CREATED_AT
        FROM RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        ORDER BY CREATED_AT DESC
    """)

    waiting_df = df[df["STATUS"] == "WAITING"]

    if waiting_df.empty:
        st.success("No waiting requests.")
    else:
        for _, row in waiting_df.iterrows():
            st.warning(f"Table {row['TABLE_NUMBER']} - {row['REQUEST_TYPE']}")
            st.write(f"Time: {row['CREATED_AT']}")

            if st.button(f"Mark Completed - Request {row['REQUEST_ID']}"):
                update_request(int(row["REQUEST_ID"]))
                st.rerun()

            st.divider()
