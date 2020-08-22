# August 2020, Lewis Gaul

"""
Declarative CLI.

"""

__all__ = ("CLIParser", "RootNode")

from .clis.argparse import CLIParser
from .schema import RootNode
