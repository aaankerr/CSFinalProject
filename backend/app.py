import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask import json
from flask import Response
import pymysql

# -------- DB helpers (no classes, just functions) -------- 
def get_conn():
    return pymysql.connect(
        host = os.getenv("MYSQL_HOST", "db"),
        user = os.getenv("MYSQL_USER", "user"),
        password = os.getenv("MYSQL_PASSWORD", "pass"),
        database = os.getenv("MYSQL_DATABASE", "groceries"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit = True
    )

def get_or_create_dept_id(dept_name):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM dept WHERE name=%s LIMIT 1", (dept_name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("INSERT INTO dept (name) VALUES (%s)", (dept_name,))
        return cur.lastrowid


def get_or_create_origin_id(origin_code = None):
    if not origin_code:
            origin_code = "MX"
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM origin WHERE name=%s LIMIT 1", (origin_code,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("INSERT INTO origin (name) VALUES (%s)", (origin_code,))
        return cur.lastrowid


def fetch_all_products():
    conn = get_conn()
    with conn.cursor() as cur:
        query = """ 
        SELECT p.id, p.name,
            d.name AS department,
            o.name AS origin,
            p.price,
            p.stock 
        FROM products p
        JOIN dept d ON p.dept_id = d.id
        JOIN origin o ON p.origin_id = o.id
        ORDER BY p.id;
        """
        cur.execute(query)
        return cur.fetchall()


def fetch_product(product_id):
    conn = get_conn()
    with conn.cursor() as cur:
        query = """ 
        SELECT p.id, p.name,
            d.name AS department,
            o.name AS origin,
            p.price,
            p.stock 
        FROM products p
        JOIN dept d ON p.dept_id = d.id
        JOIN origin o ON p.origin_id = o.id
        WHERE p.id = %s
        LIMIT 1;
        """
        cur.execute(query, (product_id,))
        return cur.fetchone()

def insert_product(name, department, origin, price, stock):
    dept_id = get_or_create_dept_id(department)
    origin_id = get_or_create_origin_id(origin)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT into products (name, dept_id, origin_id, price, stock)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, dept_id, origin_id, price, stock)
        )
        return cur.lastrowid


def update_product(product_id, name, department, origin, price, stock):
    dept_id = get_or_create_dept_id(department)
    origin_id = get_or_create_origin_id(origin)
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE products
            SET name = %s, dept_id = %s, origin_id = %s, price = %s, stock = %s
            WHERE id=%s
        """, (name, dept_id, origin_id, price, stock, product_id)
        )
        return cur.rowcount


def delete_product(product_id):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
        DELETE FROM products WHERE id=%s
        """, (product_id,)
        )
        return cur.rowcount


# --- Helpers to list departments and origins ---
def fetch_departments():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM dept ORDER BY name")
        return cur.fetchall()


def fetch_origins():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name AS code FROM origin ORDER BY name")
        return cur.fetchall()


# -------- Flask app --------
app = Flask(_name_, static_folder="static", static_url_path="")
CORS(app)  # allow front-end JS to call API

# Serve the static index
@app.route("/")
def root():
    return send_from_directory("static", "index.html")


# -------- REST API (only instructional messages here) --------
@app.get("/api/items")
def api_list_items():
    products = fetch_all_products()
    return jsonify(products)

@app.get("/api/items/<int:product_id>")
def api_get_item(product_id):
    product = fetch_product(product_id)
    return jsonify(product)

@app.post("/api/items")
def api_create_item():
    data = request.get_json(force=True)
    new_id = insert_product(
        data["name"],
        data["department"],
        data.get("origin"),
        float(data["price"]),
        int(data["stock"])
    )
    return jsonify(fetch_product(new_id))

@app.route("/api/items/<int:product_id>", methods=["PUT"])
def api_update_item(product_id):
    data = request.get_json(force=True)
    update_product(
        product_id,
        data["name"],
        data["department"],
        data.get("origin"),
        float(data["price"]),
        int(data["stock"])
    )
    return jsonify(fetch_product(product_id))

@app.delete("/api/items/<int:product_id>")
def api_delete_item(product_id):
    del_product = delete_product(product_id)
    return jsonify(del_product)

@app.get("/api/departments")
def api_departments():
    departments = fetch_departments()
    return jsonify(departments)

@app.get("/api/origins")
def api_origins():
    origin = fetch_origins()
    return jsonify(origin)


if _name_ == "_main_":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

