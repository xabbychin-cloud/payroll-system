from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from reportlab.pdfgen import canvas
from io import BytesIO

# Initialize Firebase
cred = credentials.Certificate(os.environ.get('FIREBASE_KEY_PATH', 'firebase-key.json'))  # Fallback for local testing
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-secret')  # Use env var for production

# Auth Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            auth.create_user(email=email, password=password)
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.get_user_by_email(email)
            session['user'] = user.uid
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

# PDF Route
@app.route('/pdf/<name>')
def generate_pdf(name):
    if 'user' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))
    try:
        emp_ref = db.collection('employees').document(name)
        emp = emp_ref.get()
        if emp.exists:
            data = emp.to_dict()
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(100, 750, f"Employee: {data['name']}")
            p.drawString(100, 730, f"Rate: ${data['rate']}")
            p.drawString(100, 710, f"Hours: {data['hours']}")
            p.drawString(100, 690, f"Deductions: ${data['deductions']}")
            p.drawString(100, 670, f"Branch: {data.get('branch', 'N/A')}")
            p.drawString(100, 650, f"Date: {data.get('date', 'N/A')}")
            # Calculations
            overtime = max(0, data['hours'] - 40)
            gross = (40 * data['rate']) + (overtime * data['rate'] * 1.5)
            taxes = gross * 0.25
            net = gross - taxes - data['deductions']
            p.drawString(100, 630, f"Gross: ${gross:.2f}, Taxes: ${taxes:.2f}, Net: ${net:.2f}")
            p.showPage()
            p.save()
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name=f"{name}_payroll.pdf", mimetype='application/pdf')
        flash('Employee not found.', 'error')
    except Exception as e:
        flash(f'PDF error: {str(e)}', 'error')
    return redirect(url_for('list_employees'))

# Employee Routes
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if 'user' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            name = request.form['name']
            rate = float(request.form['rate'])
            hours = float(request.form['hours'])
            deductions = float(request.form['deductions'])
            branch = request.form['branch']
            date = request.form['date']
            doc_ref = db.collection('employees').document(name)
            doc_ref.set({
                'name': name,
                'rate': rate,
                'hours': hours,
                'deductions': deductions,
                'branch': branch,
                'date': date
            })
            flash('Employee added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error adding employee: {str(e)}', 'error')
    return render_template('add.html')

@app.route('/remove', methods=['GET', 'POST'])
def remove_employee():
    if 'user' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            name = request.form['name']
            db.collection('employees').document(name).delete()
            flash('Employee removed.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error removing employee: {str(e)}', 'error')
    return render_template('remove.html')

@app.route('/list')
def list_employees():
    if 'user' not in session:
        flash('Please log in.', 'error')
        return redirect(url_for('login'))
    try:
        branch = request.args.get('branch')
        date = request.args.get('date')
        search = request.args.get('search')
        employees = db.collection('employees').stream()
        emp_list = []
        for emp in employees:
            data = emp.to_dict()
            if (not branch or data.get('branch') == branch) and (not date or data.get('date') == date) and (not search or search.lower() in data['name'].lower()):
                emp_list.append(data)
        return render_template('list.html', employees=emp_list)
        return render_template('index.html', employees=emp_list)  # Instead of 'list.html'
    except Exception as e:
        flash(f'Error loading employees: {str(e)}', 'error')
        return render_template('list.html', employees=[])

app = app
