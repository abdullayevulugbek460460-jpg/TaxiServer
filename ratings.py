from flask import jsonify, request
from database import get_connection


def submit_driver_rating():
    data = request.get_json(silent=True) or {}

    driver_id = int(data.get("driver_id", 0))
    order_id = int(data.get("order_id", 0))
    rating = int(data.get("rating", 0))

    if driver_id <= 0 or order_id <= 0:
        return jsonify({
            "success": False,
            "message": "driver_id va order_id kerak"
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "success": False,
            "message": "Reyting 1 dan 5 gacha bo‘lishi kerak"
        }), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT driver_id, status
                    FROM orders
                    WHERE id = %s
                """, (order_id,))

                order = cur.fetchone()

                if not order:
                    return jsonify({
                        "success": False,
                        "message": "Buyurtma topilmadi"
                    }), 404

                if int(order[0]) != driver_id:
                    return jsonify({
                        "success": False,
                        "message": "Bu buyurtma ushbu haydovchiga tegishli emas"
                    }), 403

                if str(order[1]).upper() != "COMPLETED":
                    return jsonify({
                        "success": False,
                        "message": "Faqat yakunlangan buyurtmaga baho berish mumkin"
                    }), 400

                cur.execute("""
                    INSERT INTO driver_ratings
                        (driver_id, order_id, rating)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (driver_id, order_id)
                    DO UPDATE SET rating = EXCLUDED.rating
                """, (driver_id, order_id, rating))

                conn.commit()

                cur.execute("""
                    SELECT
                        COALESCE(AVG(rating), 0),
                        COUNT(*)
                    FROM driver_ratings
                    WHERE driver_id = %s
                """, (driver_id,))

                result = cur.fetchone()

                average_rating = float(result[0] or 0)
                rating_count = int(result[1] or 0)

                return jsonify({
                    "success": True,
                    "rating": round(average_rating, 2),
                    "rating_count": rating_count
                })

    except Exception as e:
        print("Rating error:", e)
        return jsonify({
            "success": False,
            "message": "Reytingni saqlashda server xatosi"
        }), 500


def get_driver_profile():
    driver_id = request.args.get("driver_id", type=int)

    if not driver_id or driver_id <= 0:
        return jsonify({
            "success": False,
            "message": "driver_id kerak"
        }), 400

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
                    WHERE id = %s
                """, (driver_id,))

                driver = cur.fetchone()

                if not driver:
                    return jsonify({
                        "success": False,
                        "message": "Haydovchi topilmadi"
                    }), 404

                cur.execute("""
                    SELECT
                        COALESCE(AVG(rating), 0),
                        COUNT(*)
                    FROM driver_ratings
                    WHERE driver_id = %s
                """, (driver_id,))

                rating_data = cur.fetchone()

                average_rating = float(rating_data[0] or 0)
                rating_count = int(rating_data[1] or 0)

                cur.execute("""
                    SELECT COUNT(*)
                    FROM orders
                    WHERE driver_id = %s
                      AND UPPER(status) = 'COMPLETED'
                """, (driver_id,))

                completed_orders = int(cur.fetchone()[0] or 0)

                return jsonify({
                    "success": True,
                    "driver": {
                        "id": driver[0],
                        "name": driver[1],
                        "phone": driver[2],
                        "login": driver[3],
                        "car_model": driver[4],
                        "car_number": driver[5],
                        "approved": driver[6],
                        "online": driver[7],
                        "balance": float(driver[8] or 0),
                        "rating": round(average_rating, 2),
                        "rating_count": rating_count,
                        "completed_orders": completed_orders
                    }
                })

    except Exception as e:
        print("Driver profile error:", e)
        return jsonify({
            "success": False,
            "message": "Profilni yuklashda server xatosi"
        }), 500
