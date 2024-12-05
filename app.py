import streamlit as st
from streamlit_option_menu import option_menu
from utilities import UserDatabase
import pandas as pd

# Initialize the UserDatabase instance
db = UserDatabase()

exam_questions_storage = {}

# Login/Signup Flow with Graceful UI
def login_signup():
    if "username" in st.session_state:
        return
    def login_state():
        st.subheader("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if db.authenticate_user(username, password):
                st.session_state["username"] = username
                st.success(f"Welcome back, {username}!")
                st.session_state["page"] = "main_dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password.")

    def signup_state():
        st.subheader("Signup")
        username = st.text_input("Choose a Username", key="signup_username")
        email = st.text_input("Email Address", key="signup_email")
        password = st.text_input("Create Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Signup"):
            # Check if the username or email already exists in the database
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Users WHERE username = ? OR email = ?", (username, email))
            user = cursor.fetchone()
            conn.close()

            if user:
                if user[1] == username:
                    st.warning("Username already exists. Please choose a different one.")
                elif user[2] == email:
                    st.warning("Email address already in use. Please choose a different one.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    db.add_user(username, password, email, "student")  # Default user_type as "student"
                    st.session_state["username"] = username
                    st.success("Signup successful! You can now login.")
                    st.session_state["page"] = "main_dashboard"
                    st.rerun()  # Rerun after successful signup
                except ValueError as e:
                    st.error(f"There was an issue creating the account: {e}")

    if "login" not in st.session_state:
        st.session_state['login'] = True

    if st.session_state['login']:
        login_state()
        if st.button("Don't have an account? Signup here"):
            st.session_state['login'] = False
    else:
        signup_state()
        if st.button("Already have an account? Login here"):
            st.session_state['login'] = True

# Main Dashboard
def main_dashboard():
    if "username" not in st.session_state:
        st.error("Please log in to access the dashboard.")
        st.stop()

    st.title(f"Welcome, {st.session_state['username']}!")
    st.markdown("""
    Here you can start your mock exams, track your progress, and view useful insights to help you improve.
    Choose one of the options from the menu to begin.
    """)

def admin_dashboard():

    if "username" not in st.session_state:
        st.error("Please log in to access the dashboard.")
        st.stop()

    if not db.is_admin(st.session_state["username"]):
        st.error("Access Denied. Admin privileges are required.")
        st.stop()

    st.subheader("Manage Users")
    users = db.get_all_users()

    columns = ["User ID", "Username", "Email", "User Type", "Is Admin", 
               "Total Questions Attempted", "Total Correct Answers", "Total Score"]
    users_df = pd.DataFrame(users, columns=columns)

    # Ensure "Is Admin" is a Boolean column
    users_df["Is Admin"] = users_df["Is Admin"].map(lambda x: x == "Yes")

    # Display the table
    st.dataframe(users_df)

    # Dropdown for appointing new admin
    st.subheader("Appoint New Admin")
    non_admin_users = users_df[~users_df["Is Admin"]]  # Filter non-admins
    user_options = non_admin_users["Username"].tolist()

    user_to_promote = st.selectbox("Select a user to appoint as admin:", user_options)

    if user_to_promote:
        if st.button(f"Appoint {user_to_promote} as Admin"):
            try:
                db.appoint_admin(user_to_promote)
                st.success(f"{user_to_promote} has been promoted to admin.")
                st.rerun()  # Force a re-run to refresh the data
            except ValueError as e:
                st.error(e)
        elif st.button(f"Remove {user_to_promote} from Admin"):
            try:
                db.remove_admin(user_to_promote)
                st.success(f"{user_to_promote} hs been removed from admin.")
                st.rerun()  # Force a re-run to refresh the data
            except ValueError as e:
                st.error(e)
        

def exams():
    if "username" not in st.session_state:
        st.error("Please log in to take the mock exam.")
        st.stop()

    if db.is_admin(st.session_state["username"]):
        st.error("Admins cannot take exams.")
        return

    st.subheader("Select an Exam Type")
    exam_types = ["VERBAL ABILITY", " ANALYTICAL REASONING", "QUANTITATIVE REASONING", "SUBJECT KNOWLEDGE"]

    for exam in exam_types:
        if st.button(exam):
            questions = db.get_random_questions(exam)
            if not questions:
                st.error(f"No questions available for {exam}. Please try another exam type.")
                return

            # Store exam data in session state
            st.session_state["exam_questions_storage"] = {exam: questions}
            st.session_state["current_question_index"] = 0
            st.session_state["user_answers"] = []
            st.session_state["exam_type"] = exam
            st.session_state["page"] = "take_exam"
            st.rerun()
            break

def save_exam_results_frontend():
    if "username" not in st.session_state:
        st.error("You need to log in to save exam results.")
        return

    user_id = db.get_user_id(st.session_state["username"])
    user_answers = st.session_state.get("user_answers", [])

    try:
        db.save_exam_results_backend(user_id, user_answers)
        total_correct = sum(1 for _, _, is_correct in user_answers if is_correct)
        total_attempted = len(user_answers)
        st.write(f"**Your Results:**")
        st.write(f"Total Questions: {total_attempted}")
        st.write(f"Correct Answers: {total_correct}")
        st.write(f"Your Score: {int((total_correct / total_attempted) * 100) if total_attempted > 0 else 0}%")
        st.button("Go Back to Exams", on_click=lambda: st.session_state.update({"page": "exams"}))
    except Exception as e:
        st.error(f"An error occurred while saving results: {e}")

def take_exam():
    exam_type = st.session_state.get("exam_type")
    questions = st.session_state.get("exam_questions_storage", {}).get(exam_type, [])

    if not questions:
        st.error("No questions found for the selected exam type.")
        st.button("Go Back to Exams", on_click=lambda: st.session_state.update({"page": "exams"}))
        return

    current_index = st.session_state.get("current_question_index", 0)
    if current_index < len(questions):
        question = questions[current_index]
        st.subheader(f"Question {current_index + 1}/{len(questions)}")
        st.write(question[1])  # Question text

        # Display options A, B, C, D with corresponding content
        options = ["A", "B", "C", "D"]
        option_content = question[2:6]  # Assuming the options are stored in this part of the question tuple
        
        selected_option = st.radio("Choose an option:", options, format_func=lambda option: f"{option}: {option_content[options.index(option)]}", key=f"question_{current_index}")

        if st.button("Submit Answer"):
            is_correct = selected_option == question[6]  # Assuming the correct answer is stored in the 7th position
            st.session_state["user_answers"].append((question[0], selected_option, is_correct))
            st.session_state["current_question_index"] += 1
            st.rerun()
    else:
        save_exam_results_frontend()


def progress():
    st.title("User Progress")

    if "username" not in st.session_state:
        st.error("Please log in to view your progress.")
        st.stop()

    user_id = db.get_user_id(st.session_state["username"])

    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, user_type FROM Users WHERE user_id = ?", (user_id,))
    user_details = cursor.fetchone()

    if user_details:
        username, email, user_type = user_details
    else:
        st.error("User details not found.")
        return

    # Create a column layout for displaying progress metrics
    col1, col2, col3 = st.columns(3)
    
    total_attempted, total_correct, total_score = db.get_user_progress(user_id)
    
    if total_attempted > 0:
        with col1:
            st.metric("Total Questions Attempted", total_attempted)
        with col2:
            st.metric("Total Correct Answers", total_correct)
        with col3:
            st.metric("Success Percentage", total_score,"%")
    else:
        st.warning("No progress data available.")
    
    # Display additional details in an expander
    with st.expander("More Details"):
        st.write("**Detailed Statistics**")
        st.write(f"**User ID:** {user_id}")
        st.write(f"**Username:** {username}")
        st.write(f"**Email:** {email}")
        st.write(f"**User Type:** {user_type}")
    
    # Back to dashboard button
    st.button("Back to Dashboard", on_click=lambda: st.session_state.update({"page": "main_dashboard"}))

def logout_confirmation():
    st.title("Are you sure you want to log out?")

    if st.button("Confirm"):
        st.session_state.clear()  # Clear the session
        st.session_state["page"] = "login_signup"  # Redirect to login page
        st.rerun()  # Rerun the app to show the login page

def display_sidebar():
    # Create a sidebar layout
    with st.sidebar:
        # Display the logo with a large size
        st.image("logo.png", width=200)  # Adjust width to make the logo larger or smaller as needed

        # Use custom HTML to centralize and increase the title size
        st.markdown("""
        <style>
        .sidebar-title {
            text-align: center;
            font-size: 36px;  /* Adjust the size of the title */
            font-weight: bold;
        }
        .sidebar-subheading {
            text-align: center;
            font-size: 18px;  /* Adjust the size of the subheading */
            font-weight: normal;
            color: #666;  /* Optional: Change the color for the subheading */
        }
        </style>
        <div class="sidebar-title">PREP FOX</div>
        <div class="sidebar-subheading">Your exam preparation companion</div>
        """, unsafe_allow_html=True)

# Main function to control the flow
def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "login_signup"

    # Navigation Menu for Authenticated Users
    if st.session_state["page"] != "login_signup":
        menu_options = ["Home", "Exams", "User Progress", "Logout"]
        menu_icons = ["house", "book", "file-bar-graph", "box-arrow-right"]

        # Add Admin Dashboard for admins
        if "username" in st.session_state and db.is_admin(st.session_state["username"]):
            menu_options.insert(1, "Admin Dashboard")
            menu_icons.insert(1, "gear")

        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
        ) 
        if selected == "Home":
            st.session_state["page"] = "main_dashboard"
            selected = ""
        elif selected == "Admin Dashboard":
            st.session_state["page"] = "admin_dashboard"
            selected = ""
        elif selected == "Exams" and st.session_state.page != "take_exam":
            st.session_state["page"] = "exams"
            selected = ""
        elif selected == "User Progress":
            st.session_state["page"] = "user_progress"
            selected = ""
        elif selected == "Logout":
            st.session_state["page"] = "logout_confirmation"  # Show logout confirmation page
            selected = ""

    # Control flow based on the current page
    if st.session_state["page"] == "login_signup":
        display_sidebar()
        login_signup()
    elif st.session_state["page"] == "main_dashboard":
        display_sidebar()
        main_dashboard()
    elif st.session_state["page"] == "exams":
        display_sidebar()
        exams()
    elif st.session_state["page"] == "take_exam": 
        display_sidebar()
        take_exam()
    elif st.session_state["page"] == "user_progress":
        display_sidebar()
        progress()
    elif st.session_state["page"] == "admin_dashboard":
        display_sidebar()
        admin_dashboard()
    elif st.session_state["page"] == "logout_confirmation":
        display_sidebar()
        logout_confirmation()

if __name__ == "__main__":
    main()
