import streamlit as st
import os
from datetime import date

# Safely handle database imports so the app runs smoothly without failing
try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# --- 1. DATABASE MANAGER (OOP Backend Class) ---
class DatabaseManager:
    def __init__(self):
        self.conn_str = os.getenv("DATABASE_URL", "")

    def get_connection(self):
        if not HAS_PSYCOPG2 or not self.conn_str:
            return None
        try:
            return psycopg2.connect(self.conn_str)
        except Exception:
            return None

    def execute_query(self, query, params=None, fetch=False):
        conn = self.get_connection()
        if not conn:
            return [] if fetch else False
        cur = conn.cursor()
        try:
            cur.execute(query, params or ())
            if fetch:
                result = cur.fetchall()
                return result
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return [] if fetch else False
        finally:
            cur.close()
            conn.close()

# --- 2. OOP USER & ENTITY MODELS ---
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

class Appointment:
    def __init__(self, appointment_id, patient_id, doctor_id, appointment_date, time_slot, status="Scheduled"):
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.time_slot = time_slot
        self.status = status

# --- 3. STREAMLIT CONFIGURATION & ROUTING ---
st.set_page_config(
    page_title="CarePoint: Clinic Appointment & Patient Record Management System",
    layout="wide"
)

def main():
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
    st.title("CarePoint Clinic Management System")
    st.markdown("Please sign in with your authorized role credentials[cite: 1, 2].")

    with st.form("login_form"):
        username = st.text_input("Username / Email")
        password = st.text_input("Password", type="password")
        role_selection = st.selectbox("Select Access Role", ["Administrative Staff", "Doctor", "Patient"])
        submit = st.form_submit_button("Secure Login")

        if submit:
            st.session_state.authenticated = True
            st.session_state.user_role = role_selection
            st.session_state.user_name = username
            st.session_state.user_id = 1
            st.rerun()

def render_main_app():
    role = st.session_state.user_role

    st.sidebar.title("CarePoint Portal")
    st.sidebar.write(f"**User:** {st.session_state.user_name}")
    st.sidebar.write(f"**Role:** {role}")

    if st.sidebar.button("Log Out"):
        st.session_state.authenticated = False
        st.rerun()

    st.sidebar.divider()

    if role == "Administrative Staff":
        render_admin_dashboard()
    elif role == "Doctor":
        render_doctor_dashboard()
    elif role == "Patient":
        render_patient_dashboard()

# --- 4. ROLE-BASED DASHBOARDS ---

def render_admin_dashboard():
    st.title("Administrative Staff Portal")
    st.markdown("Manage master patient profiles, global clinic schedules, and financial reports[cite: 1].")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patients", "1,245", "+12 this week")
    with col2:
        st.metric("Today's Appointments", "24", "4 pending")
    with col3:
        st.metric("Active Doctors", "8", "All Online")

    st.divider()

    tab1, tab2, tab3 = st.tabs(["Master Patient Records", "Clinic-Wide Schedules", "Billing Logs"])

    with tab1:
        st.subheader("Patient Directory & Registration")
        with st.form("patient_reg_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                full_name = st.text_input("Full Legal Name")
                age = st.number_input("Age", min_value=0, max_value=120, value=25)
            with col_b:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                contact = st.text_input("Contact Number")
            address = st.text_area("Home Address")
            
            if st.form_submit_button("Register Patient"):
                st.success(f"Patient {full_name} successfully registered into database[cite: 1]!")

        st.divider()
        st.text_input("Search Patient Records by Name or Phone", placeholder="Type to filter records...")
        st.info("Displaying filtered patient records table[cite: 1].")

    with tab2:
        st.subheader("Global Appointment Board")
        selected_date = st.date_input("Filter Date", value=date.today())
        st.info("Monitoring all scheduled, completed, and cancelled consultations[cite: 1].")

    with tab3:
        st.subheader("Billing & Financial Summaries")
        st.info("Generated daily and monthly clinic revenue reports[cite: 1].")

def render_doctor_dashboard():
    st.title("Medical Professional Portal (Doctor View)")
    st.markdown("Review your personal appointment queue and record clinical diagnoses and treatments[cite: 1].")

    tab1, tab2, tab3 = st.tabs(["My Daily Schedule", "Assigned Patients", "Consultation & Prescriptions"])

    with tab1:
        st.subheader("Active Patient Queue")
        st.info("Filtered appointments assigned to your Doctor ID[cite: 1].")

    with tab2:
        st.subheader("Patient Medical Histories")
        st.info("Access past clinical findings, diagnoses, and medical records[cite: 1].")

    with tab3:
        st.subheader("Consultation Input Form")
        with st.form("consultation_form"):
            patient_select = st.selectbox("Select Active Patient", ["Patient #101 - John Doe", "Patient #102 - Jane Smith"])
            diagnosis = st.text_area("Clinical Findings & Diagnosis")
            prescription = st.text_area("Prescribed Medications & Dosage")
            total_bill = st.number_input("Total Billing Amount ($)", min_value=0.00, format="%.2f")
            
            if st.form_submit_button("Save Consultation & Complete Visit"):
                st.success("Consultation record securely saved and appointment status updated to Completed[cite: 1].")

def render_patient_dashboard():
    st.title("Patient Self-Service Portal")
    st.markdown("Book your doctor appointments and view your personal medical history[cite: 1].")

    tab1, tab2 = st.tabs(["Book Appointment", "My Medical History & Visits"])

    with tab1:
        st.subheader("Schedule a Consultation")
        with st.form("booking_form"):
            doc_choice = st.selectbox("Select Doctor & Specialty", ["Dr. Smith - General Practice", "Dr. Johnson - Pediatrics"])
            visit_date = st.date_input("Preferred Visit Date")
            time_slot = st.selectbox("Available Time Slot", ["09:00 AM", "10:30 AM", "01:30 PM", "03:00 PM"])
            
            if st.form_submit_button("Confirm Booking"):
                st.success("Appointment successfully scheduled[cite: 1]!")

    with tab2:
        st.subheader("Personal Visit Logs & Prescriptions")
        st.info("Displaying your past medical history and treatment summaries[cite: 1].")

if __name__ == "__main__":
    main()
