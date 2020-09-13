# August 2020, Lewis Gaul

"""
CLI parsing implementations.

"""

__all__ = ("AbstractCLIParser", "Namespace")

import abc
import argparse
from typing import List, Optional

from .._schema import RootNode


Namespace = argparse.Namespace


class AbstractCLIParser(metaclass=abc.ABCMeta):
    """Abstract base class for CLI parsers."""

    def __init__(self, schema: RootNode, **kwargs):
        """
        :param schema:
            The schema for the arg parsing.
        """
        pass

    @abc.abstractmethod
    def parse_args(self, args: Optional[List[str]] = None) -> Namespace:
        pass
