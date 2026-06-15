import streamlit as st

st.set_page_config(page_title="TableTap", layout="centered")

conn = st.connection("snowflake")

st.title("🍽️ TableTap")

params = st.query_params
table_number = params.get("table", None)


def run_sql(sql):
    cur = conn.raw_connection.cursor()
    try:
        cur.execute(sql)
    finally:
        cur.close()


def insert_request(table_number, request_type):
    table_number = str(table_number).replace("'", "''")
    request_type = str(request_type).replace("'", "''")

    sql = f"""
        INSERT INTO RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        (TABLE_NUMBER, REQUEST_TYPE, STATUS, CREATED_AT)
        VALUES ('{table_number}', '{request_type}', 'WAITING', CURRENT_TIMESTAMP())
    """

    run_sql(sql)


def update_request(request_id):
    sql = f"""
        UPDATE RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        SET STATUS = 'COMPLETED'
        WHERE REQUEST_ID = {int(request_id)}
    """

    run_sql(sql)


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
