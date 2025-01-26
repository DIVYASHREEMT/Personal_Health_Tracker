from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import bcrypt
import os
from creds import API_KEY
import google.generativeai as genai

# Initialize Flask app and MySQL connection
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Adjust with your MySQL username
app.config['MYSQL_PASSWORD'] = 'Shree@27'  # Adjust with your MySQL password
app.config['MYSQL_DB'] = 'health_tracker_db'
mysql = MySQL(app)

# Configure Generative AI
genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Route for Home (Login page)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  # user[2] is the password hash
            session['user'] = username  # Store username in session to keep the user logged in
            return redirect(url_for('health'))  # Redirect to health page (user dashboard)
        else:
            flash('Invalid username or password', 'danger')

    return render_template('index.html')

# Route for Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cursor.fetchone()

        if user:
            flash("Username already exists", 'danger')
            return redirect(url_for('signup'))
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        mysql.connection.commit()
        cursor.close()
        
        flash("Signup successful! Please login.", 'success')
        return redirect(url_for('home'))

    return render_template('signup.html')

# Route for Health Page (Dashboard)
@app.route('/health', methods=['GET', 'POST'])
def health():
    if 'user' not in session:  # If user is not logged in, redirect to login page
        return redirect(url_for('home'))

    username = session['user']  # Get the logged-in username

    if request.method == 'POST':
        height_cm = float(request.form['height'])  # in cm
        weight = float(request.form['weight'])  # in kg
        water = float(request.form['water_intake'])  # in liters
        sleep = float(request.form['sleep_hours'])  # in hours
        exercise = float(request.form['exercise_hours'])  # in hours

        # Convert height to meters for BMI calculation
        height_m = height_cm / 100  # Convert cm to meters

        # BMI calculation
        bmi = weight / (height_m ** 2)
        
        # BMI Categories
        if bmi < 18.5:
            bmi_category = "Underweight"
        elif 18.5 <= bmi <= 24.9:
            bmi_category = "Optimum Range"
        elif 25 <= bmi <= 29.9:
            bmi_category = "Overweight"
        elif 30 <= bmi <= 34.9:
            bmi_category = "Class I Obesity"
        elif 35 <= bmi <= 39.9:
            bmi_category = "Class II Obesity"
        else:
            bmi_category = "Class III Obesity"
        
        # Store health data in database
        cursor = mysql.connection.cursor()
        cursor.execute(""" 
            UPDATE users 
            SET height = %s, weight = %s, water_intake = %s, sleep_hours = %s, exercise_hours = %s, bmi = %s, bmi_category = %s 
            WHERE username = %s
        """, (height_cm, weight, water, sleep, exercise, bmi, bmi_category, username))
        mysql.connection.commit()
        cursor.close()
        
        # Set reminders for low water intake, sleep, and exercise
        reminders = []
        if water < 2:
            reminders.append("You should drink more water!")
        if sleep < 7:
            reminders.append("You need more sleep!")
        if exercise < 30:
            reminders.append("Try to exercise more!")
        
        return render_template('health.html', reminders=reminders, bmi=bmi, bmi_category=bmi_category, username=username)
    
    return render_template('health.html', reminders=[])

# Route for Chatbot
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        user_message = request.form['user_message']
        response = generate_response(user_message)
        return response
    return render_template('chatbot.html')

def generate_response(user_message):
    # Custom response for "Hi"
    if user_message.lower() == "hi":
        return "Hi, which medicines do you want to know about?"
    
    # Custom response for "Hello"
    if user_message.lower() == "hello":
        return "Hello! How can I assist you today?"

    # For other messages, send it to the AI model
    response = model.generate_content([
        f"input: {user_message}",
        "output: ",
    ])
    return response.text

# Route for Logout (Redirect to Home)
@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove user from session
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
