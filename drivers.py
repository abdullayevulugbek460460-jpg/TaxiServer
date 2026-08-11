from flask import request, jsonify
from database import get_connection
import math


def update_driver_location():
    data = request.get_json(silent=True) or {}

    required = ["driver_id", "latitude", "longitude"]

    for field in required:
        if field not in data:
            return jsonify({
                "success": False,
                "message": f"{field} majburiy"
            }), 400

    try:
        driver_id = int(data["driver_id"])
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])

        if not (-90 <= latitude <= 90):
            return jsonify({
                "success": False,
                "message": "Latitude noto‘g‘ri"
            }), 400

        if not (-180 <= longitude <= 180):
            return jsonify({
                "success": False,
                "message": "Longitude noto‘g‘ri"
            }), 400

        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id, approved
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

                cur.execute(
                    """
                    INSERT INTO driver_locations (
                        driver_id,
                        latitude,
                        longitude,
                        updated_at
                    )
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (driver_id)
                    DO UPDATE SET
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (driver_id, latitude, longitude)
                )

        return jsonify({
            "success": True,
            "message": "Lokatsiya yangilandi",
            "location": {
                "driver_id": driver_id,
                "latitude": latitude,
                "longitude": longitude
            }
        }), 200

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Koordinatalar noto‘g‘ri"
        }), 400

    except Exception as e:
        print("Driver location error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def get_nearest_drivers():
    try:
        data = request.get_json(silent=True) or {}

        latitude = float(data["latitude"])
        longitude = float(data["longitude"])

        radius_km = float(data.get("radius_km", 10))

        if radius_km <= 0 or radius_km > 100:
            return jsonify({
                "success": False,
                "message": "radius_km 0 dan katta va 100 dan kichik bo‘lishi kerak"
            }), 400

        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        d.id,
                        d.name,
                        d.phone,
                        d.car_model,
                        d.car_number,
                        d.online,
                        dl.latitude,
                        dl.longitude
                    FROM drivers d
                    JOIN driver_locations dl
                        ON dl.driver_id = d.id
                    WHERE d.approved = TRUE
                      AND d.online = TRUE
                    """
                )

                rows = cur.fetchall()

        drivers = []

        for row in rows:
            driver_lat = float(row[6])
            driver_lng = float(row[7])

            distance = haversine_distance(
                latitude,
                longitude,
                driver_lat,
                driver_lng
            )

            if distance <= radius_km:
                drivers.append({
                    "id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "car_model": row[3],
                    "car_number": row[4],
                    "online": row[5],
                    "latitude": driver_lat,
                    "longitude": driver_lng,
                    "distance_km": round(distance, 2)
                })

        drivers.sort(key=lambda x: x["distance_km"])

        return jsonify({
            "success": True,
            "drivers": drivers
        }), 200

    except (ValueError, TypeError, KeyError):
        return jsonify({
            "success": False,
            "message": "Lokatsiya ma'lumotlari noto‘g‘ri"
        }), 400

    except Exception as e:
        print("Nearest drivers error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def haversine_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c
