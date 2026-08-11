from flask import request, jsonify
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

        distance_km = float(data.get("estimated_distance_km", 0))
        price = float(data.get("estimated_price", 0))

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
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

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
