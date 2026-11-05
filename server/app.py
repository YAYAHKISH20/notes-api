"""Notes API: session-based authentication and user-owned notes.

Auth routes manage the login session. Note routes require a logged-in user,
and each user can only read or change their own notes.
"""

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import api, app, db
from models import Note, User


def current_user():
    """Return the logged-in User from the session, or None if nobody is logged in."""
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


class Signup(Resource):
    def post(self):
        """Create a new account, log the user in, and return the user (201).

        Returns 422 if fields are missing, the passwords don't match,
        or the username is already taken.
        """
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return {"errors": ["Username and password are required."]}, 422
        if password != data.get("password_confirmation", password):
            return {"errors": ["Passwords do not match."]}, 422
        try:
            user = User(username=username)
            user.password_hash = password  # the setter stores a bcrypt hash, never the plain password
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username already taken."]}, 422
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422
        session["user_id"] = user.id
        return user.to_dict(), 201


class CheckSession(Resource):
    def get(self):
        """Return the logged-in user so the frontend can stay logged in after a refresh, or 401."""
        user = current_user()
        if not user:
            return {}, 401
        return user.to_dict(), 200


class Login(Resource):
    def post(self):
        """Check the username and password, start a session, and return the user. 401 on failure."""
        data = request.get_json() or {}
        user = User.query.filter_by(username=data.get("username")).first()
        if user and user.authenticate(data.get("password", "")):
            session["user_id"] = user.id
            return user.to_dict(), 200
        # Same message for unknown user and wrong password, so usernames can't be probed.
        return {"errors": ["Invalid username or password."]}, 401


class Logout(Resource):
    def delete(self):
        """End the session. Returns 204, or 401 if nobody was logged in."""
        if not session.get("user_id"):
            return {"errors": ["Not logged in."]}, 401
        session.pop("user_id", None)
        return {}, 204


class NotesIndex(Resource):
    def get(self):
        """List the logged-in user's notes, newest first, paginated.

        Query params: page (default 1) and per_page (default 10, max 100).
        """
        user = current_user()
        if not user:
            return {"errors": ["Unauthorized"]}, 401
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        pagination = (
            Note.query.filter_by(user_id=user.id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
            "items": [n.to_dict() for n in pagination.items],
        }, 200

    def post(self):
        """Create a note owned by the logged-in user. Returns 201, or 422 if title/content is missing."""
        user = current_user()
        if not user:
            return {"errors": ["Unauthorized"]}, 401
        data = request.get_json() or {}
        try:
            # user_id comes from the session, never from the request body,
            # so nobody can create notes for another user.
            note = Note(
                title=data.get("title"), content=data.get("content"), user_id=user.id
            )
            db.session.add(note)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422
        return note.to_dict(), 201


class NoteByID(Resource):
    def _get_owned(self, id):
        """Find a note that belongs to the logged-in user.

        Returns (note, None) on success, or (None, error_response).
        Another user's note returns 404 rather than 403, so the API
        doesn't reveal that the note exists.
        """
        user = current_user()
        if not user:
            return None, ({"errors": ["Unauthorized"]}, 401)
        note = db.session.get(Note, id)
        if not note or note.user_id != user.id:
            return None, ({"errors": ["Note not found."]}, 404)
        return note, None

    def get(self, id):
        """Return one of the logged-in user's notes."""
        note, err = self._get_owned(id)
        return err if err else (note.to_dict(), 200)

    def patch(self, id):
        """Update the title and/or content of one of the logged-in user's notes."""
        note, err = self._get_owned(id)
        if err:
            return err
        data = request.get_json() or {}
        try:
            for field in ("title", "content"):
                if field in data:
                    setattr(note, field, data[field])
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422
        return note.to_dict(), 200

    def delete(self, id):
        """Delete one of the logged-in user's notes. Returns 204."""
        note, err = self._get_owned(id)
        if err:
            return err
        db.session.delete(note)
        db.session.commit()
        return {}, 204


api.add_resource(Signup, "/signup")
api.add_resource(CheckSession, "/check_session")
api.add_resource(Login, "/login")
api.add_resource(Logout, "/logout")
api.add_resource(NotesIndex, "/notes")
api.add_resource(NoteByID, "/notes/<int:id>")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
