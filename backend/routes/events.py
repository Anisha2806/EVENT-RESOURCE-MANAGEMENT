from flask import Blueprint, jsonify, request
from db import get_connection
from datetime import datetime

events_bp = Blueprint('events', __name__)


def validate_event_resources(event_id, resource_ids, start_time, end_time):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    conflicts = []
    for rid in resource_ids:
        sql = """
        SELECT e.event_id, e.title, e.start_time, e.end_time
        FROM EventResourceAllocation a
        JOIN Event e ON a.event_id = e.event_id
        WHERE a.resource_id = %s
        AND e.start_time < %s
        AND e.end_time > %s
        """
        params = (rid, end_time, start_time)
        if event_id:
            sql += " AND e.event_id != %s"
            params += (event_id,)
        cur.execute(sql, params)
        row = cur.fetchone()
        if row:
            conflicts.append({
                "resource_id": rid,
                "event_id": row["event_id"],
                "event_title": row["title"],
                "start_time": row["start_time"].isoformat(),
                "end_time": row["end_time"].isoformat()
            })

    conn.close()
    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts
    }


@events_bp.route('/', methods=['GET'])
def get_events():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM event ORDER BY START_TIME ")
    events = cur.fetchall()
    conn.close()
    return jsonify(events)


@events_bp.route("/<int:event_id>", methods=["GET"])
def get_event(event_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM event WHERE EVENT_ID=%s", (event_id,))
    event = cur.fetchone()
    conn.close()
    if event:
        return jsonify(event)
    else:
        return jsonify({"message": "Event not found"}), 404


@events_bp.route("/", methods=["POST"])
def create_event():
    data = request.get_json()
    if not data.get("TITLE") or not data.get("START_TIME") or not data.get("END_TIME"):
        return jsonify({"message": "Event name, start time and end time are required"}), 400

    try:
        start_time = datetime.fromisoformat(data["START_TIME"])
        end_time = datetime.fromisoformat(data["END_TIME"])
    except ValueError:
        return jsonify({"message": "Invalid date format."}), 400

    if start_time >= end_time:
        return jsonify({"message": "Start time must be before end time."}), 400

    resource_ids = data.get("resource_ids", [])
    if resource_ids:
        # FIX: pass None for event_id because this is creation of a new event
        validation = validate_event_resources(None, resource_ids, start_time, end_time)
        if not validation["valid"]:
            return jsonify({
                "error": "resource conflict detected",
                "conflicts": validation["conflicts"]
            }), 409

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO event (TITLE, START_TIME, END_TIME, DESCRIPTION) VALUES (%s, %s, %s, %s)",
        (data["TITLE"], start_time, end_time, data.get("DESCRIPTION", ""))
    )
    event_id = cur.lastrowid
    for rid in resource_ids:
        cur.execute(
            "INSERT INTO eventresourceallocation (EVENT_ID, RESOURCE_ID) VALUES (%s, %s)",
            (event_id, rid)
        )
    conn.commit()
    conn.close()
    return jsonify({"event_id": event_id, "message": "Event created successfully"}), 201

@events_bp.route("/<int:event_id>",methods=["PUT"])
def update_event(event_id):
    data=request.get_json()
    conn=get_connection()
    cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM event WHERE EVENT_ID=%s",(event_id,))
    event=cur.fetchone()    
    if not event:
        conn.close()
        return jsonify({"message":"Event not found"}),404
    
    start_time=event["start_time"]
    end_time=event["end_time"]
    if data.get("start_time"):
        try:
            start_time=datetime.fromisoformat(data["start_time"])
        except ValueError:
            conn.close()
            return jsonify({"message":"Invalid start time format."}),400
    if data.get("end_time"):
        try:
            end_time=datetime.fromisoformat(data["end_time"])
        except ValueError:
            conn.close()
            return jsonify({"message":"Invalid end time format."}),400
        
    if start_time >= end_time:
        conn.close()
        return jsonify({"message":"Start time must be before end time."}),400
    
    resource_ids=data.get("resource_ids")
    if resource_ids is not None:
        validation=validate_event_resources(event_id,resource_ids,start_time,end_time)
        if not validation["valid"]:
            conn.close()
            return jsonify({
                "error":"resource conflict detected",
                "conflicts":validation["conflicts"]
            }),409
        cur.execute("DELETE FROM eventresourceallocation WHERE EVENT_ID=%s",(event_id,))
        for rid in resource_ids:
            cur.execute(
                "INSERT INTO eventresourceallocation (EVENT_ID, RESOURCE_ID) VALUES (%s, %s)",
                (event_id, rid)
            )
    title=data.get("TITLE",event["TITLE"])
    description=data.get("DESCRIPTION",event["DESCRIPTION"])
    cur.execute(
        "UPDATE event SET TITLE=%s, START_TIME=%s, END_TIME=%s, DESCRIPTION=%s WHERE EVENT_ID=%s",
        (title, start_time, end_time, description, event_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"message":"Event updated successfully"})

@events_bp.route("/<int:event_id>",methods=["DELETE"])
def delete_event(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Event WHERE event_id=%s", (event_id,))
    if cur.rowcount == 0:
        conn.close()
        return jsonify({"error": "Event not found"}), 404
    cur.execute("DELETE FROM EventResourceAllocation WHERE event_id=%s", (event_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Event deleted successfully"})