
import matplotlib
matplotlib.use('Agg')

from flask import Flask
from flask import render_template_string
from flask import request
from flask import redirect
from flask import session
from flask import send_file

import mysql.connector
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet

import csv
import cv2
import os

app = Flask(__name__)

app.secret_key = "secret123"

# MYSQL CONNECTION
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Disha@2107",
    database="intelligentcampus"
)

# BUFFERED CURSOR
cursor = db.cursor(buffered=True)

# LOAD HTML FILES
def load_html(file):

    with open(file, "r", encoding="utf-8") as f:
        return f.read()

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        query = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        cursor.execute(query, (email, password))

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['name'] = user[1]

            return redirect('/dashboard')

        else:

            return """
            <h2>Invalid Email or Password</h2>
            <a href="/">Back</a>
            """

    return render_template_string(
        load_html("login.html")
    )

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        query = """
        INSERT INTO users(name,email,password)
        VALUES(%s,%s,%s)
        """

        cursor.execute(
            query,
            (name, email, password)
        )

        db.commit()

        return redirect('/')

    return render_template_string(
        load_html("register.html")
    )

# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/')

    try:

        query = """
        SELECT * FROM tasks
        WHERE user_id=%s
        """

        cursor.execute(
            query,
            (session['user_id'],)
        )

        tasks = cursor.fetchall()

        total = len(tasks)

        completed = 0

        for task in tasks:

            if task[4] == "Completed":
                completed += 1

        pending = total - completed

        productivity = 0

        if total > 0:

            productivity = int(
                (completed / total) * 100
            )

        # CREATE STATIC FOLDER
        if not os.path.exists("static"):
            os.makedirs("static")

        # CREATE CHART
        labels = ['Completed', 'Pending']

        if total == 0:
            values = [1, 0]
        else:
            values = [completed, pending]

        plt.figure(figsize=(4,4))

        plt.pie(
            values,
            labels=labels,
            autopct='%1.1f%%'
        )

        plt.title("Task Analytics")

        plt.savefig(
            "static/chart.png",
            bbox_inches='tight'
        )

        plt.close()

        return render_template_string(
            load_html("dashboard.html"),

            tasks=tasks,

            total=total,

            completed=completed,

            pending=pending,

            productivity=productivity,

            name=session['name']
        )

    except Exception as e:

        return f"""
        <h1>Dashboard Error</h1>
        <h3>{e}</h3>
        """

# ADD TASK
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():

    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':

        task = request.form['task']
        priority = request.form['priority']
        status = request.form['status']

        query = """
        INSERT INTO tasks(
            user_id,
            task,
            priority,
            status
        )
        VALUES(%s,%s,%s,%s)
        """

        values = (
            session['user_id'],
            task,
            priority,
            status
        )

        cursor.execute(query, values)

        db.commit()

        return redirect('/dashboard')

    return render_template_string(
        load_html("add_task.html")
    )

# DELETE TASK
@app.route('/delete/<int:id>')
def delete(id):

    query = """
    DELETE FROM tasks
    WHERE id=%s
    """

    cursor.execute(query, (id,))

    db.commit()

    return redirect('/dashboard')

# EXPORT CSV
@app.route('/export_csv')
def export_csv():

    if 'user_id' not in session:
        return redirect('/')

    query = """
    SELECT task, priority, status
    FROM tasks
    WHERE user_id=%s
    """

    cursor.execute(
        query,
        (session['user_id'],)
    )

    data = cursor.fetchall()

    with open(
        'tasks.csv',
        mode='w',
        newline='',
        encoding='utf-8'
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            'Task',
            'Priority',
            'Status'
        ])

        for row in data:

            writer.writerow(row)

    return send_file(
        'tasks.csv',
        as_attachment=True
    )

# GENERATE PDF REPORT
@app.route('/generate_pdf')
def generate_pdf():

    if 'user_id' not in session:
        return redirect('/')

    query = """
    SELECT * FROM tasks
    WHERE user_id=%s
    """

    cursor.execute(
        query,
        (session['user_id'],)
    )

    tasks = cursor.fetchall()

    total = len(tasks)

    completed = 0

    for task in tasks:

        if task[4] == "Completed":
            completed += 1

    pending = total - completed

    productivity = 0

    if total > 0:

        productivity = int(
            (completed / total) * 100
        )

    # AI REMARK
    if productivity >= 80:

        remark = "Excellent Productivity Performance"

    elif productivity >= 50:

        remark = "Good Productivity Performance"

    else:

        remark = "Needs Productivity Improvement"

    doc = SimpleDocTemplate(
        "report.pdf"
    )

    styles = getSampleStyleSheet()

    story = []

    # TITLE
    story.append(
        Paragraph(
            "IntelliCampus AI Productivity Report",
            styles['Title']
        )
    )

    story.append(Spacer(1,20))

    # USER INFO
    story.append(
        Paragraph(
            f"<b>Student Name:</b> {session['name']}",
            styles['BodyText']
        )
    )

    story.append(Spacer(1,10))

    # STATS
    story.append(
        Paragraph(
            f"<b>Total Tasks:</b> {total}",
            styles['BodyText']
        )
    )

    story.append(
        Paragraph(
            f"<b>Completed Tasks:</b> {completed}",
            styles['BodyText']
        )
    )

    story.append(
        Paragraph(
            f"<b>Pending Tasks:</b> {pending}",
            styles['BodyText']
        )
    )

    story.append(
        Paragraph(
            f"<b>Productivity Score:</b> {productivity}%",
            styles['BodyText']
        )
    )

    story.append(Spacer(1,20))

    # AI ANALYSIS
    story.append(
        Paragraph(
            f"<b>AI Analysis:</b> {remark}",
            styles['BodyText']
        )
    )

    story.append(Spacer(1,20))

    # TASK DETAILS
    story.append(
        Paragraph(
            "<b>Task Details:</b>",
            styles['Heading2']
        )
    )

    story.append(Spacer(1,10))

    if total == 0:

        story.append(
            Paragraph(
                "No tasks available.",
                styles['BodyText']
            )
        )

    else:

        for task in tasks:

            task_text = f"""
            • Task: {task[2]}
            | Priority: {task[3]}
            | Status: {task[4]}
            """

            story.append(
                Paragraph(
                    task_text,
                    styles['BodyText']
                )
            )

            story.append(Spacer(1,8))

    story.append(Spacer(1,25))

    story.append(
        Paragraph(
            "Generated by IntelliCampus AI",
            styles['Italic']
        )
    )

    doc.build(story)

    return send_file(
        "report.pdf",
        as_attachment=True
    )

# SMART ATTENTION MONITOR
@app.route('/face_detection')
def face_detection():

    cam = cv2.VideoCapture(0)

    if not cam.isOpened():

        return """
        <h2>Camera Error</h2>
        <p>Unable to access webcam.</p>
        """

    detector = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        'haarcascade_frontalface_default.xml'
    )

    focus_frames = 0
    total_frames = 0

    cv2.namedWindow("Smart Attention Monitor")

    while True:

        success, frame = cam.read()

        if not success:
            break

        total_frames += 1

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30,30)
        )

        if len(faces) > 0:

            focus_frames += 1

            status = "USER ACTIVE"

            color = (0,255,0)

        else:

            status = "NO FACE DETECTED"

            color = (0,0,255)

        for (x, y, w, h) in faces:

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                color,
                2
            )

        focus_score = int(
            (focus_frames / total_frames) * 100
        )

        cv2.putText(
            frame,
            f"Status: {status}",
            (20,40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            color,
            2
        )

        cv2.putText(
            frame,
            f"Focus Score: {focus_score}%",
            (20,80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255,255,255),
            2
        )

        cv2.putText(
            frame,
            "Press Q to Exit",
            (20,120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255,255,0),
            2
        )

        cv2.imshow(
            "Smart Attention Monitor",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if cv2.getWindowProperty(
            "Smart Attention Monitor",
            cv2.WND_PROP_VISIBLE
        ) < 1:
            break

    cam.release()

    cv2.destroyAllWindows()

    cv2.waitKey(1)

    return f"""
    <h1>Attention Monitoring Completed</h1>

    <h2>Final Focus Score: {focus_score}%</h2>

    <a href='/dashboard'>
        Back to Dashboard
    </a>
    """

# LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# RUN
if __name__ == "__main__":

    app.run(debug=True)