import streamlit as st

# ฟังก์ชันที่ใช้ในการแสดงหน้า Home
def home_page():
    st.title("Welcome to Streamlit App")

    # ถ้ามีการกดปุ่ม "New Project"
    if st.button("New Project"):
        # เปลี่ยนสถานะให้แสดงหน้าใหม่
        st.session_state.page = "project"

        # รีเฟรชหน้า
        st.experimental_rerun()

# ฟังก์ชันที่ใช้ในการแสดงหน้า Project
def project_page():
    st.title("Create a New Project")
    
    # ฟอร์มกรอกข้อมูล
    with st.form(key="login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            st.write(f"Email: {email}")
            st.write(f"Password: {password}")

# ตรวจสอบสถานะของ session_state และแสดงหน้า
if 'page' not in st.session_state:
    st.session_state.page = "home"

# แสดงหน้าตามสถานะ
if st.session_state.page == "home":
    home_page()
elif st.session_state.page == "project":
    project_page()
