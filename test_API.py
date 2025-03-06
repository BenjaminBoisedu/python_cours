import pytest
from Python_API import app, init_db, get_order_from_db, db, Order

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

@pytest.fixture(scope='function', autouse=True)
def setup_and_teardown_db():
    with app.app_context():
        if not db.is_closed():
            db.close()
        init_db()
        yield
        # Fermez la connexion à la base de données après chaque test
        if not db.is_closed():
            db.close()

def test_init_db(capsys):
    with app.app_context():
        result = init_db()
    captured = capsys.readouterr()
    assert "Initialized the database." in captured.out
    assert result == "Initialized the database."

def test_get_order_from_db():
    # Assurez-vous que la base de données est vide avant de tester
    with app.app_context():
        if not db.is_closed():
            db.close()
        db.connect()
        Order.delete().execute()  # Supprimez toutes les commandes avant de tester
        order = get_order_from_db(1)
        assert order is None

def test_home(client):
    rv = client.get('/')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'products' in data

def test_create_order(client):
    order_data = {
        "product": {
            "id": 1,
            "quantity": 2
        },
    }

    ## Test if order quantity is an integer
    assert isinstance(order_data['product']['quantity'], int)
    
    rv = client.post('/order', json=order_data)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['message'] == "Order created successfully"

def test_type_quantity_missing(client):
    order_data = {
        "product": {
            "id": 1,
        },
    }
    rv = client.post('/order', json=order_data)
    assert rv.status_code == 422
    data = rv.get_json()
    assert data['errors']['product']['code'] == "missing-fields"

def test_product_missing(client):
    order_data = {
        "product": {
            "quantity": 2,
        },
    }
    rv = client.post('/order', json=order_data)
    assert rv.status_code == 422
    data = rv.get_json()
    assert data['errors']['product']['code'] == "missing-fields"
    


def test_update_order(client):    
    order_data = {
        "order": {
            "email": "Test@test.com",
            "shipping_information": {
                "address": "123 rue de la rue",
                "city": "Ville",
                "postal_code": "A1A 1A1",
                "country": "Canada",
                "province": "QC"
            },
        },
    }
    
    rv = client.put('/order/1', json=order_data)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['message'] == "Order updated successfully"


def test_update_credit_card(client):
    order_data = {
        "credit_card": {
            "name": "Test Test",
            "number": "4242 4242 4242 4242",
            "expiration_year": "2025",
            "expiration_month": "9",
            "cvv": "123"
        },
    }

    rv = client.patch('/order/1', json=order_data)
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'transaction' in data
    # Vérifier que la transaction est un succès
    assert data['transaction']['success'] == 'true'

def payment(client):
    order_data = {
        "credit_card": {
            "name": "Test Test",
            "number": "4242 424 4242 4242",
            "expiration_year": "2024",
            "expiration_month": "9",
            "cvv": "123"
        },
    }

    rv = client.post('/order/1/',  json=order_data)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['message'] == "Order successfully paid"
    print(data)





