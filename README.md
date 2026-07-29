# DRF Shop API

## Short Description

DRF Shop API is a Django REST Framework backend for an online store. It provides product catalog management, categories, carts, orders, customer profiles, comments, JWT authentication, PostgreSQL storage, and Redis caching.

## Features

- Product and category APIs
- Product search, ordering, and filtering
- Shopping cart and cart item management
- Customer profile and order management
- Product comments and reviews
- JWT-based authentication with Djoser
- PostgreSQL and Redis support with Docker

## Tech Stack

- Python
- Django
- Django REST Framework
- Djoser
- Simple JWT
- PostgreSQL
- Redis
- Docker / Docker Compose
- Pytest

## Installation

```bash
git clone <repository-url>
cd DRF-Shop
docker compose up --build
```

Run database migrations:

```bash
docker compose exec web python manage.py migrate
```

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

## Usage

Start the application:

```bash
docker compose up
```

The API will be available at:

```text
http://localhost:8000/
```

Admin panel:

```text
http://localhost:8000/admin/
```

## Project Structure (brief)

```text
DRF-Shop/
├── config/          # Django project settings and root URLs
├── core/            # Custom user model and user serializers
├── store/           # Store models, views, serializers, filters, URLs
├── tests/           # API, model, and serializer tests
├── Dockerfile       # Web application container
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## API Endpoints

| Method | Endpoint | Description |
| ------- | -------- | ----------- |
| GET, POST | `/store/products/` | List or create products |
| GET, POST | `/store/categories/` | List or create categories |
| GET, POST | `/store/carts/` | Manage carts |
| GET, POST | `/store/carts/{cart_id}/items/` | Manage cart items |
| GET, POST | `/store/orders/` | Manage orders |
| GET, POST | `/store/orders/{order_id}/items/` | Manage order items |
| GET, POST | `/store/products/{product_id}/comments/` | Manage product comments |
| GET, PUT | `/store/customers/me/` | View or update current customer |
| POST | `/auth/users/` | Register a user |
| POST | `/auth/jwt/create/` | Create JWT tokens |
| POST | `/auth/jwt/refresh/` | Refresh JWT token |

## Author

Ali Ganji — [GitHub](https://github.com/AliGanji14)
