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
        """Queries the Supabase users table for secure login and fetches the user ID and role"""
        try:
            response = self.supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
            data = response.data
            if data:
                user = data[0]
                uid = user.get("id") or user.get("user_id") or "1001"
                return user.get("role"), uid
            return None, None
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None, None

    def register_patient(self, username, password):
        """Registers a new patient account in the users table without creating automatic dummy appointments"""
        try:
            existing = self.supabase.table("users").select("username").eq("username", username).execute()
            if existing.data:
                return False, "Username already exists. Please choose another."
            
            user_data = {
                "username": username,
                "password": password,
                "role": "Patient"
            }
            self.supabase.table("users").insert(user_data).execute()
            
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_user_completely(self, user_id, username):
        """Permanently deletes a user account from Supabase and clears their appointment records"""
        try:
            self.supabase.table("users").delete().eq("id", user_id).execute()
            self.supabase.table("appointments").delete().eq("patient_name", username).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def get_all_users(self):
        """Fetches all registered users from Supabase"""
        try:
            response = self.supabase.table("users").select("*").execute()
            return response.data
        except Exception as e:
            return []

    def get_all_appointments(self):
        """Fetches all master records (Restricted to Admin only)"""
        try:
            response = self.supabase.table("appointments").select("*").order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def get_doctor_appointments(self, doctor_name):
        """Fetches appointments for the doctor portal view"""
        try:
            response = self.supabase.table("appointments").select("*").order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def get_patient_appointments(self, patient_name):
        """Fetches appointments for a specific patient"""
        try:
            response = self.supabase.table("appointments").select("*").eq("patient_name", patient_name).order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def add_appointment(self, patient_name, doctor_id, appointment_date, appointment_time, status):
        """Adds a new appointment with double-booking prevention checks"""
        try:
            conflict_check = self.supabase.table("appointments").select("*").eq("doctor_id", doctor_id).eq("appointment_date", str(appointment_date)).eq("appointment_time", appointment_time).execute()
            
            if conflict_check.data:
                active_conflicts = [r for r in conflict_check.data if r.get("status") != "Cancelled"]
                if active_conflicts:
                    return False, f"⚠️ Time Conflict: {doctor_id} already has an appointment at {appointment_time} on {appointment_date}. Please choose another slot."

            data = {
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status
            }
            self.supabase.table("appointments").insert(data).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_appointment(self, record_id, patient_name, doctor_id, appointment_date, appointment_time, status, diagnosis, prescription):
        """Allows updating/editing patient appointments based on preferences"""
        try:
            self.supabase.table("appointments").update({
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status,
                "diagnosis": diagnosis,
                "prescription": prescription
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_consultation(self, record_id, diagnosis, prescription):
        """Updates appointment with diagnosis and prescription, automatically moving status to Pending Payment"""
        try:
            self.supabase.table("appointments").update({
                "diagnosis": diagnosis,
                "prescription": prescription,
                "status": "Pending Payment"
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def check_and_seed_records(self):
        """Ensures all 10 doctors have unevenly distributed patient counts totaling around 300 records"""
        try:
            existing = self.get_all_appointments()
            doctors = [
                "Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos", 
                "Dr. Garcia", "Dr. Mendoza", "Dr. Torres", "Dr. Ramos", 
                "Dr. Lim", "Dr. Villanueva"
            ]
            
            doctors_with_records = set(r.get("doctor_id") for r in existing)
            
            if len(existing) < 200 or not all(doc in doctors_with_records for doc in doctors):
                try:
                    self.supabase.table("appointments").delete().neq("id", 0).execute()
                except Exception:
                    pass
                
                first_names = ["Juan", "Maria", "Jose", "Ana", "Carlos", "Rosa", "Pedro", "Elena", "Miguel", "Lucia"]
                last_names = ["Santos", "Reyes", "Cruz", "Bautista", "Ocampo", "Aquino", "Garcia", "Mendoza", "Torres", "Flores"]
                times = ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"]
                statuses = ["Waiting", "Pending Payment", "Completed", "Cancelled"]

                batch_data = []
                for doc in doctors:
                    doc_patient_count = random.randint(15, 52)
                    for _ in range(doc_patient_count):
                        patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                        random_days = random.randint(-15, 15)
                        appointment_date = (datetime.now() + timedelta(days=random_days)).strftime("%Y-%m-%d")
                        appointment_time = random.choice(times)
                        status = random.choice(statuses)
                        
                        batch_data.append({
                            "patient_name": patient_name,
                            "doctor_id": doc,
                            "appointment_date": appointment_date,
                            "appointment_time": appointment_time,
                            "status": status,
                            "diagnosis": "Routine checkup and clinical evaluation normal." if status in ["Completed", "Pending Payment"] else None,
                            "prescription": "Paracetamol 500mg every 4 hours as needed." if status in ["Completed", "Pending Payment"] else None
                        })
                
                for j in range(0, len(batch_data), 100):
                    self.supabase.table("appointments").insert(batch_data[j:j+100]).execute()
        except Exception as e:
            pass

# --- MODERN STYLING & NATIVE TABLE RENDERING ---
def apply_custom_css():
    st.markdown("""
        <style>
        h1, h2, h3, h4, h5, h6, .stMarkdown p, label {
            color: #000000 !important;
            font-weight: 700 !important;
            -webkit-font-smoothing: antialiased;
        }
        .main {
            background-color: #f8fafc;
        }
        .metric-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

def render_modern_table(records):
    """Renders records using Streamlit's native data grid with customized column configurations"""
    if not records:
        st.warning("No records found.")
        return

    import pandas as pd
    df = pd.DataFrame(records)
    
    cols_order = [c for c in ['id', 'patient_name', 'doctor_id', 'appointment_date', 'appointment_time', 'status', 'diagnosis', 'prescription'] if c in df.columns]
    df = df[cols_order]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", format="%d"),
            "patient_name": st.column_config.TextColumn("Patient Name"),
            "doctor_id": st.column_config.TextColumn("Doctor"),
            "appointment_date": st.column_config.DateColumn("Date"),
            "appointment_time": st.column_config.TextColumn("Time"),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Waiting", "Pending Payment", "Completed", "Cancelled"],
                required=True
            ),
            "diagnosis": st.column_config.TextColumn("Diagnosis"),
            "prescription": st.column_config.TextColumn("Prescription")
        }
    )

def render_users_table(users):
    """Renders user accounts table"""
    if not users:
        st.warning("No user accounts found matching query.")
        return

    import pandas as pd
    df = pd.DataFrame(users)
    
    cols = [c for c in ['id', 'username', 'password', 'role'] if c in df.columns]
    df = df[cols]
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("User ID", format="%d"),
            "username": st.column_config.TextColumn("Username"),
            "password": st.column_config.TextColumn("Password"),
            "role": st.column_config.TextColumn("Role")
        }
    )

# --- MAIN APPLICATION UI ---
def main():
    st.set_page_config(page_title="CarePoint Clinic System", page_icon="💊", layout="wide")
    apply_custom_css()
    
    try:
        db = DatabaseManager()
        db.check_and_seed_records()
    except Exception as e:
        st.error("⚠️ Please configure your Supabase credentials in Streamlit Cloud Secrets.")
        return

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
