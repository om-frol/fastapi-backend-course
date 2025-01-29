import json
from fastapi import FastAPI, HTTPException

app = FastAPI()

class TaskManager:
    def __init__(self, file_path="tasks.json"):
        self.file_path = file_path
        self.tasks = self._load_tasks()
        self.next_id = max((task.get("id", 0) for task in self.tasks), default=0) + 1

    def _load_tasks(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_tasks(self):
        with open(self.file_path, "w") as f:
            json.dump(self.tasks, f, indent=4)

    def get_next_id(self):
        task_id = self.next_id
        self.next_id += 1
        return task_id

    def get_tasks(self):
        return self.tasks

    def create_task(self, task):
        task["id"] = self.get_next_id()
        self.tasks.append(task)
        self._save_tasks()
        return task["id"]

    def update_task(self, task_id, task):
        for i, t in enumerate(self.tasks):
            if t["id"] == task_id:
                self.tasks[i].update(task)
                self._save_tasks()
                return True
        return False

    def delete_task(self, task_id):
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if len(self.tasks) < initial_len:
            self._save_tasks()
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

