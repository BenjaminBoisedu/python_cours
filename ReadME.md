# Technologie Utilisée : Python

## Commande pour lancer le serveur :

- `FLASK_DEBUG=True FLASK_APP=Python_API.py flask run`

## Commande pour initialiser la base de données :

- `FLASK_DEBUG=True FLASK_APP=Python_API.py flask init-db`

## Commande pour lancer les tests :

- `pytest test_API.py`

# API REST

## GET / : Renvoie la liste des produits

## GET /order/<int:id> : Renvoie les informations d'une commande

## POST /order : Crée une commande

- Exemple de requête :

```json
{
  "products": [
    {
      "id": 1,
      "quantity": 2
    },
    {
      "id": 2,
      "quantity": 1
    }
  ]
}
```

## PUT /order/<int:id> : Modifie une commande pour ajouter les informations de livraison

- Exemple de requête :

```json
{
  "order": {
    "email": "jgnault@uqac.ca",
    "shipping_information": {
      "country": "Canada",
      "address": "201, rue Président-Kennedy",
      "postal_code": "G7X 3Y7",
      "city": "Chicoutimi",
      "province": "QC"
    }
  }
}
```

## PATCH /order/<int:id> : Ajouter une carte de crédit à une commande

- Exemple de requête :

```json
{
  "credit_card": {
    "name": "Jean-Guy Nault",
    "number": "1234567890123456",
    "expiration_year": "2023",
    "expiration_month": "12",
    "cvv": "123"
  }
}
```
