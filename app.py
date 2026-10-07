import streamlit as st
from supabase import create_client, Client

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CarePoint Clinic System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SUPABASE CONNECTION SETUP ---
# Ensure you have set these in your Streamlit secrets (.streamlit/secrets.toml)
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 3. SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = ""

# --- 4. AUTHENTICATION & LOGIN GATEWAY ---
def login_page():
    st.title("🏥 CarePoint Clinic System - Login")
    st.markdown("Please enter your credentials to access your dashboard.")

    with st.form("login_form"):
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Select Role", ["Admin", "Doctor", "Patient"])
        submit_btn = st.form_submit_button("Login")

        if submit_btn:
            # Basic validation logic (can be tied to your database users table)
            if username and password:
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Please enter both username and password.")

# --- 5. ADMIN DASHBOARD ---
def admin_dashboard():
    st.title("🛡️ Admin Dashboard")
    st.markdown("System-wide monitoring and master record management.")

    # Fetch master appointments from Supabase
    try:
        response = supabase.table("appointments").select("*").execute()
        appointments = response.data
    except Exception as e:
        st.error(f"Error fetching data from database: {e}")
        appointments = []

    st.subheader("Master Appointment Records")
    
    if not appointments:
        st.info("No appointment records found in the database.")
    else:
        # Stable standard dataframe view
        st.dataframe(
            appointments,
            use_container_width=True,
            hide_index=True
        )

    # Logout handler inside sidebar
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.user_role})")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = ""
            st.rerun()

# --- 6. DOCTOR DASHBOARD (Placeholder) ---
def doctor_dashboard():
    st.title("🩺 Doctor Portal")
    st.write("Welcome to the Doctor consultation and queue management view.")
    
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.user_role})")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = ""
            st.rerun()

# --- 7. PATIENT DASHBOARD (Placeholder) ---
def patient_dashboard():
    st.title("👤 Patient Portal")
    st.write("Welcome to your self-service booking and medical history dashboard.")
    
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username}** ({st.session_state.user_role})")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = ""
            st.rerun()

# --- 8. MAIN ROUTING CONTROLLER ---
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        role = st.session_state.user_role
        if role == "Admin":
            admin_dashboard()
        elif role == "Doctor":
            doctor_dashboard()
        elif role == "Patient":
            patient_dashboard()
        else:
            st.error("Invalid role assigned.")

if __name__ == "__main__":
    main()
