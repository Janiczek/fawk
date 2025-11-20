"""
FAWK Parser
Parses tokens into an Abstract Syntax Tree
"""

from typing import List, Optional
from fawk_lexer import Token, TokenType
from fawk_ast import *


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
        
        # Parse functions, BEGIN, patterns, and END in any order
        while self.current().type != TokenType.EOF:
            self.skip_newlines()
            
            if self.current().type == TokenType.FUNCTION:
                functions.append(self.parse_function_def())
            elif self.current().type == TokenType.BEGIN:
                if begin_block is not None:
                    self.error("Multiple BEGIN blocks not allowed")
                self.advance()
                begin_block = self.parse_block()
            elif self.current().type == TokenType.END:
                if end_block is not None:
                    self.error("Multiple END blocks not allowed")
                self.advance()
                end_block = self.parse_block()
            elif self.current().type == TokenType.LBRACE:
                # Pattern-action with no pattern
                action = self.parse_block()
                patterns.append(PatternAction(None, action))
            else:
                # Try to parse a pattern expression followed by an action block
                pattern_expr = self.try_parse_pattern()
                if pattern_expr is not None:
                    # We have a pattern, now expect an action block
                    self.skip_newlines()
                    if self.current().type != TokenType.LBRACE:
                        self.error("Expected '{' after pattern")
                    action = self.parse_block()
                    patterns.append(PatternAction(pattern_expr, action))
                else:
                    # No more valid constructs
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
        
        while self.current().type in [TokenType.EQ, TokenType.NE, TokenType.MATCH, TokenType.NOT_MATCH]:
            op = self.advance().value
            right = self.parse_comparison()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_concatenation()
        
        while self.current().type in [TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE]:
            op = self.advance().value
            right = self.parse_concatenation()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_concatenation(self) -> ASTNode:
        left = self.parse_additive()
        
        # String concatenation by juxtaposition
        # Check if next token can start a primary expression
        while self.current().type in [TokenType.STRING, TokenType.NUMBER, 
                                       TokenType.IDENTIFIER, TokenType.DOLLAR, 
                                       TokenType.LPAREN, TokenType.LBRACKET]:
            right = self.parse_additive()
            left = BinaryOp('concat', left, right)
        
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
        
        elif token.type == TokenType.REGEX:
            self.advance()
            return Regex(token.value[0], token.value[1])
        
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
    
    def try_parse_pattern(self) -> Optional[ASTNode]:
        """
        Try to parse a pattern expression.
        Returns the pattern node if successful, None otherwise.
        
        A pattern is any expression followed by a '{' block.
        This includes: regex literals, field comparisons, boolean combinations, etc.
        """
        # Save position in case we need to backtrack
        saved_pos = self.pos
        
        try:
            # Check if the current token can start a pattern expression
            token = self.current()
            
            # These tokens can start a pattern expression
            if token.type in [
                TokenType.DOLLAR,     # $1, $2, etc.
                TokenType.IDENTIFIER, # variables, function calls
                TokenType.NUMBER,     # numeric literals
                TokenType.STRING,     # string literals
                TokenType.LPAREN,     # grouped expressions, lambdas
                TokenType.LBRACKET,   # array literals
                TokenType.NOT,        # unary not
                TokenType.MINUS,      # unary minus
            ]:
                # Try to parse an expression
                pattern = self.parse_expression()
                
                # Skip newlines between pattern and action
                self.skip_newlines()
                
                # Check if followed by '{'
                if self.current().type == TokenType.LBRACE:
                    # Success! This is a pattern
                    return pattern
                else:
                    # Not followed by '{', not a pattern
                    self.pos = saved_pos
                    return None
            elif token.type == TokenType.REGEX:
                # Handle regex as part of expression (not as primary in this context)
                # Parse it as a complete expression which may include operators
                pattern = self.parse_expression()
                
                # Skip newlines between pattern and action
                self.skip_newlines()
                
                # Check if followed by '{'
                if self.current().type == TokenType.LBRACE:
                    # Success! This is a pattern
                    return pattern
                else:
                    # Not followed by '{', not a pattern
                    self.pos = saved_pos
                    return None
            else:
                # Token cannot start a pattern
                return None
        except:
            # Parsing failed, not a pattern
            self.pos = saved_pos
            return None
