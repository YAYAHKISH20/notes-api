"""Seed the database with demo users and notes.

Run from the server folder with: python seed.py
This wipes existing notes and users first, so it is safe to run more than once.
Both demo users log in with the password "password123".
"""

from faker import Faker

from app import app
from config import db
from models import Note, User

fake = Faker()

with app.app_context():
    print("Clearing data...")
    # Delete notes before users, since each note points to a user.
    Note.query.delete()
    User.query.delete()

    print("Creating users...")
    users = []
    for name in ["alice", "bob"]:
        u = User(username=name)
        u.password_hash = "password123"  # stored as a bcrypt hash
        users.append(u)
    db.session.add_all(users)
    db.session.commit()

    print("Creating notes...")
    # 15 notes per user gives enough rows to see pagination (10 per page by default).
    for u in users:
        for _ in range(15):
            db.session.add(
                Note(
                    title=fake.sentence(nb_words=4),
                    content=fake.paragraph(nb_sentences=3),
                    user_id=u.id,
                )
            )
    db.session.commit()
    print("Done. Log in as alice / password123 or bob / password123")
