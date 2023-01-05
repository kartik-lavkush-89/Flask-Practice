from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from celery import Celery

app= Flask(__name__)

app.secret_key = 'otp'

app.config['SECRET_KEY'] = "secretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://abc:root@localhost/mydatabase"
app.config['CELERY_BROKER_URL']="redis://localhost:6379/0"
app.config['CELERY_RESULT_BACKEND']="redis://localhost:6379/0"

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

celery = make_celery(app)


db=SQLAlchemy(app)
migrate = Migrate(app, db)
db.init_app(app)


from src.views.routes import app1

app.register_blueprint(app1, url_prefix = "")

if __name__== '__main__':
    print(__name__)
    app.run()