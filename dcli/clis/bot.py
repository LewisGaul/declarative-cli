# August 2020, Lewis Gaul

"""
CLI parsing in bot style.

"""

__all__ = ("CLIParser",)

from typing import List, Optional

from .._schema import RootNode
from . import AbstractCLIParser, Namespace


class CLIParser(AbstractCLIParser):
    """Argument parser using a bot style."""

    def __init__(self, schema: RootNode, **kwargs):
        """
        :param schema:
            The schema for the arg parsing.
        :param kwargs:
            Passed to base class.
        """
        super().__init__(schema, **kwargs)
        self._schema = schema

    def parse_args(self, args: Optional[List[str]] = None) -> Namespace:
        pass
