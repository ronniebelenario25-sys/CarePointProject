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
        """Fetches appointments for the doctor portal view"""
        try:
            response = self.supabase.table("appointments").select("*").order("appointment_date", desc=False).execute()
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
        """Adds a new appointment with exact time tracking and error handling"""
        try:
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

    def update_consultation(self, record_id, diagnosis, prescription, status):
        """Updates appointment with consultation diagnosis, prescription, and status"""
        try:
            self.supabase.table("appointments").update({
                "diagnosis": diagnosis,
                "prescription": prescription,
                "status": status
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
                statuses = ["Waiting", "Completed", "Cancelled"]

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
                            "diagnosis": "Routine checkup and clinical evaluation normal." if status == "Completed" else None,
                            "prescription": "Paracetamol 500mg every 4 hours as needed." if status == "Completed" else None
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
            st.info("💡 **Presentation Login Hints:**\n- Admin: `admin` / `password123`\n- Doctor: `doctor` / `password123`\n- Patient: `patient` / `password123`")
            
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
    
    selected_doctor = "All Doctors"
    doctors_list = [
        "All Doctors", "Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos", 
        "Dr. Garcia", "Dr. Mendoza", "Dr. Torres", "Dr. Ramos", "Dr. Lim", "Dr. Villanueva"
    ]
    if role == "Doctor":
        st.sidebar.markdown("---")
        selected_doctor = st.sidebar.selectbox("🩺 Filter by Doctor Name", doctors_list)

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
        st.markdown("System-wide master monitoring dashboard and record management connected directly to Supabase.")
        
        records = db.get_all_appointments()
        
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Total Database Records", value=len(records))
        m2.metric(label="Active Queue Status", value="Online 🟢")
        m3.metric(label="System Security", value="Role-Based Protected")
        
        st.markdown("---")
        
        admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📋 Master Appointment Table", "✏️ Edit / Delete Records", "➕ Add New Record"])
        
        with admin_tab1:
            st.subheader("📋 Master Appointment Database")
            if records:
                st.dataframe(records, use_container_width=True)
            else:
                st.warning("No records found in the database.")
                
        with admin_tab2:
            st.subheader("✏️ Edit or Delete Specific Records")
            st.markdown("Select a record ID below to update details or permanently remove useless entries.")
            
            if records:
                record_options = [f"ID: {r['id']} | Patient: {r['patient_name']} | Dr: {r['doctor_id']} | Date: {r['appointment_date']}" for r in records]
                selected_rec_str = st.selectbox("Select Record to Modify", record_options)
                
                selected_id = int(selected_rec_str.split("|")[0].replace("ID:", "").strip())
                current_rec = next((r for r in records if r['id'] == selected_id), None)
                
                if current_rec:
                    with st.form("admin_edit_form"):
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_patient = st.text_input("Patient Name", value=current_rec['patient_name'])
                            edit_doctor = st.selectbox("Doctor ID", doctors_list[1:], index=doctors_list[1:].index(current_rec['doctor_id']) if current_rec['doctor_id'] in doctors_list[1:] else 0)
                            edit_date = st.text_input("Appointment Date (YYYY-MM-DD)", value=current_rec['appointment_date'])
                        with col_e2:
                            edit_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], index=["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"].index(current_rec['appointment_time']) if current_rec['appointment_time'] in ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"] else 0)
                            edit_status = st.selectbox("Status", ["Waiting", "Completed", "Cancelled"], index=["Waiting", "Completed", "Cancelled"].index(current_rec['status']) if current_rec['status'] in ["Waiting", "Completed", "Cancelled"] else 0)
                        
                        edit_diag = st.text_area("Diagnosis", value=current_rec.get('diagnosis') or "")
                        edit_presc = st.text_area("Prescription", value=current_rec.get('prescription') or "")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        update_btn = col_btn1.form_submit_button("💾 Save Changes", use_container_width=True)
                        delete_btn = col_btn2.form_submit_button("🗑️ Delete Record", use_container_width=True)
                        
                        if update_btn:
                            try:
                                db.supabase.table("appointments").update({
                                    "patient_name": edit_patient,
                                    "doctor_id": edit_doctor,
                                    "appointment_date": edit_date,
                                    "appointment_time": edit_time,
                                    "status": edit_status,
                                    "diagnosis": edit_diag,
                                    "prescription": edit_presc
                                }).eq("id", selected_id).execute()
                                st.success(f"Record #{selected_id} updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating record: {e}")
                                
                        if delete_btn:
                            try:
                                db.supabase.table("appointments").delete().eq("id", selected_id).execute()
                                st.success(f"Record #{selected_id} deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting record: {e}")
            else:
                st.warning("No records available to edit or delete.")

        with admin_tab3:
            st.subheader("➕ Add a New Master Appointment Record")
            with st.form("admin_add_form"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    new_patient = st.text_input("Patient Full Name")
                    new_doctor = st.selectbox("Assign Doctor", doctors_list[1:], key="add_doc")
                with col_a2:
                    new_date = st.date_input("Appointment Date")
                    new_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], key="add_time")
                
                new_status = st.selectbox("Initial Status", ["Waiting", "Completed", "Cancelled"], key="add_status")
                
                add_submit = st.form_submit_button("➕ Insert New Record", use_container_width=True)
                
                if add_submit:
                    if new_patient.strip():
                        success, err = db.add_appointment(new_patient, new_doctor, str(new_date), new_time, new_status)
                        if success:
                            st.success(f"Successfully added record for {new_patient}!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add record: {err}")
                    else:
                        st.error("Please enter a valid patient name.")

    # --- DOCTOR PORTAL ---
    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        st.markdown(f"Welcome, **{st.session_state.username}**. Managing clinical treatments and patient queue.")
        
        all_records = db.get_doctor_appointments(st.session_state.username)
        if selected_doctor == "All Doctors":
            doc_records = all_records
        else:
            doc_records = [r for r in all_records if r.get("doctor_id") == selected_doctor]
        
        doc_tab1, doc_tab2, doc_tab3 = st.tabs([
            "🩺 Consultation & Treatment Room", 
            "📋 Patient Schedule Queue", 
            "✅ Completed & Paid Patients"
        ])
        
        with doc_tab1:
            st.subheader("🩺 Patient Consultation & Prescription Workspace")
            st.markdown("Select a patient from your queue to examine records, write diagnosis, and issue prescriptions.")
            
            if doc_records:
                patient_names_list = [f"{r['patient_name']} (ID: {r['id']} - {r['appointment_date']} {r['appointment_time']})" for r in doc_records]
                selected_patient_str = st.selectbox("Select Patient in Consultation", patient_names_list)
                
                chosen_record = next((r for r in doc_records if f"{r['patient_name']} (ID: {r['id']} - {r['appointment_date']} {r['appointment_time']})" == selected_patient_str), None)
                
                if chosen_record:
                    st.info(f"**Current Patient:** {chosen_record['patient_name']} | **Assigned Doctor:** {chosen_record['doctor_id']} | **Time Slot:** {chosen_record['appointment_date']} at {chosen_record['appointment_time']}")
                    
                    with st.form("consultation_form"):
                        st.markdown("### Clinical Examination Notes")
                        existing_diag = chosen_record.get("diagnosis") or ""
                        existing_presc = chosen_record.get("prescription") or ""
                        
                        chief_complaint = st.text_area("Chief Complaint / Symptoms", placeholder="Enter patient's symptoms...")
                        diagnosis = st.text_area("Medical Diagnosis", value=existing_diag, placeholder="Enter official diagnosis...")
                        prescription = st.text_area("Prescription & Treatment Plan", value=existing_presc, placeholder="Enter prescribed medications and dosage...")
                        
                        update_status = st.selectbox("Update Appointment Status", ["Completed", "Waiting", "Cancelled"], index=0 if chosen_record.get("status") == "Completed" else 0)
                        
                        save_consultation = st.form_submit_button("💾 Save Consultation & Issue Prescription", use_container_width=True)
                        
                        if save_consultation:
                            success, err = db.update_consultation(chosen_record["id"], diagnosis, prescription, update_status)
                            if success:
                                st.success(f"🎉 Consultation and prescription successfully saved for {chosen_record['patient_name']}!")
                                st.rerun()
                            else:
                                st.error(f"Failed to save: {err}")
            else:
                st.warning("No patients available in your queue for consultation.")

        with doc_tab2:
            col1, col2 = st.columns(2)
            col1.metric(label=f"Appointments ({selected_doctor})", value=len(doc_records))
            col2.metric(label="Clinic Queue Status", value="Active 🟢")
            
            st.markdown("---")
            st.subheader(f"🕒 Patient Schedule — {selected_doctor}")
            
            if doc_records:
                st.dataframe(doc_records, use_container_width=True)
            else:
                st.warning(f"No appointments currently available for {selected_doctor}.")

        with doc_tab3:
            st.subheader(f"✅ Completed & Paid Records — {selected_doctor}")
            st.markdown("Click or select a patient below to inspect their full medical record, diagnosis, and prescription.")
            
            completed_records = [r for r in doc_records if r.get("status") == "Completed"]
            
            if completed_records:
                completed_list = [f"{r['patient_name']} (ID: {r['id']} - Date: {r['appointment_date']})" for r in completed_records]
                selected_completed_str = st.selectbox("Select Completed Patient to View Record", completed_list, key="completed_select")
                
                selected_comp_record = next((r for r in completed_records if f"{r['patient_name']} (ID: {r['id']} - Date: {r['appointment_date']})" == selected_completed_str), None)
                
                if selected_comp_record:
                    st.markdown("---")
                    st.success(f"📄 **Medical Record & Prescription Details for {selected_comp_record['patient_name']}**")
                    
                    col_c1, col_c2 = st.columns(2)
                    with col_c1:
                        st.markdown(f"**Patient Name:** {selected_comp_record['patient_name']}")
                        st.markdown(f"**Attending Physician:** {selected_comp_record['doctor_id']}")
                        st.markdown(f"**Appointment Date & Time:** {selected_comp_record['appointment_date']} at {selected_comp_record['appointment_time']}")
                    with col_c2:
                        st.markdown(f"**Appointment Status:** `{selected_comp_record['status']}` (Paid / Completed)")
                        st.markdown(f"**Record ID:** #{selected_comp_record['id']}")
                    
                    st.markdown("### 📝 Clinical Findings & Treatment")
                    st.info(f"**Diagnosis:**\n\n{selected_comp_record.get('diagnosis') or 'No diagnosis recorded yet.'}")
                    st.warning(f"**Prescription / Medication Plan:**\n\n{selected_comp_record.get('prescription') or 'No prescription recorded yet.'}")
            else:
                st.info(f"No completed or paid patients found for {selected_doctor} yet.")

    # --- PATIENT PORTAL ---
    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        st.markdown(f"Welcome back, **{st.session_state.username}**. Manage your healthcare appointments safely and confidentially.")
        
        tab1, tab2 = st.tabs(["📅 Book New Appointment", "📋 My Confidential Appointments"])
        
        with tab1:
            st.subheader("Schedule a New Clinic Visit")
            with st.form("booking_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    p_name = st.text_input("Full Name", value=st.session_state.username)
                    doc_choice = st.selectbox("Select Attending Physician", doctors_list[1:])
                with col_b:
                    app_date = st.date_input("Preferred Date")
                    app_time = st.selectbox("Exact Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                
                book_submit = st.form_submit_button("Confirm & Secure Booking", use_container_width=True)
                
                if book_submit:
                    success, err_msg = db.add_appointment(p_name, doc_choice, app_date, app_time, "Waiting")
                    if success:
                        st.success("🎉 Appointment successfully booked and synchronized with the cloud database!")
                        st.rerun()
                    else:
                        st.error(f"Failed to submit booking. Supabase Error: {err_msg}")
                        
        with tab2:
            st.subheader("Your Personal Medical Appointments")
            my_records = db.get_patient_appointments(st.session_state.username)
            if my_records:
                st.dataframe(my_records, use_container_width=True)
            else:
                st.info("You have no scheduled appointments under this account name.")

if __name__ == "__main__":
    main()
