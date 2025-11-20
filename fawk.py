#!/usr/bin/env python3
"""
FAWK - Functional AWK Interpreter
A functional AWK dialect with first-class functions and arrays.
"""

import sys
import re
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto


# ============================================================================
# LEXER
# ============================================================================

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Keywords
    FUNCTION = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    IN = auto()
    WHILE = auto()
    BREAK = auto()
    CONTINUE = auto()
    PRINT = auto()
    BEGIN = auto()
    END = auto()
    GLOBAL = auto()
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    ASSIGN = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    ARROW = auto()        # =>
    PIPELINE = auto()     # |>
    ASSOC_ARROW = auto()  # => (for associative arrays)
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    DOLLAR = auto()
    
    # Special
    REGEX = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
        self.keywords = {
            'function': TokenType.FUNCTION,
            'return': TokenType.RETURN,
            'if': TokenType.IF,
            'else': TokenType.ELSE,
            'for': TokenType.FOR,
            'in': TokenType.IN,
            'while': TokenType.WHILE,
            'break': TokenType.BREAK,
            'continue': TokenType.CONTINUE,
            'print': TokenType.PRINT,
            'BEGIN': TokenType.BEGIN,
            'END': TokenType.END,
            'global': TokenType.GLOBAL,
        }
    
    def error(self, msg: str):
        raise SyntaxError(f"Lexer error at line {self.line}, column {self.column}: {msg}")
    
    def peek(self, offset: int = 0) -> Optional[str]:
        pos = self.pos + offset
        if pos < len(self.text):
            return self.text[pos]
        return None
    
    def advance(self) -> Optional[str]:
        if self.pos < len(self.text):
            char = self.text[self.pos]
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return char
        return None
    
    def skip_whitespace(self):
        while self.peek() and self.peek() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        if self.peek() == '#':
            while self.peek() and self.peek() != '\n':
                self.advance()
    
    def read_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        num_str = ''
        
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'):
            num_str += self.advance()
        
        value = float(num_str) if '.' in num_str else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)
    
    def read_string(self) -> Token:
        start_line = self.line
        start_col = self.column
        quote = self.advance()  # consume opening quote
        string = ''
        
        while self.peek() and self.peek() != quote:
            if self.peek() == '\\':
                self.advance()
                next_char = self.peek()
                if next_char == 'n':
                    string += '\n'
                    self.advance()
                elif next_char == 't':
                    string += '\t'
                    self.advance()
                elif next_char == '\\':
                    string += '\\'
                    self.advance()
                elif next_char == quote:
                    string += quote
                    self.advance()
                else:
                    string += next_char
                    self.advance()
            else:
                string += self.advance()
        
        if self.peek() != quote:
            self.error("Unterminated string")
        
        self.advance()  # consume closing quote
        return Token(TokenType.STRING, string, start_line, start_col)
    
    def read_identifier(self) -> Token:
        start_line = self.line
        start_col = self.column
        ident = ''
        
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'):
            ident += self.advance()
        
        token_type = self.keywords.get(ident, TokenType.IDENTIFIER)
        return Token(token_type, ident, start_line, start_col)
    
    def read_regex(self) -> Token:
        start_line = self.line
        start_col = self.column
        self.advance()  # consume opening /
        pattern = ''
        
        while self.peek() and self.peek() != '/':
            if self.peek() == '\\':
                pattern += self.advance()
                if self.peek():
                    pattern += self.advance()
            else:
                pattern += self.advance()
        
        if self.peek() != '/':
            self.error("Unterminated regex")
        
        self.advance()  # consume closing /
        
        # Check for flags (i for case-insensitive)
        flags = ''
        while self.peek() and self.peek() in 'igm':
            flags += self.advance()
        
        return Token(TokenType.REGEX, (pattern, flags), start_line, start_col)
    
    def tokenize(self) -> List[Token]:
        while self.pos < len(self.text):
            self.skip_whitespace()
            
            if not self.peek():
                break
            
            # Skip comments
            if self.peek() == '#':
                self.skip_comment()
                continue
            
            # Newline
            if self.peek() == '\n':
                token = Token(TokenType.NEWLINE, '\n', self.line, self.column)
                self.tokens.append(token)
                self.advance()
                continue
            
            # Numbers
            if self.peek().isdigit():
                self.tokens.append(self.read_number())
                continue
            
            # Strings
            if self.peek() in '"\'':
                self.tokens.append(self.read_string())
                continue
            
            # Identifiers and keywords
            if self.peek().isalpha() or self.peek() == '_':
                self.tokens.append(self.read_identifier())
                continue
            
            # Regex patterns (only at top level after brace/newline at statement position)
            # We need to be careful - regex only appears in pattern position, not in expressions
            if self.peek() == '/':
                # Check if this could be a regex based on context
                # Regex appears after: NEWLINE, RBRACE, or at start
                if len(self.tokens) == 0:
                    self.tokens.append(self.read_regex())
                    continue
                
                # Look backwards past newlines to find meaningful token
                i = len(self.tokens) - 1
                while i >= 0 and self.tokens[i].type == TokenType.NEWLINE:
                    i -= 1
                
                if i < 0:
                    # Only newlines before this
                    self.tokens.append(self.read_regex())
                    continue
                
                last_meaningful = self.tokens[i]
                # Regex can appear after RBRACE (end of block) or BEGIN/END/FUNCTION
                if last_meaningful.type in [TokenType.RBRACE, TokenType.BEGIN, TokenType.END, TokenType.FUNCTION]:
                    self.tokens.append(self.read_regex())
                    continue
            
            # Two-character operators
            start_line = self.line
            start_col = self.column
            
            if self.peek() == '=' and self.peek(1) == '>':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.ARROW, '=>', start_line, start_col))
                continue
            
            if self.peek() == '|' and self.peek(1) == '>':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.PIPELINE, '|>', start_line, start_col))
                continue
            
            if self.peek() == '=' and self.peek(1) == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQ, '==', start_line, start_col))
                continue
            
            if self.peek() == '!' and self.peek(1) == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NE, '!=', start_line, start_col))
                continue
            
            if self.peek() == '<' and self.peek(1) == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.LE, '<=', start_line, start_col))
                continue
            
            if self.peek() == '>' and self.peek(1) == '=':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.GE, '>=', start_line, start_col))
                continue
            
            if self.peek() == '&' and self.peek(1) == '&':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.AND, '&&', start_line, start_col))
                continue
            
            if self.peek() == '|' and self.peek(1) == '|':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.OR, '||', start_line, start_col))
                continue
            
            # Single-character tokens
            char = self.peek()
            single_char_tokens = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MODULO,
                '=': TokenType.ASSIGN,
                '<': TokenType.LT,
                '>': TokenType.GT,
                '!': TokenType.NOT,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                ';': TokenType.SEMICOLON,
                '$': TokenType.DOLLAR,
            }
            
            if char in single_char_tokens:
                token = Token(single_char_tokens[char], char, start_line, start_col)
                self.tokens.append(token)
                self.advance()
                continue
            
            self.error(f"Unexpected character: {char}")
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


# ============================================================================
# AST NODES
# ============================================================================

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
    then_block: Block
    else_block: Optional[Block]


@dataclass
class ForInStmt(ASTNode):
    var: str
    iterable: ASTNode
    body: Block


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: Block


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
    body: Block


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


# ============================================================================
# PARSER
# ============================================================================

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def error(self, msg: str):
        token = self.current()
        raise SyntaxError(f"Parser error at line {token.line}, column {token.column}: {msg}")
    
    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF
    
    def peek(self, offset: int = 0) -> Token:
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return self.tokens[-1]  # EOF
    
    def advance(self) -> Token:
        token = self.current()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.current()
        if token.type != token_type:
            self.error(f"Expected {token_type}, got {token.type}")
        return self.advance()
    
    def skip_newlines(self):
        while self.current().type == TokenType.NEWLINE:
            self.advance()
    
    def parse(self) -> Program:
        functions = []
        begin_block = None
        patterns = []
        end_block = None
        
        self.skip_newlines()
        
        while self.current().type != TokenType.EOF:
            self.skip_newlines()
            
            if self.current().type == TokenType.FUNCTION:
                functions.append(self.parse_function_def())
            elif self.current().type == TokenType.BEGIN:
                self.advance()
                begin_block = self.parse_block()
            elif self.current().type == TokenType.END:
                self.advance()
                end_block = self.parse_block()
            elif self.current().type == TokenType.LBRACE:
                # Pattern-action with no pattern
                action = self.parse_block()
                patterns.append(PatternAction(None, action))
            elif self.current().type == TokenType.REGEX:
                # Regex pattern with action
                token = self.advance()
                pattern_node = Regex(token.value[0], token.value[1])
                action = self.parse_block()
                patterns.append(PatternAction(pattern_node, action))
            else:
                # Could be a pattern-action
                # For simplicity, treat remaining blocks as pattern-less actions
                break
            
            self.skip_newlines()
        
        return Program(functions, begin_block, patterns, end_block)
    
    def parse_function_def(self) -> FunctionDef:
        self.expect(TokenType.FUNCTION)
        name = self.expect(TokenType.IDENTIFIER).value
        
        self.expect(TokenType.LPAREN)
        params = []
        
        if self.current().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.current().type == TokenType.COMMA:
                self.advance()
                params.append(self.expect(TokenType.IDENTIFIER).value)
        
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        
        return FunctionDef(name, params, body)
    
    def parse_block(self) -> Block:
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        statements = []
        while self.current().type != TokenType.RBRACE:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        
        self.expect(TokenType.RBRACE)
        return Block(statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        self.skip_newlines()
        
        token = self.current()
        
        if token.type == TokenType.GLOBAL:
            return self.parse_global_decl()
        elif token.type == TokenType.IF:
            return self.parse_if_stmt()
        elif token.type == TokenType.FOR:
            return self.parse_for_stmt()
        elif token.type == TokenType.WHILE:
            return self.parse_while_stmt()
        elif token.type == TokenType.RETURN:
            return self.parse_return_stmt()
        elif token.type == TokenType.BREAK:
            self.advance()
            self.skip_statement_terminator()
            return BreakStmt()
        elif token.type == TokenType.CONTINUE:
            self.advance()
            self.skip_statement_terminator()
            return ContinueStmt()
        elif token.type == TokenType.PRINT:
            return self.parse_print_stmt()
        elif token.type == TokenType.LBRACE:
            return self.parse_block()
        elif token.type in [TokenType.NEWLINE, TokenType.SEMICOLON]:
            self.advance()
            return None
        else:
            return self.parse_expr_stmt()
    
    def parse_global_decl(self) -> GlobalDecl:
        self.expect(TokenType.GLOBAL)
        names = [self.expect(TokenType.IDENTIFIER).value]
        
        while self.current().type == TokenType.COMMA:
            self.advance()
            names.append(self.expect(TokenType.IDENTIFIER).value)
        
        self.skip_statement_terminator()
        return GlobalDecl(names)
    
    def parse_if_stmt(self) -> IfStmt:
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        
        then_block = self.parse_block()
        else_block = None
        
        if self.current().type == TokenType.ELSE:
            self.advance()
            else_block = self.parse_block()
        
        return IfStmt(condition, then_block, else_block)
    
    def parse_for_stmt(self) -> ForInStmt:
        self.expect(TokenType.FOR)
        self.expect(TokenType.LPAREN)
        var = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        
        return ForInStmt(var, iterable, body)
    
    def parse_while_stmt(self) -> WhileStmt:
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        body = self.parse_block()
        
        return WhileStmt(condition, body)
    
    def parse_return_stmt(self) -> ReturnStmt:
        self.expect(TokenType.RETURN)
        
        value = None
        if self.current().type not in [TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE]:
            value = self.parse_expression()
        
        self.skip_statement_terminator()
        return ReturnStmt(value)
    
    def parse_print_stmt(self) -> PrintStmt:
        self.expect(TokenType.PRINT)
        args = []
        
        if self.current().type not in [TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE]:
            args.append(self.parse_expression())
            while self.current().type == TokenType.COMMA:
                self.advance()
                args.append(self.parse_expression())
        
        self.skip_statement_terminator()
        return PrintStmt(args)
    
    def parse_expr_stmt(self) -> ExprStmt:
        expr = self.parse_expression()
        self.skip_statement_terminator()
        return ExprStmt(expr)
    
    def skip_statement_terminator(self):
        while self.current().type in [TokenType.NEWLINE, TokenType.SEMICOLON]:
            self.advance()
    
    def parse_expression(self) -> ASTNode:
        return self.parse_pipeline()
    
    def parse_pipeline(self) -> ASTNode:
        left = self.parse_assignment()
        
        # Skip newlines before pipeline operator to allow multi-line pipelines
        self.skip_newlines()
        
        while self.current().type == TokenType.PIPELINE:
            self.advance()
            self.skip_newlines()  # Skip newlines after pipeline operator too
            right = self.parse_assignment()
            left = Pipeline(left, right)
            self.skip_newlines()  # Check for more pipeline operators
        
        return left
    
    def parse_assignment(self) -> ASTNode:
        expr = self.parse_or()
        
        if self.current().type == TokenType.ASSIGN:
            self.advance()
            value = self.parse_expression()
            return Assignment(expr, value)
        
        return expr
    
    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        
        while self.current().type == TokenType.OR:
            op = self.advance().value
            right = self.parse_and()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_and(self) -> ASTNode:
        left = self.parse_equality()
        
        while self.current().type == TokenType.AND:
            op = self.advance().value
            right = self.parse_equality()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_equality(self) -> ASTNode:
        left = self.parse_comparison()
        
        while self.current().type in [TokenType.EQ, TokenType.NE]:
            op = self.advance().value
            right = self.parse_comparison()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        
        while self.current().type in [TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE]:
            op = self.advance().value
            right = self.parse_additive()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        
        while self.current().type in [TokenType.PLUS, TokenType.MINUS]:
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_unary()
        
        while self.current().type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        if self.current().type in [TokenType.NOT, TokenType.MINUS]:
            op = self.advance().value
            operand = self.parse_unary()
            return UnaryOp(op, operand)
        
        return self.parse_postfix()
    
    def parse_postfix(self) -> ASTNode:
        expr = self.parse_primary()
        
        while True:
            if self.current().type == TokenType.LPAREN:
                # Function call
                self.advance()
                args = []
                
                if self.current().type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    while self.current().type == TokenType.COMMA:
                        self.advance()
                        args.append(self.parse_expression())
                
                self.expect(TokenType.RPAREN)
                expr = FunctionCall(expr, args)
            
            elif self.current().type == TokenType.LBRACKET:
                # Array access
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = ArrayAccess(expr, index)
            
            else:
                break
        
        return expr
    
    def parse_primary(self) -> ASTNode:
        token = self.current()
        
        if token.type == TokenType.NUMBER:
            self.advance()
            return Number(token.value)
        
        elif token.type == TokenType.STRING:
            self.advance()
            return String(token.value)
        
        elif token.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(token.value)
        
        elif token.type == TokenType.DOLLAR:
            self.advance()
            index = self.parse_unary()
            return FieldAccess(index)
        
        elif token.type == TokenType.LPAREN:
            # Could be grouped expression or lambda
            if self.is_lambda():
                return self.parse_lambda()
            else:
                self.advance()
                expr = self.parse_expression()
                self.expect(TokenType.RPAREN)
                return expr
        
        elif token.type == TokenType.LBRACKET:
            return self.parse_array_literal()
        
        else:
            self.error(f"Unexpected token: {token.type}")
    
    def is_lambda(self) -> bool:
        # Look ahead to see if this is a lambda
        saved_pos = self.pos
        
        try:
            if self.current().type != TokenType.LPAREN:
                return False
            
            self.advance()
            
            # Empty params
            if self.current().type == TokenType.RPAREN:
                self.advance()
                result = self.current().type == TokenType.ARROW
                self.pos = saved_pos
                return result
            
            # Check for parameter list
            if self.current().type != TokenType.IDENTIFIER:
                self.pos = saved_pos
                return False
            
            self.advance()
            
            while self.current().type == TokenType.COMMA:
                self.advance()
                if self.current().type != TokenType.IDENTIFIER:
                    self.pos = saved_pos
                    return False
                self.advance()
            
            if self.current().type != TokenType.RPAREN:
                self.pos = saved_pos
                return False
            
            self.advance()
            result = self.current().type == TokenType.ARROW
            self.pos = saved_pos
            return result
        
        except:
            self.pos = saved_pos
            return False
    
    def parse_lambda(self) -> Lambda:
        self.expect(TokenType.LPAREN)
        params = []
        
        if self.current().type != TokenType.RPAREN:
            params.append(self.expect(TokenType.IDENTIFIER).value)
            while self.current().type == TokenType.COMMA:
                self.advance()
                params.append(self.expect(TokenType.IDENTIFIER).value)
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.ARROW)
        body = self.parse_block()
        
        return Lambda(params, body)
    
    def parse_array_literal(self) -> ASTNode:
        self.expect(TokenType.LBRACKET)
        elements = []
        pairs = []
        is_assoc = False
        
        if self.current().type != TokenType.RBRACKET:
            first_expr = self.parse_expression()
            
            # Check if it's an associative array
            if self.current().type == TokenType.ARROW:
                is_assoc = True
                self.advance()
                value_expr = self.parse_expression()
                pairs.append((first_expr, value_expr))
                
                while self.current().type == TokenType.COMMA:
                    self.advance()
                    if self.current().type == TokenType.RBRACKET:
                        break
                    key_expr = self.parse_expression()
                    self.expect(TokenType.ARROW)
                    value_expr = self.parse_expression()
                    pairs.append((key_expr, value_expr))
            else:
                elements.append(first_expr)
                while self.current().type == TokenType.COMMA:
                    self.advance()
                    if self.current().type == TokenType.RBRACKET:
                        break
                    elements.append(self.parse_expression())
        
        self.expect(TokenType.RBRACKET)
        
        if is_assoc:
            return AssocArray(pairs)
        else:
            return ArrayLiteral(elements)


# ============================================================================
# INTERPRETER
# ============================================================================

class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
    
    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            return 0  # AWK default for undefined variables
    
    def set(self, name: str, value: Any):
        self.vars[name] = value
    
    def set_local(self, name: str, value: Any):
        self.vars[name] = value
    
    def has(self, name: str) -> bool:
        if name in self.vars:
            return True
        elif self.parent:
            return self.parent.has(name)
        return False


class FawkArray:
    """Represents a FAWK array (can be regular or associative)"""
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        # Convert key to appropriate type
        if isinstance(key, (int, float)):
            key = int(key)
        else:
            key = str(key)
        return self.data.get(key, 0)
    
    def set(self, key, value):
        if isinstance(key, (int, float)):
            key = int(key)
        else:
            key = str(key)
        self.data[key] = value
    
    def keys(self):
        return list(self.data.keys())
    
    def values(self):
        return list(self.data.values())
    
    def length(self):
        return len(self.data)
    
    def copy(self):
        """Create a deep copy of this array"""
        new_arr = FawkArray()
        for key, value in self.data.items():
            if isinstance(value, FawkArray):
                new_arr.data[key] = value.copy()
            else:
                new_arr.data[key] = value
        return new_arr
    
    def __repr__(self):
        # Display as array-like for regular indices, dict-like for assoc
        if all(isinstance(k, int) for k in self.data.keys()):
            # Try to display as regular array
            if not self.data:
                return "[]"
            max_idx = max(self.data.keys())
            if all(i in self.data for i in range(max_idx + 1)):
                return "[" + ", ".join(str(self.data[i]) for i in range(max_idx + 1)) + "]"
        
        # Display as associative array
        items = [f"{k} => {v}" for k, v in self.data.items()]
        return "[" + ", ".join(items) + "]"


class UserFunction:
    def __init__(self, params: List[str], body: Block, closure_env: Environment):
        self.params = params
        self.body = body
        self.closure_env = closure_env


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
        self.globals_declared = set()
        
        # AWK built-in variables
        self.NR = 0  # Number of records
        self.NF = 0  # Number of fields
        self.fields = []  # Current line fields
        
        # Built-in functions
        self.register_builtins()
    
    def register_builtins(self):
        self.functions['length'] = lambda arr: arr.length() if isinstance(arr, FawkArray) else len(str(arr))
        self.functions['map'] = self.builtin_map
        self.functions['filter'] = self.builtin_filter
        self.functions['reduce'] = self.builtin_reduce
        self.functions['sum_array'] = self.builtin_sum_array
        self.functions['match'] = self.builtin_match
        self.functions['split'] = self.builtin_split
    
    def builtin_map(self, func, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("map requires an array")
        
        result = FawkArray()
        for key in arr.keys():
            value = arr.get(key)
            result.set(key, self.call_function(func, [value]))
        return result
    
    def builtin_filter(self, pred, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("filter requires an array")
        
        result = FawkArray()
        for key in arr.keys():
            value = arr.get(key)
            if self.is_truthy(self.call_function(pred, [value])):
                result.set(key, value)
        return result
    
    def builtin_reduce(self, func, initial, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("reduce requires an array")
        
        acc = initial
        for key in arr.keys():
            value = arr.get(key)
            acc = self.call_function(func, [acc, value])
        return acc
    
    def builtin_sum_array(self, arr):
        if not isinstance(arr, FawkArray):
            return 0
        total = 0
        for key in arr.keys():
            value = arr.get(key)
            total += value if isinstance(value, (int, float)) else 0
        return total
    
    def builtin_match(self, pattern, text):
        """Match a regex pattern and return array with full match and groups"""
        import re
        text_str = str(text)
        match = re.search(pattern, text_str)
        
        result = FawkArray()
        if match:
            # Index 0: full match
            result.set(0, match.group(0))
            # Index 1+: captured groups
            for i, group in enumerate(match.groups(), 1):
                result.set(i, group if group is not None else "")
        
        return result
    
    def builtin_split(self, separator, text):
        """Split text by separator and return array"""
        text_str = str(text)
        sep_str = str(separator)
        
        parts = text_str.split(sep_str)
        
        result = FawkArray()
        for i, part in enumerate(parts):
            result.set(i, part)
        
        return result
    
    def error(self, msg: str):
        raise RuntimeError(f"Runtime error: {msg}")
    
    def is_truthy(self, value) -> bool:
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value != ""
        elif isinstance(value, FawkArray):
            return value.length() > 0
        elif value is None:
            return False
        return True
    
    def to_number(self, value):
        """Convert value to number (like AWK does)"""
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            # Try to parse as number
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, AttributeError):
                return 0  # AWK default for non-numeric strings
        return 0
    
    def eval(self, node: ASTNode) -> Any:
        method_name = f'eval_{node.__class__.__name__}'
        method = getattr(self, method_name, None)
        if method:
            return method(node)
        else:
            self.error(f"No eval method for {node.__class__.__name__}")
    
    def eval_Program(self, node: Program) -> None:
        # Program evaluation is handled by run() method
        pass
    
    def eval_Block(self, node: Block) -> Any:
        result = None
        for stmt in node.statements:
            result = self.eval(stmt)
        return result
    
    def eval_GlobalDecl(self, node: GlobalDecl) -> None:
        for name in node.names:
            self.globals_declared.add(name)
            if name not in self.global_env.vars:
                self.global_env.set(name, 0)
    
    def eval_IfStmt(self, node: IfStmt) -> Any:
        condition = self.eval(node.condition)
        if self.is_truthy(condition):
            return self.eval(node.then_block)
        elif node.else_block:
            return self.eval(node.else_block)
        return None
    
    def eval_ForInStmt(self, node: ForInStmt) -> None:
        iterable = self.eval(node.iterable)
        
        if not isinstance(iterable, FawkArray):
            self.error("for-in requires an array")
        
        for key in iterable.keys():
            self.current_env.set_local(node.var, key)
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                continue
    
    def eval_WhileStmt(self, node: WhileStmt) -> None:
        while self.is_truthy(self.eval(node.condition)):
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                continue
    
    def eval_ReturnStmt(self, node: ReturnStmt) -> None:
        value = self.eval(node.value) if node.value else None
        raise ReturnException(value)
    
    def eval_BreakStmt(self, node: BreakStmt) -> None:
        raise BreakException()
    
    def eval_ContinueStmt(self, node: ContinueStmt) -> None:
        raise ContinueException()
    
    def eval_PrintStmt(self, node: PrintStmt) -> None:
        if not node.args:
            print()
        else:
            values = [self.value_to_string(self.eval(arg)) for arg in node.args]
            print(" ".join(values))
    
    def value_to_string(self, value) -> str:
        if isinstance(value, FawkArray):
            return str(value)
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, float):
            # Format floats nicely
            if value == int(value):
                return str(int(value))
            return str(value)
        elif value is None:
            return ""
        return str(value)
    
    def eval_ExprStmt(self, node: ExprStmt) -> Any:
        return self.eval(node.expr)
    
    def eval_BinaryOp(self, node: BinaryOp) -> Any:
        left = self.eval(node.left)
        right = self.eval(node.right)
        
        op = node.op
        
        # Arithmetic operations - convert to numbers
        if op == '+':
            return self.to_number(left) + self.to_number(right)
        elif op == '-':
            return self.to_number(left) - self.to_number(right)
        elif op == '*':
            return self.to_number(left) * self.to_number(right)
        elif op == '/':
            right_num = self.to_number(right)
            if right_num == 0:
                self.error("Division by zero")
            return self.to_number(left) / right_num
        elif op == '%':
            return self.to_number(left) % self.to_number(right)
        # Comparison operations - use as-is for now
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return self.to_number(left) < self.to_number(right)
        elif op == '<=':
            return self.to_number(left) <= self.to_number(right)
        elif op == '>':
            return self.to_number(left) > self.to_number(right)
        elif op == '>=':
            return self.to_number(left) >= self.to_number(right)
        # Logical operations
        elif op == '&&':
            return self.is_truthy(left) and self.is_truthy(right)
        elif op == '||':
            return self.is_truthy(left) or self.is_truthy(right)
        else:
            self.error(f"Unknown binary operator: {op}")
    
    def eval_UnaryOp(self, node: UnaryOp) -> Any:
        operand = self.eval(node.operand)
        
        if node.op == '-':
            return -operand
        elif node.op == '!':
            return not self.is_truthy(operand)
        else:
            self.error(f"Unknown unary operator: {node.op}")
    
    def eval_Assignment(self, node: Assignment) -> Any:
        value = self.eval(node.value)
        
        if isinstance(node.target, Identifier):
            name = node.target.name
            
            # Check if it's a global
            if name in self.globals_declared:
                self.global_env.set(name, value)
            else:
                self.current_env.set_local(name, value)
        
        elif isinstance(node.target, ArrayAccess):
            array = self.eval(node.target.array)
            if not isinstance(array, FawkArray):
                # Auto-vivify array
                array = FawkArray()
                if isinstance(node.target.array, Identifier):
                    name = node.target.array.name
                    if name in self.globals_declared:
                        self.global_env.set(name, array)
                    else:
                        self.current_env.set_local(name, array)
            
            index = self.eval(node.target.index)
            array.set(index, value)
        
        else:
            self.error("Invalid assignment target")
        
        return value
    
    def eval_ArrayLiteral(self, node: ArrayLiteral) -> FawkArray:
        arr = FawkArray()
        for i, elem in enumerate(node.elements):
            arr.set(i, self.eval(elem))
        return arr
    
    def eval_AssocArray(self, node: AssocArray) -> FawkArray:
        arr = FawkArray()
        for key_expr, value_expr in node.pairs:
            key = self.eval(key_expr)
            value = self.eval(value_expr)
            arr.set(key, value)
        return arr
    
    def eval_ArrayAccess(self, node: ArrayAccess) -> Any:
        array = self.eval(node.array)
        if not isinstance(array, FawkArray):
            return 0  # AWK behavior
        
        index = self.eval(node.index)
        return array.get(index)
    
    def eval_FunctionCall(self, node: FunctionCall) -> Any:
        func = self.eval(node.func)
        args = [self.eval(arg) for arg in node.args]
        
        return self.call_function(func, args)
    
    def call_function(self, func, args):
        if callable(func) and not isinstance(func, UserFunction):
            # Built-in function
            return func(*args)
        elif isinstance(func, UserFunction):
            # User-defined function
            if len(args) != len(func.params):
                self.error(f"Function expects {len(func.params)} arguments, got {len(args)}")
            
            # Create new environment for function
            func_env = Environment(func.closure_env)
            for param, arg in zip(func.params, args):
                # Copy arrays when passing as arguments (pass by value)
                if isinstance(arg, FawkArray):
                    func_env.set_local(param, arg.copy())
                else:
                    func_env.set_local(param, arg)
            
            # Execute function body
            saved_env = self.current_env
            self.current_env = func_env
            
            try:
                result = self.eval(func.body)
                # For lambdas with single expression, implicitly return the value
                if isinstance(func.body, Block) and len(func.body.statements) == 1:
                    stmt = func.body.statements[0]
                    if isinstance(stmt, ExprStmt):
                        # Implicit return for single-expression lambdas
                        result = self.eval(stmt.expr)
            except ReturnException as e:
                result = e.value
            finally:
                self.current_env = saved_env
            
            return result
        else:
            self.error(f"Not a function: {func}")
    
    def eval_Lambda(self, node: Lambda) -> UserFunction:
        return UserFunction(node.params, node.body, self.current_env)
    
    def eval_Pipeline(self, node: Pipeline) -> Any:
        left_value = self.eval(node.left)
        
        # The right side should be a function call
        # We append the left value as the last argument
        if isinstance(node.right, FunctionCall):
            func = self.eval(node.right.func)
            args = [self.eval(arg) for arg in node.right.args]
            args.append(left_value)  # Add piped value as last argument
            return self.call_function(func, args)
        else:
            self.error("Pipeline right side must be a function call")
    
    def eval_Identifier(self, node: Identifier) -> Any:
        name = node.name
        
        # Check for built-in variables
        if name == 'NR':
            return self.NR
        elif name == 'NF':
            return self.NF
        
        # Check for functions
        if name in self.functions:
            return self.functions[name]
        
        # Check for variables
        return self.current_env.get(name)
    
    def eval_Number(self, node: Number) -> float:
        return node.value
    
    def eval_String(self, node: String) -> str:
        return node.value
    
    def eval_Regex(self, node: Regex) -> bool:
        """Evaluate regex pattern against current line ($0)"""
        import re
        line = " ".join(self.fields) if self.fields else ""
        flags = 0
        if 'i' in node.flags:
            flags |= re.IGNORECASE
        try:
            return bool(re.search(node.pattern, line, flags))
        except re.error as e:
            self.error(f"Invalid regex pattern: {e}")
    
    def eval_FieldAccess(self, node: FieldAccess) -> Any:
        index = self.eval(node.index)
        index = int(index)
        
        if index == 0:
            return " ".join(self.fields)
        elif 1 <= index <= len(self.fields):
            return self.fields[index - 1]
        else:
            return ""
    
    def run(self, program: Program, input_lines: List[str] = None):
        # Register functions
        for func_def in program.functions:
            self.functions[func_def.name] = UserFunction(
                func_def.params, func_def.body, self.global_env
            )
        
        # Execute BEGIN block with its own local environment
        if program.begin_block:
            begin_env = Environment(self.global_env)
            saved_env = self.current_env
            self.current_env = begin_env
            try:
                self.eval(program.begin_block)
            finally:
                self.current_env = saved_env
        
        # Process input lines with pattern-action blocks
        if input_lines:
            for line in input_lines:
                self.NR += 1
                # Split line into fields (simple comma-separated for now)
                line = line.rstrip('\n')
                self.fields = line.split(',')
                self.NF = len(self.fields)
                
                # Execute pattern-action blocks
                for pattern_action in program.patterns:
                    # Check if pattern matches (or no pattern)
                    should_execute = False
                    if pattern_action.pattern is None:
                        should_execute = True
                    else:
                        # Evaluate pattern
                        should_execute = self.is_truthy(self.eval(pattern_action.pattern))
                    
                    if should_execute:
                        action_env = Environment(self.global_env)
                        saved_env = self.current_env
                        self.current_env = action_env
                        try:
                            self.eval(pattern_action.action)
                        finally:
                            self.current_env = saved_env
        else:
            # No input, just execute pattern-less actions
            for pattern_action in program.patterns:
                if pattern_action.pattern is None:
                    action_env = Environment(self.global_env)
                    saved_env = self.current_env
                    self.current_env = action_env
                    try:
                        self.eval(pattern_action.action)
                    finally:
                        self.current_env = saved_env
        
        # Execute END block with its own local environment
        if program.end_block:
            end_env = Environment(self.global_env)
            saved_env = self.current_env
            self.current_env = end_env
            try:
                self.eval(program.end_block)
            finally:
                self.current_env = saved_env


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: fawk.py <script.fawk> [input_file]")
        sys.exit(1)
    
    script_file = sys.argv[1]
    
    with open(script_file, 'r') as f:
        source = f.read()
    
    # Tokenize
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    program = parser.parse()
    
    # Interpret
    interpreter = Interpreter()
    
    # Read input if provided
    input_lines = []
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r') as f:
            input_lines = f.readlines()
    
    interpreter.run(program, input_lines)


if __name__ == '__main__':
    main()
