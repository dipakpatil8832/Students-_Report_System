from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from utils.helpers import validate_grade, calculate_average, subject_list
import os


app = Flask(__name__)
app.jinja_env.globals['getattr'] = getattr
app.config['SECRET_KEY'] = 'dev-secret-key'  # Change in production



app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@host/db'


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)

def init_db():
    
    with app.app_context():
        db.create_all()
        print("✅ Database initialized successfully.")


init_db()



class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    math = db.Column(db.Float, nullable=True)
    science = db.Column(db.Float, nullable=True)
    english = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'roll_number': self.roll_number,
            'math': self.math,
            'science': self.science,
            'english': self.english
        }

    def average(self):
        scores = [s for s in (self.math, self.science, self.english) if s is not None]
        return calculate_average(scores) if scores else None


# ---------------------- Routes ----------------------
@app.route('/')
def index():
    students = Student.query.order_by(Student.roll_number).all()
    return render_template('index.html', students=students)


@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll = request.form.get('roll_number', '').strip()
        if not name or not roll:
            flash('Name and Roll Number are required.', 'danger')
            return redirect(url_for('add_student'))

        student = Student(name=name, roll_number=roll)
        db.session.add(student)
        try:
            db.session.commit()
            flash('Student added successfully.', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Roll number already exists. Use a unique roll number.', 'danger')
            return redirect(url_for('add_student'))

    return render_template('add_student.html')


@app.route('/student/<int:student_id>')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('view_student.html', student=student, subjects=subject_list())


@app.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll = request.form.get('roll_number', '').strip()
        if not name or not roll:
            flash('Name and Roll Number are required.', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))
        student.name = name
        student.roll_number = roll
        try:
            db.session.commit()
            flash('Student updated.', 'success')
            return redirect(url_for('view_student', student_id=student.id))
        except IntegrityError:
            db.session.rollback()
            flash('Roll number already exists.', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))
    return render_template('edit_student.html', student=student)


@app.route('/student/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('index'))


@app.route('/student/<int:student_id>/grades', methods=['GET', 'POST'])
def add_grades(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        grades = {}
        for subj in subject_list():
            val = request.form.get(subj)
            if val == '' or val is None:
                grades[subj] = None
                continue
            valid, msg, num = validate_grade(val)
            if not valid:
                flash(f'Invalid grade for {subj.capitalize()}: {msg}', 'danger')
                return redirect(url_for('add_grades', student_id=student_id))
            grades[subj] = num
        student.math = grades.get('math')
        student.science = grades.get('science')
        student.english = grades.get('english')
        db.session.commit()
        flash('Grades updated successfully.', 'success')
        return redirect(url_for('view_student', student_id=student.id))
    return render_template('add_grades.html', student=student, subjects=subject_list())


@app.route('/report/class')
def class_report():
    students = Student.query.all()
    subject_summaries = {}
    for subj in subject_list():
        scores = [getattr(s, subj) for s in students if getattr(s, subj) is not None]
        subject_summaries[subj] = {
            'count': len(scores),
            'average': calculate_average(scores) if scores else None,
            'topper': None
        }
        if scores:
            top_score = max(scores)
            toppers = [s for s in students if getattr(s, subj) == top_score]
            subject_summaries[subj]['topper'] = toppers[0].to_dict() if toppers else None

    overall_scores = []
    for s in students:
        avg = s.average()
        if avg is not None:
            overall_scores.append(avg)
    class_average = calculate_average(overall_scores) if overall_scores else None

    return render_template('class_report.html', students=students,
                           subject_summaries=subject_summaries, class_average=class_average,
                           subjects=subject_list())


@app.route('/search', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        results = Student.query.filter(
            (Student.name.ilike(f'%{q}%')) | (Student.roll_number.ilike(f'%{q}%'))
        ).all()
    return render_template('search.html', query=q, results=results)


# ---------------------- Run Application ----------------------
if __name__ == '__main__':
    app.run(debug=True)



