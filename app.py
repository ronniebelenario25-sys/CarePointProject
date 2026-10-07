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
        
        # Admin Action Tabs
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
