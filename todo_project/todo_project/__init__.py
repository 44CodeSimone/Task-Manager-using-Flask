import os
import logging
from logging.handlers import SysLogHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '45cf93c4d41348cd9980674ade9a7356')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///site.db')

if os.environ.get('TESTING') == '1':
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False


def configure_syslog_logger():
    logger = logging.getLogger('task_manager_security')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        syslog_handler = SysLogHandler(address='/dev/log')
        formatter = logging.Formatter(
            'TaskManagerFlask[%(process)d]: %(levelname)s - %(message)s'
        )
        syslog_handler.setFormatter(formatter)
        logger.addHandler(syslog_handler)

    return logger


security_logger = configure_syslog_logger()

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'danger'

bcrypt = Bcrypt(app)

# Always put Routes at end
from todo_project import routes
from todo_project import models

with app.app_context():
    db.create_all()
