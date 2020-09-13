# August 2020, Lewis Gaul

"""
CLI parsing in argparse style.

"""

__all__ = ("CLIParser",)

import argparse
import sys
from typing import List, Optional

from .._schema import RootNode
from . import AbstractCLIParser, Namespace


class CLIParser(AbstractCLIParser):
    """Argument parser based on argparse."""

    def __init__(self, schema: RootNode, *, prog: Optional[str] = None):
        """
        :param schema:
            The schema for the arg parsing.
        :param prog:
            The program name.
        """
        super().__init__(schema)
        self._schema = schema
        self._prog = prog

    def parse_args(self, args: Optional[List[str]] = None, namespace=None) -> Namespace:
        if args is None:
            args = sys.argv

        # Take a copy of the args.
        remaining_args = list(args)
        # Loop through the args until we find a non-keyword.
        node = self._schema
        consumed_args = []
        show_help = False
        while node.subtree and remaining_args:
            arg = remaining_args[0]
            if arg in ["-h", "--help"]:
                # TODO: Not sure how best to handle a 'help' arg:
                #   - Accept anywhere or only after the last given keyword
                #   - Treat as help for last given node, or for the node it
                #     appears directly after (break here instead of continue)
                #  Currently accepted anywhere and enacted on last given node.
                show_help = True
                remaining_args.pop(0)
                continue
            keywords = {x.keyword: x for x in node.subtree}
            if arg in keywords:
                consumed_args.append(remaining_args.pop(0))
                node = keywords[arg]
            else:
                break

        if show_help:
            remaining_args.insert(0, "--help")

        # Construct an arg parser for the node we reached.
        if self._prog:
            prog_args = [self._prog] + consumed_args
        else:
            prog_args = consumed_args
        parser = argparse.ArgumentParser(
            prog=" ".join(prog_args),
            description=node.help,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        # Use subparsers to represent the subnodes in displayed help.
        if node.subtree and show_help:
            subparsers = parser.add_subparsers(title="submodes")
            subparsers.required = node.command is None
            for subnode in node.subtree:
                subparsers.add_parser(subnode.keyword, help=subnode.help)
        # Add arguments for end-of-command.
        for arg in node.args:
            name = arg.name.replace("-", "_") if arg.positional else "--" + arg.name
            kwargs = dict()
            kwargs["help"] = arg.help
            if arg.type is bool:
                kwargs["action"] = "store_true"
            elif arg.type is list:
                kwargs["nargs"] = argparse.REMAINDER
            parser.add_argument(name, **kwargs)

        args_ns = parser.parse_args(remaining_args, namespace)
        args_ns.command = node.command
        args_ns.remaining_args = remaining_args
        return args_ns
