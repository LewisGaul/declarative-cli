# August 2020, Lewis Gaul

"""
Declarative CLI package.

"""

__all__ = ("Frontend", "create_cli_parser")

import enum
from typing import Type

import yaml

from ._schema import RootNode
from ._utils import PathLike
from .clis import bot as bot_cli
from .clis import standard as standard_cli


class Frontend(enum.Enum):
    ARGPARSE = enum.auto()
    BOT = enum.auto()

    def get_parser(self) -> Type[clis.AbstractCLIParser]:
        if self is self.ARGPARSE:
            return standard_cli.CLIParser
        elif self is self.BOT:
            return bot_cli.CLIParser
        else:
            raise ValueError("Unsupported frontend")


def create_cli_parser(
    file: PathLike, frontend: Frontend = Frontend.ARGPARSE, **kwargs
) -> clis.AbstractCLIParser:
    """
    Create and return a CLI parser.

    :param file:
        The file declaring the CLI.
    :param frontend:
        The frontend to use for parsing the CLI args.
    :param kwargs:
        Passed on the to CLI parser at creation.
    :return:
        A CLI parser instance.
    """
    with open(file) as f:
        loaded_schema = RootNode.from_dict(yaml.safe_load(f))
    return frontend.get_parser()(loaded_schema, **kwargs)
