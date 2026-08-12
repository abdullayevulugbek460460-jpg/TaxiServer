import time
import jwt

from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import JWT_SECRET
from database import get_connection


def _json():
    return request.get_json(silent=True) or {}


def _new_token(user_type, user_id):
    payload = {
        "type": user_type,
        "id": int(user_id),
        "iat": int(time.time())
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )


def register_passenger():
    data = _json()

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "Ism va telefon raqami kerak"
        }), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id, name, phone
                    FROM users
                    WHERE phone = %s
                """, (phone,))

                existing = cur.fetchone()

                if existing:
                    return jsonify({
                        "success": True,
                        "message": "Bu telefon raqami avval ro‘yxatdan o‘tgan",
                        "user": {
                            "id": existing[0],
                            "name": existing[1],
                            "phone": existing[2]
                        }
                    }), 200

                cur.execute("""
                    INSERT INTO users
                    (name, phone, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    name,
                    phone,
                    "NO_PASSWORD"
                ))

                user_id = cur.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "Yo‘lovchi muvaffaqiyatli ro‘yxatdan o‘tdi",
            "user": {
                "id": user_id,
                "name": name,
                "phone": phone
            }
        }), 201

    except Exception as e:
        print("Passenger register error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500

def login_passenger():
    data = _json()

    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not phone or not password:
        return jsonify({
            "success": False,
            "message": "Telefon va parol kerak"
        }), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, phone, password_hash
                    FROM users
                    WHERE phone = %s
                """, (phone,))

                user = cur.fetchone()

        if not user or not check_password_hash(
            user[3],
            password
        ):
            return jsonify({
                "success": False,
                "message": "Telefon yoki parol noto‘g‘ri"
            }), 401

        token = _new_token("passenger", user[0])

        return jsonify({
            "success": True,
            "message": "Login muvaffaqiyatli",
            "token": token,
            "user": {
                "id": user[0],
                "name": user[1],
                "phone": user[2]
            }
        })

    except Exception as e:
        print("Passenger login error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def register_driver():
    data = _json()

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    login = str(data.get("login", "")).strip()
    password = str(data.get("password", ""))
    car_model = str(data.get("car_model", "")).strip()
    car_number = str(data.get("car_number", "")).strip()

    if not all([
        name,
        phone,
        login,
        password,
        car_model,
        car_number
    ]):
        return jsonify({
            "success": False,
            "message": "Barcha maydonlarni kiriting"
        }), 400

    if len(password) < 4:
        return jsonify({
            "success": False,
            "message": "Parol kamida 4 ta belgidan iborat bo‘lsin"
        }), 400

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id
                    FROM drivers
                    WHERE phone = %s
                """, (phone,))

                if cur.fetchone():
                    return jsonify({
                        "success": False,
                        "message": "Bu telefon raqami band"
                    }), 409

                cur.execute("""
                    SELECT id
                    FROM drivers
                    WHERE LOWER(login) = LOWER(%s)
                """, (login,))

                if cur.fetchone():
                    return jsonify({
                        "success": False,
                        "message": "Bu login band"
                    }), 409

                cur.execute("""
                    INSERT INTO drivers
                    (
                        name,
                        phone,
                        login,
                        password_hash,
                        car_model,
                        car_number,
                        approved,
                        online,
                        balance
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE, FALSE, 0)
                    RETURNING id
                """, (
                    name,
                    phone,
                    login,
                    password_hash,
                    car_model,
                    car_number
                ))

                driver_id = cur.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "Haydovchi ro‘yxatdan o‘tdi. Admin tasdig‘i kutilmoqda.",
            "driver": {
                "id": driver_id,
                "name": name,
                "phone": phone,
                "login": login,
                "car_model": car_model,
                "car_number": car_number,
                "approved": False,
                "online": False
            }
        }), 201

    except Exception as e:
        print("Driver register error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def login_driver():
    data = _json()

    login = str(data.get("login", "")).strip()
    password = str(data.get("password", ""))

    if not login or not password:
        return jsonify({
            "success": False,
            "message": "Login va parol kerak"
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
                        password_hash,
                        car_model,
                        car_number,
                        approved,
                        online,
                        balance
                    FROM drivers
                    WHERE LOWER(login) = LOWER(%s)
                """, (login,))

                driver = cur.fetchone()

        if not driver or not check_password_hash(
            driver[4],
            password
        ):
            return jsonify({
                "success": False,
                "message": "Login yoki parol noto‘g‘ri"
            }), 401

        if not driver[7]:
            return jsonify({
                "success": False,
                "message": "Admin hali haydovchini tasdiqlamagan"
            }), 403

        token = _new_token("driver", driver[0])

        return jsonify({
            "success": True,
            "message": "Login muvaffaqiyatli",
            "token": token,
            "driver": {
                "id": driver[0],
                "name": driver[1],
                "phone": driver[2],
                "login": driver[3],
                "car_model": driver[5],
                "car_number": driver[6],
                "approved": driver[7],
                "online": driver[8],
                "balance": float(driver[9])
            }
        })

    except Exception as e:
        print("Driver login error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500


def get_token_data():
    header = request.headers.get("Authorization", "")

    if not header.startswith("Bearer "):
        return None

    token = header[7:].strip()

    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        return None

def change_driver_password():
    data = _json()

    driver_id = data.get("driver_id")
    new_password = str(data.get("new_password", ""))

    if not driver_id or not new_password:
        return jsonify({
            "success": False,
            "message": "driver_id va new_password majburiy"
        }), 400

    if len(new_password) < 4:
        return jsonify({
            "success": False,
            "message": "Parol kamida 4 ta belgidan iborat bo‘lishi kerak"
        }), 400

    try:
        password_hash = generate_password_hash(new_password)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE drivers
                    SET password_hash = %s
                    WHERE id = %s
                    RETURNING id, name, login
                """, (password_hash, int(driver_id)))

                driver = cur.fetchone()

        if not driver:
            return jsonify({
                "success": False,
                "message": "Haydovchi topilmadi"
            }), 404

        return jsonify({
            "success": True,
            "message": "Haydovchi paroli muvaffaqiyatli o‘zgartirildi",
            "driver": {
                "id": driver[0],
                "name": driver[1],
                "login": driver[2]
            }
        })

    except Exception as e:
        print("Change driver password error:", e)

        return jsonify({
            "success": False,
            "message": "Server xatosi"
        }), 500

