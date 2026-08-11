from flask import request, jsonify

from config import ADMIN_API_KEY
from database import get_connection


def check_admin():
    key = request.headers.get("X-Admin-Key", "")

    if not ADMIN_API_KEY or key != ADMIN_API_KEY:
        return False

    return True


def get_drivers():
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        name,
                        phone,
                        login,
                        car_model,
                        car_number,
                        approved,
                        online,
                        balance
                    FROM drivers
                    ORDER BY id DESC
                """)

                rows = cur.fetchall()

        drivers = []

        for driver in rows:
            drivers.append({
                "id": driver[0],
                "name": driver[1],
                "phone": driver[2],
                "login": driver[3],
                "car_model": driver[4],
                "car_number": driver[5],
                "approved": driver[6],
                "online": driver[7],
                "balance": float(driver[8])
            })

        return jsonify({
            "success": True,
            "drivers": drivers
        })

    except Exception as e:
        print("Get drivers error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def approve_driver(driver_id):
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE drivers
                    SET approved = TRUE
                    WHERE id = %s
                    RETURNING id, name, approved
                """, (driver_id,))

                driver = cur.fetchone()

        if not driver:
            return jsonify({
                "success": False,
                "message": "Haydovchi topilmadi"
            }), 404

        return jsonify({
            "success": True,
            "message": "Haydovchi tasdiqlandi",
            "driver": {
                "id": driver[0],
                "name": driver[1],
                "approved": driver[2]
            }
        })

    except Exception as e:
        print("Approve driver error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def reject_driver(driver_id):
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE drivers
                    SET
                        approved = FALSE,
                        online = FALSE
                    WHERE id = %s
                    RETURNING id, name
                """, (driver_id,))

                driver = cur.fetchone()

        if not driver:
            return jsonify({
                "success": False,
                "message": "Haydovchi topilmadi"
            }), 404

        return jsonify({
            "success": True,
            "message": "Haydovchi rad etildi",
            "driver": {
                "id": driver[0],
                "name": driver[1],
                "approved": False,
                "online": False
            }
        })

    except Exception as e:
        print("Reject driver error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500
