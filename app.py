import os
import uuid
import psycopg2
from flask import Flask, request, jsonify, render_template_string


app = Flask(__name__)

def get_conn():
    conn_str = os.environ["POSTGRESQLCONNSTR_default"]

    # Convert Azure format → dict
    settings = dict(item.split("=") for item in conn_str.split(";") if item)

    return psycopg2.connect(
        host=settings["Host"],
        database=settings["Database"],
        user=settings["Username"],
        password=settings["Password"],
        sslmode="require"
    )


@app.route("/")
def home():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT userid, COUNT(*) FROM items GROUP BY userid")
            rows = cur.fetchall()

    html = """
    <h1>Users</h1>
    <ul>
    {% for u in users %}
      <li>{{ u[0] }} — {{ u[1] }} items</li>
    {% endfor %}
    </ul>
    """

    return render_template_string(html, users=rows)



@app.route("/items", methods=["POST"])
def create_item():
    data = request.json
    item_id = str(uuid.uuid4())

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO items (id, userid, name) VALUES (%s, %s, %s)",
                (item_id, data["userId"], data["name"])
            )

    return jsonify({"id": item_id})


@app.route("/items/<user_id>")
def get_items(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, createdat FROM items WHERE userid=%s",
                (user_id,)
            )
            rows = cur.fetchall()

    return jsonify([
        {"id": str(r[0]), "name": r[1], "createdAt": r[2].isoformat()}
        for r in rows
    ])


if __name__ == "__main__":
    app.run()
