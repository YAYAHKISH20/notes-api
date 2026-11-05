from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import api, app, db
from models import Note, User


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return {"errors": ["Username and password are required."]}, 422
        if password != data.get("password_confirmation", password):
            return {"errors": ["Passwords do not match."]}, 422
        try:
            user = User(username=username)
            user.password_hash = password
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
        user = current_user()
        if not user:
            return {}, 401
        return user.to_dict(), 200


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        user = User.query.filter_by(username=data.get("username")).first()
        if user and user.authenticate(data.get("password", "")):
            session["user_id"] = user.id
            return user.to_dict(), 200
        return {"errors": ["Invalid username or password."]}, 401


class Logout(Resource):
    def delete(self):
        if not session.get("user_id"):
            return {"errors": ["Not logged in."]}, 401
        session.pop("user_id", None)
        return {}, 204


class NotesIndex(Resource):
    def get(self):
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
        user = current_user()
        if not user:
            return {"errors": ["Unauthorized"]}, 401
        data = request.get_json() or {}
        try:
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
        user = current_user()
        if not user:
            return None, ({"errors": ["Unauthorized"]}, 401)
        note = db.session.get(Note, id)
        if not note or note.user_id != user.id:
            return None, ({"errors": ["Note not found."]}, 404)
        return note, None

    def get(self, id):
        note, err = self._get_owned(id)
        return err if err else (note.to_dict(), 200)

    def patch(self, id):
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
