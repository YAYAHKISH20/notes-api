# Notes API

A Flask REST API with session-based authentication. Each user can only see and edit their own notes.

## Setup

```bash
pipenv install
pipenv shell
cd server
export FLASK_APP=app.py
flask db init
flask db migrate -m "initial"
flask db upgrade
python seed.py
python app.py
```

The server runs at http://localhost:5555. Seeded logins: `alice` / `password123` and `bob` / `password123`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /signup | Create account and log in (`username`, `password`, optional `password_confirmation`) |
| POST | /login | Log in (`username`, `password`) |
| GET | /check_session | Return the logged-in user, or 401 |
| DELETE | /logout | Log out |
| GET | /notes?page=1&per_page=10 | Your notes, paginated |
| POST | /notes | Create a note (`title`, `content`) |
| GET | /notes/:id | Get one of your notes |
| PATCH | /notes/:id | Update `title` and/or `content` |
| DELETE | /notes/:id | Delete a note |

All `/notes` routes return 401 when not logged in and 404 for notes that belong to someone else.

## Quick test with curl

```bash
curl -c cookies.txt -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' http://localhost:5555/login
curl -b cookies.txt http://localhost:5555/notes
```
