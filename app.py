import streamlit as st
import sqlite3

# --- DATABASE MANAGER CLASS ---
class DatabaseManager:
    def __init__(self, db_name="carepoint.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def init_db(self):
        """Initializes database tables and default test users."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table for role-based login
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        ''')
        
        # Appointments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT,
                doctor_id TEXT,
                appointment_date TEXT,
                status TEXT
            )
        ''')
        
        # Insert default test accounts for testing each role
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'password123', 'Admin')")
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('doctor', 'password123', 'Doctor')")
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('patient', 'password123', 'Patient')")
        
        conn.commit()
        conn.close()

    def authenticate(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

# --- MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="CarePoint Clinic System", layout="wide")
    db = DatabaseManager()

    # Session State Initialization
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None

    # 1. Login Gateway
    if not st.session_state.authenticated:
        st.title("🔐 CarePoint Login Portal")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                role = db.authenticate(username, password)
                if role:
                    st.session_state.authenticated = True
                    st.session_state.role = role
                    st.session_state.username = username
                    st.success(f"Logged in successfully as {role}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Try: admin, doctor, or patient with password123")
        return

    # 2. Role-Based Dynamic Routing After Authentication
    role = st.session_state.role
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {role}")
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

    # --- ADMIN PORTAL ROUTE ---
    if role == "Admin":
        st.title("🛠️ Administrative Staff Portal")
        st.write("Manage clinic-wide operations, master patient records, and schedules.")
        tab1, tab2 = st.tabs(["Master Records", "Clinic Schedules"])
        with tab1:
            st.subheader("Patient Management CRUD Table")
            st.info("Admin can view, add, and update patient records here.")
        with tab2:
            st.subheader("Clinic-Wide Schedule Overview")
            st.info("Admin can oversee doctor timetables and assignments.")

    # --- DOCTOR PORTAL ROUTE ---
    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        st.write(f"Viewing assigned patient queue for Dr. {st.session_state.username}")
        st.subheader("Assigned Daily Patient Queue")
        st.code(f"SELECT * FROM appointments WHERE doctor_id = '{st.session_state.username}' AND status = 'Waiting'")
        
        with st.form("consultation_form"):
            st.text_area("Diagnosis & Consultation Notes")
            st.text_area("Prescription Details")
            if st.form_submit_button("Complete Record"):
                st.success("Consultation record updated successfully!")

    # --- PATIENT PORTAL ROUTE ---
    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        st.write("Book your appointment slots and view your personal medical history.")
        tab1, tab2 = st.tabs(["Book Appointment", "My Personal History"])
        with tab1:
            with st.form("booking_form"):
                st.date_input("Select Visit Date")
                st.selectbox("Choose Doctor", ["Dr. Smith", "Dr. Cruz"])
                if st.form_submit_button("Confirm Booking"):
                    st.success("Appointment slot reserved successfully!")
        with tab2:
            st.subheader("My Visit History")
            st.code(f"SELECT * FROM appointments WHERE patient_name = '{st.session_state.username}'")

if __name__ == "__main__":
    main()
