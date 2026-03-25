from flask import Flask, request, jsonify, render_template
import random
import datetime

import os
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# In-memory data store
data = {
    "name": [], "phno": [], "add": [], "checkin": [], "checkout": [],
    "room": [], "price": [], "rc": [], "p": [], "roomno": [], "custid": [], "day": []
}

ROOM_PRICES = {
    "Standard Non-AC": 3500,
    "Standard AC": 4000,
    "3-Bed Non-AC": 4500,
    "3-Bed AC": 5000
}

MENU = {
    1: 20, 2: 25, 3: 25, 4: 25, 5: 30, 6: 30, 7: 50, 8: 50, 9: 70, 10: 70,
    11: 110, 12: 110, 13: 110, 14: 110, 15: 110,
    16: 110, 17: 110, 18: 120, 19: 120, 20: 140, 21: 140, 22: 140,
    23: 140, 24: 140, 25: 140, 26: 140, 27: 150, 28: 150,
    29: 15, 30: 15, 31: 20, 32: 20,
    33: 90, 34: 90, 35: 110, 36: 110,
    37: 100, 38: 110, 39: 130, 40: 130, 41: 130, 42: 140,
    43: 60, 44: 60, 45: 60, 46: 60
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/book", methods=["POST"])
def book():
    d = request.json
    name, phno, add_ = d["name"], d["phno"], d["address"]
    checkin, checkout, room_type = d["checkin"], d["checkout"], d["room_type"]

    if not name or not phno or not add_:
        return jsonify({"error": "Name, phone and address are required"}), 400

    # Check duplicate unpaid phone
    for idx, ph in enumerate(data["phno"]):
        if ph == phno and data["p"][idx] == 0:
            return jsonify({"error": "Phone number already has an unpaid booking"}), 400

    try:
        ci = datetime.datetime.strptime(checkin, "%Y-%m-%d")
        co = datetime.datetime.strptime(checkout, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    if co <= ci:
        return jsonify({"error": "Check-out must be after check-in"}), 400

    days = (co - ci).days
    price = ROOM_PRICES.get(room_type)
    if not price:
        return jsonify({"error": "Invalid room type"}), 400

    rn = random.randrange(40) + 300
    cid = random.randrange(40) + 10
    while rn in data["roomno"] or cid in data["custid"]:
        rn = random.randrange(60) + 300
        cid = random.randrange(60) + 10

    data["name"].append(name)
    data["phno"].append(phno)
    data["add"].append(add_)
    data["checkin"].append(checkin)
    data["checkout"].append(checkout)
    data["room"].append(room_type)
    data["price"].append(price)
    data["rc"].append(0)
    data["p"].append(0)
    data["roomno"].append(rn)
    data["custid"].append(cid)
    data["day"].append(days)

    return jsonify({"message": "Room booked successfully", "room_no": rn, "customer_id": cid})

@app.route("/api/order", methods=["POST"])
def order():
    d = request.json
    cid = d["customer_id"]
    items = d["items"]  # list of item numbers

    for idx, c in enumerate(data["custid"]):
        if c == cid and data["p"][idx] == 0:
            total = sum(MENU.get(int(item), 0) for item in items)
            data["rc"][idx] += total
            return jsonify({"message": "Order placed", "bill": total, "total_rc": data["rc"][idx]})

    return jsonify({"error": "Invalid or already paid customer ID"}), 400

@app.route("/api/payment", methods=["POST"])
def payment():
    d = request.json
    phno = d["phno"]

    for idx, ph in enumerate(data["phno"]):
        if ph == phno and data["p"][idx] == 0:
            total = data["price"][idx] * data["day"][idx] + data["rc"][idx]
            bill = {
                "name": data["name"][idx],
                "phno": data["phno"][idx],
                "address": data["add"][idx],
                "checkin": data["checkin"][idx],
                "checkout": data["checkout"][idx],
                "room": data["room"][idx],
                "room_charges": data["price"][idx] * data["day"][idx],
                "restaurant_charges": data["rc"][idx],
                "total": total
            }
            data["p"][idx] = 1
            data["roomno"][idx] = 0
            data["custid"][idx] = 0
            return jsonify({"message": "Payment successful", "bill": bill})

    return jsonify({"error": "No pending payment found for this phone number"}), 400

@app.route("/api/records", methods=["GET"])
def records():
    result = []
    for idx in range(len(data["name"])):
        result.append({
            "name": data["name"][idx],
            "phno": data["phno"][idx],
            "address": data["add"][idx],
            "checkin": data["checkin"][idx],
            "checkout": data["checkout"][idx],
            "room": data["room"][idx],
            "price": data["price"][idx],
            "status": "Paid" if data["p"][idx] == 1 else "Pending"
        })
    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
