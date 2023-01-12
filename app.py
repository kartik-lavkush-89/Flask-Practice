"""""""""""""""""""""""""""""""""""""""""""""""""MAIN  APP FILE"""""""""""""""""""""""""""""""""""""""""""""""""""""""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from celery import Celery
from dotenv import load_dotenv
from flask_caching import Cache

load_dotenv()

app= Flask(__name__)

app.secret_key = 'otp'

cache = Cache()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND')
app.config["CACHE_TYPE"] = "SimpleCache"

cache.init_app(app)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend="redis://127.0.0.1:6379/0",
        broker="redis://127.0.0.1:6379/0"
    )

    class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

    celery.Task = ContextTask  # Creating a celery task runnable
    return celery
app.app_context().push()
app.test_request_context().push()
celery = make_celery(app)


db=SQLAlchemy(app)
migrate = Migrate(app, db)
db.init_app(app)


from src.views.routes import app1

app.register_blueprint(app1, url_prefix = "")

if __name__== '__main__':
    app.run()