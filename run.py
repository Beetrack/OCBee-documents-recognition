from app.settings.settings import config, DEBUG
from app.api.app import app

if __name__ == '__main__':
    app.config.update(config)
    app.run(debug=DEBUG)
