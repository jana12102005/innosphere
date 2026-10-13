# app.py

import os
from flask import Flask, render_template
from backend.config import (
    SECRET_KEY,
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    SQLALCHEMY_ENGINE_OPTIONS,
    UPLOAD_PATHS,
)
from backend.db import db, init_db

from backend.auth       import auth_bp
from backend.candidates import candidates_bp
from backend.events     import events_bp
from backend.projects   import projects_bp
from backend.certs      import certs_bp
from backend.gallery    import gallery_bp
from backend.team       import team_bp
from backend.chatbot    import chatbot_bp


def create_app():
    app = Flask(__name__, template_folder="templates",
                static_folder="static", static_url_path="/static")

    app.secret_key                               = SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"]        = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]      = SQLALCHEMY_ENGINE_OPTIONS

    # Keep cert output dir for local PDF caching (optional)
    app.config["UPLOAD_PATHS"] = UPLOAD_PATHS
    try:
        os.makedirs(UPLOAD_PATHS["certs"], exist_ok=True)
    except OSError:
        pass

    db.init_app(app)
    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(certs_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(chatbot_bp)

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    @app.errorhandler(404)
    def page_not_found(e):
        try:    return render_template("404.html"), 404
        except: return "<h1>404 – Page Not Found</h1>", 404

    @app.errorhandler(500)
    def internal_error(e):
        try:    return render_template("500.html"), 500
        except: return "<h1>500 – Internal Server Error</h1>", 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
