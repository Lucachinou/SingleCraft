import importlib
import os
from pathlib import Path

def register_blueprints(app):
    for file in Path("blueprints").iterdir():
        if file.is_file():
            if file.name != "__init__.py" and file.name != "__pycache__" and file.name != "BlueprintsManager.py":
                module = importlib.import_module(f"{file.parent.name}.{file.name[:-3]}")
                if hasattr(module, "bp"):
                    app.logger.info("Registering {0} with url_prefix {1}".format(module.bp.name, module.bp.url_prefix))
                    app.register_blueprint(module.bp)
