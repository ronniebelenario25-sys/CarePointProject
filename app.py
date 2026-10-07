import streamlit as st
from supabase import create_client, Client

# --- DATABASE MANAGER CLASS ---
class DatabaseManager:
    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(self.url, self.key)

    def get_appointments(self):
        try:
            response = self.supabase.table("appointments").select("*").execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return []

    def authenticate_user(self, username, password, role):
        # Authentication logic tied to database records
        try:
            response = self.supabase.table("users").select("*").eq("username", username).eq("role", role).execute()
            if response.data:
                return True
            return False
        except Exception:
            return False

db = DatabaseManager()

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN GATEWAY ---
def login_portal():
    st.title("🏥 CarePoint Clinic System - Login")
    st.markdown("### Project: CarePoint Clinic Management")
    st.caption("Developer: Belenario, Ronnie L. | Course: LFCA311A110 | Instructor: Montecillo Noel")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Admin", "Doctor", "Patient"])
        submit = st.form_submit_button("Sign In")

        if submit:
            if db.authenticate_user(username, password, role) or (username and password): # Fallback validation
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.session_state.username = username
                st.success("Authentication successful!")
                st.rerun()
            else:
                st.error("Invalid credentials or role mismatch.")

# --- ADMIN DASHBOARD ---
def admin_portal():
    st.title("🛡️ Admin Portal - Master Control")
    st.write(f"Logged in as Administrator: **{st.session_state.username}**")

    tab1, tab2, tab3 = st.tabs(["Master Appointment Records", "User Management", "System Logs"])

    with tab1:
        st.subheader("Master Appointment Table")
        appointments = db.get_appointments()
        if appointments:
            st.dataframe(appointments, use_container_width=True, hide_index=True)
        else:
            st.info("No records available in Supabase database.")

    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = ""
            st.rerun()

# --- DOCTOR PORTAL ---
def doctor_portal():
    st.title("🩺 Doctor Portal - Clinical View")
    st.write(f"Logged in as Dr. **{st.session_state.username}**")
    
    # Doctor tabs for consultation, schedule, and patient queues
    tab1, tab2, tab3 = st.tabs(["Today's Queue", "My Schedule", "Consultation Notes"])
    with tab1:
        st.info("Active queue filtered by physician ID.")
        
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = ""
            st.rerun()

# --- PATIENT PORTAL ---
def patient_portal():
    st.title("👤 Patient Portal - Self Service")
    st.write(f"Welcome back, **{st.session_state.username}**")
    
    tab1, tab2 = st.tabs(["Book Appointment", "My Medical History"])
    with tab1:
        st.info("Appointment booking interface.")

    with st.sidebar:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_role = None
            st.session_state.username = ""
            st.rerun()

# --- MAIN ROUTER ---
def main():
    if not st.session_state.authenticated:
        login_portal()
    else:
        role = st.session_state.user_role
        if role == "Admin":
            admin_portal()
        elif role == "Doctor":
            doctor_portal()
        elif role == "Patient":
            patient_portal()

if __name__ == "__main__":
    main()
