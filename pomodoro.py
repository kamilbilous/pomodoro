from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta

app = FastAPI()

class Task(BaseModel):
    id: str
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field(default= "TODO", pattern =r"^(TODO|IN_PROGRESS|DONE)$")

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)

class PomodoroSession(BaseModel):
    task_id: str
    start_time: datetime
    end_time: datetime
    completed: bool

tasks = [
{
"id": 1,
"title": "Nauka FastAPI",
"description": "Przygotować przykładowe API z dokumentacją",
"status": "TODO",
}
]
# Tablica dla timerów Pomodoro
pomodoro_sessions = [
{
"task_id": 1,
"start_time": "2025-01-09T12:00:00",
"end_time": "2025-01-09T12:25:00",
"completed": True,
}
]
@app.route('/')
@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    if any(t["title"] == task.title for t in tasks):
        raise HTTPException(status_code=400, detail="Task name must be unique.")
    new_task = {
        "id": max(t["id"] for t in tasks) + 1 if tasks else 1,
        "title": task.title,
        "description": task.description,
        "status": "TODO",
    }
    tasks.append(new_task)
    return new_task
@app.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[str] = Query(None, regex="^(TODO|IN_PROGRESS|DONE)$")):
    if status:
        return [task for task in tasks if task["status"] == status]
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, task_update: TaskCreate):
    for task in tasks:
        if task["id"] == task_id:
            if any(t["title"] == task_update.title and t["id"] != task_id for t in tasks):
                raise HTTPException(status_code=400, detail="Task name must be unique.")
            task["title"] = task_update.title
            task["description"] = task_update.description
            return task
    raise HTTPException(status_code=404, detail="Task not found.")

@app.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: str):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return {"message": "Task deleted ."}
    raise HTTPException(status_code=404, detail="Task not found.")

@app.post("/pomodoro", response_model=PomodoroSession)
def create_pomodoro_session(task_id: str):
    if not any(task["id"] == task_id for task in tasks):
        raise HTTPException(status_code=404, detail="Task not found.")
    if any(session["task_id"] == task_id and not session["completed"] for session in pomodoro_sessions):
        raise HTTPException(status_code=400, detail="Active Pomodoro session already exists for this task.")
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=25)
    session = {
        "task_id": task_id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "completed": False,
    }
    pomodoro_sessions.append(session)
    return session

@app.post("/pomodoro/{task_id}/stop", response_model=dict)
def stop_pomodoro_session(task_id: str):
    for session in pomodoro_sessions:
        if session["task_id"] == task_id and not session["completed"]:
            session["completed"] = True
            return {"message": "Pomodoro session stopped."}
    raise HTTPException(status_code=400, detail="No active Pomodoro session for this task.")

@app.get("/pomodoro/stats", response_model=dict)
def get_pomodoro_stats():
    stats = {}
    total_time = timedelta()
    for session in pomodoro_sessions:
        if session["completed"]:
            stats[session["task_id"]] = stats.get(session["task_id"], 0) + 1
            total_time += datetime.fromisoformat(session["end_time"]) - datetime.fromisoformat(session["start_time"])
    return {"sessions": stats, "total_time": total_time.total_seconds() // 60}