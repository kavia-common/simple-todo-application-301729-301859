from typing import List

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import get_db, init_db
from .models import TodoCreate, TodoOut, TodoUpdate

# Initialize DB schema on startup
init_db()

app = FastAPI(
    title="Todo API",
    description="FastAPI backend for a simple Todo application with SQLite persistence. "
                "Provides endpoints to create, list, update (including toggle completion), and delete tasks.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Health", "description": "Basic service health checks."},
        {"name": "Todos", "description": "Operations for managing todo items."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production consider scoping to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Health Check", description="Simple health check endpoint.")
def health_check():
    """Health check endpoint returning a basic status message."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/todos",
    response_model=List[TodoOut],
    tags=["Todos"],
    summary="List all todos",
    description="Returns a list of all todo items.",
)
def list_todos():
    """List all todo items in the database."""
    with get_db() as conn:
        cur = conn.execute(
            "SELECT id, title, completed, created_at, updated_at FROM todos ORDER BY id DESC"
        )
        rows = cur.fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "completed": bool(row["completed"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


# PUBLIC_INTERFACE
@app.post(
    "/todos",
    response_model=TodoOut,
    status_code=201,
    tags=["Todos"],
    summary="Create a new todo",
    description="Creates a new todo item and returns it.",
)
def create_todo(todo: TodoCreate):
    """Create a new todo item."""
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO todos (title, completed) VALUES (?, ?)",
            (todo.title.strip(), 1 if todo.completed else 0),
        )
        new_id = cur.lastrowid
        cur = conn.execute(
            "SELECT id, title, completed, created_at, updated_at FROM todos WHERE id = ?",
            (new_id,),
        )
        row = cur.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


# PUBLIC_INTERFACE
@app.get(
    "/todos/{todo_id}",
    response_model=TodoOut,
    tags=["Todos"],
    summary="Get a single todo",
    description="Fetch a single todo item by its ID.",
)
def get_todo(todo_id: int = Path(..., description="ID of the todo to fetch")):
    """Get a todo by ID."""
    with get_db() as conn:
        cur = conn.execute(
            "SELECT id, title, completed, created_at, updated_at FROM todos WHERE id = ?",
            (todo_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


# PUBLIC_INTERFACE
@app.patch(
    "/todos/{todo_id}",
    response_model=TodoOut,
    tags=["Todos"],
    summary="Update a todo",
    description="Update one or more fields of a todo item. Provide any combination of 'title' and 'completed'.",
)
def update_todo(todo_id: int, todo: TodoUpdate):
    """Update an existing todo item."""
    if todo.title is None and todo.completed is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    fields = []
    params = []
    if todo.title is not None:
        fields.append("title = ?")
        params.append(todo.title.strip())
    if todo.completed is not None:
        fields.append("completed = ?")
        params.append(1 if todo.completed else 0)

    fields.append("updated_at = datetime('now')")
    set_clause = ", ".join(fields)

    with get_db() as conn:
        # Ensure the record exists
        cur = conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")

        conn.execute(f"UPDATE todos SET {set_clause} WHERE id = ?", (*params, todo_id))
        cur = conn.execute(
            "SELECT id, title, completed, created_at, updated_at FROM todos WHERE id = ?",
            (todo_id,),
        )
        row = cur.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


# PUBLIC_INTERFACE
@app.post(
    "/todos/{todo_id}/toggle",
    response_model=TodoOut,
    tags=["Todos"],
    summary="Toggle completion status",
    description="Toggles the 'completed' status of a todo item.",
)
def toggle_todo(todo_id: int):
    """Toggle the completion status of a todo item."""
    with get_db() as conn:
        cur = conn.execute("SELECT completed FROM todos WHERE id = ?", (todo_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        new_completed = 0 if row["completed"] else 1
        conn.execute(
            "UPDATE todos SET completed = ?, updated_at = datetime('now') WHERE id = ?",
            (new_completed, todo_id),
        )
        cur = conn.execute(
            "SELECT id, title, completed, created_at, updated_at FROM todos WHERE id = ?",
            (todo_id,),
        )
        row = cur.fetchone()
        return {
            "id": row["id"],
            "title": row["title"],
            "completed": bool(row["completed"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


# PUBLIC_INTERFACE
@app.delete(
    "/todos/{todo_id}",
    status_code=204,
    tags=["Todos"],
    summary="Delete a todo",
    description="Deletes a todo item by its ID.",
)
def delete_todo(todo_id: int):
    """Delete a todo by ID."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo not found")
    return JSONResponse(status_code=204, content=None)
