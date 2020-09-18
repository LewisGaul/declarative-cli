# August 2020, Lewis Gaul

"""
CLI parsing in bot style.

"""

__all__ = ("CLIParser",)

import argparse
import sys
from typing import List, NoReturn, Optional, Text

from .._schema import NodeBase, RootNode
from . import AbstractCLIParser, Namespace


class _ArgParseError(Exception):
    """Error parsing args."""


class _CustomArgumentParser(argparse.ArgumentParser):
    """Customised version of an argument parser from argparse."""

    def error(self, message: Text) -> NoReturn:
        raise _ArgParseError(message)


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

    def parse_args(self, args: Optional[List[str]] = None, namespace=None) -> Namespace:
        if args is None:
            args = sys.argv
        if namespace is None:
            namespace = Namespace()

        # Take a copy of the args.
        remaining_args = list(args)

        # Determine whether to show help output.
        show_help = False
        try:
            if remaining_args[0] == "help":
                show_help = True
                remaining_args.pop(0)
            if remaining_args[-1] in ["?", "help"]:
                show_help = True
                remaining_args.pop(-1)
        except IndexError:
            pass

        # Loop through the args until we find a non-keyword.
        node = self._schema
        consumed_args = []
        while node.subtree and remaining_args:
            arg = remaining_args[0]
            keywords = {x.keyword: x for x in node.subtree}
            if arg in keywords:
                consumed_args.append(remaining_args.pop(0))
                node = keywords[arg]
            else:
                break

        if show_help:
            print(self.format_help(node))
            sys.exit(0)

        # Use argparse to parse the command, but don't let it give error output.
        parser = _CustomArgumentParser(add_help=False)

        argv_for_argparse = remaining_args.copy()
        for arg in node.args:
            if arg.positional:
                name = arg.name.replace("-", "_")
            else:
                # Convert optional args to use dashes.
                name = "--" + arg.name
                # TODO: This is a hack, relying on no arg name/value clashes.
                #  This also unintentionally allows specifying with the dashes!
                argv_for_argparse = [
                    "--" + a if a == arg.name else a for a in argv_for_argparse
                ]
            kwargs = dict()
            if arg.type is bool:
                kwargs["action"] = "store_true"
            elif arg.type is list:
                kwargs["nargs"] = argparse.REMAINDER
            parser.add_argument(name, **kwargs)

        try:
            namespace = parser.parse_args(argv_for_argparse, namespace)
        except _ArgParseError as e:
            print("Error parsing the command:", e, file=sys.stderr)
            print(self.format_help(node), file=sys.stderr)
            sys.exit(2)

        namespace.command = node.command
        namespace.remaining_args = remaining_args

        return namespace

    def format_help(self, node: NodeBase) -> str:
        """Format help text for a given node."""
        # Start with the keywords already entered.
        tmp_node = node
        keywords = ["<bot>"]
        while tmp_node.keyword:
            keywords.insert(1, tmp_node.keyword)
            tmp_node = tmp_node.parent

        # Include subnode options if not at the end of a chain.
        valid_end_of_chain = node.command is not None
        if node.subtree:
            options = [n.keyword for n in node.subtree]
            if valid_end_of_chain:
                brace_chars = "[]"
            else:
                brace_chars = "{}"
            if options:
                opts_string = brace_chars[0] + " | ".join(options) + brace_chars[1]
            else:
                opts_string = ""
        else:
            options = []
            for arg_opt in node.args:
                if arg_opt.type is bool:
                    options.append(arg_opt.name)
                else:
                    options.append(arg_opt.name + " ...")
            opts_string = " ".join("[{}]".format(opt) for opt in options)

        return " ".join(keywords + [opts_string])
