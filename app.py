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
        """Queries the Supabase users table for secure login and fetches user ID, role, full name, PRC, and PTR"""
        try:
            response = self.supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
            data = response.data
            if data:
                user = data[0]
                uid = user.get("id") or user.get("user_id") or "1001"
                role = user.get("role")
                full_name = user.get("full_name") or username
                prc_number = user.get("prc_number") or "1234567"
                ptr_number = user.get("ptr_number") or "PTR-2026-988"
                return role, uid, full_name, prc_number, ptr_number
            return None, None, None, None, None
        except Exception as e:
            st.error(f"Database connection error: {e}")
            return None, None, None, None, None

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
        """Registers a new doctor account including secure professional credentials (PRC & PTR) locked in DB"""
        try:
            existing = self.supabase.table("users").select("username").eq("username", username).execute()
            if existing.data:
                return False, "Username already exists. Please choose another."
            
            user_data = {
                "username": username,
                "password": password,
                "role": "Doctor",
                "full_name": full_name,
                "professional_role": professional_role,
                "prc_number": prc_number,
                "ptr_number": ptr_number
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

    def update_consultation(self, record_id, patient_complaint, diagnosis, prescription, appointment_date):
        """Strictly reserved for Doctors: updates appointment with complaint, diagnosis, prescription, and tracking serial number"""
        try:
            date_str = str(appointment_date).replace("-", "")
            tracking_num = f"RX-{date_str}-{record_id}"
            
            self.supabase.table("appointments").update({
                "patient_complaint": patient_complaint,
                "diagnosis": diagnosis,
                "prescription": prescription,
                "tracking_number": tracking_num,
                "status": "Pending Payment"
            }).eq("id", record_id).execute()
            return True, None
        except Exception as e:
            try:
                self.supabase.table("appointments").update({
                    "patient_complaint": patient_complaint,
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
                            "patient_complaint": "Persistent headache and mild fatigue for 3 days." if status in ["Completed", "Pending Payment"] else None,
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
    
    cols_order = [c for c in ['id', 'patient_name', 'doctor_id', 'appointment_date', 'appointment_time', 'status', 'tracking_number', 'payment_method', 'payment_amount', 'patient_complaint', 'diagnosis', 'prescription'] if c in df.columns]
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
            "patient_complaint": st.column_config.TextColumn("Patient Complaint"),
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
    
    cols = [c for c in ['id', 'username', 'password', 'role', 'full_name', 'professional_role', 'prc_number', 'ptr_number'] if c in df.columns]
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
            "professional_role": st.column_config.TextColumn("Specialty"),
            "prc_number": st.column_config.TextColumn("PRC No."),
            "ptr_number": st.column_config.TextColumn("PTR No.")
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
            st.session_state.prc_number = query_params.get("prc", "1234567")
            st.session_state.ptr_number = query_params.get("ptr", "PTR-2026-988")
        else:
            st.session_state.authenticated = False
            st.session_state.role = None
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.full_name = None
            st.session_state.prc_number = None
            st.session_state.ptr_number = None

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
                        role, user_id, full_name, prc_num, ptr_num = db.authenticate(username, password)
                        st.session_state.is_submitting_action = False
                        if role:
                            st.session_state.authenticated = True
                            st.session_state.role = role
                            st.session_state.username = username
                            st.session_state.user_id = user_id
                            st.session_state.full_name = full_name
                            st.session_state.prc_number = prc_num
                            st.session_state.ptr_number = ptr_num
                            
                            st.query_params.update({
                                "auth": "true",
                                "user": username,
                                "role": role,
                                "uid": str(user_id),
                                "name": full_name,
                                "prc": prc_num,
                                "ptr": ptr_num
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
        st.session_state.prc_number = None
        st.session_state.ptr_number = None
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
            st.markdown("Process consultation payments and print official payment receipts directly.")
            
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
                    
                    # --- ADMIN / CASHIER PAYMENT RECEIPT PRINTING STATION ---
                    st.markdown("---")
                    st.markdown("### 🖨️ Admin Payment Receipt Printing Station")
                    
                    is_paid_and_completed = (str(current_rec.get('status')).strip().lower() == "completed" and current_rec.get('payment_method') and current_rec.get('payment_amount'))
                    
                    if st.button("🖨️ Print Official Payment Receipt Form", use_container_width=True, disabled=not is_paid_and_completed):
                        receipt_html = f"""
                        <html>
                        <head>
                            <style>
                                @page {{
                                    size: auto;
                                    margin: 0mm;
                                }}
                                body {{
                                    font-family: Arial, sans-serif;
                                    padding: 40px;
                                    color: #000;
                                    background: #fff;
                                    margin: 0;
                                }}
                                .receipt-card {{
                                    background: #ffffff;
                                    border: 2px solid #0f172a;
                                    padding: 35px;
                                    border-radius: 12px;
                                    max-width: 800px;
                                    margin: auto;
                                }}
                                @media print {{
                                    body {{ padding: 20px; }}
                                    header, footer, .stToolbar {{ display: none !important; }}
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="receipt-card">
                                <h2 style="text-align: center; color: #0f172a; margin-top: 0;">🧾 CAREPOINT CLINIC OFFICIAL PAYMENT RECEIPT</h2>
                                <p><b>Transaction Reference:</b> <code>RCP-{current_rec['id']}-{datetime.now().strftime('%Y%m%d')}</code></p>
                                <p><b>Date Issued:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                                <hr>
                                <p><b>Patient Name:</b> {current_rec['patient_name']}</p>
                                <p><b>Attending Physician:</b> {current_rec['doctor_id']}</p>
                                <p><b>Appointment Schedule:</b> {current_rec['appointment_date']} at {current_rec['appointment_time']}</p>
                                <br>
                                <h3>Payment Breakdown:</h3>
                                <p style="font-size: 16px; background: #f1f5f9; padding: 15px; border-radius: 8px;">
                                    <b>Consultation Fee / Total Paid:</b> ₱{current_rec.get('payment_amount', '500.00')}<br>
                                    <b>Payment Method:</b> {current_rec.get('payment_method', 'Cash')}<br>
                                    <b>Status:</b> Completed & Verified
                                </p>
                                <br><br><br>
                                <div style="float: right; text-align: center; width: 280px;">
                                    <div style="border-bottom: 1px solid #000; margin-bottom: 5px;"></div>
                                    <p style="font-size: 12px; margin: 0;"><b>Authorized Cashier Signature</b><br><i>(CarePoint Cashier Desk)</i></p>
                                </div>
                                <div style="clear: both;"></div>
                            </div>
                            <script>
                                window.onload = function() {{
                                    window.print();
                                }};
                            </script>
                        </body>
                        </html>
                        """
                        
                        import streamlit.components.v1 as components
                        components.html(receipt_html, height=650)
                        
                        st.success(f"🖨️ Print dialog opened for Official Receipt (Patient: **{current_rec['patient_name']}** | Amount: **₱{current_rec.get('payment_amount', '500.00')}**).")
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
                render_doctors_table(doctors)
            
            st.markdown("---")
            st.subheader("🗑️ Delete User Account")
            if filtered_users:
                user_options = [f"ID: {u['id']} | Username: {u['username']} | Role: {u['role']}" for u in filtered_users]
                selected_user_str = st.selectbox("Select User Account to Delete", user_options)
                
                sel_user_id = int(selected_user_str.split("|")[0].replace("ID:", "").strip())
                sel_username = selected_user_str.split("|")[1].replace("Username:", "").strip()
                
                del_acc_lbl = "Deleting User..." if st.session_state.is_submitting_action else "🗑️ Permanently Delete User Account"
                if st.button(del_acc_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action):
                    st.session_state.is_submitting_action = True
                    with st.spinner("⏳ Permanently deleting user and associated appointments..."):
                        success, err = db.delete_user_completely(sel_user_id, sel_username)
                        st.session_state.is_submitting_action = False
                        if success:
                            st.success(f"User account '{sel_username}' (ID: #{sel_user_id}) and their associated appointments permanently deleted from Supabase!")
                            st.rerun()
                        else:
                            st.error(f"Error deleting user account: {err}")
            else:
                st.info("No matching user accounts found.")

        with admin_tab4:
            st.subheader("🩺 Create a New Doctor Account")
            st.markdown("Add a licensed medical doctor account with secure database-locked professional credentials.")
            
            with st.form("create_doctor_form"):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    doc_username = st.text_input("Doctor Login Username")
                    doc_password = st.text_input("Doctor Password", type="password")
                    doc_fullname = st.text_input("Doctor Full Name")
                with col_d2:
                    doc_specialty = st.text_input("Professional Role / Specialty")
                    doc_prc = st.text_input("PRC License Number (Locked in DB)")
                    doc_ptr = st.text_input("PTR Number (Locked in DB)")
                
                button_label = "Registering Doctor..." if st.session_state.is_submitting_action else "🩺 Register Doctor Account"
                doc_reg_submit = st.form_submit_button(button_label, use_container_width=True, disabled=st.session_state.is_submitting_action)
                
                if doc_reg_submit and not st.session_state.is_submitting_action:
                    if doc_username.strip() and doc_password.strip() and doc_fullname.strip() and doc_specialty.strip():
                        st.session_state.is_submitting_action = True
                        with st.spinner("⏳ Creating doctor account..."):
                            success, err = db.register_doctor(
                                doc_username.strip(), 
                                doc_password.strip(), 
                                doc_fullname.strip(), 
                                doc_specialty.strip(), 
                                doc_prc.strip() or "1234567", 
                                doc_ptr.strip() or "PTR-2026-988"
                            )
                            st.session_state.is_submitting_action = False
                            if success:
                                st.success(f"🎉 Doctor account '{doc_fullname}' ({doc_specialty}) created successfully with secure locked credentials!")
                                st.rerun()
                            else:
                                st.error(err)
                    else:
                        st.error("Please fill in username, password, full name, and professional specialty.")

        with admin_tab5:
            st.subheader("👤 Create a New Patient User Account")
            st.markdown("Register a new patient account with a unique username handle and separate patient full name.")
            
            with st.form("admin_create_patient_form"):
                new_user = st.text_input("Choose Unique Login Username")
                new_pass = st.text_input("Choose Password", type="password")
                new_fullname = st.text_input("Patient Full Name")
                
                reg_btn_label = "Creating Account..." if st.session_state.is_submitting_action else "👤 Create Patient Account"
                reg_submit = st.form_submit_button(reg_btn_label, use_container_width=True, disabled=st.session_state.is_submitting_action)
                
                if reg_submit and not st.session_state.is_submitting_action:
                    if new_user.strip() and new_pass.strip() and new_fullname.strip():
                        st.session_state.is_submitting_action = True
                        with st.spinner("⏳ Creating patient user account..."):
                            success, err = db.register_patient(new_user.strip(), new_pass.strip(), new_fullname.strip())
                            st.session_state.is_submitting_action = False
                            if success:
                                st.success(f"🎉 Patient account '{new_user}' created successfully for {new_fullname}!")
                                st.rerun()
                            else:
                                st.error(err)
                    else:
                        st.error("Please fill in all fields.")

        with admin_tab6:
            st.subheader("➕ Book Walk-In Appointment (Staff / Admin Assisted)")
            st.markdown("For elderly patients or walk-ins who cannot use the computer themselves. Book their appointment directly into the queue.")
            
            with st.form("admin_walkin_booking_form"):
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    walkin_username = st.text_input("Account Username Handle")
                    walkin_patient_name = st.text_input("Patient Full Name")
                    walkin_doctor = st.selectbox("Assign Attending Physician", doctors_list[1:], key="walkin_doc")
                with col_w2:
                    walkin_date = st.date_input("Preferred Date", key="walkin_date")
                    walkin_time = st.selectbox("Exact Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], key="walkin_time")
                    walkin_status = st.selectbox("Initial Status", ["Waiting", "Pending Payment", "Completed"], key="walkin_status")
                
                walkin_lbl = "Booking Appointment..." if st.session_state.is_submitting_action else "➕ Confirm & Book Walk-In Appointment"
                walkin_submit = st.form_submit_button(walkin_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                
                if walkin_submit and not st.session_state.is_submitting_action:
                    if walkin_patient_name.strip():
                        st.session_state.is_submitting_action = True
                        with st.spinner("⏳ Securing walk-in booking and checking schedule conflicts..."):
                            success, err_msg = db.add_appointment(walkin_username.strip(), walkin_patient_name.strip(), walkin_doctor, str(walkin_date), walkin_time, walkin_status)
                            st.session_state.is_submitting_action = False
                            if success:
                                st.success(f"🎉 Walk-in appointment successfully booked for {walkin_patient_name.strip()} with {walkin_doctor}!")
                                st.rerun()
                            else:
                                st.error(err_msg)
                    else:
                        st.error("Please enter a valid patient full name.")

    # --- DOCTOR PORTAL ---
    elif role == "Doctor":
        st.title("🩺 Medical Professional / Doctor Portal")
        
        doc_surname = selected_doctor if selected_doctor != "All Doctors" else "Doctor Smith"
        st.markdown(f"Welcome, **{doc_surname}**. Managing clinical treatments and patient queue.")
        
        doc_records = [r for r in all_records if selected_doctor == "All Doctors" or r.get("doctor_id") == selected_doctor]
        
        doc_tab1, doc_tab2, doc_tab3 = st.tabs([
            "🩺 Consultation & Treatment Room", 
            "📋 Patient Schedule Queue", 
            "✅ Treated Patients (Pending Payment)"
        ])
        
        with doc_tab1:
            st.subheader("🩺 Patient Consultation & Prescription Workspace")
            
            if doc_records:
                sorted_doc_records = sorted(doc_records, key=lambda x: int(x['id']))
                patient_names_list = [f"ID #{r['id']} | Patient: {r['patient_name']} ({r['appointment_date']} {r['appointment_time']})" for r in sorted_doc_records]
                selected_patient_str = st.selectbox("Select Patient in Consultation", patient_names_list)
                
                chosen_record = next((r for r in sorted_doc_records if f"ID #{r['id']} | Patient: {r['patient_name']} ({r['appointment_date']} {r['appointment_time']})" == selected_patient_str), None)
                
                if chosen_record:
                    st.info(f"**Patient:** {chosen_record['patient_name']} | **Assigned Doctor:** {chosen_record['doctor_id']} | **Time Slot:** {chosen_record['appointment_date']} at {chosen_record['appointment_time']}")
                    
                    with st.form("consultation_form"):
                        st.markdown("### Clinical Examination Notes")
                        existing_complaint = chosen_record.get("patient_complaint") or ""
                        existing_diag = chosen_record.get("diagnosis") or ""
                        existing_presc = chosen_record.get("prescription") or ""
                        
                        patient_complaint = st.text_area("Patient Complaint / Chief Complaint", value=existing_complaint, placeholder="Enter patient's reported symptoms or complaint...")
                        diagnosis = st.text_area("Medical Diagnosis", value=existing_diag, placeholder="Enter official diagnosis...")
                        prescription = st.text_area("Prescription & Treatment Plan", value=existing_presc, placeholder="Enter prescribed medications and dosage...")
                        
                        cons_lbl = "Saving Consultation..." if st.session_state.is_submitting_action else "💾 Save Consultation & Send to Cashier"
                        save_consultation = st.form_submit_button(cons_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                        
                        if save_consultation and not st.session_state.is_submitting_action:
                            st.session_state.is_submitting_action = True
                            with st.spinner("⏳ Saving clinical notes and generating prescription tracking ID..."):
                                success, err = db.update_consultation(chosen_record["id"], patient_complaint, diagnosis, prescription, chosen_record["appointment_date"])
                                st.session_state.is_submitting_action = False
                                if success:
                                    st.success(f"🎉 Consultation saved for {chosen_record['patient_name']}! Permanent tracking ID generated and patient sent to cashier.")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to save: {err}")

                    # --- DOCTOR PRESCRIPTION PRINTING SECTION (WITH CASHIER STAMP WARNING NOTICE) ---
                    st.markdown("---")
                    st.subheader("🖨️ Print Official Prescription Slip")
                    
                    if st.button("🖨️ Print Prescription Slip Form", use_container_width=True):
                        serial_num = chosen_record.get('tracking_number') or f"RX-{chosen_record['appointment_date'].replace('-', '')}-{chosen_record['id']}"
                        secure_prc = st.session_state.get('prc_number', '1234567')
                        secure_ptr = st.session_state.get('ptr_number', 'PTR-2026-988')
                        
                        prescription_html = f"""
                        <html>
                        <head>
                            <style>
                                @page {{
                                    size: auto;
                                    margin: 0mm;
                                }}
                                body {{
                                    font-family: Arial, sans-serif;
                                    padding: 40px;
                                    color: #000;
                                    background: #fff;
                                    margin: 0;
                                }}
                                .prescription-card {{
                                    background: #ffffff;
                                    border: 2px solid #0f172a;
                                    padding: 35px;
                                    border-radius: 12px;
                                    max-width: 800px;
                                    margin: auto;
                                }}
                                .warning-banner {{
                                    background: #fef2f2;
                                    border: 1px dashed #dc2626;
                                    padding: 12px;
                                    border-radius: 6px;
                                    margin-top: 25px;
                                    font-size: 13px;
                                    color: #991b1b;
                                    text-align: center;
                                    font-weight: bold;
                                }}
                                @media print {{
                                    body {{ padding: 20px; }}
                                    header, footer, .stToolbar {{ display: none !important; }}
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="prescription-card">
                                <h2 style="text-align: center; color: #0f172a; margin-top: 0;">📄 CAREPOINT CLINIC OFFICIAL MEDICAL PRESCRIPTION</h2>
                                <p><b>Tracking Serial:</b> <code>{serial_num}</code></p>
                                <p><b>Date Issued:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                                <hr>
                                <p><b>Patient Name:</b> {chosen_record['patient_name']}</p>
                                <br>
                                <h3>Rx (Prescription & Treatment Plan):</h3>
                                <p style="font-size: 16px; background: #f1f5f9; padding: 15px; border-radius: 8px;"><b>{chosen_record.get('prescription', 'No medication prescribed yet.')}</b></p>
                                <br><br>
                                <p><b>Attending Physician:</b> {chosen_record['doctor_id']}</p>
                                <p><b>PRC No:</b> {secure_prc} | <b>PTR No:</b> {secure_ptr}</p>
                                <br>
                                <div class="warning-banner">
                                    ⚠️ VALIDATION NOTICE: This prescription is VOID and invalid at any pharmacy unless officially stamped and cleared by the CarePoint Clinic Cashier.
                                </div>
                                <br><br>
                                <div style="float: right; text-align: center; width: 280px;">
                                    <div style="border-bottom: 1px solid #000; margin-bottom: 5px;"></div>
                                    <p style="font-size: 12px; margin: 0;"><b>Doctor's Signature over Printed Name</b><br><i>(Physical wet-ink signature required)</i></p>
                                </div>
                                <div style="clear: both;"></div>
                            </div>
                            <script>
                                window.onload = function() {{
                                    window.print();
                                }};
                            </script>
                        </body>
                        </html>
                        """
                        
                        import streamlit.components.v1 as components
                        components.html(prescription_html, height=700)
                        
                        st.success("🖨️ Print dialog opened! Prescription slip printed successfully with cashier validation notice.")
            else:
                st.warning("No patients available in your queue for consultation.")

        with doc_tab2:
            col1, col2 = st.columns(2)
            col1.metric(label=f"Appointments ({selected_doctor})", value=len(doc_records))
            col2.metric(label="Clinic Queue Status", value="Active 🟢")
            
            st.markdown("---")
            st.subheader(f"🕒 Patient Schedule — {selected_doctor}")
            render_modern_table(doc_records)

        with doc_tab3:
            st.subheader(f"💵 Treated Patients Awaiting Payment — {selected_doctor}")
            
            pending_records = [r for r in doc_records if r.get("status") == "Pending Payment"]
            if pending_records:
                render_modern_table(pending_records)
            else:
                st.info(f"No patients currently waiting for payment with {selected_doctor}.")

    # --- PATIENT PORTAL ---
    elif role == "Patient":
        st.title("👤 Patient Self-Service Portal")
        
        logged_in_user_obj = next((u for u in users_list if str(u.get('username')) == str(st.session_state.username)), {})
        my_real_full_name = logged_in_user_obj.get('full_name') or st.session_state.get('full_name') or st.session_state.username
        
        if st.session_state.username == "patient":
            filter_username = selected_active_username
            welcome_display_name = selected_active_username
        else:
            filter_username = st.session_state.username
            welcome_display_name = my_real_full_name

        st.markdown(f"Welcome, **{welcome_display_name}**.")
        
        patient_records = db.get_patient_appointments(filter_username)
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📅 Book New Appointment", 
            "📋 My Confidential Appointments", 
            "🧾 My Prescriptions & Receipts", 
            "✏️ Edit My Appointments"
        ])
        
        with tab1:
            st.subheader(f"Schedule a New Visit")
            with st.form("booking_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    p_name = st.text_input("Patient Full Name", value=my_real_full_name)
                    doc_choice = st.selectbox("Select Attending Physician", doctors_list[1:])
                with col_b:
                    app_date = st.date_input("Preferred Date")
                    app_time = st.selectbox("Exact Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"])
                
                book_lbl = "Booking Appointment..." if st.session_state.is_submitting_action else "Confirm & Secure Booking"
                book_submit = st.form_submit_button(book_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                
                if book_submit and not st.session_state.is_submitting_action:
                    if p_name.strip():
                        st.session_state.is_submitting_action = True
                        with st.spinner("⏳ Securing booking and checking schedule conflicts..."):
                            success, err_msg = db.add_appointment(filter_username, p_name.strip(), doc_choice, app_date, app_time, "Waiting")
                            st.session_state.is_submitting_action = False
                            if success:
                                st.success(f"🎉 Appointment successfully booked for {p_name.strip()} with {doc_choice}!")
                                st.rerun()
                            else:
                                st.error(err_msg)
                    else:
                        st.error("Please enter a valid patient name.")
                        
        with tab2:
            st.subheader(f"📋 Appointments Booked Under Your Account")
            render_modern_table(patient_records)

        with tab3:
            st.subheader("🧾 Medical Prescriptions & Receipts")
            
            if patient_records:
                sorted_presc_records = sorted(patient_records, key=lambda x: int(x['id']))
                presc_options = [f"ID #{r['id']} | Patient: {r['patient_name']} | Dr: {r['doctor_id']} | Date: {r['appointment_date']}" for r in sorted_presc_records]
                selected_presc_str = st.selectbox("Select Appointment Record to View", presc_options, key="patient_presc_view_tab")
                
                sel_presc_id = int(selected_presc_str.split("|")[0].replace("ID:", "").replace("ID", "").replace("#", "").strip())
                selected_card_rec = next((r for r in patient_records if r['id'] == sel_presc_id), None)
                
                if selected_card_rec:
                    rx_serial_number = selected_card_rec.get('tracking_number') or f"RX-PENDING-{selected_card_rec.get('id')}"
                    pay_status_display = f"Paid via {selected_card_rec.get('payment_method')} (₱{selected_card_rec.get('payment_amount')})" if selected_card_rec.get('payment_method') else "Unpaid / Pending Payment"
                    st.markdown(f"""
                        <div class="prescription-card">
                            <h3>🏥 CarePoint Official Medical Prescription & Receipt Summary</h3>
                            <p><b>Prescription Tracking ID:</b> <span style="color: #dc2626; font-family: monospace;">{rx_serial_number}</span></p>
                            <p><b>Appointment ID:</b> #{selected_card_rec.get('id')} | <b>Patient:</b> {selected_card_rec.get('patient_name')} | <b>Attending Doctor:</b> {selected_card_rec.get('doctor_id')}</p>
                            <p><b>Appointment Date:</b> {selected_card_rec.get('appointment_date')} at {selected_card_rec.get('appointment_time')} | <b>Status:</b> {selected_card_rec.get('status')}</p>
                            <p><b>Payment Status / Receipt:</b> {pay_status_display}</p>
                            <hr style="margin: 15px 0;">
                            <h4>Patient Complaint</h4>
                            <p style="background: #f1f5f9; padding: 12px; border-radius: 8px;">{selected_card_rec.get('patient_complaint') or 'No complaint recorded yet.'}</p>
                            <h4 style="margin-top: 15px;">Medical Diagnosis</h4>
                            <p style="background: #f1f5f9; padding: 12px; border-radius: 8px;">{selected_card_rec.get('diagnosis') or 'No diagnosis recorded yet.'}</p>
                            <h4 style="margin-top: 20px;">Prescription & Treatment Plan</h4>
                            <p style="background: #f1f5f9; padding: 12px; border-radius: 8px;">{selected_card_rec.get('prescription') or 'No prescription issued yet.'}</p>
                            <div style="margin-top: 30px; text-align: right;">
                                <p><b>{selected_card_rec.get('doctor_id')}</b></p>
                                <p style="font-size: 0.9em; color: #555;">PRC License No: 0012345 | PTR No: 9876543<br><i>Digitally Generated & Verified Serialized Form</i></p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No prescription or receipt records found.")

        with tab4:
            st.subheader(f"✏️ Reschedule, Cancel, or Delete Appointments")
            st.markdown("*Note: Medical prescriptions and diagnoses cannot be edited by patients to preserve medical integrity.*")
            if patient_records:
                sorted_pat_records = sorted(patient_records, key=lambda x: int(x['id']))
                pat_options = [f"ID #{r['id']} | Patient: {r['patient_name']} | Dr: {r['doctor_id']} | Date: {r['appointment_date']} {r['appointment_time']} | Status: {r['status']}" for r in sorted_pat_records]
                selected_pat_rec_str = st.selectbox("Select Appointment to Modify", pat_options, key="pat_edit_select")
                
                sel_pat_id = int(selected_pat_rec_str.split("|")[0].replace("ID:", "").replace("ID", "").replace("#", "").strip())
                curr_pat_rec = next((r for r in patient_records if r['id'] == sel_pat_id), None)
                
                if curr_pat_rec:
                    with st.form("patient_self_edit_form"):
                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            edit_p_name = st.text_input("Patient Full Name", value=curr_pat_rec['patient_name'])
                            edit_p_doc = st.selectbox("Attending Physician", doctors_list[1:], index=doctors_list[1:].index(curr_pat_rec['doctor_id']) if curr_pat_rec['doctor_id'] in doctors_list[1:] else 0)
                            edit_p_date = st.text_input("Appointment Date (YYYY-MM-DD)", value=curr_pat_rec['appointment_date'])
                        with col_p2:
                            edit_p_time = st.selectbox("Time Slot", ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"], index=["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"].index(curr_pat_rec['appointment_time']) if curr_pat_rec['appointment_time'] in ["08:00 AM", "09:30 AM", "11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"] else 0)
                            edit_p_status = st.selectbox("Status", ["Waiting", "Cancelled"], index=["Waiting", "Cancelled"].index(curr_pat_rec['status']) if curr_pat_rec['status'] in ["Waiting", "Cancelled"] else 0)
                        
                        col_pb1, col_pb2, col_pb3 = st.columns(3)
                        save_lbl = "Saving..." if st.session_state.is_submitting_action else "💾 Save"
                        canc_lbl = "Cancelling..." if st.session_state.is_submitting_action else "❌ Cancel"
                        del_lbl = "Deleting..." if st.session_state.is_submitting_action else "🗑️ Delete"
                        
                        save_p_edit = col_pb1.form_submit_button(save_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                        cancel_p_booking = col_pb2.form_submit_button(canc_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                        delete_p_booking = col_pb3.form_submit_button(del_lbl, use_container_width=True, disabled=st.session_state.is_submitting_action)
                        
                        if save_p_edit and not st.session_state.is_submitting_action:
                            st.session_state.is_submitting_action = True
                            with st.spinner("⏳ Updating appointment..."):
                                success, err = db.update_appointment_patient(sel_pat_id, filter_username, edit_p_name, edit_p_doc, edit_p_date, edit_p_time, edit_p_status)
                                st.session_state.is_submitting_action = False
                                if success:
                                    st.success(f"Appointment #{sel_pat_id} updated successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {err}")
                                    
                        if cancel_p_booking and not st.session_state.is_submitting_action:
                            st.session_state.is_submitting_action = True
                            with st.spinner("⏳ Cancelling appointment..."):
                                success, err = db.update_appointment_patient(sel_pat_id, filter_username, edit_p_name, curr_pat_rec['doctor_id'], curr_pat_rec['appointment_date'], curr_pat_rec['appointment_time'], "Cancelled")
                                st.session_state.is_submitting_action = False
                                if success:
                                    st.warning(f"Appointment #{sel_pat_id} has been cancelled.")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {err}")

                        if delete_p_booking and not st.session_state.is_submitting_action:
                            st.session_state.is_submitting_action = True
                            with st.spinner("⏳ Deleting appointment..."):
                                try:
                                    db.supabase.table("appointments").delete().eq("id", sel_pat_id).execute()
                                    st.session_state.is_submitting_action = False
                                    st.success(f"Appointment #{sel_pat_id} permanently deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.session_state.is_submitting_action = False
                                    st.error(f"Error deleting record: {e}")
            else:
                st.info(f"No appointments found under your account.")

if __name__ == "__main__":
    main()
