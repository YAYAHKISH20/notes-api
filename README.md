give me full code for each
# Notes API — Full Auth Flask Backend

A secure RESTful Flask API for a personal notes app. Users sign up and log in with **session-based authentication** (signed cookies), then create, read, update and delete their own notes. Every note belongs to one user, and users can never see or change anyone else's notes. The notes index is paginated. Passwords are hashed with Flask-Bcrypt and are never stored or returned in plain text.

Built to work with the **session** version of the provided frontend client.

## Tech stack

Flask 2.2 · Flask-RESTful · Flask-SQLAlchemy · Flask-Migrate · Flask-Bcrypt · Marshmallow · Faker · SQLite

## Project structure

```
notes-api/
├── Pipfile
├── README.md
└── server/
    ├── app.py          # routes / resources + auth decorator
    ├── config.py       # app, db, bcrypt, migrate, api setup
    ├── models.py       # User + Note models and Marshmallow schemas
    ├── seed.py         # demo data
    └── migrations/     # Flask-Migrate (Alembic) migrations
```

## Installation

Requires Python 3.8+ and Pipenv.

```bash
git clone <your-repo-url>
cd notes-api
pipenv install
pipenv shell
```

Set up and seed the database:

```bash
cd server
export FLASK_APP=app.py
flask db upgrade      # applies the existing migrations
python seed.py        # creates 2 demo users with 15 notes each
```

Demo logins after seeding: `alice` / `password123` and `bob` / `password123`.

> If you change the models later: `flask db migrate -m "describe change"` then `flask db upgrade`.

## Running the app

From the `server/` folder:

```bash
python app.py
```

The API runs at **http://localhost:5555**. (`flask run --port 5555` works too.)

Optional environment variables: `SECRET_KEY` (signs the session cookie — set this in production) and `DATABASE_URI` (defaults to SQLite).

## Endpoints

All request and response bodies are JSON. Notes endpoints require a logged-in session; otherwise they return `401`.

### Auth

| Method | Path | Description | Success |
|---|---|---|---|
| POST | `/signup` | Create an account and log in. Body: `{"username", "password", "password_confirmation"?}`. Username 3–50 chars, password ≥ 6 chars. | `201` user |
| POST | `/login` | Log in. Body: `{"username", "password"}`. | `200` user |
| GET | `/check_session` | Return the logged-in user (used to keep users logged in on refresh). | `200` user |
| DELETE | `/logout` | Log out and clear the session. | `204` |

User JSON: `{"id": 1, "username": "alice"}`

### Notes (owned by the logged-in user)

| Method | Path | Description | Success |
|---|---|---|---|
| GET | `/notes?page=1&per_page=10` | Paginated list of **your** notes, newest first. `per_page` max 50. | `200` |
| POST | `/notes` | Create a note. Body: `{"title", "content"}`. | `201` note |
| GET | `/notes/<id>` | Get one of your notes. | `200` note |
| PATCH | `/notes/<id>` | Update `title` and/or `content` of one of your notes. | `200` note |
| DELETE | `/notes/<id>` | Delete one of your notes. | `204` |

Paginated response:

```json
{
  "page": 1,
  "per_page": 10,
  "total": 15,
  "total_pages": 2,
  "notes": [
    {
      "id": 15,
      "title": "Grocery list",
      "content": "Milk, eggs, coffee",
      "created_at": "2026-11-05T18:44:34",
      "updated_at": "2026-11-05T18:44:34",
      "user_id": 1
    }
  ]
}
```

### Errors

| Status | When |
|---|---|
| `400` | Invalid pagination params (e.g. `page=0`) |
| `401` | Not logged in, or wrong username/password |
| `404` | Note doesn't exist **or belongs to another user** (the API doesn't reveal which) |
| `422` | Validation failed (missing/blank title or content, short password, taken username) |

## Security notes

- Passwords are hashed with bcrypt; the hash is write-only on the model and never serialized.
- A note's owner is always taken from the session, never from the request body.
- Every note query is filtered by the current user's id, so other users' notes are unreachable.
