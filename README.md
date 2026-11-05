# Notes API - Full Auth Flask Backend

A secure RESTful Flask API for a personal notes app. Users sign up and log in with **session-based authentication**, then create, read, update and delete their own notes. Every note belongs to one user, and users can never see or change anyone else's notes. The notes index is paginated. Passwords are hashed with Flask-Bcrypt and are never stored or returned in plain text.

Built to work with the **client-with-sessions** frontend from the course repo.

## Tech stack

Flask 2.2 · Flask-RESTful · Flask-SQLAlchemy · Flask-Migrate · Flask-Bcrypt · Faker · SQLite

## Project structure

```
notes-api/
├── Pipfile / Pipfile.lock
├── README.md
└── server/
    ├── app.py        # auth routes and notes CRUD
    ├── config.py     # Flask app, database, bcrypt and API setup
    ├── models.py     # User and Note models
    ├── seed.py       # demo users and notes
    └── migrations/   # Flask-Migrate files
```

## Installation

```bash
pipenv install
pipenv shell
cd server
export FLASK_APP=app.py
flask db upgrade
python seed.py
```

`flask db upgrade` creates the database from the included migrations. `seed.py` wipes the data and adds two demo users with 15 notes each:

- `alice` / `password123`
- `bob` / `password123`

Werkzeug is pinned to 2.3.8 because 2.2.2 does not run on Python 3.12 or newer.

## Running the server

From the `server` folder, with the pipenv shell active:

```bash
python app.py
```

The API runs at `http://localhost:5555`, the port the session client's proxy expects.

## Endpoints

All request and response bodies are JSON. Errors come back as `{"errors": ["message"]}`.

### Auth

| Method | Path | Body | Success | Description |
|---|---|---|---|---|
| POST | `/signup` | `username`, `password`, `password_confirmation` (optional) | 201 + user | Creates an account and logs the user in |
| POST | `/login` | `username`, `password` | 200 + user | Logs in and starts a session |
| GET | `/check_session` | none | 200 + user | Returns the logged-in user, or `{}` with 401 |
| DELETE | `/logout` | none | 204 | Ends the session |

A user is returned as `{"id": 1, "username": "alice"}`.

### Notes (login required)

| Method | Path | Body | Success | Description |
|---|---|---|---|---|
| GET | `/notes?page=1&per_page=10` | none | 200 | The logged-in user's notes, newest first, paginated |
| POST | `/notes` | `title`, `content` | 201 + note | Creates a note owned by the logged-in user |
| GET | `/notes/<id>` | none | 200 + note | Returns one of your notes |
| PATCH | `/notes/<id>` | `title` and/or `content` | 200 + note | Updates one of your notes |
| DELETE | `/notes/<id>` | none | 204 | Deletes one of your notes |

`page` defaults to 1 and `per_page` defaults to 10 (maximum 100). The index response looks like:

```json
{
  "page": 1,
  "per_page": 10,
  "total": 15,
  "total_pages": 2,
  "items": [
    {
      "id": 15,
      "title": "Example title",
      "content": "Example content",
      "created_at": "2026-11-05T20:00:00",
      "updated_at": "2026-11-05T20:00:00",
      "user_id": 1
    }
  ]
}
```

### Error codes

| Code | Meaning |
|---|---|
| `401` | Not logged in, or wrong username or password |
| `404` | Note doesn't exist or belongs to another user (the API doesn't reveal which) |
| `422` | Validation failed: missing or blank fields, passwords don't match, or username already taken |

## Security notes

- Passwords are hashed with bcrypt. The hash can't be read from the model and is never included in responses.
- A note's owner is always taken from the session, never from the request body.
- Every note lookup is filtered by the logged-in user's id, so other users' notes can't be read, edited or deleted.

## Testing with the frontend

1. Start this API with `python app.py` (port 5555).
2. In the course repo's `client-with-sessions` folder, run `npm install` then `npm start`.
3. Open `http://localhost:4000` and sign up or log in as `alice` / `password123`.
