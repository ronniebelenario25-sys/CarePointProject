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
        """Queries the Supabase users table for secure login and fetches user ID, role, and full name"""
        try:
            response = self.supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
            data = response.data
            if data:
                user = data[0]
                uid = user.get("id") or user.get("user_id") or "1001"
                role = user.get("role")
                full_name = user.get("full_name") or username
                return role, uid, full_name
            return None, None, None
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None, None, None

    def register_patient(self, username, password, full_name):
        """Registers a new patient account with a unique username handle and separate full name"""
        try:
            existing = self.supabase.table("users").select("username").eq("username", username).execute()
            if existing.data:
                return False, "Username already exists. Please choose another."
            
            user_data = {
                "username": username,
                "password": password,
                "role": "Patient",
                "full_name": full_name
            }
            self.supabase.table("users").insert(user_data).execute()
            return True, None
        except Exception as e:
            if "full_name" in str(e):
                return False, "Database error: Please add a 'full_name' text column to your Supabase 'users' table."
            return False, str(e)

    def delete_user_completely(self, user_id, username):
        """Permanently deletes a user account and all their associated appointments by username handle"""
        try:
            self.supabase.table("users").delete().eq("id", user_id).execute()
            self.supabase.table("users").delete().eq("username", username).execute()
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

    def get_patient_appointments(self, username):
        """Fetches appointments for a specific patient username handle"""
        try:
            response = self.supabase.table("appointments").select("*").eq("patient_name", username).order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def add_appointment(self, username, doctor_id, appointment_date, appointment_time, status):
        """Adds a new appointment tied securely to the unique account username handle"""
        try:
            conflict_check = self.supabase.table("appointments").select("*").eq("doctor_id", doctor_id).eq("appointment_date", str(appointment_date)).eq("appointment_time", appointment_time).execute()
            
            if conflict_check.data:
                active_conflicts = [r for r in conflict_check.data if r.get("status"] != "Cancelled"]
                if active_conflicts:
                    return False, f"⚠️ Time Conflict: {doctor_id} already has an appointment at {appointment_time} on {appointment_date}. Please choose another slot."

            data = {
                "patient_name": username, # Uses unique username handle as the primary unique key
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status
            }
            self.supabase.table("appointments").insert(data).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_appointment(self, record_id, username, doctor_id, appointment_date, appointment_time, status, diagnosis, prescription):
        """Allows updating/editing patient appointments"""
        try:
            self.supabase.table("appointments").update({
                "patient_name": username,
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

def render_modern_table(records, users_list=None):
    """Renders records using Streamlit's native data grid and translates username handles to full names for readability"""
    if not records:
        st.warning("No records found.")
        return

    import pandas as pd
    formatted_records = []
    
    # Map username handles to full names if users_list is provided
    username_to_fullname = {}
    if users_list:
        for u in users_list:
            username_to_fullname[u.get('username')] = u.get('full_name') or u.get('username')

    for r in records:
        rec_copy = r.copy()
        raw_pname = rec_copy.get('patient_name')
        if raw_pname in username_to_fullname:
            rec_copy['patient_name'] = f"{username_to_fullname[raw_pname]} ({raw_pname})"
        formatted_records.append(rec_copy)

    df = pd.DataFrame(formatted_records)
    cols_order = [c for c in ['id', 'patient_name', 'doctor_id', 'appointment_date', 'appointment_time', 'status', 'diagnosis', 'prescription'] if c in df.columns]
    df = df[cols_order]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", format="%d"),
            "patient_name": st.column_config.TextColumn("Patient Name (Account)"),
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
    
    cols = [c for c in ['id', 'username', 'password', 'role', 'full_name'] if c in df.columns]
    df = df[cols]
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("User ID", format="%d"),
            "username": st.column_config.TextColumn("Username"),
            "password": st.column_config.TextColumn("Password"),
            "role": st.column_config.TextColumn("Role"),
            "full_name": st.column_config.TextColumn("Full Name")
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
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.full_name = None

    # --- 1. LOGIN GATEWAY & REGISTRATION ---
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align: center; color: #000000;'>💊 CarePoint Clinic Management System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #000000; font-weight: 600;'>Secure Cloud-Powered Healthcare & Queue Portal</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            auth_tab1, auth_tab2 = st.tabs(["🔐 Login", "📝 Create Patient Account"])
            
            with auth_tab1:
                st.info("💡 **Presentation Login Hints:**\n- Admin: `admin` / `password123`\n- Doctor: `doctor` / `password123`\n- Patient: `patient` / `password123`")
                
                with st.form("login_form"):
                    st.subheader("Account Login")
                    username = st.text_input("Username", value="admin")
                    password = st.text_input("Password", type="password", value="password123")
                    submit = st.form_submit_button("Access Portal", use_container_width=True)
                    
                    if submit:
                        role, user_id, full_name = db.authenticate(username, password)
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.role = role
                            st.session_state.username = username
                            st.session_state.user_id = user_id
                            st.session_state.full_name = full_name
                            st.success(f"Authenticated successfully as {role}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")
                            
            with auth_tab2:
                st.subheader("New Patient Registration")
                st.markdown("Create an account with a unique username and separate patient full name.")
                
                with st.form("register_form"):
                    new_user = st.text_input("Choose Unique Login Username (e.g., patient_user)")
                    new_pass = st.text_input("Choose Password", type="password")
                    new_fullname = st.text_input("Patient Full Name (e.g., John Doe)")
                    reg_submit = st.form_submit_button("Register Account", use_container_width=True)
                    
                    if reg_submit:
                        if new_user.strip() and new_pass.strip() and new_fullname.strip():
                            success, err = db.register_patient(new_user.strip(), new_pass.strip(), new_fullname.strip())
                            if success:
                                st.success(f"🎉 Patient account '{new_user}' created successfully for {new_fullname}! You can now log in.")
                            else:
                                st.error(err)
                        else:
                            st.error("Please fill in all fields.")
        return

    # --- 2. SIDEBAR NAVIGATION ---
    role = st.session_state.role
    st.sidebar.markdown(f"### 👤 User: **{st.session_state.username}**")
    st.sidebar.markdown(f"**Account ID:** `#{st.session_state.get('user_id', 'N/A')}`")
    
    display_role_label = "Master Patient" if st.session_state.username == "patient" else role
    st.sidebar.markdown(f"**Access Role:** `{display_role_label}`")
    
    selected_doctor = "All Doctors"
    doctors_list = [
        "All Doctors", "Dr. Smith", "Dr. Cruz", "Dr. Reyes", "Dr. Santos", 
        "Dr. Garcia", "Dr. Mendoza", "Dr. Torres", "Dr. Ramos", "Dr. Lim", "Dr. Villanueva"
    ]
    if role == "Doctor":
        st.sidebar.markdown("---")
        selected_doctor = st.sidebar.selectbox("🩺 Filter by Doctor Name", doctors_list)

    all_records = db.get_all_appointments()
    users_list = db.get_all_users()
    
    patient_options_map = {}
    for u in users_list:
        if str(u.get('role')).lower() == 'patient':
            disp_name = u.get('full_name') or u.get('username')
            display_label = f"ID #{u.get('id')} - {disp_name} ({u.get('username')})"
            patient_options_map[display_label] = u.get('username')
            
    for r in all_records:
        p_name = r.get('patient_name')
        if p_name and not any(p_name == val for val in patient_options_map.values()):
            display_label = f"Appointment - {p_name}"
            patient_options_map[display_label] = p_name

    patient_labels_list = sorted(list(patient_options_map.keys()))
    if not patient_labels_list:
        patient_labels_list = ["ID #1 - Patient"]
        patient_options_map["ID #1 - Patient"] = "patient"

    if role == "Patient":
        st.sidebar.markdown("---")
        if st.session_state.username == "patient":
            selected_label = st.sidebar.selectbox("Demo Patient Switcher (ID Filtered)", patient_labels_list)
            selected_active_username = patient_options_map[selected_label]
        else:
            selected_active_username = st.session_state.username
            current_user_obj = next((u for u in users_list if str(u.get('username')) == str(st.session_state.username)), {})
            display_name_sidebar = current_user_obj.get('full_name') or st.session_state.get('full_name') or st.session_state.username
            st.sidebar.info(f"**Viewing Dashboard for:**\n`{display_name_sidebar}` (ID #{st.session_state.get('user_id')})")

    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.full_name = None
        st.rerun()

    # --- 3. ROLE-BASED DASHBOARDS ---
    
    # --- ADMIN PORTAL ---
    if role == "Admin":
        st.title("🛠️ Administrative Control Center (Cashier & Master Management)")
        st.markdown("System-wide master monitoring dashboard, cashier payment verification, and record management.")
        
        records = db.get_all_appointments()
        pending_payment_count = len([r for r in records if r.get("status") == "Pending Payment"])
        
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Total Database Records", value=len(records))
        m2.metric(label="Pending Payments / Cashier Queue", value=pending_payment_count)
        m3.metric(label="Registered Accounts", value=len(users_list))
        
        st.markdown("---")
        
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "📋 Master Appointment Table", 
            "💵 Cashier & Edit Records", 
            "👥 Manage User Accounts",
            "➕ Add New Record"
        ])
        
        with admin_tab1:
            st.subheader("📋 Master Appointment Database")
            render_modern_table(records, users_list)
                
        with admin_tab2:
            st.subheader("💵 Cashier Payment Verification & Record Editing")
            st.markdown("Select a patient appointment to verify payment, mark as **Completed**, or update details.")
            
            if records:
                record_options = [f"ID: {r['id']} | Patient: {r['patient_name']} | Status: {r['status']} | Dr: {r['doctor_id']}" for r in records]
                selected_rec_str = st.selectbox("Select Record for Cashier / Modification", record_options)
                
                selected_id = int(selected_rec_str.split("|")[0].replace("ID:", "").strip())
                current_rec = next((r for r in records if r['id'] == selected_id), None)
                
                if current_rec:
                    with st.form("admin_edit_form"):
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_patient = st.text_input("Patient Username / Handle", value=current_rec['patient_name'])
                            edit_doctor = st.selectbox("Doctor ID", doctors_list[1:], index=doctors_list[1:].index(current_rec['doctor_id']) if current_rec['doctor_id'] in doctors_list[1:] else 0)
                            edit_date = st.text_input("Appointment Date (YYYY-MM-DD)", value=current_rec['appointment_date'])
                        with col_e2:
                            edit_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], index=["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"].index(current_rec['appointment_time']) if current_rec['appointment_time'] in ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"] else 0)
                            edit_status = st.selectbox("Status", ["Waiting", "Pending Payment", "Completed", "Cancelled"], index=["Waiting", "Pending Payment", "Completed", "Cancelled"].index(current_rec['status']) if current_rec['status'] in ["Waiting", "Pending Payment", "Completed", "Cancelled"] else 0)
                        
                        edit_diag = st.text_area("Diagnosis", value=current_rec.get('diagnosis') or "")
                        edit_presc = st.text_area("Prescription", value=current_rec.get('prescription') or "")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        update_btn = col_btn1.form_submit_button("💾 Save Changes & Mark Paid", use_container_width=True)
                        delete_btn = col_btn2.form_submit_button("🗑️ Delete Record", use_container_width=True)
                        
                        if update_btn:
                            success, err = db.update_appointment(selected_id, edit_patient, edit_doctor, edit_date, edit_time, edit_status, edit_diag, edit_presc)
                            if success:
                                st.success(f"Record #{selected_id} updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error updating record: {err}")
                                
                        if delete_btn:
                            try:
                                db.supabase.table("appointments").delete().eq("id", selected_id).execute()
                                st.success(f"Record #{selected_id} deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting record: {e}")
            else:
                st.warning("No records available to edit.")

        with admin_tab3:
            st.subheader("👥 Manage Registered User Accounts")
            st.markdown("Filter, search, and manage registered patient and doctor accounts in Supabase.")
            
            search_query = st.text_input("🔍 Search Accounts by Username or User ID", placeholder="Type username or user ID to filter...").strip().lower()
            non_admin_users = [u for u in users_list if str(u.get("role")).lower() != "admin"]
            
            if search_query:
                filtered_users = [
                    u for u in non_admin_users 
                    if search_query in str(u.get("username", "")).lower() 
                    or search_query in str(u.get("id", "")).lower()
                ]
            else:
                filtered_users = non_admin_users
                
            acc_tab1, acc_tab2 = st.tabs(["👤 Patient Accounts", "🩺 Doctor Accounts"])
            patients = [u for u in filtered_users if str(u.get("role")).lower() == "patient"]
            doctors = [u for u in filtered_users if str(u.get("role")).lower() == "doctor"]
            
            with acc_tab1:
                st.markdown(f"### 👤 Registered Patients ({len(patients)})")
                render_users_table(patients)
                
            with acc_tab2:
                st.markdown(f"### 🩺 Registered Doctors ({len(doctors)})")
                render_users_table(doctors)
            
            st.markdown("---")
            st.subheader("🗑️ Delete User Account")
            if filtered_users:
                user_options = [f"ID: {u['id']} | Username: {u['username']} | Role: {u['role']}" for u in filtered_users]
                selected_user_str = st.selectbox("Select User Account to Delete", user_options)
                
                sel_user_id = int(selected_user_str.split("|")[0].replace("ID:", "").strip())
                sel_username = selected_user_str.split("|")[1].replace("Username:", "").strip()
                
                if st.button("🗑️ Permanently Delete User Account", use_container_width=True):
                    success, err = db.delete_user_completely(sel_user_id, sel_username)
                    if success:
                        st.success(f"User account '{sel_username}' (ID: #{sel_user_id}) and their associated appointments permanently deleted from Supabase!")
                        st.rerun()
                    else:
                        st.error(f"Error deleting user account: {err}")
            else:
                st.info("No matching user accounts found.")

        with admin_tab4:
            st.subheader("➕ Add a New Master Appointment Record")
            with st.form("admin_add_form"):
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    new_patient = st.text_input("Patient Username / Handle")
                    new_doctor = st.selectbox("Assign Doctor", doctors_list[1:], key="add_doc")
                with col_a2:
                    new_date = st.date_input("Appointment Date")
                    new_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], key="add_time")
                
                new_status = st.selectbox("Initial Status", ["Waiting", "Pending Payment", "Completed", "Cancelled"], key="add_status")
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
                        st.error("Please enter a valid patient username.")

    # --- DOCTOR PORTAL ---
    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        st.markdown(f"Welcome, **{st.session_state.username}**. Managing clinical treatments and patient queue.")
        
        doc_records = [r for r in all_records if selected_doctor == "All Doctors" or r.get("doctor_id") == selected_doctor]
        
        doc_tab1, doc_tab2, doc_tab3 = st.tabs([
            "🩺 Consultation & Treatment Room", 
            "📋 Patient Schedule Queue", 
            "✅ Treated Patients (Pending Payment)"
        ])
        
        with doc_tab1:
            st.subheader("🩺 Patient Consultation & Prescription Workspace")
            st.markdown("Select a patient from your queue to examine records, write diagnosis, and issue prescriptions. *Note: Saving moves the patient to the cashier payment queue.*")
            
            if doc_records:
                patient_names_list = [f"{r['patient_name']} (ID: {r['id']} - {r['appointment_date']} {r['appointment_time']})" for r in doc_records]
                selected_patient_str = st.selectbox("Select Patient in Consultation", patient_names_list)
                
                chosen_record = next((r for r in doc_records if f"{r['patient_name']} (ID: {r['id']} - {r['appointment_date']} {r['appointment_time']})" == selected_patient_str), None)
                
                if chosen_record:
                    st.info(f"**Current Patient Handle:** {chosen_record['patient_name']} | **Assigned Doctor:** {chosen_record['doctor_id']} | **Time Slot:** {chosen_record['appointment_date']} at {chosen_record['appointment_time']}")
                    
                    with st.form("consultation_form"):
                        st.markdown("### Clinical Examination Notes")
                        existing_diag = chosen_record.get("diagnosis") or ""
                        existing_presc = chosen_record.get("prescription") or ""
                        
                        chief_complaint = st.text_area("Chief Complaint / Symptoms", placeholder="Enter patient's symptoms...")
                        diagnosis = st.text_area("Medical Diagnosis", value=existing_diag, placeholder="Enter official diagnosis...")
                        prescription = st.text_area("Prescription & Treatment Plan", value=existing_presc, placeholder="Enter prescribed medications and dosage...")
                        
                        save_consultation = st.form_submit_button("💾 Save Consultation & Send to Cashier", use_container_width=True)
                        
                        if save_consultation:
                            success, err = db.update_consultation(chosen_record["id"], diagnosis, prescription)
                            if success:
                                st.success(f"🎉 Consultation saved for {chosen_record['patient_name']}! Patient sent to cashier for payment verification.")
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
            render_modern_table(doc_records, users_list)

        with doc_tab3:
            st.subheader(f"💵 Treated Patients Awaiting Payment — {selected_doctor}")
            st.markdown("Patients who have completed their consultation and are waiting to pay at the admin desk.")
            
            pending_records = [r for r in doc_records if r.get("status") == "Pending Payment"]
            if pending_records:
                render_modern_table(pending_records, users_list)
            else:
                st.info(f"No patients currently waiting for payment with {selected_doctor}.")

    # --- PATIENT PORTAL ---
    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        
        logged_in_user_obj = next((u for u in users_list if str(u.get('username')) == str(st.session_state.username)), {})
        my_real_full_name = logged_in_user_obj.get('full_name') or st.session_state.get('full_name') or st.session_state.username
        
        if st.session_state.username == "patient":
            welcome_display_name = selected_active_username
            filter_username = selected_active_username
        else:
            welcome_display_name = my_real_full_name
            filter_username = st.session_state.username  # Strict unique account handle used for database queries!

        st.markdown(f"Welcome, **{welcome_display_name}** (`{filter_username}`).")
        
        # Filter appointments strictly by the unique account username handle to prevent name collisions
        patient_records = [r for r in all_records if r.get('patient_name') == filter_username]
        
        tab1, tab2, tab3 = st.tabs(["📅 Book New Appointment", "📋 My Confidential Appointments", "✏️ Edit My Appointments"])
        
        with tab1:
            st.subheader(f"Schedule a New Visit for {welcome_display_name}")
            with st.form("booking_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    # Display real full name on form, while passing filter_username to database backend
                    p_name_display = st.text_input("Patient Full Name", value=welcome_display_name, disabled=True)
                    doc_choice = st.selectbox("Select Attending Physician", doctors_list[1:])
                with col_b:
                    app_date = st.date_input("Preferred Date")
                    app_time = st.selectbox("Exact Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                
                book_submit = st.form_submit_button("Confirm & Secure Booking", use_container_width=True)
                
                if book_submit:
                    success, err_msg = db.add_appointment(filter_username, doc_choice, app_date, app_time, "Waiting")
                    if success:
                        st.success(f"🎉 Appointment successfully booked for {welcome_display_name} ({filter_username}) with {doc_choice}!")
                        st.rerun()
                    else:
                        st.error(err_msg)
                        
        with tab2:
            st.subheader(f"📋 Appointments for {welcome_display_name}")
            render_modern_table(patient_records, users_list)

        with tab3:
            st.subheader(f"✏️ Edit, Cancel, or Delete Appointments for {welcome_display_name}")
            if patient_records:
                pat_options = [f"ID: {r['id']} | Dr: {r['doctor_id']} | Date: {r['appointment_date']} {r['appointment_time']} | Status: {r['status']}" for r in patient_records]
                selected_pat_rec_str = st.selectbox("Select Appointment to Modify", pat_options, key="pat_edit_select")
                
                sel_pat_id = int(selected_pat_rec_str.split("|")[0].replace("ID:", "").strip())
                curr_pat_rec = next((r for r in patient_records if r['id'] == sel_pat_id), None)
                
                if curr_pat_rec:
                    with st.form("patient_self_edit_form"):
                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            edit_p_name = st.text_input("Patient Username Handle", value=curr_pat_rec['patient_name'], disabled=True)
                            edit_p_doc = st.selectbox("Attending Physician", doctors_list[1:], index=doctors_list[1:].index(curr_pat_rec['doctor_id']) if curr_pat_rec['doctor_id'] in doctors_list[1:] else 0)
                            edit_p_date = st.text_input("Appointment Date (YYYY-MM-DD)", value=curr_pat_rec['appointment_date'])
                        with col_p2:
                            edit_p_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], index=["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"].index(curr_pat_rec['appointment_time']) if curr_pat_rec['appointment_time'] in ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"] else 0)
                            edit_p_status = st.selectbox("Status", ["Waiting", "Cancelled"], index=["Waiting", "Cancelled"].index(curr_pat_rec['status']) if curr_pat_rec['status'] in ["Waiting", "Cancelled"] else 0)
                        
                        col_pb1, col_pb2, col_pb3 = st.columns(3)
                        save_p_edit = col_pb1.form_submit_button("💾 Save", use_container_width=True)
                        cancel_p_booking = col_pb2.form_submit_button("❌ Cancel", use_container_width=True)
                        delete_p_booking = col_pb3.form_submit_button("🗑️ Delete", use_container_width=True)
                        
                        if save_p_edit:
                            success, err = db.update_appointment(sel_pat_id, filter_username, edit_p_doc, edit_p_date, edit_p_time, edit_p_status, curr_pat_rec.get('diagnosis'), curr_pat_rec.get('prescription'))
                            if success:
                                st.success(f"Appointment #{sel_pat_id} updated successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error: {err}")
                                
                        if cancel_p_booking:
                            success, err = db.update_appointment(sel_pat_id, filter_username, curr_pat_rec['doctor_id'], curr_pat_rec['appointment_date'], curr_pat_rec['appointment_time'], "Cancelled", curr_pat_rec.get('diagnosis'), curr_pat_rec.get('prescription'))
                            if success:
                                st.warning(f"Appointment #{sel_pat_id} has been cancelled.")
                                st.rerun()
                            else:
                                st.error(f"Error: {err}")

                        if delete_p_booking:
                            try:
                                db.supabase.table("appointments").delete().eq("id", sel_pat_id).execute()
                                st.success(f"Appointment #{sel_pat_id} permanently deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting record: {e}")
            else:
                st.info(f"No appointments found for {welcome_display_name}.")

if __name__ == "__main__":
    main()
