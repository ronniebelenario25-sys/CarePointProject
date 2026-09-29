import random
from datetime import datetime, timedelta
import streamlit as st
from supabase import create_client, Client

# --- SUPABASE DATABASE MANAGER ---
class DatabaseManager:
    def __init__(self):
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        self.supabase: Client = create_client(url, key)

    def authenticate(self, username, password):
        """Queries the Supabase users table for secure role-based login"""
        try:
            response = self.supabase.table("users").select("role").eq("username", username).eq("password", password).execute()
            data = response.data
            return data[0]["role"] if data else None
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None

    def get_all_appointments(self):
        """Fetches all master records (Restricted to Admin only)"""
        try:
            response = self.supabase.table("appointments").select("*").order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def get_doctor_appointments(self, doctor_name):
        """Security isolation: Fetches only appointments assigned to the specific doctor"""
        try:
            # Matches doctor username/name format (e.g., 'doctor' or 'Dr. Smith')
            response = self.supabase.table("appointments").select("*").ilike("doctor_id", f"%{doctor_name}%").order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def get_patient_appointments(self, patient_name):
        """Security isolation: Fetches only appointments belonging to the logged-in patient"""
        try:
            response = self.supabase.table("appointments").select("*").eq("patient_name", patient_name).order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def add_appointment(self, patient_name, doctor_id, appointment_date, appointment_time, status):
        """Adds a new appointment with exact time tracking"""
        try:
            data = {
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status
            }
            self.supabase.table("appointments").insert(data).execute()
            return True
        except Exception as e:
            return False

    def check_and_seed_records(self):
        """Seeds initial realistic records if database table is empty"""
        try:
            existing = self.get_all_appointments()
            if len(existing) < 10:
                first_names = ["Juan", "Maria", "Jose", "Ana", "Carlos", "Rosa", "Pedro", "Elena", "Miguel", "Lucia"]
                last_names = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Aquino", "Garcia", "Mendoza", "Torres", "Flores"]
                doctors = ["Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos"]
                times = ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"]
                statuses = ["Waiting", "Completed", "Cancelled"]

                batch_data = []
                for i in range(1, 301):
                    patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                    doctor_id = random.choice(doctors)
                    random_days = random.randint(-15, 15)
                    appointment_date = (datetime.now() + timedelta(days=random_days)).strftime("%Y-%m-%d")
                    appointment_time = random.choice(times)
                    status = random.choice(statuses)
                    
                    batch_data.append({
                        "patient_name": patient_name,
                        "doctor_id": doctor_id,
                        "appointment_date": appointment_date,
                        "appointment_time": appointment_time,
                        "status": status
                    })
                
                for j in range(0, len(batch_data), 100):
                    self.supabase.table("appointments").insert(batch_data[j:j+100]).execute()
        except Exception as e:
            pass

# --- MAIN APPLICATION UI ---
def main():
    st.set_page_config(page_title="CarePoint Clinic System", page_icon="💊", layout="wide")
    
    try:
        db = DatabaseManager()
        db.check_and_seed_records()
    except Exception as e:
        st.error("⚠️ Please configure your Supabase credentials in Streamlit Cloud Secrets.")
        return

    # Session State Initialization
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None

    # --- 1. LOGIN GATEWAY ---
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>💊 CarePoint Clinic Management System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280;'>Secure Cloud-Powered Healthcare & Queue Portal</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.info("💡 **Presentation Login Hints:**\n- Admin: `admin` / `password123`\n- Doctor: `doctor` / `password123` (or use `Dr. Smith`)\n- Patient: `patient` / `password123`")
            
            with st.form("login_form"):
                st.subheader("Account Login")
                username = st.text_input("Username", value="admin")
                password = st.text_input("Password", type="password", value="password123")
                submit = st.form_submit_button("Access Portal", use_container_width=True)
                
                if submit:
                    role = db.authenticate(username, password)
                    if role:
                        st.session_state.authenticated = True
                        st.session_state.role = role
                        st.session_state.username = username
                        st.success(f"Authenticated successfully as {role}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")
        return

    # --- 2. SIDEBAR NAVIGATION ---
    role = st.session_state.role
    st.sidebar.markdown(f"### 👤 Welcome, **{st.session_state.username}**")
    st.sidebar.markdown(f"**Access Role:** `{role}`")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

    # --- 3. ROLE-BASED DASHBOARDS ---
    
    # --- ADMIN PORTAL ---
    if role == "Admin":
        st.title("🛠️ Administrative Control Center")
        st.markdown("System-wide master monitoring dashboard connected directly to Supabase cloud storage.")
        
        records = db.get_all_appointments()
        
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Total Database Records", value=len(records))
        m2.metric(label="Active Queue Status", value="Online 🟢")
        m3.metric(label="System Security", value="Role-Based Protected")
        
        st.markdown("---")
        st.subheader("📋 Master Appointment Database")
        if records:
            st.dataframe(records, use_container_width=True)
        else:
            st.warning("No records found in the database.")

    # --- DOCTOR PORTAL (SECURED & ISOLATED) ---
    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        st.markdown(f"Welcome, **{st.session_state.username}**. Managing your personal clinical schedule and patient queue.")
        
        # Security Isolation Query: Filter only records assigned to this doctor
        doc_records = db.get_doctor_appointments(st.session_state.username)
        
        col1, col2 = st.columns(2)
        col1.metric(label="Your Assigned Appointments", value=len(doc_records))
        col2.metric(label="Clinic Queue Status", value="Active 🟢")
        
        st.markdown("---")
        st.subheader("🕒 Your Assigned Patient Schedule")
        st.markdown("> *Privacy Notice: To protect patient data compliance, only appointments assigned to your professional ID are visible here.*")
        
        if doc_records:
            st.dataframe(doc_records, use_container_width=True)
        else:
            st.warning("No appointments currently assigned to your account name. (If testing, try updating doctor names or check sample assignments).")

    # --- PATIENT PORTAL (SECURED & ISOLATED) ---
    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        st.markdown(f"Welcome back, **{st.session_state.username}**. Manage your healthcare appointments safely and confidentially.")
        
        tab1, tab2 = st.tabs(["📅 Book New Appointment", "📋 My Confidential Appointments"])
        
        with tab1:
            st.subheader("Schedule a New Clinic Visit")
            with st.form("booking_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    p_name = st.text_input("Full Name (Match with account name)", value=st.session_state.username)
                    doc_choice = st.selectbox("Select Attending Physician", ["Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos"])
                with col_b:
                    app_date = st.date_input("Preferred Date")
                    app_time = st.selectbox("Exact Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                
                book_submit = st.form_submit_button("Confirm & Secure Booking", use_container_width=True)
                
                if book_submit:
                    success = db.add_appointment(p_name, doc_choice, app_date, app_time, "Waiting")
                    if success:
                        st.success("🎉 Appointment successfully booked and synchronized with the cloud database!")
                        st.rerun()
                    else:
                        st.error("Failed to submit appointment booking. Please check database inputs.")
                        
        with tab2:
            st.subheader("Your Personal Medical Appointments")
            st.markdown("> *Note: For patient data privacy, only appointments booked under your personal account name are visible here.*")
            
            my_records = db.get_patient_appointments(st.session_state.username)
            if my_records:
                st.dataframe(my_records, use_container_width=True)
            else:
                st.info("You have no scheduled appointments. Switch to the **Book New Appointment** tab to schedule your first visit!")

if __name__ == "__main__":
    main()
