from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, session, send_file, request
from flask_sqlalchemy import SQLAlchemy
from form import InfoForm, EmailForm
from flask_bootstrap import Bootstrap
import jwt
from io import BytesIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'SomeSecretKey'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///form-data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


# checks if u already filed the form and if so will not let u access to the decorated route
def not_allow_with_token(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if session.get("token"):
            flash("U already filled the form")
            return redirect(url_for("home"))
        return func(*args, **kwargs)

    return inner


# checks if u filled the form in the register route and if not will redirect u there
def check_for_data_id(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if session.get("data_id"):
            return func(*args, **kwargs)
        flash("U need to fill the form in register to access this page")
        return redirect(url_for("home"))

    return inner


# checks if u already filed the form and if so will allow u to access the decorated route
def allow_only_with_token(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if session.get("token"):
            return func(*args, **kwargs)
        flash("U need to fill all the forms to made this action")
        return redirect(url_for("home"))

    return inner


class User(db.Model):
    __tablename__ = "form-data"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    img_file_name = db.Column(db.String(1000))
    img_file = db.Column(db.LargeBinary)
    pdf_file_name = db.Column(db.String(1000))
    pdf_file = db.Column(db.LargeBinary)
    comment_field = db.Column(db.String(1000))
    email = db.Column(db.String(100))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["POST", "GET"])
@not_allow_with_token
def register():
    form = InfoForm()
    if form.validate_on_submit():
        # get hold on the form data
        pdf_file = form.pdf_file.data
        img_file = form.img_file.data
        name = form.name.data
        last_name = form.last_name.data
        img_file_name = img_file.filename
        pdf_file_name = pdf_file.filename
        comment_field = form.free_field.data
        # crate a new row in the db with the form data
        new_user = User(
            name=name,
            last_name=last_name,
            img_file_name=img_file_name,
            img_file=img_file.read(),
            pdf_file_name=pdf_file_name,
            pdf_file=pdf_file.read(),
            comment_field=comment_field,
        )
        db.session.add(new_user)
        db.session.commit()
        # get hold of the new user id that been added
        data_id = new_user.id
        session["data_id"] = data_id
        return redirect(url_for("enter_email"))
    return render_template("register.html", form=form)


@app.route("/email", methods=["POST", "GET"])
@not_allow_with_token
@check_for_data_id
def enter_email():
    form = EmailForm()
    if form.validate_on_submit():
        data_id = session.get("data_id")
        new_user = User.query.get(data_id)
        new_user.email = form.email.data
        # crate a token after all the data in the form was filled

        token = jwt.encode({"name": new_user.name,
                            "last-name": new_user.last_name,
                            "email": new_user.email,
                            "id": new_user.id}, app.config['SECRET_KEY'])
        session["token"] = token

        db.session.commit()
        return redirect(url_for("home"))

    return render_template("get-email.html", form=form)


# this path will give your data from the db
@app.route("/get-data")
@allow_only_with_token
def get_data():
    # get hold of the jwt data
    token = session["token"]
    decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
    # use the data from the jwt token to get the data from the db
    data = User.query.get(decoded["id"])
    # send the files if requested
    if request.method == "GET":
        if request.args.get("file") == "pdf":
            return send_file(BytesIO(data.pdf_file), download_name=data.pdf_file_name, as_attachment=True)
        elif request.args.get("file") == "img":
            return send_file(BytesIO(data.img_file), download_name=data.img_file_name, as_attachment=True)

    return render_template("get-data.html", data=data)


# this path will delete the saved token, useful for testing
@app.route("/delete")
@allow_only_with_token
def delete():
    session.clear()
    flash("session cleared")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
