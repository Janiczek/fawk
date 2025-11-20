"""
FAWK AST (Abstract Syntax Tree)
Defines all AST node classes
"""

from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    functions: List['FunctionDef']
    begin_block: Optional['Block']
    patterns: List['PatternAction']
    end_block: Optional['Block']


@dataclass
class FunctionDef(ASTNode):
    name: str
    params: List[str]
    body: 'Block'


@dataclass
class PatternAction(ASTNode):
    pattern: Optional[ASTNode]
    action: 'Block'


@dataclass
class Block(ASTNode):
    statements: List[ASTNode]


@dataclass
class GlobalDecl(ASTNode):
    names: List[str]


@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_block: 'Block'
    else_block: Optional['Block']


@dataclass
class ForInStmt(ASTNode):
    var: str
    iterable: ASTNode
    body: 'Block'


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: 'Block'


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]


@dataclass
class BreakStmt(ASTNode):
    pass


@dataclass
class ContinueStmt(ASTNode):
    pass


@dataclass
class PrintStmt(ASTNode):
    args: List[ASTNode]


@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode


@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode


@dataclass
class Assignment(ASTNode):
    target: ASTNode
    value: ASTNode


@dataclass
class ArrayLiteral(ASTNode):
    elements: List[ASTNode]


@dataclass
class AssocArray(ASTNode):
    pairs: List[tuple]  # [(key_expr, value_expr), ...]


@dataclass
class ArrayAccess(ASTNode):
    array: ASTNode
    index: ASTNode


@dataclass
class FunctionCall(ASTNode):
    func: ASTNode
    args: List[ASTNode]


@dataclass
class Lambda(ASTNode):
    params: List[str]
    body: 'Block'


@dataclass
class Pipeline(ASTNode):
    left: ASTNode
    right: ASTNode


@dataclass
class Identifier(ASTNode):
    name: str


@dataclass
class Number(ASTNode):
    value: float


@dataclass
class String(ASTNode):
    value: str


@dataclass
class Regex(ASTNode):
    pattern: str
    flags: str


@dataclass
class FieldAccess(ASTNode):
    index: ASTNode
