"""
FAWK AST (Abstract Syntax Tree)
Defines all AST node classes
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Tuple


@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    functions: List['FunctionDef']
    begin_blocks: List['Block']
    beginfile_blocks: List['Block']
    patterns: List['PatternAction']
    endfile_blocks: List['Block']
    end_blocks: List['Block']


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
    # List of (name, optional_initial_value) tuples
    # If initial_value is None, the variable is initialized to 0
    declarations: List[Tuple[str, Optional[ASTNode]]]


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
class ForStmt(ASTNode):
    init: Optional[ASTNode]
    condition: Optional[ASTNode]
    update: Optional[ASTNode]
    body: 'Block'


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: 'Block'


@dataclass
class DoWhileStmt(ASTNode):
    body: 'Block'
    condition: ASTNode


@dataclass
class SwitchCase(ASTNode):
    value: Optional[ASTNode]  # None for default case
    statements: List[ASTNode]


@dataclass
class SwitchStmt(ASTNode):
    expr: ASTNode
    cases: List['SwitchCase']


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]


@dataclass
class ExitStmt(ASTNode):
    code: Optional[ASTNode]


@dataclass
class NextStmt(ASTNode):
    pass


@dataclass
class NextFileStmt(ASTNode):
    pass


@dataclass
class BreakStmt(ASTNode):
    pass


@dataclass
class ContinueStmt(ASTNode):
    pass


@dataclass
class PrintWithRedirectStmt(ASTNode):
    args: List[ASTNode]
    redirect_type: str  # ">" or ">>"
    redirect_target: ASTNode  # Expression that evaluates to filename


@dataclass
class PrintfWithRedirectStmt(ASTNode):
    args: List[ASTNode]
    redirect_type: str  # ">" or ">>"
    redirect_target: ASTNode  # Expression that evaluates to filename


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
class TernaryOp(ASTNode):
    """Ternary operator: condition ? true_expr : false_expr"""
    condition: ASTNode
    true_expr: ASTNode
    false_expr: ASTNode


@dataclass
class PrefixIncrement(ASTNode):
    """Prefix increment: ++x"""
    operand: ASTNode


@dataclass
class PrefixDecrement(ASTNode):
    """Prefix decrement: --x"""
    operand: ASTNode


@dataclass
class PostfixIncrement(ASTNode):
    """Postfix increment: x++"""
    operand: ASTNode


@dataclass
class PostfixDecrement(ASTNode):
    """Postfix decrement: x--"""
    operand: ASTNode


@dataclass
class Assignment(ASTNode):
    target: ASTNode
    value: ASTNode
    op: str = "="  # "=", "+=", "-=", "*=", "/="


@dataclass
class ArrayLiteral(ASTNode):
    elements: List[ASTNode]


@dataclass
class AssocArray(ASTNode):
    pairs: List[tuple]  # [(key_expr, value_expr), ...]


@dataclass
class Access(ASTNode):
    array: ASTNode
    indices: List[ASTNode]  # Support multiple indices for multi-dimensional arrays


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


@dataclass
class DeleteStmt(ASTNode):
    target: ASTNode  # Variable, Access, or FieldAccess to delete


@dataclass
class DelarrayStmt(ASTNode):
    target: ASTNode  # Array variable to delete all elements from


@dataclass
class InOp(ASTNode):
    """Check if key(s) exist in array - supports (i,j) in arr syntax"""
    indices: List[ASTNode]  # Can be multiple indices for multi-dimensional check
    array: ASTNode


@dataclass
class CommaExpr(ASTNode):
    """Comma expression - evaluates all expressions and returns concatenated key"""
    exprs: List[ASTNode]


@dataclass
class PipedGetline(ASTNode):
    """Piped getline: cmd | getline var"""
    command: ASTNode  # Expression that evaluates to command string
    target: Optional[str]  # Variable name to store result, None for $0


@dataclass
class DestructurePattern(ASTNode):
    """Destructuring pattern for array assignment: [x, y] or [[x, y], [z, w]]"""
    patterns: List[ASTNode]  # List of patterns (Identifier or nested DestructurePattern)
