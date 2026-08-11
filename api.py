from flask import Flask, jsonify, request
from config import PORT, DEBUG
from admin import get_drivers, approve_driver, reject_driver
from database import init_db
from orders import create_order, get_orders, accept_order, update_order_status
from drivers import (
    update_driver_location,
    get_nearest_drivers,
    update_driver_online
)
from auth import (
    register_passenger,
    login_passenger,
    register_driver,
    login_driver
)

app = Flask(__name__)

try:
    init_db()
except Exception as e:
    print("Database init error:", e)
@app.post("/driver/location")
def driver_location():
    return update_driver_location()
@app.post("/driver/<int:driver_id>/online")
def driver_online(driver_id):
    from flask import request

    data = request.get_json(silent=True) or {}
    data["driver_id"] = driver_id
    request._cached_json = (data, data)

    return update_driver_online()

@app.post("/drivers/nearest")
def drivers_nearest():
    return get_nearest_drivers()
@app.get("/")
def home():
    return jsonify({
        "success": True,
        "service": "TaxiServer",
        "version": "1.0.0",
        "status": "online"
    })


@app.get("/health")
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })


@app.post("/auth/passenger/register")
def auth_passenger_register():
    return register_passenger()


@app.post("/auth/passenger/login")
def auth_passenger_login():
    return login_passenger()


@app.post("/auth/driver/register")
def auth_driver_register():
    return register_driver()


@app.post("/auth/driver/login")
def auth_driver_login():
    return login_driver()

@app.post("/orders/<int:order_id>/accept")
def order_accept(order_id):
    data = request.get_json(silent=True) or {}
    data["order_id"] = order_id
    request._cached_json = (data, data)

    return accept_order()


@app.post("/orders/<int:order_id>/status")
def order_status(order_id):
    data = request.get_json(silent=True) or {}
    data["order_id"] = order_id
    request._cached_json = (data, data)

    return update_order_status()

@app.post("/orders")
def orders_create():
    return create_order()


@app.get("/orders")
def orders_list():
    return get_orders()


@app.get("/admin/drivers")
def admin_drivers():
    return get_drivers()


@app.post("/admin/drivers/<int:driver_id>/approve")
def admin_approve_driver(driver_id):
    return approve_driver(driver_id)


@app.post("/admin/drivers/<int:driver_id>/reject")
def admin_reject_driver(driver_id):
    return reject_driver(driver_id)


@app.get("/api")
def api_info():
    return jsonify({
        "success": True,
        "service": "Taxi API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "passenger": "/passenger",
            "driver": "/driver",
            "orders": "/orders",
            "admin": "/admin"
        }
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=DEBUG
    )
