import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="TableTap", layout="centered")

conn = st.connection("snowflake")

RESTAURANT_NAME = "The Grill House Sandton"

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: white;
}
.restaurant-name {
    color: #cbd5e1;
    font-size: 24px;
    margin-top: -20px;
    margin-bottom: 30px;
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
.timer-card {
    background-color: #111827;
    padding: 12px;
    border-radius: 10px;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("🍽️ TableTap")
st.markdown(f"<div class='restaurant-name'>{RESTAURANT_NAME}</div>", unsafe_allow_html=True)

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


def format_time(seconds):
    if seconds is None:
        return "Not completed"

    if str(seconds) == "nan":
        return "Not completed"

    seconds = int(seconds)
    minutes = seconds // 60
    remaining_seconds = seconds % 60

    return f"{minutes} min {remaining_seconds} sec"


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
    st.subheader("🔔 Live Waiter Dashboard")

    st_autorefresh(interval=5000, key="dashboard_refresh")

    df = conn.query("""
        SELECT
            REQUEST_ID,
            TABLE_NUMBER,
            REQUEST_TYPE,
            STATUS,
            TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS STARTED_AT_SAST,
            DATEDIFF(
                'second',
                CREATED_AT,
                CONVERT_TIMEZONE('Africa/Johannesburg', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ
            ) AS SECONDS_WAITING
        FROM RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        WHERE STATUS = 'WAITING'
        ORDER BY CREATED_AT DESC
    """, ttl=0)

    if df.empty:
        st.success("No waiting requests.")
    else:
        st.error(f"🔔 {len(df)} active request(s) waiting!")

        for _, row in df.iterrows():
            waiting_time = format_time(row["SECONDS_WAITING"])

            st.markdown(
                f"""
                <div class="request-card">
                    🔔 Table {row['TABLE_NUMBER']} - {row['REQUEST_TYPE']}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="timer-card">
                    Started at: {row['STARTED_AT_SAST']} SAST<br>
                    Waiting time: {waiting_time}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(f"✅ Mark Completed - Request {row['REQUEST_ID']}"):
                update_request(int(row["REQUEST_ID"]))
                st.rerun()

            st.divider()

    st.subheader("Completed Requests")

    completed_df = conn.query("""
        SELECT
            REQUEST_ID,
            TABLE_NUMBER,
            REQUEST_TYPE,
            TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS STARTED_AT_SAST,
            TO_CHAR(COMPLETED_AT, 'YYYY-MM-DD HH24:MI:SS') AS COMPLETED_AT_SAST,
            DATEDIFF('second', CREATED_AT, COMPLETED_AT) AS RESPONSE_SECONDS
        FROM RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        WHERE STATUS = 'COMPLETED'
        ORDER BY COMPLETED_AT DESC
        LIMIT 10
    """, ttl=0)

    if completed_df.empty:
        st.info("No completed requests yet.")
    else:
        completed_df["RESPONSE_TIME"] = completed_df["RESPONSE_SECONDS"].apply(format_time)

        completed_df = completed_df[
            [
                "TABLE_NUMBER",
                "REQUEST_TYPE",
                "STARTED_AT_SAST",
                "COMPLETED_AT_SAST",
                "RESPONSE_TIME"
            ]
        ]

        st.dataframe(completed_df, width="stretch")
