# login_page.py

import streamlit as st

# You can define your authentication method here
# This is a simple example using hardcoded users (for illustration purposes only)

def check_user(username, password):
    # Example user database
    users = {"Adam": "Miertnemtudok94", "user": "secret"}
    return username in users and users[username] == password

def login_page():
    st.title('Login Page')

    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button('Login'):
        if check_user(username, password):
            st.session_state['logged_in'] = True
            st.rerun()
            st.success(f"Logged in as {username}")
            # Debugging line
            st.write("Login successful, session state 'logged_in' set to True.")
            # Here, you might also use st.experimental_rerun() to refresh the page
        else:
            st.error("Incorrect username or password")
