import json
from fastapi import FastAPI, HTTPException
import threading

app = FastAPI()

class TaskManager:
    def __init__(self, file_path="tasks.json"):
        self.file_path = file_path
        self.lock = threading.Lock()
        self.next_id = self._load_next_id()

    def _load_next_id(self):
        try:
            with open(self.file_path, "r") as f:
                tasks = json.load(f)
                return max((task.get("id", 0) for task in tasks), default=0) + 1
        except FileNotFoundError:
            return 1

    def _load_tasks(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_tasks(self, tasks):
        with open(self.file_path, "w") as f:
            json.dump(tasks, f, indent=4)

    def get_next_id(self):
        with self.lock:
            task_id = self.next_id
            self.next_id += 1
            return task_id

    def get_tasks(self):
        with self.lock:
            return self._load_tasks()

    def create_task(self, task):
        with self.lock:
            tasks = self._load_tasks()
            task["id"] = self.get_next_id()
            tasks.append(task)
            self._save_tasks(tasks)
            return task["id"]

    def update_task(self, task_id, task):
        with self.lock:
            tasks = self._load_tasks()
            for i, t in enumerate(tasks):
                if t["id"] == task_id:
                    tasks[i].update(task)
                    self._save_tasks(tasks)
                    return True
            return False

    def delete_task(self, task_id):
        with self.lock:
            tasks = self._load_tasks()
            initial_len = len(tasks)
            tasks = [t for t in tasks if t["id"] != task_id]
            if len(tasks) < initial_len:
                self._save_tasks(tasks)
                return True
            return False

task_manager = TaskManager()

@app.get("/tasks")
def get_tasks():
    return task_manager.get_tasks()

@app.post("/tasks")
def create_task(task: dict):
    task_id = task_manager.create_task(task)
    return {"message": "Task created successfully", "task_id": task_id}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: dict):
    if task_manager.update_task(task_id, task):
        return {"message": "Task updated successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_manager.delete_task(task_id):
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

