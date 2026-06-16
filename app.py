import os
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import snowflake.connector

st.set_page_config(page_title="TableTap", layout="centered")

RESTAURANT_NAME = "The Grill House Sandton"


@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
        client_session_keep_alive=True
    )


conn = get_connection()


st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

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

.error-card {
    background-color: #7f1d1d;
    color: white;
    padding: 25px;
    border-radius: 14px;
    text-align: center;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)


st.title("🍽️ TableTap")
st.markdown(
    f"<div class='restaurant-name'>{RESTAURANT_NAME}</div>",
    unsafe_allow_html=True
)

params = st.query_params
table_number = params.get("table", None)


def run_sql(sql):
    cur = conn.cursor()
    try:
        cur.execute("ALTER SESSION SET TIMEZONE = 'Africa/Johannesburg'")
        cur.execute(sql)
    finally:
        cur.close()


def query_df(sql):
    cur = conn.cursor()
    try:
        cur.execute("ALTER SESSION SET TIMEZONE = 'Africa/Johannesburg'")
        cur.execute(sql)
        return cur.fetch_pandas_all()
    finally:
        cur.close()


def insert_request(table_number, request_type):
    table_number = str(table_number).replace("'", "''")
    request_type = str(request_type).replace("'", "''")

    sql = f"""
        INSERT INTO RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        (
            TABLE_NUMBER,
            REQUEST_TYPE,
            STATUS,
            CREATED_AT
        )
        VALUES
        (
            '{table_number}',
            '{request_type}',
            'WAITING',
            CONVERT_TIMEZONE(
                'Africa/Johannesburg',
                CURRENT_TIMESTAMP()
            )::TIMESTAMP_NTZ
        )
    """

    run_sql(sql)


def update_request(request_id, waiter_name):
    waiter_name = str(waiter_name).replace("'", "''")

    sql = f"""
        UPDATE RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
        SET
            STATUS = 'COMPLETED',
            COMPLETED_BY = '{waiter_name}',
            COMPLETED_AT =
                CONVERT_TIMEZONE(
                    'Africa/Johannesburg',
                    CURRENT_TIMESTAMP()
                )::TIMESTAMP_NTZ
        WHERE REQUEST_ID = {int(request_id)}
    """

    run_sql(sql)


def format_time(seconds):
    if seconds is None or str(seconds) == "nan":
        return "Not completed"

    seconds = int(seconds)
    minutes = seconds // 60
    remaining_seconds = seconds % 60

    return f"{minutes} min {remaining_seconds} sec"


def show_customer_error():
    st.markdown(
        f"""
        <div class="error-card">
            <h3>⚠️ Service Temporarily Unavailable</h3>
            <p>{RESTAURANT_NAME}</p>
            <p>Please notify a waiter directly.</p>
            <p>We apologize for the inconvenience.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_staff_error():
    st.error("Unable to connect to the service database. Please refresh the page or contact support.")


def play_bell_sound():
    components.html(
        """
        <audio autoplay loop>
            <source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg" type="audio/ogg">
        </audio>
        """,
        height=0
    )


def browser_notification(title, message):
    safe_title = str(title).replace('"', '\\"').replace("'", "\\'")
    safe_message = str(message).replace('"', '\\"').replace("'", "\\'")

    components.html(
        f"""
        <script>
        if ("Notification" in window) {{
            if (Notification.permission === "default") {{
                Notification.requestPermission();
            }}

            if (Notification.permission === "granted") {{
                new Notification("{safe_title}", {{
                    body: "{safe_message}",
                    icon: "https://cdn-icons-png.flaticon.com/512/3075/3075977.png"
                }});
            }}
        }}
        </script>
        """,
        height=0
    )


if table_number:

    st.subheader(f"Table {table_number}")
    st.write("How can we assist you?")

    if st.button("🔔 Call Waiter"):
        try:
            insert_request(table_number, "Call Waiter")
            st.success("Thank you. A waiter has been notified and will assist you shortly.")
        except Exception:
            show_customer_error()

    if st.button("💳 Request Bill"):
        try:
            insert_request(table_number, "Request Bill")
            st.success("Thank you. Your bill request has been sent. A waiter will bring it shortly.")
        except Exception:
            show_customer_error()

    if st.button("🥤 Order Drinks"):
        try:
            insert_request(table_number, "Order Drinks")
            st.success("Thank you. A waiter has been notified to assist you with drinks.")
        except Exception:
            show_customer_error()

    if st.button("🍽️ Request Menu"):
        try:
            insert_request(table_number, "Request Menu")
            st.success("Thank you. A waiter will bring the menu shortly.")
        except Exception:
            show_customer_error()


else:

    st.subheader("🔔 Live Waiter Dashboard")

    st_autorefresh(
        interval=5000,
        key="dashboard_refresh"
    )

    waiter_name = st.selectbox(
        "Select Waiter",
        [
            "Mpho",
            "Paul",
            "Eva",
            "Seja",
            "John",
            "David",
            "Sammuel",
            "Anna"
        ]
    )

    try:
        waiting_df = query_df("""
            SELECT
                REQUEST_ID,
                TABLE_NUMBER,
                REQUEST_TYPE,
                STATUS,
                TO_CHAR(
                    CREATED_AT,
                    'YYYY-MM-DD HH24:MI:SS'
                ) AS STARTED_AT_SAST,
                DATEDIFF(
                    'second',
                    CREATED_AT,
                    CONVERT_TIMEZONE(
                        'Africa/Johannesburg',
                        CURRENT_TIMESTAMP()
                    )::TIMESTAMP_NTZ
                ) AS SECONDS_WAITING
            FROM RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
            WHERE STATUS = 'WAITING'
            ORDER BY CREATED_AT DESC
        """)
    except Exception:
        show_staff_error()
        st.stop()

    if waiting_df.empty:
        st.success("No waiting requests.")
    else:
        play_bell_sound()

        first_request = waiting_df.iloc[0]

        browser_notification(
            "🔔 New TableTap Request",
            f"Table {first_request['TABLE_NUMBER']} - {first_request['REQUEST_TYPE']}"
        )

        st.error(
            f"🔔 {len(waiting_df)} active request(s) waiting! "
            "Bell will continue ringing until all waiting requests are completed."
        )

        for _, row in waiting_df.iterrows():

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
                    Waiting Time: {waiting_time}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(f"✅ Mark Completed - Request {row['REQUEST_ID']}"):
                try:
                    update_request(
                        int(row["REQUEST_ID"]),
                        waiter_name
                    )
                    st.rerun()
                except Exception:
                    show_staff_error()

            st.divider()

    st.subheader("Recent Completed Requests History")

    try:
        completed_df = query_df("""
            SELECT
                REQUEST_ID,
                TABLE_NUMBER,
                REQUEST_TYPE,
                COALESCE(COMPLETED_BY, 'Not captured') AS COMPLETED_BY,
                TO_CHAR(
                    CREATED_AT,
                    'YYYY-MM-DD HH24:MI:SS'
                ) AS STARTED_AT_SAST,
                TO_CHAR(
                    COMPLETED_AT,
                    'YYYY-MM-DD HH24:MI:SS'
                ) AS COMPLETED_AT_SAST,
                DATEDIFF(
                    'second',
                    CREATED_AT,
                    COMPLETED_AT
                ) AS RESPONSE_SECONDS
            FROM RESTAURANT_APP.PUBLIC.WAITER_REQUESTS
            WHERE STATUS = 'COMPLETED'
            ORDER BY COALESCE(COMPLETED_AT, CREATED_AT) DESC
            LIMIT 10
        """)
    except Exception:
        show_staff_error()
        st.stop()

    if completed_df.empty:
        st.info("No completed requests yet.")
    else:
        completed_df["RESPONSE_TIME"] = completed_df["RESPONSE_SECONDS"].apply(format_time)

        completed_df = completed_df[
            [
                "TABLE_NUMBER",
                "REQUEST_TYPE",
                "COMPLETED_BY",
                "STARTED_AT_SAST",
                "COMPLETED_AT_SAST",
                "RESPONSE_TIME"
            ]
        ]

        st.dataframe(completed_df, width="stretch")
