from flask import Flask, jsonify, request, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import sqlite3

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

execution_history = []


def init_database():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            schedule TEXT,
            status TEXT,
            created TEXT
        )
    """)

    conn.commit()
    conn.close()


init_database()


def run_task(task_name):
    start = datetime.now()

    print(f"▶️ Running: {task_name}")

    status = "Success"

    finish = datetime.now()

    execution_history.append({
        "task": task_name,
        "status": status,
        "started": str(start),
        "finished": str(finish)
    })

    print(f"✅ {task_name} completed!")


def create_cron_task(task_name, hour, minute):
    job_id = "cron_" + task_name.replace(" ", "_")

    scheduler.add_job(
        run_task,
        CronTrigger(hour=hour, minute=minute),
        args=[task_name],
        id=job_id,
        replace_existing=True
    )

    task = {
        "id": job_id,
        "name": task_name,
        "schedule": f"Daily at {hour:02d}:{minute:02d}",
        "status": "Scheduled",
        "created": str(datetime.now())
    }

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO tasks
        (id, name, schedule, status, created)
        VALUES (?, ?, ?, ?, ?)
    """, (
        task["id"],
        task["name"],
        task["schedule"],
        task["status"],
        task["created"]
    ))

    conn.commit()
    conn.close()

    return task


@app.route("/")
@app.route("/dashboard")
def dashboard():

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Task Scheduler & Job Runner</title>

        <style>
            body {
                font-family: Arial;
                max-width: 900px;
                margin: auto;
                padding: 20px;
                background: #f5f5f5;
            }

            .card {
                background: white;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 10px;
            }

            input, button {
                padding: 10px;
                margin: 5px;
            }

            button {
                cursor: pointer;
            }
        </style>
    </head>

    <body>

        <h1>⏰ Task Scheduler & Job Runner</h1>

        <div class="card">
            <h2>➕ Create Cron Job</h2>

            <input id="name" placeholder="Task name">

            <input id="hour"
                   type="number"
                   min="0"
                   max="23"
                   placeholder="Hour">

            <input id="minute"
                   type="number"
                   min="0"
                   max="59"
                   placeholder="Minute">

            <button onclick="createTask()">
                Create Cron Job
            </button>
        </div>

        <div class="card">
            <h2>📋 Scheduled Tasks</h2>
            <div id="tasks"></div>
        </div>

        <div class="card">
            <h2>📊 Execution History</h2>
            <div id="history"></div>
        </div>

        <script>

        async function createTask() {

            const name =
                document.getElementById("name").value;

            const hour =
                document.getElementById("hour").value;

            const minute =
                document.getElementById("minute").value;

            await fetch(
                `/create?name=${encodeURIComponent(name)}&hour=${hour}&minute=${minute}`
            );

            loadTasks();
        }


        async function loadTasks() {

            const response =
                await fetch("/tasks");

            const tasks =
                await response.json();

            document.getElementById("tasks").innerHTML =
                tasks.map(task =>
                    `<p>
                        <b>${task.name}</b>
                        — ${task.schedule}
                        — ${task.status}
                    </p>`
                ).join("");
        }


        async function loadHistory() {

            const response =
                await fetch("/history");

            const history =
                await response.json();

            document.getElementById("history").innerHTML =
                history.map(item =>
                    `<p>
                        <b>${item.task}</b>
                        — ${item.status}<br>
                        Started: ${item.started}<br>
                        Finished: ${item.finished}
                    </p>`
                ).join("");
        }


        loadTasks();
        loadHistory();

        setInterval(loadHistory, 5000);

        </script>

    </body>
    </html>
    """)


@app.route("/create")
def create():

    name = request.args.get("name")

    hour = int(request.args.get("hour"))

    minute = int(request.args.get("minute"))

    task = create_cron_task(
        name,
        hour,
        minute
    )

    return jsonify(task)


@app.route("/tasks")
def get_tasks():

    conn = sqlite3.connect("tasks.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, schedule, status, created
        FROM tasks
    """)

    rows = cursor.fetchall()

    conn.close()

    tasks = []

    for row in rows:

        tasks.append({
            "id": row[0],
            "name": row[1],
            "schedule": row[2],
            "status": row[3],
            "created": row[4]
        })

    return jsonify(tasks)


@app.route("/history")
def get_history():

    return jsonify(execution_history)


if __name__ == "__main__":

    print("🚀 Task Scheduler & Job Runner started!")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
