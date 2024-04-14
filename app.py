from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os, time
import logging
from aws_xray_sdk.core import xray_recorder, patch, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
import requests

LOGFILE_NAME = "/var/log/app.log"

dburl = os.environ['RDS_ENDPOINT']
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(LOGFILE_NAME)
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
app.logger.addHandler(fh)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://Admin:password@{dburl}/taskdb"
app.config['SQLALCHEMY_POOL_SIZE'] = 100
db = SQLAlchemy(app)

# X-Ray設定
plugins = ('EC2Plugin',)
xray_recorder.configure(plugins=plugins)
xray_recorder.configure(service='chaos_kitty_demo_app')

# SQLAlchemyをパッチする
patch_all()

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
    n = 5  # 計算するフィボナッチ数列の項数

    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n - 1) + fib(n - 2)

    start_time = time.time()
    result = fib(n)
    end_time = time.time()

    execution_time = end_time - start_time
    app.logger.info(f"Fibonacci of {n} is {result} (Execution time: {execution_time:.6f} seconds)")

    return render_template("index.html", todo_list=todo_list)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title")
    new_todo = Todo(title=title)
    db.session.add(new_todo)
    db.session.commit()
    app.logger.info(f'add task "{title}"')
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    app.logger.info(f'delete task "{todo}"')
    return redirect(url_for("home"))

@app.route("/deletealldoneitems", methods=["GET", "POST"])
def delete_alldoneitems():
    todo_list = Todo.query.all()
    for todo in todo_list:
        db.session.delete(todo)
    db.session.commit()
    app.logger.info(f'delete all tasks')
    return redirect(url_for("home"))

@app.route("/cpu_load", methods=["GET"])
def cpu_load():
    start_time = time.time()
    duration = 5  # 5秒間CPUを占有する

    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        if elapsed_time > duration:
            break
        # CPUを占有する処理
        for i in range(10000000):
            pass
    app.logger.info(f'CPU load completed')

    return "CPU load completed"

@app.route("/fibonacci", methods=["GET"])
def fibonacci():
    n = 35  # 計算するフィボナッチ数列の項数

    def fib(n):
        if n <= 1:
            return n
        else:
            return fib(n - 1) + fib(n - 2)

    start_time = time.time()
    result = fib(n)
    end_time = time.time()

    execution_time = end_time - start_time
    app.logger.info(f"Fibonacci of {n} is {result} (Execution time: {execution_time:.6f} seconds)")

    return f"Fibonacci of {n} is {result}"

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False,host='0.0.0.0', port=8080, threaded=True)