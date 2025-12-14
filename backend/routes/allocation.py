from flask import request, jsonify
from app import app
from db import get_connection
from datetime import datetime

def is_overlap(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1

@app.route('/api/allocations', methods=['POST'])

def allocate_resources():
    data=request.get_json()
    event_id=data.get("event_id")
    resource_id=data.get("resource_id")

    if not event_id or not resource_id:
        return jsonify({"error":"event_id and resource_id are required"}),400

    conn=get_connection()
    cur=conn.cursor(dictionary=True)

    cur.execute(
    "SELECT start_time, end_time FROM Event WHERE event_id = %s",
    (event_id,)
    )
    event=cur.fetchone()
    if not event:
        conn.close()
        return jsonify({"error":"Event not found"}),404
    
    cur.execute("""   SELECT e.event_id
        FROM EventResourceAllocation a
        JOIN Event e ON a.event_id = e.event_id
        WHERE a.resource_id = %s
        AND e.start_time < %s
        AND e.end_time > %s
    """, (resource_id, event["end_time"], event["start_time"]))

    conflict=cur.fetchone()
    if conflict:
        conn.close()
        return jsonify({"error": "Resource already booked"}), 409
    
    cur.execute("INSERT INTO EventResourceAllocation (event_id, resource_id) VALUES (%s, %s)", (event_id, resource_id))
    conn.commit()
    conn.close()

    return jsonify({"message":"Resource allocated successfully"}),201