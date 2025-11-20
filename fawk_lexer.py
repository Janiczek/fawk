"""
FAWK Lexer
Tokenizes FAWK source code
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, List, Optional


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
    DO = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    BREAK = auto()
    CONTINUE = auto()
    EXIT = auto()
    NEXT = auto()
    NEXTFILE = auto()
    PRINT = auto()
    BEGIN = auto()
    END = auto()
    BEGINFILE = auto()
    ENDFILE = auto()
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
    MATCH = auto()        # ~
    NOT_MATCH = auto()    # !~
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
    COLON = auto()
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
            'do': TokenType.DO,
            'switch': TokenType.SWITCH,
            'case': TokenType.CASE,
            'default': TokenType.DEFAULT,
            'break': TokenType.BREAK,
            'continue': TokenType.CONTINUE,
            'exit': TokenType.EXIT,
            'next': TokenType.NEXT,
            'nextfile': TokenType.NEXTFILE,
            'print': TokenType.PRINT,
            'BEGIN': TokenType.BEGIN,
            'END': TokenType.END,
            'BEGINFILE': TokenType.BEGINFILE,
            'ENDFILE': TokenType.ENDFILE,
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
                    # Preserve backslash for unknown escapes (e.g., \$ or \. for regex)
                    string += '\\'
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
            
            # Regex patterns (can appear in pattern position and in expressions)
            # We need to be careful - regex only appears where expressions can start
            if self.peek() == '/':
                # Check if this could be a regex based on context
                # Regex appears after: NEWLINE, RBRACE, operators, or at start
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
                # Regex can appear after:
                # - Block delimiters: RBRACE, BEGIN, END, BEGINFILE, ENDFILE, FUNCTION
                # - Operators where expressions can start: AND, OR, NOT, LPAREN, COMMA
                # - Comparison/match operators: EQ, NE, LT, LE, GT, GE, MATCH, NOT_MATCH
                # - Other operators: ASSIGN
                if last_meaningful.type in [
                    TokenType.RBRACE, TokenType.BEGIN, TokenType.END, TokenType.BEGINFILE, TokenType.ENDFILE, TokenType.FUNCTION,
                    TokenType.AND, TokenType.OR, TokenType.NOT,
                    TokenType.LPAREN, TokenType.COMMA,
                    TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE,
                    TokenType.MATCH, TokenType.NOT_MATCH,
                    TokenType.ASSIGN,
                ]:
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
            
            if self.peek() == '!' and self.peek(1) == '~':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.NOT_MATCH, '!~', start_line, start_col))
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
                '~': TokenType.MATCH,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                ';': TokenType.SEMICOLON,
                ':': TokenType.COLON,
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
