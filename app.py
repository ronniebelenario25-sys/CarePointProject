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
            return False, str(e)

    def register_doctor(self, username, password, full_name, professional_role, prc_number, ptr_number):
        """Registers a new doctor account including professional role / specialty"""
        try:
            existing = self.supabase.table("users").select("username").eq("username", username).execute()
            if existing.data:
                return False, "Username already exists. Please choose another."
            
            user_data = {
                "username": username,
                "password": password,
                "role": "Doctor",
                "full_name": full_name,
                "professional_role": professional_role
            }
            self.supabase.table("users").insert(user_data).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_user_completely(self, user_id, username):
        """Permanently deletes a user account and all their associated appointments"""
        try:
            self.supabase.table("users").delete().eq("id", user_id).execute()
            self.supabase.table("users").delete().eq("username", username).execute()
            self.supabase.table("appointments").delete().eq("account_username", username).execute()
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
        """Fetches all master records"""
        try:
            response = self.supabase.table("appointments").select("*").order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def get_patient_appointments(self, username):
        """Fetches appointments booked by a specific account username"""
        try:
            response = self.supabase.table("appointments").select("*").eq("account_username", username).order("appointment_date", desc=False).execute()
            if not response.data:
                response = self.supabase.table("appointments").select("*").eq("patient_name", username).order("appointment_date", desc=False).execute()
            return response.data
        except Exception as e:
            return []

    def add_appointment(self, account_username, patient_name, doctor_id, appointment_date, appointment_time, status):
        """Adds a new appointment linked to the account username and specific patient name with double booking protection"""
        try:
            conflict_check = self.supabase.table("appointments").select("*").eq("doctor_id", doctor_id).eq("appointment_date", str(appointment_date)).eq("appointment_time", appointment_time).execute()
            
            if conflict_check.data:
                active_conflicts = [r for r in conflict_check.data if r.get("status") != "Cancelled"]
                if active_conflicts:
                    return False, f"⚠️ Time Conflict: {doctor_id} already has an appointment at {appointment_time} on {appointment_date}. Please choose another slot."

            data = {
                "account_username": account_username,
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

    def process_cashier_payment(self, record_id, payment_method, payment_amount, status, account_username, patient_name, doctor_id, appointment_date, appointment_time):
        """Allows Admin/Cashier to process payment and update status using the selected dropdown option"""
        try:
            self.supabase.table("appointments").update({
                "account_username": account_username,
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status,
                "payment_method": payment_method,
                "payment_amount": str(payment_amount)
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            try:
                self.supabase.table("appointments").update({
                    "account_username": account_username,
                    "patient_name": patient_name,
                    "doctor_id": doctor_id,
                    "appointment_date": str(appointment_date),
                    "appointment_time": appointment_time,
                    "status": status
                }).eq("id", record_id).execute()
                return True, None
            except Exception as e2:
                return False, str(e2)

    def update_appointment_admin(self, record_id, account_username, patient_name, doctor_id, appointment_date, appointment_time, status):
        """Allows Admin to update schedule status, date, time, and patient details WITHOUT altering clinical diagnosis or prescription"""
        try:
            self.supabase.table("appointments").update({
                "account_username": account_username,
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_appointment_patient(self, record_id, account_username, patient_name, doctor_id, appointment_date, appointment_time, status):
        """Allows Patient to update/reschedule or cancel their appointment details WITHOUT altering medical diagnosis or prescription"""
        try:
            self.supabase.table("appointments").update({
                "account_username": account_username,
                "patient_name": patient_name,
                "doctor_id": doctor_id,
                "appointment_date": str(appointment_date),
                "appointment_time": appointment_time,
                "status": status
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def update_consultation(self, record_id, diagnosis, prescription, appointment_date):
        """Strictly reserved for Doctors: updates appointment with diagnosis, prescription, and tracking serial number"""
        try:
            date_str = str(appointment_date).replace("-", "")
            tracking_num = f"RX-{date_str}-{record_id}"
            
            self.supabase.table("appointments").update({
                "diagnosis": diagnosis,
                "prescription": prescription,
                "tracking_number": tracking_num,
                "status": "Pending Payment"
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            try:
                self.supabase.table("appointments").update({
                    "diagnosis": diagnosis,
                    "prescription": prescription,
                    "status": "Pending Payment"
                }).eq("id", record_id).execute()
                return True, None
            except Exception as e2:
                return False, str(e2)

    def check_and_seed_records(self):
        """Ensures all 10 doctors have unevenly distributed patient counts totaling around 300 records"""
        try:
            existing = self.get_all_appointments()
            doctors = [
                "Dr. Smith (General Practitioner)", 
                "Dr. Cruz (Neurologist)", 
                "Dr. Reyes (Pediatrician)", 
                "Dr. Santos (Cardiologist)", 
                "Dr. Garcia (Dermatologist)", 
                "Dr. Mendoza (Ophthalmologist)", 
                "Dr. Torres (Orthopedic Surgeon)", 
                "Dr. Ramos (ENT Specialist)", 
                "Dr. Lim (Psychiatrist)", 
                "Dr. Villanueva (Obstetrician-Gynecologist)"
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
                    for i in range(doc_patient_count):
                        patient_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                        random_days = random.randint(-15, 15)
                        appointment_date = (datetime.now() + timedelta(days=random_days)).strftime("%Y-%m-%d")
                        appointment_time = random.choice(times)
                        status = random.choice(statuses)
                        
                        date_str = appointment_date.replace('-', '')
                        tracking_num = f"RX-{date_str}-{i+1000}" if status in ["Completed", "Pending Payment"] else None
                        
                        batch_data.append({
                            "account_username": "admin",
                            "patient_name": patient_name,
                            "doctor_id": doc,
                            "appointment_date": appointment_date,
                            "appointment_time": appointment_time,
                            "status": status,
                            "diagnosis": "Routine checkup and clinical evaluation normal." if status in ["Completed", "Pending Payment"] else None,
                            "prescription": "Paracetamol 500mg every 4 hours as needed." if status in ["Completed", "Pending Payment"] else None,
                            "tracking_number": tracking_num,
                            "payment_method": "Cash" if status == "Completed" else None,
                            "payment_amount": "500.00" if status == "Completed" else None
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
        .prescription-card {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_modern_table(records):
    """Renders records using Streamlit's native data grid"""
    if not records:
        st.warning("No records found.")
        return

    import pandas as pd
    df = pd.DataFrame(records)
    
    cols_order = [c for c in ['id', 'patient_name', 'doctor_id', 'appointment_date', 'appointment_time', 'status', 'tracking_number', 'payment_method', 'payment_amount', 'diagnosis', 'prescription'] if c in df.columns]
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
            "tracking_number": st.column_config.TextColumn("Tracking ID"),
            "payment_method": st.column_config.TextColumn("Payment Method"),
            "payment_amount": st.column_config.TextColumn("Amount Paid"),
            "diagnosis": st.column_config.TextColumn("Diagnosis"),
            "prescription": st.column_config.TextColumn("Prescription")
        }
    )

def render_doctors_table(users):
    """Renders doctor accounts table including professional role / specialty"""
    if not users:
        st.warning("No doctor accounts found.")
        return

    import pandas as pd
    df = pd.DataFrame(users)
    
    cols = [c for c in ['id', 'username', 'password', 'role', 'full_name', 'professional_role'] if c in df.columns]
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
            "full_name": st.column_config.TextColumn("Full Name"),
            "professional_role": st.column_config.TextColumn("Professional Role / Specialty")
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

    # --- SESSION STATE & URL QUERY PERSISTENCE INITIALIZATION ---
    if "authenticated" not in st.session_state:
        query_params = st.query_params
        if "auth" in query_params and query_params["auth"] == "true":
            st.session_state.authenticated = True
            st.session_state.username = query_params.get("user", "admin")
            st.session_state.role = query_params.get("role", "Admin")
            st.session_state.user_id = query_params.get("uid", "1001")
            st.session_state.full_name = query_params.get("name", st.session_state.username)
        else:
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.full_name = None

    if "is_submitting_action" not in st.session_state:
        st.session_state.is_submitting_action = False

    # --- 1. LOGIN GATEWAY ---
    if not st.session_state.authenticated:
        st.markdown("<h1 style='text-align: center; color: #000000;'>💊 CarePoint Clinic Management System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #000000; font-weight: 600;'>Secure Cloud-Powered Healthcare & Queue Portal</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.info("💡 **Presentation Login Hints:**\n- Admin: `admin` / `password123`\n- Doctor: `doctor` / `password123`\n- Patient: `patient` / `password123`")
            
            with st.form("login_form"):
                st.subheader("Account Login")
                username = st.text_input("Username", value="admin")
                password = st.text_input("Password", type="password", value="password123")
                
                login_btn_label = "Logging in..." if st.session_state.is_submitting_action else "Access Portal"
                submit = st.form_submit_button(login_btn_label, use_container_width=True, disabled=st.session_state.is_submitting_action)
                
                if submit and not st.session_state.is_submitting_action:
                    st.session_state.is_submitting_action = True
                    with st.spinner("⏳ Authenticating credentials..."):
                        role, user_id, full_name = db.authenticate(username, password)
                        st.session_state.is_submitting_action = False
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.role = role
                            st.session_state.username = username
                            st.session_state.user_id = user_id
                            st.session_state.full_name = full_name
                            
                            st.query_params.update({
                                "auth": "true",
                                "user": username,
                                "role": role,
                                "uid": str(user_id),
                                "name": full_name
                            })
                            
                            st.success(f"Authenticated successfully as {role}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")
        return

    # --- 2. SIDEBAR NAVIGATION ---
    role = st.session_state.role
    st.sidebar.markdown(f"### 👤 User: **{st.session_state.username}**")
    st.sidebar.markdown(f"**Account ID:** `#{st.session_state.get('user_id', 'N/A')}`")
    
    display_role_label = "Master Patient" if st.session_state.username == "patient" else role
    st.sidebar.markdown(f"**Access Role:** `{display_role_label}`")
    
    users_list = db.get_all_users()
    
    base_doctors = [
        "Dr. Smith (General Practitioner)", 
        "Dr. Cruz (Neurologist)", 
        "Dr. Reyes (Pediatrician)", 
        "Dr. Santos (Cardiologist)", 
        "Dr. Garcia (Dermatologist)", 
        "Dr. Mendoza (Ophthalmologist)", 
        "Dr. Torres (Orthopedic Surgeon)", 
        "Dr. Ramos (ENT Specialist)", 
        "Dr. Lim (Psychiatrist)", 
        "Dr. Villanueva (Obstetrician-Gynecologist)"
    ]
    
    registered_docs = [
        f"{u.get('full_name')} ({u.get('professional_role')})" 
        for u in users_list 
        if str(u.get('role')).lower() == 'doctor' and u.get('full_name')
    ]
    
    combined_doctors = base_doctors + [d for d in registered_docs if d not in base_doctors]
    doctors_list = ["All Doctors"] + combined_doctors

    selected_doctor = "All Doctors"
    if role == "Doctor":
        st.sidebar.markdown("---")
        selected_doctor = st.sidebar.selectbox("🩺 Filter by Doctor Name", doctors_list)

    all_records = db.get_all_appointments()
    
    patient_options_map = {}
    for u in users_list:
        if str(u.get('role')).lower() == 'patient':
            disp_name = u.get('full_name') or u.get('username')
            display_label = f"ID #{u.get('id')} - {disp_name} ({u.get('username')})"
            patient_options_map[display_label] = u.get('username')
            
    for r in all_records:
        p_name = r.get('account_username') or r.get('patient_name')
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
        st.query_params.clear()
        st.rerun()

    # --- 3. ROLE-BASED DASHBOARDS ---
    
    # --- ADMIN PORTAL ---
    if role == "Admin":
        st.title("🛠️ Administrative Control Center (Cashier & Master Management)")
        st.markdown("System-wide master monitoring dashboard, cashier payment processing, and scheduling management.")
        
        records = db.get_all_appointments()
        pending_payment_count = len([r for r in records if r.get("status") == "Pending Payment"])
        
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Total Database Records", value=len(records))
        m2.metric(label="Pending Payments / Cashier Queue", value=pending_payment_count)
        m3.metric(label="Registered Accounts", value=len(users_list))
        
        st.markdown("---")
        
        admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5, admin_tab6 = st.tabs([
            "📋 Master Appointment Table", 
            "💵 Cashier Checkout & Schedule", 
            "👥 Manage User Accounts",
            "🩺 Create Doctor Account",
            "👤 Create User Account",
            "➕ Book Walk-In Appointment"
        ])
        
        with admin_tab1:
            st.subheader("📋 Master Appointment Database")
            render_modern_table(records)
                
        with admin_tab2:
            st.subheader("💵 Cashier Payment Verification & Checkout Desk")
            st.markdown("Process consultation payments and print official receipts or prescriptions separately.")
            
            if records:
                sorted_records = sorted(records, key=lambda x: int(x['id']))
                record_options = [f"ID #{r['id']} | Patient: {r['patient_name']} | Status: {r['status']} | Dr: {r['doctor_id']}" for r in sorted_records]
                selected_rec_str = st.selectbox("Select Record for Cashier Checkout / Printing", record_options)
                
                selected_id = int(selected_rec_str.split("|")[0].replace("ID:", "").replace("ID", "").replace("#", "").strip())
                current_rec = next((r for r in records if r['id'] == selected_id), None)
                
                if current_rec:
                    with st.form("admin_cashier_form"):
                        st.markdown(f"### 💳 Checkout & Verification for Patient: **{current_rec['patient_name']}** (ID #{current_rec['id']})")
                        
                        # --- CASHIER SECURE VIEW (Prescription & Appointment info ONLY, Diagnosis Hidden) ---
                        st.markdown("---")
                        st.markdown("#### 📄 Authenticated Appointment & Prescription Details (Cashier View)")
                        rx_serial = current_rec.get('tracking_number') or f"RX-PENDING-{current_rec.get('id')}"
                        st.info(f"**Prescription Tracking ID:** `{rx_serial}`\n\n"
                                f"**Patient Name:** {current_rec['patient_name']}\n\n"
                                f"**Attending Physician:** {current_rec['doctor_id']}\n\n"
                                f"**Appointment Schedule:** {current_rec['appointment_date']} at {current_rec['appointment_time']}\n\n"
                                f"**Prescription / Treatment Plan:**\n{current_rec.get('prescription') or 'No prescription issued yet.'}")
                        st.markdown("---")
                        
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            pay_method = st.selectbox("Payment Method", ["Cash", "GCash", "Credit/Debit Card", "Health Insurance / HMO"], index=0)
                            pay_amount = st.text_input("Payment Amount (PHP)", value="500.00")
                        with col_c2:
                            status_options = ["Pending Payment", "Completed", "Waiting", "Cancelled"]
                            default_status_index = status_options.index(current_rec['status']) if current_rec['status'] in status_options else 1
                            edit_status_cashier = st.selectbox("Update Status", status_options, index=default_status_index)
                        
                        st.markdown("---")
                        st.markdown("### 📋 Schedule Details")
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_acc = st.text_input("Account Username", value=current_rec.get('account_username') or current_rec['patient_name'])
                            edit_patient = st.text_input("Patient Full Name", value=current_rec['patient_name'])
                            edit_doctor = st.selectbox("Doctor ID", doctors_list[1:], index=doctors_list[1:].index(current_rec['doctor_id']) if current_rec['doctor_id'] in doctors_list[1:] else 0)
                        with col_e2:
                            edit_date = st.text_input("Appointment Date (YYYY-MM-DD)", value=current_rec['appointment_date'])
                            edit_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], index=["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"].index(current_rec['appointment_time']) if current_rec['appointment_time'] in ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"] else 0)
                        
                        col_btn1, col_btn2 = st.columns(2)
                        pay_lbl = "Processing..." if st.session_state.is_submitting_action else "💰 Process Payment & Complete"
                        del_lbl = "Deleting..." if st.session_state.is_submitting_action else "🗑️ Delete Record"
                        
                        process_pay_btn = col_btn1.form_submit_button(pay_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                        delete_btn = col_btn2.form_submit_button(del_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                        
                        if process_pay_btn and not st.session_state.is_submitting_action:
                            st.session_state.is_submitting_action = True
                            with st.spinner("⏳ Processing payment..."):
                                success, err = db.process_cashier_payment(selected_id, pay_method, pay_amount, edit_status_cashier, edit_acc, edit_patient, edit_doctor, edit_date, edit_time)
                                st.session_state.is_submitting_action = False
                                if success:
                                    st.success(f"Payment of ₱{pay_amount} processed via {pay_method} for Record #{selected_id}! Status updated to {edit_status_cashier}.")
                                    st.rerun()
                                else:
                                    st.error(f"Error processing payment: {err}")
                                    
                        if delete_btn and not st.session_state.is_submitting_action:
                            st.session_state.is_submitting_action = True
                            with st.spinner("⏳ Deleting record..."):
                                try:
                                    db.supabase.table("appointments").delete().eq("id", selected_id).execute()
                                    st.session_state.is_submitting_action = False
                                    st.success(f"Record #{selected_id} deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.session_state.is_submitting_action = False
                                    st.error(f"Error deleting record: {e}")

        with admin_tab3:
            st.subheader("👥 User Account Directory & Management")
            render_users_table(users_list)
            
            st.markdown("---")
            st.subheader("🗑️ Delete User Account")
            with st.form("delete_user_form"):
                user_to_delete_username = st.text_input("Enter Username to Delete Permanently")
                del_user_submit = st.form_submit_button("Delete User & Associated Records")
                if del_user_submit:
                    target_user = next((u for u in users_list if u.get('username') == user_to_delete_username), None)
                    if target_user:
                        success, err = db.delete_user_completely(target_user.get('id'), user_to_delete_username)
                        if success:
                            st.success(f"User '{user_to_delete_username}' and all associated appointments deleted successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error deleting user: {err}")
                    else:
                        st.error("Username not found in database.")

        with admin_tab4:
            st.subheader("🩺 Register New Doctor Account")
            with st.form("admin_doc_reg"):
                doc_user = st.text_input("Doctor Username")
                doc_pass = st.text_input("Password", type="password")
                doc_name = st.text_input("Doctor Full Name (e.g., Dr. Juan Santos, M.D.)")
                doc_spec = st.text_input("Professional Specialty / Role (e.g., Cardiologist)")
                doc_prc = st.text_input("PRC License Number")
                doc_ptr = st.text_input("PTR Number")
                doc_submit = st.form_submit_button("Create Doctor Account")
                if doc_submit:
                    if doc_user and doc_pass and doc_name:
                        success, err = db.register_doctor(doc_user, doc_pass, doc_name, doc_spec, doc_prc, doc_ptr)
                        if success:
                            st.success(f"Doctor account for {doc_name} created successfully!")
                            st.rerun()
                        else:
                            st.error(err)
                    else:
                        st.error("Please fill in all required fields.")

        with admin_tab5:
            st.subheader("👤 Register General User / Patient Account")
            with st.form("admin_user_reg"):
                u_user = st.text_input("Username Handle")
                u_pass = st.text_input("Password", type="password")
                u_name = st.text_input("Full Name")
                u_submit = st.form_submit_button("Create User Account")
                if u_submit:
                    if u_user and u_pass and u_name:
                        success, err = db.register_patient(u_user, u_pass, u_name)
                        if success:
                            st.success(f"Patient account for {u_name} created successfully!")
                            st.rerun()
                        else:
                            st.error(err)
                    else:
                        st.error("Please fill in all fields.")

        with admin_tab6:
            st.subheader("➕ Book Walk-In Appointment")
            with st.form("walkin_form"):
                wi_patient = st.text_input("Patient Full Name")
                wi_doctor = st.selectbox("Assign Doctor", doctors_list[1:])
                wi_date = st.date_input("Appointment Date", datetime.now())
                wi_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                wi_submit = st.form_submit_button("Book Walk-In Appointment")
                if wi_submit:
                    success, err = db.add_appointment("admin", wi_patient, wi_doctor, str(wi_date), wi_time, "Waiting")
                    if success:
                        st.success(f"Walk-in appointment for {wi_patient} booked successfully!")
                        st.rerun()
                    else:
                        st.error(err)

    # --- DOCTOR PORTAL ---
    elif role == "Doctor":
        st.title("👨‍⚕️ Doctor's Consultation & Prescription Module")
        st.markdown(f"Welcome, **{st.session_state.full_name}** | Review patient queues, save clinical diagnoses, prescribe medications, and print verified prescriptions.")
        
        doc_records = db.get_all_appointments()
        if selected_doctor != "All Doctors":
            doc_records = [r for r in doc_records if r.get('doctor_id') == selected_doctor]
            
        doc_tab1, doc_tab2 = st.tabs(["📋 Assigned Patient Queue", "📝 Consultation & Prescription Desk"])
        
        with doc_tab1:
            st.subheader("Assigned Appointments & Queue")
            render_modern_table(doc_records)
            
        with doc_tab2:
            st.subheader("Consultation Diagnosis & Prescription Entry")
            if doc_records:
                sorted_doc_recs = sorted(doc_records, key=lambda x: int(x['id']))
                rec_choices = [f"ID #{r['id']} | Patient: {r['patient_name']} | Date: {r['appointment_date']} | Status: {r['status']}" for r in sorted_doc_recs]
                selected_rec_choice = st.selectbox("Select Patient Appointment for Consultation", rec_choices)
                
                sel_id = int(selected_rec_choice.split("|")[0].replace("ID:", "").replace("ID", "").replace("#", "").strip())
                sel_rec = next((r for r in doc_records if r['id'] == sel_id), None)
                
                if sel_rec:
                    with st.form("doctor_consultation_form"):
                        st.markdown(f"### Patient: **{sel_rec['patient_name']}** (Schedule: {sel_rec['appointment_date']} at {sel_rec['appointment_time']})")
                        
                        diag_input = st.text_area("Clinical Diagnosis", value=sel_rec.get('diagnosis') or "")
                        rx_input = st.text_area("Prescription / Treatment Plan", value=sel_rec.get('prescription') or "")
                        
                        doc_submit_btn = st.form_submit_button("Save Diagnosis & Generate Tracking Serial")
                        
                        if doc_submit_btn:
                            success, err = db.update_consultation(sel_id, diag_input, rx_input, sel_rec['appointment_date'])
                            if success:
                                st.success(f"Consultation saved for Record #{sel_id}! Status updated to Pending Payment.")
                                st.rerun()
                            else:
                                st.error(f"Error saving consultation: {err}")

                    st.markdown("---")
                    st.subheader("🖨️ Print Official Prescription Slip")
                    
                    prc_num_input = st.text_input("Your PRC License Number", value="1234567")
                    ptc_num_input = st.text_input("Your PTR / Clinic Number", value="PTR-2026-988")
                    
                    if st.button("Print Prescription Slip Form"):
                        serial_num = sel_rec.get('tracking_number') or f"RX-{sel_rec['appointment_date'].replace('-', '')}-{sel_id}"
                        st.markdown("---")
                        st.markdown(f"""
                        <div class="prescription-card">
                            <h2 style="text-align: center; color: #0f172a;">📄 CAREPOINT CLINIC OFFICIAL MEDICAL PRESCRIPTION</h2>
                            <p><b>Tracking Serial:</b> `{serial_num}`</p>
                            <p><b>Date Issued:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                            <hr>
                            <p><b>Patient Name:</b> {sel_rec['patient_name']}</p>
                            <p><b>Clinical Diagnosis:</b> {sel_rec.get('diagnosis', 'Not specified')}</p>
                            <br>
                            <h3>Rx (Prescription Details):</h3>
                            <p style="font-size: 16px; background: #f1f5f9; padding: 15px; border-radius: 8px;"><b>{sel_rec.get('prescription', 'No medication prescribed yet.')}</b></p>
                            <br><br>
                            <p><b>Attending Physician:</b> {sel_rec['doctor_id']}</p>
                            <p><b>PRC No:</b> {prc_num_input} | <b>PTR No:</b> {ptc_num_input}</p>
                            <br><br>
                            <div style="float: right; text-align: center; width: 250px;">
                                <div style="border-bottom: 1px solid #000; margin-bottom: 5px;"></div>
                                <p style="font-size: 12px; margin: 0;"><b>Doctor's Signature over Printed Name</b><br><i>(Physical wet-ink signature required)</i></p>
                            </div>
                            <div style="clear: both;"></div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info("💡 Present this printed prescription slip to the patient. They must proceed to the cashier/admin to settle payment or arrange a promissory note for validation.")

    # --- PATIENT PORTAL ---
    elif role == "Patient":
        st.title("👤 Patient Portal & Appointment Manager")
        st.markdown(f"Welcome, **{st.session_state.full_name}** | View your appointments, booking history, and prescribed treatments.")
        
        target_uname = selected_active_username if st.session_state.username == "patient" else st.session_state.username
        patient_records = db.get_patient_appointments(target_uname)
        
        m1, m2 = st.columns(2)
        m1.metric(label="Your Total Appointments", value=len(patient_records))
        active_rx_count = len([r for r in patient_records if r.get("prescription")])
        m2.metric(label="Prescriptions Issued", value=active_rx_count)
        
        st.markdown("---")
        
        pt_tab1, pt_tab2 = st.tabs(["📋 My Appointments & Prescriptions", "➕ Book New Appointment"])
        
        with pt_tab1:
            st.subheader("Your Appointment History")
            render_modern_table(patient_records)
            
            if patient_records:
                st.markdown("---")
                st.subheader("📄 View Prescriptions & Payment Statuses")
                rx_options = [f"ID #{r['id']} | Dr. {r['doctor_id']} | Date: {r['appointment_date']} | Status: {r['status']}" for r in patient_records]
                chosen_rx_str = st.selectbox("Select Appointment to View Details", rx_options)
                
                chosen_id = int(chosen_rx_str.split("|")[0].replace("ID:", "").replace("ID", "").replace("#", "").strip())
                chosen_rec = next((r for r in patient_records if r['id'] == chosen_id), None)
                
                if chosen_rec:
                    st.info(f"**Tracking Serial:** `{chosen_rec.get('tracking_number', 'Pending')}`\n\n"
                            f"**Status / Clearance:** `{chosen_rec['status']}`\n\n"
                            f"**Diagnosis:** {chosen_rec.get('diagnosis', 'Pending evaluation')}\n\n"
                            f"**Prescription:** {chosen_rec.get('prescription', 'No prescription issued yet.')}")
                    
                    if chosen_rec['status'] == "Completed":
                        st.success("✅ Payment verified by cashier.")
                    else:
                        st.warning("⚠️ Payment pending with cashier.")
                        
        with pt_tab2:
            st.subheader("Book a New Consultation Appointment")
            with st.form("patient_booking_form"):
                p_name_input = st.text_input("Patient Full Name", value=st.session_state.full_name)
                doc_choice = st.selectbox("Select Doctor", doctors_list[1:])
                date_choice = st.date_input("Appointment Date", datetime.now() + timedelta(days=1))
                time_choice = st.selectbox("Preferred Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                
                book_submit = st.form_submit_button("Submit Appointment Booking")
                if book_submit:
                    success, err = db.add_appointment(st.session_state.username, p_name_input, doc_choice, str(date_choice), time_choice, "Waiting")
                    if success:
                        st.success("Appointment booked successfully! Our clinic staff will review your slot.")
                        st.rerun()
                    else:
                        st.error(err)

if __name__ == "__main__":
    main()
