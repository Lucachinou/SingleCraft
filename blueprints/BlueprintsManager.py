import importlib
import os
import flask

from pathlib import Path

def register_blueprints(app: flask.Flask):
    for file in Path(__file__).parent.iterdir():
        if file.is_file():
            if file.name != "__init__.py" and file.name != "__pycache__" and file.name != "BlueprintsManager.py" and file.name != ".DS_Store":
                try:
                    module = importlib.import_module(f"{file.parent.name}.{file.name[:-3]}")
                    app.logger.info("Registering {0} with url_prefix {1}".format(module.bp.name, module.bp.url_prefix))
                    app.register_blueprint(module.bp)
                except Exception as e:
                    app.logger.error("An error occurred while loading {0}: {1}".format(file.name, str(e)))