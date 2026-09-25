from fastapi import FastAPI, status, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from models import CreateUserRequest, UserResponse, UpdateUserResponse, BusinessException, TableInfo, TableListResponse, QueryResponse

from contextlib import asynccontextmanager
from database import init_db, close_db, get_db, get_raw_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()

app = FastAPI(
    title="Week 1 API",
    description="FastAPI demo — Spring Boot bridge",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/dummy")
def get_dummy():
    return {"status": "dummy endpoint"}

# Path parameter — same as @PathVariable in Spring
@app.get("/items/{item_id}")
def get_item(item_id: int):          # type hint = automatic validation
    return {"item_id": item_id, "name": f"Item {item_id}"}

# Query parameter — same as @RequestParam in Spring
@app.get("/search")
def search_items(
    query: str,                      # required — no default
    limit: int = 10,                 # optional — has default
    offset: int = 0
):
    return {
        "query": query,
        "limit": limit,
        "offset": offset,
        "results": []
    }

FAKE_ITEMS_LIST = [
    {"id": 1, "name": "Laptop",     "category": "electronics", "in_stock": True},
    {"id": 2, "name": "Desk Chair", "category": "furniture",   "in_stock": False},
    {"id": 3, "name": "Keyboard",   "category": "electronics", "in_stock": False},
]

@app.get("/items")
def get_items(
    category: str = None,  
    in_stock: bool = True
):
    results = FAKE_ITEMS_LIST

    if category is not None:
        results = [item for item in results if item["category"] == category]

    results = [item for item in results if item["in_stock"] == in_stock]

    return {"items": results, "count": len(results)}

_fake_db: dict[int, dict] = {}
_next_id = 1

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_200_OK)
def create_user(request: CreateUserRequest):
    global _next_id

    user = {
        "id": _next_id,
        "name": request.name,
        "email": request.email,
        "age": request.age
    }

    _fake_db[_next_id] = user
    _next_id += 1

    return user

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    if user_id not in _fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return _fake_db[user_id]

@app.put("/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
def update_user(user_id: int, request: UpdateUserResponse):
    if user_id not in _fake_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    
    existing_user = _fake_db[user_id]

    updated_user = request.model_dump(exclude_unset=True)

    existing_user.update(updated_user)

    _fake_db[user_id] = existing_user

    return existing_user

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exception: BusinessException):
    return JSONResponse(status_code=400, content={"error_code": exception.code, "message": exception.message})

@app.get("/trigger-error")
def trigger_error():
    return BusinessException(
        message="Something went Wrong",
        code="USER_INACTIVE"
    )


@app.get("/vantage/tables", response_model=TableListResponse)
def list_tables(db=Depends(get_db)):
    result = db("""
        SELECT TableName, TableKind
        FROM DBC.TablesV
        WHERE DatabaseName = 'demo_user'
    """)

    rows = result.fetchall()

    tables = [
        {"table_name": row[0], "table_kind": row[1]}
        for row in rows
    ]

    return {
        "tables": tables,
        "count": len(tables),
        "database": "demo_user"
    }

@app.get("/vantage/tables/{table_name}", response_model=QueryResponse)
def get_table_details(table_name: str, limit: int = 5):
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid table name. Only letter, numbers and underscore allowed."
        )

    limit = max(1, min(limit, 100))

    try:

        conn = get_raw_connection()
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT TOP {limit} * FROM demo_user.{table_name}"
        )

        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        sample = [dict(zip(columns, row)) for row in rows]

        cursor.execute(
            f"SELECT COUNT(*) FROM demo_user.{table_name}"
        )

        row_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "table": table_name,
            "row_count": row_count,
            "columns": columns,
            "sample_rows": sample
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )

@app.get("/vantage/version")
def db_version(db=Depends(get_db)):
    result = db(
        "SELECT InfoData FROM DBC.DBCInfoV WHERE InfoKey = 'VERSION'"
    )
    row = result.fetchone()
    version = row[0].strip() if row else "unknown"
    return {"version": version, "status": "connected"}

@app.post("/db_users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_db_user(request: CreateUserRequest):
    try:
        conn = get_raw_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO demo_user.api_users(name, email, age) 
            VALUES(?,?,?)
        """, (request.name, request.email, request.age))

        conn.commit()

        # ── Fetch the row we just created ─────────────────────────
        # Teradata IDENTITY columns: fetch the latest for this session
        cursor.execute("""
            SELECT TOP 1 user_id, name, email, age, created_at
            FROM demo_user.api_users
            ORDER BY user_id DESC
        """)
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=500, detail="Insert appeared to succeed but row not found")

        return {
            "id":         row[0],
            "name":       row[1].strip(),
            "email":      row[2].strip(),
            "age":        row[3],
            "created_at": row[4]
        }


    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()  

@app.get("/db_users/{user_id}", response_model=UserResponse)
def get_db_user(user_id: int, db=Depends(get_db)):

    results = db(f"""
        SELECT user_id, name, email, age, created_at
        FROM demo_user.api_users
        WHERE user_id = {user_id}
    """)
    row = results.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
        
    
    return {
        "id":         row[0],
        "name":       row[1].strip(),
        "email":      row[2].strip(),
        "age":        row[3],
        "created_at": row[4]
    }