from flask import request, jsonify
from app import app
from db import get_connection
from datetime import datetime


@app.route('/api/utilisation', methods=['GET'])
def resource_utilisation_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"error": "start_date and end_date are required"}), 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            r.resource_id,
            r.resource_name,
            IFNULL(SUM(
                TIMESTAMPDIFF(
                    HOUR,
                    GREATEST(e.start_time, %s),
                    LEAST(e.end_time, %s)
                )
            ), 0) AS total_hours_used
        FROM Resource r
        LEFT JOIN EventResourceAllocation a 
            ON r.resource_id = a.resource_id
        LEFT JOIN Event e 
            ON a.event_id = e.event_id
            AND e.start_time < %s
            AND e.end_time > %s
        GROUP BY r.resource_id, r.resource_name
        ORDER BY r.resource_name
    """, (start_date, end_date, end_date, start_date))

    utilisation_data = cur.fetchall()

    for row in utilisation_data:
        cur.execute("""
            SELECT COUNT(*) AS upcoming_count
            FROM EventResourceAllocation a
            JOIN Event e ON a.event_id = e.event_id
            WHERE a.resource_id = %s
            AND e.start_time > NOW()
        """, (row["resource_id"],))

        row["upcoming_bookings"] = cur.fetchone()["upcoming_count"]

    conn.close()

    return jsonify(utilisation_data)
