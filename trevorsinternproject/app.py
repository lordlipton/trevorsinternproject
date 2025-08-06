from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import subprocess
import crypt
import pwd

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads'

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('dev', 'dev123'))
        conn.commit()
        conn.close()

def create_system_dev_user():
    username = "dev"
    password = "dev123"
    try:
        pwd.getpwnam(username)  # Check if user exists
        print(f"User '{username}' already exists.")
    except KeyError:
        print(f"Creating system user '{username}'...")
        encrypted_password = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))
        subprocess.run(["useradd", "-m", "-p", encrypted_password, username], check=True)
        print(f"User '{username}' created with password '{password}'.")

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    return f'File {file.filename} uploaded.'

@app.route('/admin')
def admin():
    if session.get('username') != 'dev':
        return 'Unauthorized', 403
    return 'Welcome to the admin panel!'

if __name__ == '__main__':
    init_db()
    create_system_dev_user()
    app.run(host='0.0.0.0', port=80, debug=True)
