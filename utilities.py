import sqlite3
import bcrypt

class UserDatabase:
    def __init__(self, db_name="beta.db"):
        self.db_name = db_name

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def authenticate_user(self, username, password):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT password FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                hashed_password = user[0]
                if bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8")):
                    return True
            return False
        finally:
            conn.close()

    def add_user(self, username, password, email, user_type):
        conn = self._get_connection()
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            cursor.execute("INSERT INTO Users (username, password, email, user_type) VALUES (?, ?, ?, ?)", 
                           (username, hashed_password, email, user_type))
            conn.commit()
            print("User created successfully!")
            return True
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                raise ValueError("Username already exists.")
            elif "email" in str(e):
                raise ValueError("Email address already exists.")
            else:
                raise ValueError("Database error.")
        finally:
            conn.close()

    def is_admin(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Query to check the user_type instead of is_admin column
            cursor.execute("SELECT user_type FROM Users WHERE username = ?", (username,))
            result = cursor.fetchone()
            # Check if the user_type is 'admin'
            return result[0] == "admin" if result else False
        finally:
            conn.close()


    def appoint_admin(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Users SET user_type = 'admin' WHERE username = ?", (username,))
            if cursor.rowcount == 0:
                raise ValueError("User not found.")
            conn.commit()
            return True
        finally:
            conn.close()

    def remove_admin(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Users SET user_type = 'student' WHERE username = ?", (username,))
            if cursor.rowcount == 0:
                raise ValueError("User not found.")
            conn.commit()
            return True
        finally:
            conn.close()


    def get_all_users(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    u.user_id, u.username, u.email, u.user_type, u.user_type, 
                    IFNULL(SUM(p.questions_attempted), 0) AS total_attempted,
                    IFNULL(SUM(p.correct_answers), 0) AS total_correct,
                    IFNULL(SUM(p.score), 0) AS total_score
                FROM Users u
                LEFT JOIN UserProgress p ON u.user_id = p.user_id
                GROUP BY u.user_id;
            """)
            users = cursor.fetchall()
            return users
        finally:
            conn.close()


    def get_random_questions(self, exam_type, num_questions=10):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Debug: Log the query parameters
        print(f"Fetching questions for exam_type: {exam_type}, num_questions: {num_questions}")

        cursor.execute(''' 
            SELECT question_id, question_text, option_a, option_b, option_c, option_d, correct_answer
            FROM Questions
            WHERE question_type = ?
            ORDER BY RANDOM()
            LIMIT ?;
        ''', (exam_type, num_questions))
        
        questions = cursor.fetchall()
        conn.close()
        
        print(exam_type)

        # Debug: Log the fetched results
        print(f"Fetched {len(questions)} questions for exam type: {exam_type}")
        
        # Fallback: If no questions were found
        if len(questions) == 0:
            print(f"No questions found for exam type: {exam_type}. Please check your database.")
        
        return questions

    def get_user_id(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM Users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                raise ValueError("User not found.")
        finally:
            conn.close()

    def save_exam_results_backend(self, user_id, user_answers):
        conn = self._get_connection()
        cursor = conn.cursor()
        total_attempted = len(user_answers)
        total_correct = sum(1 for _, _, is_correct in user_answers if is_correct)
        score = int((total_correct / total_attempted) * 100) if total_attempted > 0 else 0

        try:
            cursor.execute(
                "INSERT INTO UserProgress (user_id, questions_attempted, correct_answers, score) "
                "VALUES (?, ?, ?, ?)",
                (user_id, total_attempted, total_correct, score)
            )

            for question_id, selected_answer, is_correct in user_answers:
                cursor.execute(
                    "INSERT INTO UserAnswers (user_id, question_id, selected_answer, is_correct) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, question_id, selected_answer, is_correct)
                )

            conn.commit()
        finally:
            conn.close()

    # New method to calculate user progress (Total Attempted, Correct Answers, and Score)
    def get_user_progress(self, user_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT questions_attempted, correct_answers, score FROM UserProgress WHERE user_id = ?", (user_id,))
            progress_data = cursor.fetchall()

            if not progress_data:
                return 0, 0, 0  # No data found for user
            
            # Calculate totals
            total_attempted = sum(data[0] for data in progress_data)
            total_correct = sum(data[1] for data in progress_data)
            total_score = (total_correct/total_attempted)*100

            return total_attempted, total_correct, total_score
        finally:
            conn.close()
