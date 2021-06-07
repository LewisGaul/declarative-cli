# June 2021, Lewis Gaul

"""
Parsing of a CLI schema.

"""

__all__ = ("Arg", "NodeBase", "RootNode", "SubNode")

import enum
import typing
from typing import Any, Dict, List, Optional

import marshmallow
from marshmallow import Schema, fields
from marshmallow_enum import EnumField


class ArgType(enum.Enum):
    """Possible arg types."""

    INTEGER = enum.auto()
    STRING = enum.auto()
    FLOAT = enum.auto()
    FLAG = enum.auto()
    TEXT = enum.auto()


class Arg(Schema):
    """Schema arg."""

    name: str = fields.Str(required=True)
    help_: str = fields.Str(required=True)
    command: Optional[str] = fields.Str(missing=None)
    positional: bool = fields.Bool(missing=False)
    type_: ArgType = EnumField(ArgType, missing=ArgType.STRING)
    enum: Optional[List[str]] = fields.List(fields.Str(), missing=None)
    default: Optional[Any] = None  # TODO: Need to interpret this as the type corresponding to 'type_' field...


class NodeBase(Schema):
    """Base class for nodes."""

    keyword: Optional[str] = fields.Str(missing=None)
    help_: str = fields.Str(required=True)
    command: Optional[str] = fields.Str(missing=None)
    args: Optional[List[Arg]] = fields.List(fields.Nested(Arg), missing=None)
    subtree: Optional[List["NodeBase"]] = fields.List(fields.Nested("NodeBase"), missing=None)

    @marshmallow.post_load
    def set_subtree_parents(self):
        self.parent = None  # type: Optional[NodeBase]
        for x in self.subtree:
            x.parent = self


class RootNode(NodeBase):
    """Root schema node."""

    def __repr__(self):
        return "<RootNode>"


class SubNode(NodeBase):
    """Sub schema node."""

    def __repr__(self):
        keywords = []
        node = self
        while node.keyword:
            keywords.insert(0, node.keyword)
            node = node.parent
        return "<SubNode({})>".format(".".join(keywords))
