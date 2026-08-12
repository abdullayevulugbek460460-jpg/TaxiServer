from flask import request, jsonify
import math
from database import get_connection


def create_order():
    data = request.get_json(silent=True) or {}

    required = [
        "passenger_id",
        "pickup_lat",
        "pickup_lng",
        "destination_lat",
        "destination_lng"
    ]

    for field in required:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"{field} majburiy"
            }), 400

    try:
        passenger_id = int(data["passenger_id"])
        pickup_lat = float(data["pickup_lat"])
        pickup_lng = float(data["pickup_lng"])
        destination_lat = float(data["destination_lat"])
        destination_lng = float(data["destination_lng"])

        # Masofani koordinatalardan avtomatik hisoblash (Haversine)
        lat1 = math.radians(pickup_lat)
        lon1 = math.radians(pickup_lng)
        lat2 = math.radians(destination_lat)
        lon2 = math.radians(destination_lng)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1)
            * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )

        distance_km = 6371.0 * 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        distance_km = round(distance_km, 2)

        # Tarif: boshlang'ich 5000 so'm + har km uchun 2000 so'm
        start_price = 5000
        price_per_km = 2000
        price = round(start_price + distance_km * price_per_km, 0)

        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE id = %s
                    """,
                    (passenger_id,)
                )

                passenger = cur.fetchone()

                if not passenger:
                    return jsonify({
                        "success": False,
                        "message": "Yo‘lovchi topilmadi"
                    }), 404

                cur.execute(
                    """
                    INSERT INTO orders (
                        passenger_id,
                        pickup_lat,
                        pickup_lng,
                        destination_lat,
                        destination_lng,
                        estimated_distance_km,
                        estimated_price,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'NEW')
                    RETURNING id
                    """,
                    (
                        passenger_id,
                        pickup_lat,
                        pickup_lng,
                        destination_lat,
                        destination_lng,
                        distance_km,
                        price
                    )
                )

                order_id = cur.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "Buyurtma yaratildi",
            "order": {
                "id": order_id,
                "passenger_id": passenger_id,
                "pickup_lat": pickup_lat,
                "pickup_lng": pickup_lng,
                "destination_lat": destination_lat,
                "destination_lng": destination_lng,
                "estimated_distance_km": distance_km,
                "estimated_price": price,
                "status": "NEW"
            }
        }), 201

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Ma'lumot formati noto‘g‘ri"
        }), 400

    except Exception as e:
        print("Create order error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def get_orders():
    driver_id = request.args.get("driver_id", type=int)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                if driver_id:
                    cur.execute(
                        """
                        SELECT
                            id,
                            passenger_id,
                            driver_id,
                            pickup_lat,
                            pickup_lng,
                            destination_lat,
                            destination_lng,
                            estimated_distance_km,
                            estimated_price,
                            status,
                            created_at,
                            updated_at
                        FROM orders
                        WHERE status = 'NEW'
                           OR driver_id = %s
                        ORDER BY id DESC
                        """,
                        (driver_id,)
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            id,
                            passenger_id,
                            driver_id,
                            pickup_lat,
                            pickup_lng,
                            destination_lat,
                            destination_lng,
                            estimated_distance_km,
                            estimated_price,
                            status,
                            created_at,
                            updated_at
                        FROM orders
                        ORDER BY id DESC
                        """
                    )

                rows = cur.fetchall()

        orders = []

        for row in rows:
            orders.append({
                "id": row[0],
                "passenger_id": row[1],
                "driver_id": row[2],
                "pickup_lat": row[3],
                "pickup_lng": row[4],
                "destination_lat": row[5],
                "destination_lng": row[6],
                "estimated_distance_km": float(row[7] or 0),
                "estimated_price": float(row[8] or 0),
                "status": row[9],
                "created_at": row[10].isoformat() if row[10] else None,
                "updated_at": row[11].isoformat() if row[11] else None
            })

        return jsonify({
            "success": True,
            "orders": orders
        }), 200

    except Exception as e:
        print("Get orders error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def accept_order():
    data = request.get_json(silent=True) or {}

    if "order_id" not in data or "driver_id" not in data:
        return jsonify({
            "success": False,
            "message": "order_id va driver_id majburiy"
        }), 400

    try:
        order_id = int(data["order_id"])
        driver_id = int(data["driver_id"])

        with get_connection() as conn:
            with conn.cursor() as cur:

                # Haydovchini tekshirish
                cur.execute(
                    """
                    SELECT id, approved, online
                    FROM drivers
                    WHERE id = %s
                    """,
                    (driver_id,)
                )

                driver = cur.fetchone()

                if not driver:
                    return jsonify({
                        "success": False,
                        "message": "Haydovchi topilmadi"
                    }), 404

                if not driver[1]:
                    return jsonify({
                        "success": False,
                        "message": "Haydovchi hali tasdiqlanmagan"
                    }), 403

                if not driver[2]:
                    return jsonify({
                        "success": False,
                        "message": "Haydovchi offline"
                    }), 403

                # ATOMIC ACCEPT:
                # Faqat status NEW bo'lgan buyurtmani olish mumkin.
                cur.execute(
                    """
                    UPDATE orders
                    SET
                        driver_id = %s,
                        status = 'ACCEPTED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND status = 'NEW'
                      AND driver_id IS NULL
                    RETURNING
                        id,
                        passenger_id,
                        driver_id,
                        pickup_lat,
                        pickup_lng,
                        destination_lat,
                        destination_lng,
                        estimated_distance_km,
                        estimated_price,
                        status,
                        created_at,
                        updated_at
                    """,
                    (driver_id, order_id)
                )

                order = cur.fetchone()

                if not order:
                    return jsonify({
                        "success": False,
                        "message": "Buyurtma mavjud emas yoki boshqa haydovchi allaqachon qabul qilgan"
                    }), 409

        return jsonify({
            "success": True,
            "message": "Buyurtma qabul qilindi",
            "order": {
                "id": order[0],
                "passenger_id": order[1],
                "driver_id": order[2],
                "pickup_lat": order[3],
                "pickup_lng": order[4],
                "destination_lat": order[5],
                "destination_lng": order[6],
                "estimated_distance_km": float(order[7] or 0),
                "estimated_price": float(order[8] or 0),
                "status": order[9],
                "created_at": order[10].isoformat() if order[10] else None,
                "updated_at": order[11].isoformat() if order[11] else None
            }
        }), 200

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "order_id yoki driver_id noto‘g‘ri"
        }), 400

    except Exception as e:
        print("Accept order error:", e)

def update_order_status():
    data = request.get_json(silent=True) or {}

    if "order_id" not in data or "driver_id" not in data or "status" not in data:
        return jsonify({
            "success": False,
            "message": "order_id, driver_id va status majburiy"
        }), 400

    try:
        order_id = int(data["order_id"])
        driver_id = int(data["driver_id"])
        new_status = str(data["status"]).upper().strip()

        allowed_statuses = {
            "ARRIVING": ["ACCEPTED"],
            "STARTED": ["ARRIVING"],
            "COMPLETED": ["STARTED"],
            "CANCELLED": ["NEW", "ACCEPTED", "ARRIVING"]
        }

        if new_status not in allowed_statuses:
            return jsonify({
                "success": False,
                "message": "Noto‘g‘ri status"
            }), 400

        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        driver_id,
                        status,
                        estimated_price
                    FROM orders
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (order_id,)
                )

                order = cur.fetchone()

                if not order:
                    return jsonify({
                        "success": False,
                        "message": "Buyurtma topilmadi"
                    }), 404

                current_driver_id = order[1]
                current_status = order[2]
                price = float(order[3] or 0)

                if current_driver_id != driver_id:
                    return jsonify({
                        "success": False,
                        "message": "Bu buyurtma sizga tegishli emas"
                    }), 403

                if current_status not in allowed_statuses[new_status]:
                    return jsonify({
                        "success": False,
                        "message": (
                            f"{current_status} holatidan "
                            f"{new_status} holatiga o‘tib bo‘lmaydi"
                        )
                    }), 409

                cur.execute(
                    """
                    UPDATE orders
                    SET
                        status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND driver_id = %s
                      AND status = %s
                    RETURNING id, driver_id, status
                    """,
                    (
                        new_status,
                        order_id,
                        driver_id,
                        current_status
                    )
                )

                updated = cur.fetchone()

                if not updated:
                    return jsonify({
                        "success": False,
                        "message": "Buyurtma holati o‘zgartirilmadi"
                    }), 409

                # COMPLETED bo‘lganda haydovchiga 90% daromad.
                # Har bir order uchun faqat bir marta hisoblanadi.
                if new_status == "COMPLETED":
                    commission = round(price * 0.10, 2)
                    driver_income = round(price - commission, 2)

                    cur.execute(
                        """
                        SELECT id
                        FROM driver_earnings
                        WHERE order_id = %s
                        FOR UPDATE
                        """,
                        (order_id,)
                    )

                    existing_earning = cur.fetchone()

                    if existing_earning:
                        return jsonify({
                            "success": False,
                            "message": "Bu buyurtma uchun daromad allaqachon hisoblangan"
                        }), 409

                    cur.execute(
                        """
                        UPDATE drivers
                        SET balance = balance + %s
                        WHERE id = %s
                        RETURNING id
                        """,
                        (driver_income, driver_id)
                    )

                    balance_updated = cur.fetchone()

                    if not balance_updated:
                        return jsonify({
                            "success": False,
                            "message": "Haydovchi topilmadi"
                        }), 404

                    cur.execute(
                        """
                        INSERT INTO driver_earnings (
                            driver_id,
                            order_id,
                            amount,
                            commission,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """,
                        (
                            driver_id,
                            order_id,
                            driver_income,
                            commission
                        )
                    )

        return jsonify({
            "success": True,
            "message": f"Buyurtma statusi {new_status} bo‘ldi",
            "order": {
                "id": order_id,
                "driver_id": driver_id,
                "status": new_status
            }
        }), 200

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "order_id, driver_id yoki status noto‘g‘ri"
        }), 400

    except Exception as e:
        print("Update order status error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500
