from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from uuid import uuid4
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

tasks: Dict[str, Task] = {}
pomodoro_sessions: List[PomodoroSession] = []
@app.route('/')
@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    if any(t.title == task.title for t in task.values()):
        raise HTTPException(status_code=400, detail="Task name must be unique")
    task_id = str(uuid4())
    new_task = Task(id = task_id, title = task.title, description = task.description, status = task.status)
    tasks[task_id] = new_task
    return new_task
@app.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[str] = Query(regex="^(None,TODO|IN_PROGRESS|DONE)$")):
    if status:
        return [task for task in tasks.values() if task.status == status]
    return list(tasks.values())
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, task_update: TaskCreate):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    if any(t.title == task_update.title and t.id != task_id for t in tasks.values()):
        raise HTTPException(status_code=400, detail="Task name must be unique")
    tasks[task_id].title = task_update.title
    tasks[task_id].description = task_update.description
    tasks[task_id].status = task_update.status
    return tasks[task_id]
@app.delete("/tasks/{task_id}", response_model=dict)
def delete_task(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id]
    return {"message": "Task deleted"}

@app.post("/pomodoro", response_model=PomodoroSession)
def create_pomodoro_session(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    if any(session.task_id == task_id and session.end_time > datetime.utcnow() for session in pomodoro_sessions):
        raise HTTPException(status_code=400, detail="Active Pomodoro session already exists for this task.")
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(minutes=25)
    session = PomodoroSession(task_id=task_id, start_time=start_time, end_time=end_time, completed=False)
    pomodoro_sessions.append(session)
    return session
@app.post("/pomodoro/{task_id}/stop", response_model=dict)
def stop_pomodoro_session(task_id: str):
    for session in pomodoro_sessions:
        if session.task_id == task_id and not session.completed:
            session.completed = True
            return {"message": "Pomodoro session stopped"}
        raise HTTPException(status_code=400, detail="No active pomodoro session for this task")
@app.get("/pomodoro/stats", response_model=dict)
def get_pomodoro_stats():
    stats = {}
    total_time = timedelta()
    for session in pomodoro_sessions:
        if session.completed:
            stats[session.task_id] = stats.get(session.task_id, 0) + 1
            total_time += session.end_time - session.start_time
    return {"sessions": stats, "total_time": total_time.total_seconds() // 60}
