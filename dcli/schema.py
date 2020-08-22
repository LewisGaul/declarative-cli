# August 2020, Lewis Gaul

"""
Handling for a CLI schema.

"""

__all__ = ("Arg", "NodeBase", "RootNode", "SubNode")

import typing
from typing import Dict, List, Optional


class Arg:
    """Schema arg."""

    def __init__(
        self,
        *,
        name: str,
        help_: str,
        command: Optional[str] = None,
        positional: bool = False,
        type_: typing.Type = str,
        enum: Optional[List] = None,
        default: Optional = None,
    ):
        self.name = name
        self.help = help_
        self.command = command
        self.positional = positional
        self.type = type_
        self.enum = enum
        self.default = default

    @classmethod
    def from_dict(cls, data: Dict[str, typing.Any]) -> "Arg":
        kwargs = data.copy()
        kwargs["help_"] = kwargs.pop("help")
        kwargs["type_"] = cls._process_type_field(kwargs.pop("type", "string"))
        return cls(**kwargs)

    @staticmethod
    def _process_type_field(value: str) -> typing.Type:
        # TODO: 'type' should be an enum rather than a Python type.
        accepted_types = {
            "integer": int,
            "string": str,
            "float": float,
            "flag": bool,
            "text": list,
        }
        if value in accepted_types:
            value = accepted_types[value]
        else:
            raise ValueError(
                "Unrecognised type {!r}, accepted types are: {}".format(
                    value, ", ".join(accepted_types)
                )
            )
        return value


class NodeBase:
    """Base class for nodes."""

    def __init__(
        self,
        *,
        keyword: Optional[str] = None,
        help_: str,
        command: Optional[str] = None,
        args: Optional[List[Arg]] = None,
        subtree: Optional[List["NodeBase"]] = None,
    ):
        self.keyword = keyword
        self.help = help_
        self.command = command
        self.args = args if args else []
        self.subtree = subtree if subtree else []
        self.parent = None  # type: Optional[NodeBase]
        for x in subtree:
            x.parent = self

    @classmethod
    def from_dict(cls, data: Dict[str, typing.Any]) -> "NodeBase":
        kwargs = data.copy()
        kwargs["help_"] = kwargs.pop("help")
        kwargs["args"] = cls._process_args_field(kwargs.pop("args", []))
        kwargs["subtree"] = cls._process_subtree_field(kwargs.pop("subtree", []))
        return cls(**kwargs)

    @staticmethod
    def _process_subtree_field(value: List[Dict[str, typing.Any]]) -> List["NodeBase"]:
        return [SubNode.from_dict(x) for x in value]

    @staticmethod
    def _process_args_field(value: List[Dict[str, typing.Any]]) -> List[Arg]:
        return [Arg.from_dict(x) for x in value]


class RootNode(NodeBase):
    """Root schema node."""

    def __init__(self, **kwargs):
        if "keyword" in kwargs:
            raise TypeError("__init__() got an unexpected keyword argument 'keyword'")
        super().__init__(**kwargs)

    def __repr__(self):
        return "<RootNode>"


class SubNode(NodeBase):
    """Sub schema node."""

    def __init__(self, *, keyword: str, **kwargs):
        kwargs["keyword"] = keyword
        super().__init__(**kwargs)

    def __repr__(self):
        keywords = []
        node = self
        while node.keyword:
            keywords.insert(0, node.keyword)
            node = node.parent
        return "<SubNode({})>".format(".".join(keywords))
