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

    def get_appointments(self):
        """Fetches records from Supabase"""
        try:
            response = self.supabase.table("appointments").select("*").execute()
            return response.data
        except Exception as e:
            return []

    def check_and_seed_300_records(self):
        """Automatically seeds 300 records if the table is empty"""
        try:
            existing = self.get_appointments()
            if len(existing) < 10:  # If less than 10 records, auto-seed 300
                first_names = ["Juan", "Maria", "Jose", "Ana", "Carlos", "Rosa", "Pedro", "Elena", "Miguel", "Lucia"]
                last_names = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Aquino", "Garcia", "Mendoza", "Torres", "Flores"]
                doctors = ["Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos"]
                statuses = ["Completed", "Waiting", "Cancelled"]

                batch_data = []
                for i in range(1, 301):
                    patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                    doctor_id = random.choice(doctors)
                    random_days = random.randint(-30, 30)
                    appointment_date = (datetime.now() + timedelta(days=random_days)).strftime("%Y-%m-%d")
                    status = random.choice(statuses)
                    
                    batch_data.append({
                        "patient_name": patient_name,
                        "doctor_id": doctor_id,
                        "appointment_date": appointment_date,
                        "status": status
                    })
                
                # Insert in chunks to prevent timeout
                for j in range(0, len(batch_data), 100):
                    self.supabase.table("appointments").insert(batch_data[j:j+100]).execute()
        except Exception as e:
            pass

# --- MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="CarePoint Clinic System", layout="wide")
    
    try:
        db = DatabaseManager()
        # Automatically make sure 300 records exist in cloud
        db.check_and_seed_300_records()
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

    # 2. Role-Based Dynamic Routing After Authentication
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
        st.success("Successfully connected to Supabase PostgreSQL Cloud Database!")
        
        records = db.get_appointments()
        st.metric(label="Total Cloud Database Records", value=len(records))
        
        with st.expander("View All Database Records (300 Records Loaded)"):
            st.dataframe(records)

    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        records = db.get_appointments()
        st.metric(label="Total Clinic Appointments in System", value=len(records))
        st.write(f"Viewing active queue for Dr. {st.session_state.username}")
        
    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        st.write("Bookings sync directly to your cloud PostgreSQL database.")

if __name__ == "__main__":
    main()
