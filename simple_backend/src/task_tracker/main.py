from fastapi import FastAPI

app = FastAPI()

tasks = []
next_id = 0

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
    return {"message": "Task created successfully"}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: dict):
    for t in tasks:
        if t["id"] == task_id:
            t.update(task)
            return {"message": "Task updated successfully"}
    return {"message": "Task not found"}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    global tasks
    tasks = [t for t in tasks if t["id"] != task_id]
    return {"message": "Task deleted successfully"}