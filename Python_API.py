from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from peewee import *
import requests
import json

app = Flask(__name__)
CORS(app)

db = SqliteDatabase('orders.db')

class BaseModel(Model):
    class Meta:
        database = db

class Order(BaseModel):
    id = IntegerField(primary_key=True)
    total_price = FloatField()
    total_price_tax = FloatField()
    email = CharField()
    credit_card = CharField()
    shipping_information = CharField()
    paid = BooleanField()
    transaction = CharField()
    product = CharField()
    shipping_price = FloatField()

def init_db():
    db.create_tables([Order])
    print("Initialized the database.")
    return "Initialized the database."

@app.cli.command("init-db")
def init_db_command():
    """Initialize the database."""
    init_db()
    print("Initialized the database.")

def get_order_from_db(id):
    order = Order.select().where(Order.id == id).first()
    return order
    
data = None  

@app.route('/')
def home():
    global data
    # async request to the API
    url = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return jsonify(data)
    else:
        return jsonify({"error": "Erreur lors de la requête"}), response.status_code
    
@app.route('/order', methods=['POST'])
def create_order():    
    global data
    if data is None:
        home()

    
    if 'quantity' not in request.json['product']:
        return jsonify({"errors": {
                "product": {
                    "code": "missing-fields",
                    "name": "La création d'une commande nécessite une quantité"
                }
            }
        }), 422
    
    if 'id' not in request.json['product']:
        return jsonify({"errors": {
                "product": {
                    "code": "missing-fields",
                    "name": "La création d'une commande nécessite un produit"
                }
            }
        }), 422
    
    product_id = request.json['product']['id']
    for product in data["products"]:
        if product["id"] == product_id:

            break
    else:
        return jsonify({"error": "Product not found"}), 404
    
    if product['in_stock'] != True:
        return jsonify({"errors": {
                "product": {
                    "code": "out-of-inventory",
                    "name": "Le produit demandé n'est pas en inventaire"
                }
            }
        }), 422
    
    def calculate_shipping_price(weight):
        if weight < 500:
            return 5
        elif weight > 500 and weight < 2000:
            return 10
        else:
            return 25
    
    order = Order(
        total_price=product['price'] * request.json['product']['quantity'],
        total_price_tax=product['price'] * request.json['product']['quantity'] * 1.15,
        email=json.dumps({}),
        credit_card=json.dumps({}),
        shipping_information=json.dumps({}),
        paid=False,
        transaction=json.dumps({}),
        product=json.dumps(request.json['product']),
        shipping_price=json.dumps(calculate_shipping_price(product['weight']))
    )

    order.save()
    return jsonify({"message": "Order created successfully"}), 201

@app.route('/order/<int:id>', methods=['GET'])
def get_order(id):
    order = get_order_from_db(id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({
        "order": {
            "id": order.id,
            "total_price": order.total_price,
            "total_price_tax": order.total_price_tax,
            "email": json.loads(order.email),
            "credit_card": json.loads(order.credit_card),
            "shipping_information": json.loads(order.shipping_information),
            "paid": order.paid,
            "transaction": json.loads(order.transaction),
            "product": json.loads(order.product),
            "shipping_price": order.shipping_price
        }
    })

@app.route('/order/<int:id>', methods=['PUT'])
def update_order(id):
    order = get_order_from_db(id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    
    if 'email' not in request.json["order"] or 'shipping_information' not in request.json['order'] :
        return jsonify({"error": "Email and shipping information are required"}), 422
    
    print(request.json['order']['shipping_information'])

    if 'province' not in request.json["order"]['shipping_information']:
        return jsonify({"error": "Province is required"}), 422
    
    if 'province' in request.json["order"]['shipping_information']:
            province = request.json["order"]['shipping_information']['province']
            if province == "QC":
                order.total_price_tax = order.total_price * 1.15
            elif province == "ON":
                order.total_price_tax = order.total_price * 1.13
            elif province == "BC":
                order.total_price_tax = order.total_price * 1.12
            elif province == "AB":
                order.total_price_tax = order.total_price * 1.05
            elif province == "NS":
                order.total_price_tax = order.total_price * 1.15

    order = Order.update(
        email=json.dumps(request.json['order']['email']),
        total_price_tax=order.total_price_tax,
        shipping_information=json.dumps(request.json['order']['shipping_information'])

    ).where(Order.id == id).execute()

    return jsonify({"message": "Order updated successfully"})

@app.route('/order/<int:id>', methods=['PATCH'])
def Update_credit_card(id):
    order = get_order_from_db(id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    
    if 'credit_card' not in request.json:
        return jsonify({"errors": {
            "credit_card": {
                "code": "missing-fields",
                "name": "Credit card information is required"
            }
        }}), 422
    
    credit_card = request.json['credit_card']
    required_fields = ['name', 'number', 'expiration_year', 'expiration_month', 'cvv']
    for field in required_fields:
        if field not in credit_card:
            return jsonify({"errors": {
                "credit_card": {
                    "code": "missing-fields",
                    "name": f"Credit card {field} is required"
                }
            }}), 422

    # Vérifier que l'année d'expiration est valide (pas dans le passé)
    if int(credit_card['expiration_year']) < 2024:
        return jsonify({"errors": {
            "credit_card": {
                "code": "expired",
                "name": "Credit card is expired"
            }
        }}), 422

    # Vérifier que le mois d'expiration est valide (1-12)
    if not (1 <= int(credit_card['expiration_month']) <= 12):
        return jsonify({"errors": {
            "credit_card": {
                "code": "invalid-month",
                "name": "Invalid expiration month"
            }
        }}), 422

    amount_charged = order.total_price_tax + order.shipping_price

    url = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"
    response = requests.post(url, json={
        "credit_card": {
            "name": credit_card['name'],
            "number": credit_card['number'],
            "expiration_year": credit_card['expiration_year'],
            "expiration_month": credit_card['expiration_month'],
            "cvv": credit_card['cvv']
        },
        "amount_charged": amount_charged
    })

    if response.status_code != 200:
        try:
            return jsonify(response.json()), response.status_code
        except requests.exceptions.JSONDecodeError:
            return jsonify({"error": "An error occurred while processing the payment"}), response.status_code

    order = Order.update(
        credit_card=json.dumps(credit_card),
        paid=True,
        transaction=json.dumps(response.json())
    ).where(Order.id == id).execute()

    # You need to return the response from the payment API
    return jsonify(response.json())

    


if __name__ == '__main__':
    app.run(debug=True)