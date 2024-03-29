from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from aws_xray_sdk.core import xray_recorder, patch
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
import requests

dburl = os.environ['RDS_ENDPOINT']
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://Admin:password@{dburl}/taskdb"
db = SQLAlchemy(app)

# X-Ray設定
plugins = ('EC2Plugin',)
xray_recorder.configure(plugins=plugins)
xray_recorder.configure(service='chaos_kitty_demo_app')

# HTTPリクエストに利用するモジュールを指定
libraries = (['requests'])
patch(libraries)

# X-Rayサンプリングルールの設定
sampling_rule_path = os.getcwd() + "/" + "sampling_rule.json"
xray_recorder.configure(sampling_rules=sampling_rule_path)

# FlaskとX-Rayを連携
XRayMiddleware(app, xray_recorder)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))


@app.route("/", methods=["GET", "POST"])
def home():
    todo_list = Todo.query.all()
    return render_template("index.html", todo_list=todo_list)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    new_todo = Todo(title=title)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False,host='0.0.0.0', port=8080)