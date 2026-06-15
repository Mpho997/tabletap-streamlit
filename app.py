import streamlit as st

st.set_page_config(page_title="TableTap", layout="centered")

conn = st.connection("snowflake")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}
.main-card {
    background-color: #111827;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
}
.request-card {
    background-color: #f59e0b;
    color: #111827;
    padding: 18px;
    border-radius: 14px;
    font-size: 20px;
    font-weight: bold;
    margin-top: 15px;
}
.completed-card {
    background-color: #16a34a;
    color: white;
    padding: 15px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🍽️ TableTap")

params = st.query_params
table_number = params.get("table", None)


def run_sql(sql):
    cur = conn.raw_connection.cursor()
    try:
        cur.execute("ALTER SESSION SET TIMEZONE = 'Africa/Johannesburg'")
        cur.execute(sql)
    finally:
        cur.close()


def insert_request(table_number, request_type):
    table_number = str(table_number).replace("'", "''")
    request_type = str(request_type).replace("'", "''")

    sql = f"""
        INSERT INTO RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        (TABLE_NUMBER, REQUEST_TYPE, STATUS, CREATED_AT)
        VALUES (
            '{table_number}',
            '{request_type}',
            'WAITING',
            CONVERT_TIMEZONE('Africa/Johannesburg', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
        )
    """
    run_sql(sql)


def update_request(request_id):
    sql = f"""
        UPDATE RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        SET STATUS = 'COMPLETED',
            COMPLETED_AT = CONVERT_TIMEZONE('Africa/Johannesburg', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
        WHERE REQUEST_ID = {int(request_id)}
    """
    run_sql(sql)


if table_number:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)

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

    st.markdown('</div>', unsafe_allow_html=True)

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
            TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS STARTED_AT,
            TO_CHAR(COMPLETED_AT, 'YYYY-MM-DD HH24:MI:SS') AS COMPLETED_AT
        FROM RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        WHERE STATUS = 'WAITING'
        ORDER BY CREATED_AT DESC
    """, ttl=0)

    if df.empty:
        st.success("No waiting requests.")
    else:
        for _, row in df.iterrows():
            st.markdown(
                f"""
                <div class="request-card">
                    Table {row['TABLE_NUMBER']} - {row['REQUEST_TYPE']}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.write(f"Started at: {row['STARTED_AT']} SAST")

            if st.button(f"Mark Completed - Request {row['REQUEST_ID']}"):
                update_request(int(row["REQUEST_ID"]))
                st.rerun()

            st.divider()
