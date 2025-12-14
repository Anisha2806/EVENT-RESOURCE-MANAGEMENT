
print("Resources routes loaded")

from app import app
from flask import request, jsonify
from db import get_connection


@app.route('/api/resources', methods=['GET'])
def get_resources():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM Resource")
    resources = cur.fetchall()

    conn.close()
    return jsonify(resources)



@app.route('/api/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM Resource WHERE resource_id = %s", (resource_id,))
    resource = cur.fetchone()

    conn.close()

    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    return jsonify(resource)


@app.route('/api/resources', methods=['POST'])
def create_resource():
    data = request.get_json()

    if not data.get("resource_name") or not data.get("resource_type"):
        return jsonify({"error": "resource_name and resource_type required"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO Resource (resource_name, resource_type) VALUES (%s, %s)",
        (data["resource_name"], data["resource_type"])
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Resource created"}), 201

@app.route('/api/resources/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    data = request.get_json()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE Resource SET resource_name=%s, resource_type=%s WHERE resource_id=%s",
        (data.get("resource_name"), data.get("resource_type"), resource_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Resource updated"})

@app.route('/api/resources/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM Resource WHERE resource_id=%s", (resource_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Resource deleted"})
