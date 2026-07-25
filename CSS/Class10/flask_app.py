from flask import Flask, request, redirect, url_for, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///students.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Database Model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    gender = db.Column(db.String(20))
    class_name = db.Column(db.String(50))


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        student = Student(
            name=request.form["name"],
            email=request.form["email"],
            password=request.form["password"],
            gender=request.form["gender"],
            class_name=request.form["Class"],
        )

        db.session.add(student)
        db.session.commit()

        return redirect(url_for("submissions"))

    return send_file("form1.html")


@app.route("/submissions")
def submissions():
    students = Student.query.all()
    return render_template("submissions.html", students1=students)


if __name__ == "__main__":
    app.run( host='0.0.0.0' ,debug=True)