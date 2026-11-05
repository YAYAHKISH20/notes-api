"""App setup shared by app.py, models.py and seed.py.

Creates the Flask app and the extensions (database, migrations, bcrypt, REST API)
in one place, so the other files can import them without circular imports.
"""

import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

app = Flask(__name__)

# The secret key signs the session cookie that keeps users logged in.
# Set SECRET_KEY in the environment for anything beyond local development.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# SQLite file in the instance/ folder by default; DATABASE_URL overrides it.
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///app.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False  # pretty-print JSON responses

# Gives foreign keys predictable names so Flask-Migrate can alter them later.
metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)
db = SQLAlchemy(metadata=metadata)
db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
api = Api(app)
