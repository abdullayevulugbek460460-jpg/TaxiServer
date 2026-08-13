import os
from flask import request, jsonify

from database import get_connection


PAYMENT_CARD_NUMBER = os.environ.get(
    "PAYMENT_CARD_NUMBER",
    ""
)


def create_topup_request():
    data = request.get_json(silent=True) or {}

    if "driver_id" not in data or "amount" not in data:
        return jsonify({
            "success": False,
            "message": "driver_id va amount majburiy"
        }), 400

    try:
        driver_id = int(data["driver_id"])
        amount = float(data["amount"])
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "driver_id yoki amount noto‘g‘ri"
        }), 400

    if driver_id <= 0:
        return jsonify({
            "success": False,
            "message": "driver_id noto‘g‘ri"
        }), 400

    if amount <= 0:
        return jsonify({
            "success": False,
            "message": "To‘lov summasi 0 dan katta bo‘lishi kerak"
        }), 400

    if not PAYMENT_CARD_NUMBER:
        return jsonify({
            "success": False,
            "message": "To‘lov kartasi sozlanmagan"
        }), 500

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id, name, phone
                    FROM drivers
                    WHERE id = %s
                """, (driver_id,))

                driver = cur.fetchone()

                if not driver:
                    return jsonify({
                        "success": False,
                        "message": "Haydovchi topilmadi"
                    }), 404

                cur.execute("""
                    INSERT INTO balance_topup_requests (
                        driver_id,
                        amount,
                        card_number,
                        status
                    )
                    VALUES (%s, %s, %s, 'PENDING')
                    RETURNING id, amount, status, created_at
                """, (
                    driver_id,
                    amount,
                    PAYMENT_CARD_NUMBER
                ))

                payment = cur.fetchone()

        return jsonify({
            "success": True,
            "message": "To‘lov so‘rovi yaratildi",
            "payment": {
                "id": payment[0],
                "amount": float(payment[1]),
                "status": payment[2],
                "created_at": payment[3].isoformat()
            },
            "payment_card": PAYMENT_CARD_NUMBER
        }), 201

    except Exception as e:
        print("Create topup error:", e)

        return jsonify({
            "success": False,
            "message": "To‘lov so‘rovini yaratib bo‘lmadi"
        }), 500


def get_driver_balance():
    driver_id = request.args.get("driver_id", type=int)

    if not driver_id or driver_id <= 0:
        return jsonify({
            "success": False,
            "message": "driver_id noto‘g‘ri"
        }), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, balance
                    FROM drivers
                    WHERE id = %s
                """, (driver_id,))

                driver = cur.fetchone()

        if not driver:
            return jsonify({
                "success": False,
                "message": "Haydovchi topilmadi"
            }), 404

        return jsonify({
            "success": True,
            "driver": {
                "id": driver[0],
                "name": driver[1],
                "balance": float(driver[2] or 0)
            }
        })

    except Exception as e:
        print("Get driver balance error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500
