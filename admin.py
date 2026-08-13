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


def get_topup_requests():
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
                        p.id,
                        p.driver_id,
                        d.name,
                        d.phone,
                        p.amount,
                        p.card_number,
                        p.status,
                        p.created_at,
                        p.processed_at,
                        p.processed_by
                    FROM balance_topup_requests p
                    JOIN drivers d ON d.id = p.driver_id
                    ORDER BY p.id DESC
                """)

                rows = cur.fetchall()

        requests = []

        for row in rows:
            requests.append({
                "id": row[0],
                "driver_id": row[1],
                "driver_name": row[2],
                "driver_phone": row[3],
                "amount": float(row[4]),
                "card_number": row[5],
                "status": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "processed_at": row[8].isoformat() if row[8] else None,
                "processed_by": row[9]
            })

        return jsonify({
            "success": True,
            "requests": requests
        })

    except Exception as e:
        print("Get topup requests error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def approve_topup_request(payment_id):
    if not check_admin():
        return jsonify({
            "success": False,
            "message": "Admin ruxsati rad etildi"
        }), 401

    try:
        payment_id = int(payment_id)

        admin_key = request.headers.get("X-Admin-Key", "")

        with get_connection() as conn:
            with conn.cursor() as cur:

                # Faqat PENDING so‘rovni bloklab olamiz.
                # Shu sababli bir so‘rov ikki marta tasdiqlanmaydi.
                cur.execute("""
                    SELECT
                        id,
                        driver_id,
                        amount,
                        status
                    FROM balance_topup_requests
                    WHERE id = %s
                    FOR UPDATE
                """, (payment_id,))

                payment = cur.fetchone()

                if not payment:
                    return jsonify({
                        "success": False,
                        "message": "To‘lov so‘rovi topilmadi"
                    }), 404

                if payment[3] != "PENDING":
                    return jsonify({
                        "success": False,
                        "message": "Bu to‘lov so‘rovi allaqachon qayta ishlangan",
                        "status": payment[3]
                    }), 409

                # Balansni oshiramiz.
                cur.execute("""
                    UPDATE drivers
                    SET balance = balance + %s
                    WHERE id = %s
                    RETURNING id, name, balance
                """, (
                    payment[2],
                    payment[1]
                ))

                driver = cur.fetchone()

                if not driver:
                    return jsonify({
                        "success": False,
                        "message": "Haydovchi topilmadi"
                    }), 404

                # To‘lovni tasdiqlaymiz.
                cur.execute("""
                    UPDATE balance_topup_requests
                    SET
                        status = 'APPROVED',
                        processed_at = CURRENT_TIMESTAMP,
                        processed_by = %s
                    WHERE id = %s
                """, (
                    admin_key,
                    payment_id
                ))

        return jsonify({
            "success": True,
            "message": "To‘lov tasdiqlandi va balans to‘ldirildi",
            "payment_id": payment_id,
            "driver": {
                "id": driver[0],
                "name": driver[1],
                "balance": float(driver[2])
            }
        }), 200

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "payment_id noto‘g‘ri"
        }), 400

    except Exception as e:
        print("Approve topup error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500
