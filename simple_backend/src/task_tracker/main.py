import json
import os
from urllib import request, error
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("JSONBIN_API_KEY")

if not API_KEY:
    raise ValueError("JSONBIN_API_KEY environment variable not set.")

app = FastAPI()

class Task(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

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
        try:
            with request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                return data["record"]
        except error.HTTPError as e:
            if e.code == 404:
                return []  # Return empty list if bin is not found
            raise  # Re-raise other HTTP errors
        except json.JSONDecodeError:
            return []  # Return empty list if JSON is invalid

    def update_tasks(self, tasks):
        data = json.dumps(tasks).encode("utf-8")
        req = request.Request(self.base_url, data=data, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }, method="PUT")
        with request.urlopen(req) as response:
            pass

storage = JsonBinStorage(api_key=API_KEY)

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    try:
        return storage.get_tasks()
    except (error.HTTPError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving tasks: {e}")

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: Task):
    try:
        tasks = storage.get_tasks()
        task_dict = task.dict()
        task_dict["id"] = max((t.get("id", 0) for t in tasks), default=0) + 1
        tasks.append(task_dict)
        storage.update_tasks(tasks)
        return {"message": "Task created successfully", "task_id": task_dict["id"]}
    except (error.HTTPError, json.JSONDecodeError, ValidationError) as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # Convert ValidationError to string

@app.put("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def update_task(task_id: int, task: Task):
    try:
        tasks = storage.get_tasks()
        for i, t in enumerate(tasks):
            if t.get("id") == task_id:
                tasks[i].update(task.dict())
                storage.update_tasks(tasks)
                return {"message": "Task updated successfully"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    except (error.HTTPError, json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) # Convert ValidationError to string

@app.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: int):
    try:
        tasks = storage.get_tasks()
        initial_len = len(tasks)
        tasks = [t for t in tasks if t.get("id") == task_id]
        if len(tasks) < initial_len:
            storage.update_tasks(tasks)
            return {"message": "Task deleted successfully"}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    except (error.HTTPError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting task: {e}")

