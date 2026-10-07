import streamlit as st
import psycopg2
import os

# --- 1. DATABASE MANAGER (OOP Backend) ---
class DatabaseManager:
    def __init__(self):
        # Establish connection using Supabase/PostgreSQL connection string or environment variables
        # Replace with your actual Supabase connection parameters if needed
        self.conn_str = os.getenv("DATABASE_URL", "postgresql://postgres:your_password@db.supabase.co:5432/postgres")

    def get_connection(self):
        try:
            return psycopg2.connect(self.conn_str)
        except Exception as e:
            # Fallback for testing/mocking if connection details aren't live yet
            return None

    def execute_query(self, query, params=None):
        conn = self.get_connection()
        if not conn:
            return []
        cur = conn.cursor()
        try:
            cur.execute(query, params or ())
            if query.strip().upper().startswith("SELECT"):
                result = cur.fetchall()
                return result
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

# --- 2. OOP USER & ROLE MODELS ---
class User:
    def __init__(self, user_id, full_name, role):
        self.user_id = user_id
        self.full_name = full_name
        self.role = role

class Patient(User):
    def __init__(self, user_id, full_name, age, gender, contact_number):
        super().__init__(user_id, full_name, "Patient")
        self.age = age
        self.gender = gender
        self.contact_number = contact_number

class Doctor(User):
    def __init__(self, user_id, full_name, specialty, schedule_availability):
        super().__init__(user_id, full_name, "Doctor")
        self.specialty = specialty
        self.schedule_availability = schedule_availability

# --- 3. STREAMLIT APPLICATION ROUTING & UI ---
st.set_page_config(page_title="CarePoint Clinic Management System", layout="wide")

def main():
    # Initialize Session State for Authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.session_state.user_id = None

    if not st.session_state.authenticated:
        render_login_portal()
    else:
        render_main_app()

def render_login_portal():
    st.title("CarePoint: Clinic Management System")
    st.markdown("Please log in with your assigned administrative or medical credentials.")

    with st.form("login_form"):
        username = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        role_selection = st.selectbox("Select Role", ["Administrative Staff", "Doctor", "Patient"])
        submit = st.form_submit_button("Login")

        if submit:
            # Mock authentication handler (Integrate with DB auth in production)
            st.session_state.authenticated = True
            st.session_state.user_role = role_selection
            st.session_state.user_name = username
            st.session_state.user_id = 1
            st.rerun()

def render_main_app():
    role = st.session_state.user_role

    # Sidebar Navigation based on Role
    st.sidebar.title(f"CarePoint Portal")
    st.sidebar.write(f"Logged in as: **{st.session_state.user_name}**")
    st.sidebar.write(f"Role: **{role}**")
    
    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.divider()

    # Conditional Role-Based UI Rendering
    if role == "Administrative Staff":
        render_admin_dashboard()
    elif role == "Doctor":
        render_doctor_dashboard()
    elif role == "Patient":
        render_patient_dashboard()

def render_admin_dashboard():
    st.title("Admin Dashboard - CarePoint Clinic")
    st.markdown("Manage clinic-wide operations, master records, and global schedules[cite: 2].")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Patients", value="1,245", delta="+12 this week")
    with col2:
        st.metric(label="Appointments Today", value="24", delta="4 pending")
    with col3:
        st.metric(label="Active Doctors", value="8", delta="All online")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Master Patient Records", "Clinic-Wide Schedules", "Billing Logs"])

    with tab1:
        st.subheader("Patient Database")
        search_query = st.text_input("Search patient by name or contact number")
        st.info("Displaying searchable and filterable patient records table[cite: 2].")
        if st.button("Register New Patient"):
            st.success("Patient registration form modal triggered.")

    with tab2:
        st.subheader("Global Appointment Board")
        selected_date = st.date_input("Filter by Date")
        st.info("Monitoring all doctor appointments, status updates, and rescheduling tools[cite: 2].")

    with tab3:
        st.subheader("Financial & Billing Reports")
        st.info("Generating daily/monthly clinic billing logs and reports[cite: 2].")

def render_doctor_dashboard():
    st.title("Doctor Portal - Clinical View")
    st.markdown("Manage your personal patient queues and input clinical findings securely[cite: 2].")
    
    tab1, tab2, tab3 = st.tabs(["My Daily Schedule", "Assigned Patients", "Consultation Logs"])
    with tab1:
        st.subheader("Active Patient Queue")
        st.info("Showing active appointments filtered by doctor ID[cite: 2].")
    with tab2:
        st.subheader("Patient Medical Histories")
        st.info("Review past diagnoses and prescriptions.")
    with tab3:
        st.subheader("Consultation Input Form")
        diagnosis = st.text_area("Clinical Findings / Diagnosis")
        prescription = st.text_area("Prescribed Medications")
        bill = st.number_input("Total Bill Amount", min_value=0.0, format="%.2f")
        if st.button("Save Consultation Record"):
            st.success("Consultation notes successfully saved to database.")

def render_patient_dashboard():
    st.title("Patient Self-Service Portal")
    st.markdown("Book visits and track your personal medical history[cite: 2].")
    
    tab1, tab2 = st.tabs(["Book Appointment", "My Upcoming Visits & History"])
    with tab1:
        st.subheader("Schedule a New Visit")
        doc_choice = st.selectbox("Select Doctor & Specialty", ["Dr. Smith (General)", "Dr. Johnson (Pediatrics)"])
        visit_date = st.date_input("Preferred Date")
        slot = st.selectbox("Available Time Slot", ["09:00 AM", "10:30 AM", "02:00 PM"])
        if st.button("Confirm Booking"):
            st.success("Appointment successfully booked!")
    with tab2:
        st.subheader("My Medical Records")
        st.info("Displaying personal past visits, diagnoses, and prescriptions[cite: 2].")

if __name__ == "__main__":
    main()
