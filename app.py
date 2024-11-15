import streamlit as st

# Sample data for the mock exam (for demonstration)
questions = {
    "Math": [
        {"question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "answer": "4"},
        {"question": "What is 5 * 5?", "options": ["20", "25", "30", "35"], "answer": "25"},
    ],
    "Geography": [
        {"question": "What is the capital of France?", "options": ["Berlin", "Madrid", "Paris", "Rome"], "answer": "Paris"},
        {"question": "Which is the largest ocean?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "answer": "Pacific"},
    ],
}

# Login/Signup page
def login_signup():
    st.title("NAT PREP APP")

    menu = st.sidebar.selectbox("Choose Action", ["Login", "Signup"])

    if menu == "Signup":
        st.subheader("Create a New Account")
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Sign Up"):
            if password == confirm_password:
                st.session_state["username"] = username  # Simulate user creation
                st.session_state["page"] = "main_dashboard"  # Direct to main dashboard
                st.success("Account created successfully! Please log in.")
            else:
                st.error("Passwords do not match.")

    elif menu == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username:
                st.session_state["username"] = username  # Simulate login
                st.session_state["page"] = "main_dashboard"  # Direct to main dashboard
                st.rerun()  # Use rerun to trigger page transition
            else:
                st.error("Please enter a valid username.")

# Main Dashboard
def main_dashboard():
    st.title("Main Dashboard")

    if "username" not in st.session_state:
        st.error("Please log in to access the dashboard.")
        st.stop()

    st.write(f"Welcome, {st.session_state['username']}!")

    # Sidebar with logout button
    with st.sidebar:
        if st.button("Logout"):
            del st.session_state["username"]
            del st.session_state["page"]
            st.success("You have logged out successfully!")
            st.rerun()  # Rerun after logout

    # Dashboard buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Take Mock Exam"):
            st.session_state["page"] = "select_category"
            st.rerun()  # Rerun to go to the select category page
    with col2:
        if st.button("User Progress"):
            st.session_state["page"] = "user_progress"
            st.rerun()  # Rerun to go to the user progress page

# Select Mock Exam Category
def select_category():
    st.title("Select Exam Category")
    
    if "username" not in st.session_state:
        st.error("Please log in to take the mock exam.")
        st.stop()

    category = st.selectbox("Choose a category", list(questions.keys()))

    if st.button("Start Exam"):
        st.session_state["page"] = "start_exam"
        st.session_state["category"] = category
        st.rerun()  # Rerun to start the mock exam

    if st.button("Go Back"):
        st.session_state["page"] = "main_dashboard"
        st.rerun()  # Rerun to go back to the main dashboard

# Start Mock Exam
def start_exam():
    category = st.session_state["category"]
    st.title(f"{category} Mock Exam")
    
    if "username" not in st.session_state:
        st.error("Please log in to take the mock exam.")
        st.stop()

    # Set up the questions
    question_number = st.session_state.get("question_number", 0)
    total_questions = len(questions[category])

    if question_number < total_questions:
        question = questions[category][question_number]
        st.write(question["question"])
        selected_option = st.radio("Choose an answer:", question["options"])

        if st.button("Next"):
            if selected_option == question["answer"]:
                st.session_state["correct_answers"] = st.session_state.get("correct_answers", 0) + 1
            st.session_state["question_number"] = question_number + 1
            st.rerun()  # Use rerun instead of experimental_rerun()
    else:
        st.write("You have completed the exam!")
        score = st.session_state.get("correct_answers", 0)
        st.write(f"Your score: {score} / {total_questions}")

        if st.button("Go Back to Dashboard"):
            del st.session_state["question_number"]
            del st.session_state["correct_answers"]
            st.session_state["page"] = "main_dashboard"
            st.rerun()  # Rerun to go back to the main dashboard

# Show User Progress
def show_progress():
    st.title("User Progress")

    if "username" not in st.session_state:
        st.error("Please log in to view your progress.")
        st.stop()

    # Simulate user progress (number of questions attempted and correct answers)
    attempted = st.session_state.get("question_number", 0)
    correct = st.session_state.get("correct_answers", 0)
    total_questions = sum(len(q) for q in questions.values())

    st.subheader(f"Progress of {st.session_state['username']}")
    st.write(f"Questions Attempted: {attempted}/{total_questions}")
    st.write(f"Correct Answers: {correct}")
    
    # Display progress in a more visual way
    st.progress(correct / total_questions)

    if st.button("Go Back"):
        st.session_state["page"] = "main_dashboard"
        st.rerun()  # Rerun to go back to the main dashboard

# Main App Logic
def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "login_signup"
    
    if st.session_state["page"] == "login_signup":
        login_signup()
    elif st.session_state["page"] == "main_dashboard":
        main_dashboard()
    elif st.session_state["page"] == "select_category":
        select_category()
    elif st.session_state["page"] == "start_exam":
        start_exam()
    elif st.session_state["page"] == "user_progress":
        show_progress()

if __name__ == "__main__":
    main()
