import os
import logging
import sqlite3
from pathlib import Path

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix


class Base(DeclarativeBase):
    pass


# Create data directory if it doesn't exist
data_dir = Path("./data")
data_dir.mkdir(exist_ok=True)

# Create empty database file if it doesn't exist
db_path = data_dir / "spylolenigma.db"
if not db_path.exists():
    conn = sqlite3.connect(str(db_path))
    conn.close()

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database with absolute path to avoid permission issues
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path.absolute()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models for table creation
    from models import Enigma, UserProgress
    # Create database tables
    db.create_all()
    
    # Import and run the initial data setup
    from game_data import setup_initial_enigmas
    setup_initial_enigmas()

logging.basicConfig(level=logging.DEBUG)
