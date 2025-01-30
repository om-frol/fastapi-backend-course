import json
from urllib import request
from fastapi import FastAPI, HTTPException

app = FastAPI()

class JsonBinStorage:
    def __init__(self, api_key, bin_id=None):
        self.api_key = api_key
        self.bin_id = bin_id or self._create_bin()
        self.base_url = f"https://api.jsonbin.io/v3/b/{self.bin_id}"

    def _create_bin(self):
        url = "https://api.jsonbin.io/v3/b"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        req = request.Request(url, headers=headers, method="POST")
        with request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["_id"]

    def get_tasks(self):
        req = request.Request(self.base_url, headers={
            "Authorization": f"Bearer {self.api_key}"
        })
        with request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["record"]

    def update_tasks(self, tasks):
        data = json.dumps(tasks).encode("utf-8")
        req = request.Request(self.base_url, data=data, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }, method="PUT")
        with request.urlopen(req) as response:
            pass

storage = JsonBinStorage(api_key="$2a$10$sym4wDB8Jo.ewdwoOl8R9O6A5zPflfoGssY.wnxDEWEuxWtJA4h4y")

@app.get("/tasks")
def get_tasks():
    return storage.get_tasks()

@app.post("/tasks")
def create_task(task: dict):
    tasks = storage.get_tasks()
    task["id"] = max((t.get("id", 0) for t in tasks), default=0) + 1
    tasks.append(task)
    storage.update_tasks(tasks)
    return {"message": "Task created successfully", "task_id": task["id"]}

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: dict):
    tasks = storage.get_tasks()
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            tasks[i].update(task)
            storage.update_tasks(tasks)
            return {"message": "Task updated successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    tasks = storage.get_tasks()
    initial_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < initial_len:
        storage.update_tasks(tasks)
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

