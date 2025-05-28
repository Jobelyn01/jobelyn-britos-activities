from asyncio import open_connection
import calendar
from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
import hashlib

app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'employee_info'

SALT = 'qwertyuio123456 '

mysql = MySQL(app)

@app.route('/')
def index ():
        return render_template('login.html')


@app.route('/home')
def home ():
        return render_template('home.html')


@app.route('/check-user', methods=['POST'])
def check_user():
    try:
         data = request.get_json()


         username = request.form['username']
         password = request.form['password']

         salted = str(SALT + password).encode('utf-8')
         hash = hashlib.sha512(salted).hexdigest()


         cur = mysql.connection.cursor()
         cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, hash))
         user = cur.fetchone()
         cur.close()

         if user:
              return jsonify({ 'success': True})
         else:
              return jsonify({ 'success': False})
           
    except Exception as e:
         return jsonify({"error": str(e)}), 500
    
@app.route('/add-employees', methods=['POST'])
def add_employees():
     try:
          lname = request.form['lname']
          fname = request.form['fname']
          mname = request.form['mname']
          position = request.form['position']
          office = request.form['office']

          cur = mysql.connection.cursor()
          cur.execute("SELECT * FROM employee WHERE lname=%s AND fname=%s AND mname=%s AND position=%s AND office=%s", (lname, fname, mname, position, office))
          employee = cur.fetchone()
          cur.close()

          if employee:
               return jsonify({ 'success': True})
          else:
               return jsonify({ 'succes': False})
     except Exception as e:
          return jsonify({"error": str(e)}), 500
     
@app.route('/get-employees', methods=['GET'])
def get_employees():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM employee_information")
        employess = cur.fetchall()
        cur.close()

        return jsonify(employess)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
from flask import request, render_template, redirect, url_for
from datetime import date, datetime

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        employee_id = request.form['employee_id']
        status = request.form['status']  # Can be 'Present', 'Absent', 'Late', 'On Leave'
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Optional: prevent duplicate attendance entries for the same employee and date
        cur.execute("SELECT * FROM attendance WHERE employee_id = %s AND date = %s", (employee_id, date))
        exists = cur.fetchone()
        if not exists:
            cur.execute(
                "INSERT INTO attendance (employee_id, status, date) VALUES (%s, %s, %s)",
                (employee_id, status, date)
            )
            mysql.connection.commit()

    # Display data for current month
    now = datetime.now()
    year, month = now.year, now.month
    days_in_month = calendar.monthrange(year, month)[1]

    # Get distinct employee IDs for the month
    cur.execute("SELECT DISTINCT employee_id FROM attendance WHERE YEAR(date) = %s AND MONTH(date) = %s", (year, month))
    employees = [row[0] for row in cur.fetchall()]

    # Initialize dictionary to store attendance data
    attendance_data = {emp_id: {} for emp_id in employees}

    cur.execute(
        "SELECT employee_id, status, DAY(date) FROM attendance WHERE YEAR(date) = %s AND MONTH(date) = %s",
        (year, month)
    )
    for emp_id, status, day in cur.fetchall():
        attendance_data[emp_id][day] = status

    cur.close()

    return render_template('attendance.html', year=year, month=month, days_in_month=days_in_month,
                           attendance_data=attendance_data, calendar=calendar)

@app.route('/payroll')
def payroll():
    conn = mysql.connection
    cur = conn.cursor()

    # Get current month and year
    now = datetime.now()
    year, month = now.year, now.month

    # Get distinct employees who have attendance this month
    cur.execute("SELECT DISTINCT employee_id FROM attendance WHERE YEAR(date)=%s AND MONTH(date)=%s", (year, month))
    employees = [row[0] for row in cur.fetchall()]

    payroll_data = []
    DAILY_SALARY = 500  # example fixed daily salary

    for emp_id in employees:
        # Get counts by status
        cur.execute("""
            SELECT status, COUNT(*) FROM attendance
            WHERE employee_id=%s AND YEAR(date)=%s AND MONTH(date)=%s
            GROUP BY status
        """, (emp_id, year, month))
        counts = dict(cur.fetchall())  # e.g. {'Present': 20, 'Absent': 2, 'Late': 1, 'On Leave': 2}

        present_days = counts.get('Present', 0)
        late_days = counts.get('Late', 0)
        absent_days = counts.get('Absent', 0)
        on_leave_days = counts.get('On Leave', 0)

        # Calculate salary
        # Absent deduct full daily salary, Late deduct half daily salary, On Leave no deduction
        total_days = present_days + late_days + absent_days + on_leave_days
        gross_salary = total_days * DAILY_SALARY
        deduction = (absent_days * DAILY_SALARY) + (on_leave_days * DAILY_SALARY) + (late_days * (DAILY_SALARY / 2))
        total_salary = gross_salary - deduction

        payroll_data.append({
            'employee_id': emp_id,
            'present_days': present_days,
            'late_days': late_days,
            'absent_days': absent_days,
            'on_leave_days': on_leave_days,
            'total_salary': f"{total_salary:.2f}"
        })

    cur.close()

    return render_template('payroll.html', payroll_data=payroll_data, year=year, month=month)


@app.route('/update_status', methods=['POST'])
def update_status():
    emp_id = request.form.get('emp_id')
    new_status = request.form.get('status')

    if emp_id and new_status:
        conn = mysql.connection
        cur = conn.cursor()
        try:
            cur.execute("UPDATE employees SET status=%s WHERE id=%s", (new_status, emp_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return f"An error occurred: {str(e)}", 500
        finally:
            cur.close()

    return redirect(url_for('employee_status'))


@app.route('/employee_status', methods=['GET', 'POST'])
def employee_status():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        emp_id = request.form['employee_id']
        status = request.form['status']
        cur.execute("UPDATE employee_status SET status = %s WHERE id = %s", (status, emp_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('employee_status'))

    cur.execute("SELECT * FROM employee_status")
    employees = cur.fetchall()
    cur.close()
    return render_template('employee_status.html', employees=employees)


if __name__ =='_app.py_':
     app.run(debug=True)           