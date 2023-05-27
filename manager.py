from backend.index import app
from backend.model import *
from flask_migrate import Migrate, MigrateCommand

migrate = Migrate(app, db)

if __name__ == '__main__':
    pass