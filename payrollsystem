import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase (replace with your key path)
cred = credentials.Certificate('firebase-key.json')  # Or use env var for security
firebase_admin.initialize_app(cred)
db = firestore.client()

def add_employee(name, rate, hours, deductions):
    doc_ref = db.collection('employees').document(name)
    doc_ref.set({
        'name': name,
        'rate': rate,
        'hours': hours,
        'deductions': deductions
    })
    print(f"Added {name} to Firebase.")

def remove_employee(name):
    db.collection('employees').document(name).delete()
    print(f"Removed {name} from Firebase.")

def list_employees():
    employees = db.collection('employees').stream()
    for emp in employees:
        print(emp.to_dict())

def calculate_pay(employee):
    rate = employee['rate']
    hours = employee['hours']
    deductions = employee['deductions']
    overtime_hours = max(0, hours - 40)
    gross = (40 * rate) + (overtime_hours * rate * 1.5)
    taxes = gross * 0.25  # Customizable
    net = gross - taxes - deductions
    return gross, taxes, net

def generate_report():
    employees = db.collection('employees').stream()
    total_gross = 0
    total_net = 0
    print("\n--- Payroll Report ---")
    for emp in employees:
        data = emp.to_dict()
        gross, taxes, net = calculate_pay(data)
        total_gross += gross
        total_net += net
        print(f"{data['name']}: Gross ${gross:.2f}, Taxes ${taxes:.2f}, Deductions ${data['deductions']:.2f}, Net ${net:.2f}")
    print(f"Total Gross: ${total_gross:.2f}, Total Net: ${total_net:.2f}\n")

def main():
    while True:
        print("1. Add Employee\n2. Remove Employee\n3. List Employees\n4. Generate Report\n5. Exit")
        choice = input("Choose: ")
        if choice == '1':
            name = input("Name: ")
            rate = float(input("Hourly Rate: "))
            hours = float(input("Hours Worked: "))
            deductions = float(input("Deductions: "))
            add_employee(name, rate, hours, deductions)
        elif choice == '2':
            name = input("Name to remove: ")
            remove_employee(name)
        elif choice == '3':
            list_employees()
        elif choice == '4':
            generate_report()
        elif choice == '5':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
