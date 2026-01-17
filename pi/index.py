from flask import Flask, render_template, request, redirect, url_for, send_file, session
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from reportlab.pdfgen import canvas
from io import BytesIO

# Initialize Firebase
cred = credentials.Certificate(os.environ['FIREBASE_KEY_PATH'])
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # For session management

# Auth Routes (Basic Firebase Auth integration)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.create_user(email=email, password=password)
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error: {e}"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.get_user_by_email(email)
            session['user'] = user.uid
            return redirect(url_for('index'))
        except Exception as e:
            return f"Error: {e}"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# PDF Generation Route
@app.route('/pdf/<name>')
def generate_pdf(name):
    if 'user' not in session:
        return redirect(url_for('login'))
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
        # Add calculations here
        p.showPage()
        p.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"{name}.pdf", mimetype='application/pdf')
    return "Employee not found"

# Updated Employee Routes with Filters
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
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
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/remove', methods=['GET', 'POST'])
def remove_employee():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        db.collection('employees').document(name).delete()
        return redirect(url_for('index'))
    return render_template('remove.html')

@app.route('/list')
def list_employees():
    if 'user' not in session:
        return redirect(url_for('login'))
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

@app.route('/report')
def generate_report():
    if 'user' not in session:
        return redirect(url_for('login'))
    branch = request.args.get('branch')
    date = request.args.get('date')
    employees = db.collection('employees').stream()
    report_data = []
    total_gross = 0
    total_net = 0
    for emp in employees:
        data = emp.to_dict()
        if (not branch or data.get('branch') == branch) and (not date or data.get('date') == date):
            rate = data['rate']
            hours = data['hours']
            deductions = data['deductions']
            overtime_hours = max(0, hours - 40)
            gross = (40 * rate) + (overtime_hours * rate * 1.5)
            taxes = gross * 0.25
            net = gross - taxes - deductions
            total_gross += gross
            total_net += net
            report_data.append({
                'name': data['name'],
                'gross': gross,
                'taxes': taxes,
                'deductions': deductions,
                'net': net
            })
    return render_template('report.html', report=report_data, total_gross=total_gross, total_net=total_net)

app = app
