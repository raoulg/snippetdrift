from importlib.metadata import version

from snippetdrift.cli import app

__version__ = version("snippetdrift")

__all__ = ["app", "__version__"]
