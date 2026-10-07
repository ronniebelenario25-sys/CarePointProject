import streamlit as st

def render_aligned_appointment_list(appointments):
    st.subheader("Master Appointment Records")
    
    # Use explicit column ratios [Patient, Doctor/Date, Status, Actions]
    # This ensures columns match the natural length of your text fields
    for appt in appointments:
        with st.container(border=True): # Adds a clean card border
            cols = st.columns([2.5, 2.0, 1.5, 1.0], vertical_alignment="center")
            
            with cols[0]:
                st.markdown(f"**Patient:** {appt.get('patient_name')}")
                st.caption(f"ID: {appt.get('id')}")
                
            with cols[1]:
                st.text(f"Dr. {appt.get('doctor_name')}")
                st.caption(f"{appt.get('date')}")
                
            with cols[2]:
                status = appt.get('status', 'Pending')
                if status == 'Confirmed':
                    st.success(status)
                else:
                    st.warning(status)
                    
            with cols[3]:
                if st.button("Edit", key=f"edit_{appt.get('id')}"):
                    # Trigger edit modal/state
                    pass
