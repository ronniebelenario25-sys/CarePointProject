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
        """Queries the Supabase users table"""
        try:
            response = self.supabase.table("users").select("role").eq("username", username).eq("password", password).execute()
            data = response.data
            return data[0]["role"] if data else None
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None

    def get_all_appointments(self):
        """Fetches all records (for Admin/Doctors)"""
        try:
            response = self.supabase.table("appointments").select("*").execute()
            return response.data
        except Exception as e:
            return []

    def get_patient_appointments(self, patient_name):
        """Fetches only appointments belonging to a specific patient"""
        try:
            response = self.supabase.table("appointments").select("*").eq("patient_name", patient_name).execute()
            return response.data
        except Exception as e:
            return []

    def add_appointment(self, patient_name, doctor_id, appointment_date, appointment_time, status):
        """Allows adding a new appointment with exact time"""
        try:
            data = {
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "status": status
            }
            self.supabase.table("appointments").insert(data).execute()
            return True
        except Exception as e:
            return False

    def check_and_seed_records(self):
        """Automatically seeds records with exact times if table is sparse"""
        try:
            existing = self.get_all_appointments()
            if len(existing) < 10:
                first_names = ["Juan", "Maria", "Jose", "Ana", "Carlos", "Rosa", "Pedro", "Elena", "Miguel", "Lucia"]
                last_names = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Aquino", "Garcia", "Mendoza", "Torres", "Flores"]
                doctors = ["Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos"]
                times = ["09:00 AM", "10:30 AM", "01:00 PM", "03:30 PM"]
                statuses = ["Completed", "Waiting", "Cancelled"]

                batch_data = []
                for i in range(1, 301):
                    patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                    doctor_id = random.choice(doctors)
                    random_days = random.randint(-30, 30)
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

# --- MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="CarePoint Clinic System", layout="wide")
    
    try:
        db = DatabaseManager()
        db.check_and_seed_records()
    except Exception as e:
        st.error("Please configure your Supabase secrets in Streamlit settings.")
        return

    # Session State Initialization
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None

    # 1. Login Gateway
    if not st.session_state.authenticated:
        st.title("🔐 CarePoint Login Portal (Supabase Cloud)")
        st.info("💡 **Test Accounts:**\n- Admin: `admin` / `password123`\n- Doctor: `doctor` / `password123`\n- Patient: `patient` / `password123` (or book under your own name!)")
        
        with st.form("login_form"):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="password123")
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
                    st.error("Invalid username or password.")
        return

    # 2. Sidebar Navigation & Logout
    role = st.session_state.role
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.markdown(f"**Role:** {role}")
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()

    # --- PORTALS ---
    if role == "Admin":
        st.title("🛠️ Administrative Staff Portal")
        st.success("Connected to Supabase PostgreSQL Cloud Database!")
        records = db.get_all_appointments()
        st.metric(label="Total Cloud Database Records", value=len(records))
        
        with st.expander("View All Master Records"):
            st.dataframe(records, use_container_width=True)

    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        records = db.get_all_appointments()
        st.metric(label="Total System Appointments", value=len(records))
        
        st.subheader("📋 Active Patient Appointment Queue (With Exact Times)")
        if records:
            st.dataframe(records, use_container_width=True)
        else:
            st.warning("No appointments found.")

    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        st.write(f"Welcome, **{st.session_state.username}**. You can only view your own confidential medical appointments.")
        
        tab1, tab2 = st.tabs(["📅 Book New Appointment", "📋 My Personal Appointments"])
        
        with tab1:
            with st.form("booking_form"):
                st.subheader("Schedule Appointment with Exact Time")
                p_name = st.text_input("Your Full Name (e.g. Juan Santos or match your username)", value=st.session_state.username)
                doc_choice = st.selectbox("Select Doctor", ["Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos"])
                app_date = st.date_input("Appointment Date")
                app_time = st.selectbox("Appointment Exact Time", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                book_submit = st.form_submit_button("Confirm Booking")
                
                if book_submit:
                    success = db.add_appointment(p_name, doc_choice, str(app_date), app_time, "Waiting")
                    if success:
                        st.success("Appointment booked successfully with exact time and synced to cloud!")
                        st.rerun()
                    else:
                        st.error("Failed to book appointment.")
                        
        with tab2:
            st.subheader("Your Confidential Appointments")
            # SECURITY FILTER: Only fetch records matching this patient's name
            my_records = db.get_patient_appointments(st.session_state.username)
            if my_records:
                st.dataframe(my_records, use_container_width=True)
            else:
                st.info("You have no active appointments booked under this account name. Try booking one in the first tab, or ensure your username matches your patient name!")

if __name__ == "__main__":
    main()
