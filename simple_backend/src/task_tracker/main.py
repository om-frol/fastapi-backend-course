import json
from fastapi import FastAPI, HTTPException

app = FastAPI()

TASKS_FILE = "tasks.json"

def load_tasks():
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

tasks = load_tasks()
next_id = max((task.get("id", 0) for task in tasks), default=0) + 1

def get_next_id():
    global next_id
    next_id += 1
    return next_id

@app.get("/tasks")
def get_tasks():
    return tasks

@app.post("/tasks")
def create_task(task: dict):
    task["id"] = get_next_id()
    tasks.append(task)
    save_tasks(tasks)
    return {"message": "Task created successfully", "task_id": task["id"]}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: dict):
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks[i].update(task)
            save_tasks(tasks)
            return {"message": "Task updated successfully"}

    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    global tasks
    initial_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < initial_len:
        save_tasks(tasks)
        return {"message": "Task deleted successfully"}

    raise HTTPException(status_code=404, detail="Task not found")

