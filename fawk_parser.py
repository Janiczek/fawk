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
        self.in_print_context = False  # Flag to disable > and >= as comparison in print
    
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
        beginfile_block = None
        patterns = []
        endfile_block = None
        end_block = None
        
        self.skip_newlines()
        
        # Parse functions, BEGIN, BEGINFILE, patterns, ENDFILE, and END in any order
        while self.current().type != TokenType.EOF:
            self.skip_newlines()
            
            if self.current().type == TokenType.FUNCTION:
                functions.append(self.parse_function_def())
            elif self.current().type == TokenType.BEGIN:
                if begin_block is not None:
                    self.error("Multiple BEGIN blocks not allowed")
                self.advance()
                begin_block = self.parse_block()
            elif self.current().type == TokenType.BEGINFILE:
                if beginfile_block is not None:
                    self.error("Multiple BEGINFILE blocks not allowed")
                self.advance()
                beginfile_block = self.parse_block()
            elif self.current().type == TokenType.ENDFILE:
                if endfile_block is not None:
                    self.error("Multiple ENDFILE blocks not allowed")
                self.advance()
                endfile_block = self.parse_block()
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
        
        return Program(functions, begin_block, beginfile_block, patterns, endfile_block, end_block)
    
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
        elif token.type == TokenType.DO:
            return self.parse_do_while_stmt()
        elif token.type == TokenType.SWITCH:
            return self.parse_switch_stmt()
        elif token.type == TokenType.RETURN:
            return self.parse_return_stmt()
        elif token.type == TokenType.EXIT:
            return self.parse_exit_stmt()
        elif token.type == TokenType.NEXT:
            self.advance()
            self.skip_statement_terminator()
            return NextStmt()
        elif token.type == TokenType.NEXTFILE:
            self.advance()
            self.skip_statement_terminator()
            return NextFileStmt()
        elif token.type == TokenType.BREAK:
            self.advance()
            self.skip_statement_terminator()
            return BreakStmt()
        elif token.type == TokenType.CONTINUE:
            self.advance()
            self.skip_statement_terminator()
            return ContinueStmt()
        elif token.type == TokenType.DELETE:
            return self.parse_delete_stmt()
        elif token.type == TokenType.DELARRAY:
            return self.parse_delarray_stmt()
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
    
    def parse_delete_stmt(self):
        from fawk_ast import DeleteStmt
        self.expect(TokenType.DELETE)
        
        # Parse the target (identifier, array access, or field access)
        target = self.parse_postfix()
        
        self.skip_statement_terminator()
        return DeleteStmt(target)
    
    def parse_delarray_stmt(self):
        from fawk_ast import DelarrayStmt
        self.expect(TokenType.DELARRAY)
        
        # Parse the target (must be an identifier - array variable name)
        target = self.parse_postfix()
        
        self.skip_statement_terminator()
        return DelarrayStmt(target)
    
    def parse_if_stmt(self) -> IfStmt:
        self.expect(TokenType.IF)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        
        # Check if braces are present - if not, parse single statement
        if self.current().type == TokenType.LBRACE:
            then_block = self.parse_block()
        else:
            # Parse single statement and wrap in Block
            stmt = self.parse_statement()
            if stmt is None:
                self.error("Expected statement after if condition")
            from fawk_ast import Block
            then_block = Block([stmt])
        
        else_block = None
        
        if self.current().type == TokenType.ELSE:
            self.advance()
            # Check if braces are present for else - if not, parse single statement
            if self.current().type == TokenType.LBRACE:
                else_block = self.parse_block()
            else:
                # Parse single statement and wrap in Block
                stmt = self.parse_statement()
                if stmt is None:
                    self.error("Expected statement after else")
                from fawk_ast import Block
                else_block = Block([stmt])
        
        return IfStmt(condition, then_block, else_block)
    
    def parse_for_stmt(self):
        self.expect(TokenType.FOR)
        self.expect(TokenType.LPAREN)
        
        # Save position to check if this is for-in or C-style for loop
        saved_pos = self.pos
        
        # Try to parse as for-in first
        # Look for: identifier IN expression
        if self.current().type == TokenType.IDENTIFIER:
            var_name = self.current().value
            self.advance()
            if self.current().type == TokenType.IN:
                # It's a for-in loop
                self.advance()
                iterable = self.parse_expression()
                self.expect(TokenType.RPAREN)
                # Check if braces are present - if not, parse single statement
                if self.current().type == TokenType.LBRACE:
                    body = self.parse_block()
                else:
                    # Parse single statement and wrap in Block
                    stmt = self.parse_statement()
                    if stmt is None:
                        self.error("Expected statement after for-in loop")
                    from fawk_ast import Block
                    body = Block([stmt])
                return ForInStmt(var_name, iterable, body)
            else:
                # Not for-in, restore position and parse as C-style for
                self.pos = saved_pos
        
        # Parse C-style for loop: for (init; condition; update) body
        # init
        init = None
        if self.current().type != TokenType.SEMICOLON:
            init = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        
        # condition
        condition = None
        if self.current().type != TokenType.SEMICOLON:
            condition = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        
        # update
        update = None
        if self.current().type != TokenType.RPAREN:
            update = self.parse_expression()
        self.expect(TokenType.RPAREN)
        
        # Check if braces are present - if not, parse single statement
        if self.current().type == TokenType.LBRACE:
            body = self.parse_block()
        else:
            # Parse single statement and wrap in Block
            stmt = self.parse_statement()
            if stmt is None:
                self.error("Expected statement after for loop")
            from fawk_ast import Block
            body = Block([stmt])
        return ForStmt(init, condition, update, body)
    
    def parse_while_stmt(self) -> WhileStmt:
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        # Check if braces are present - if not, parse single statement
        if self.current().type == TokenType.LBRACE:
            body = self.parse_block()
        else:
            # Parse single statement and wrap in Block
            stmt = self.parse_statement()
            if stmt is None:
                self.error("Expected statement after while condition")
            from fawk_ast import Block
            body = Block([stmt])
        
        return WhileStmt(condition, body)
    
    def parse_do_while_stmt(self) -> DoWhileStmt:
        self.expect(TokenType.DO)
        # Check if braces are present - if not, parse single statement
        if self.current().type == TokenType.LBRACE:
            body = self.parse_block()
        else:
            # Parse single statement and wrap in Block
            stmt = self.parse_statement()
            if stmt is None:
                self.error("Expected statement after do")
            from fawk_ast import Block
            body = Block([stmt])
        self.expect(TokenType.WHILE)
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.skip_statement_terminator()
        
        return DoWhileStmt(body, condition)
    
    def parse_switch_stmt(self) -> SwitchStmt:
        self.expect(TokenType.SWITCH)
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        cases = []
        while self.current().type != TokenType.RBRACE:
            if self.current().type == TokenType.CASE:
                self.advance()
                value = self.parse_expression()
                self.expect(TokenType.COLON)
                self.skip_newlines()
                
                # Parse statements until next case/default/rbrace
                statements = []
                while self.current().type not in [TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE]:
                    stmt = self.parse_statement()
                    if stmt:
                        statements.append(stmt)
                    self.skip_newlines()
                
                cases.append(SwitchCase(value, statements))
            
            elif self.current().type == TokenType.DEFAULT:
                self.advance()
                self.expect(TokenType.COLON)
                self.skip_newlines()
                
                # Parse statements until next case/default/rbrace
                statements = []
                while self.current().type not in [TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE]:
                    stmt = self.parse_statement()
                    if stmt:
                        statements.append(stmt)
                    self.skip_newlines()
                
                cases.append(SwitchCase(None, statements))
            
            else:
                self.error(f"Expected 'case' or 'default' in switch, got {self.current().type}")
        
        self.expect(TokenType.RBRACE)
        return SwitchStmt(expr, cases)
    
    def parse_return_stmt(self) -> ReturnStmt:
        self.expect(TokenType.RETURN)
        
        value = None
        if self.current().type not in [TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE]:
            value = self.parse_expression()
        
        self.skip_statement_terminator()
        return ReturnStmt(value)
    
    def parse_exit_stmt(self) -> ExitStmt:
        self.expect(TokenType.EXIT)
        
        code = None
        if self.current().type not in [TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE]:
            code = self.parse_expression()
        
        self.skip_statement_terminator()
        return ExitStmt(code)
    
    def parse_print_stmt(self) -> PrintStmt:
        self.expect(TokenType.PRINT)
        args = []
        
        # Consume opening parenthesis if present (print supports both print "x" and print("x"))
        has_paren = False
        if self.current().type == TokenType.LPAREN:
            self.advance()
            has_paren = True
        
        # Parse print arguments (stop before comparison operators to allow redirection)
        if self.current().type not in [TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, 
                                        TokenType.GT, TokenType.REDIRECT_APPEND, TokenType.RPAREN]:
            # Parse arguments at concatenation level (before comparisons)
            args.append(self.parse_print_arg())
            while self.current().type == TokenType.COMMA:
                self.advance()
                # Check if we hit a redirection operator or closing paren
                if self.current().type in [TokenType.GT, TokenType.REDIRECT_APPEND, TokenType.RPAREN]:
                    break
                args.append(self.parse_print_arg())
        
        # Consume closing parenthesis if we consumed opening one
        if has_paren:
            if self.current().type == TokenType.RPAREN:
                self.advance()
            # If no closing paren, that's okay - print can work without it
        
        # Check for redirection
        redirect_type = None
        redirect_target = None
        
        if self.current().type == TokenType.GT:
            redirect_type = ">"
            self.advance()
            redirect_target = self.parse_expression()
        elif self.current().type == TokenType.REDIRECT_APPEND:
            redirect_type = ">>"
            self.advance()
            redirect_target = self.parse_expression()
        
        self.skip_statement_terminator()
        return PrintStmt(args, redirect_type, redirect_target)
    
    def parse_print_arg(self) -> ASTNode:
        """Parse a print argument (stops before assignment/pipeline)"""
        # Parse at the OR level but with > and >= reserved for redirection
        # Set flag to disable > and >= as comparison operators
        saved = self.in_print_context
        self.in_print_context = True
        try:
            result = self.parse_or()
            return result
        finally:
            self.in_print_context = saved
    
    def parse_printf_stmt(self) -> 'PrintfStmt':
        from fawk_ast import PrintfStmt
        self.expect(TokenType.PRINTF)
        args = []
        
        # Parse printf arguments (stop before comparison operators to allow redirection)
        if self.current().type not in [TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, 
                                        TokenType.GT, TokenType.REDIRECT_APPEND]:
            args.append(self.parse_print_arg())
            while self.current().type == TokenType.COMMA:
                self.advance()
                # Check if we hit a redirection operator
                if self.current().type in [TokenType.GT, TokenType.REDIRECT_APPEND]:
                    break
                args.append(self.parse_print_arg())
        
        # Check for redirection
        redirect_type = None
        redirect_target = None
        
        if self.current().type == TokenType.GT:
            redirect_type = ">"
            self.advance()
            redirect_target = self.parse_expression()
        elif self.current().type == TokenType.REDIRECT_APPEND:
            redirect_type = ">>"
            self.advance()
            redirect_target = self.parse_expression()
        
        self.skip_statement_terminator()
        return PrintfStmt(args, redirect_type, redirect_target)
    
    def parse_expr_stmt(self):
        # For printf/print detection, we need to parse carefully
        # Check if this might be a printf/print call before parsing full expression
        if self.current().type == TokenType.IDENTIFIER and self.current().value in ['printf', 'print']:
            saved_pos = self.pos
            func_name = self.current().value
            self.advance()
            
            # Check if followed by LPAREN (function call)
            if self.current().type == TokenType.LPAREN:
                # Reset and parse as expression, but stop before comparisons
                self.pos = saved_pos
                # Set print context to prevent > from being consumed as comparison
                saved_context = self.in_print_context
                self.in_print_context = True
                try:
                    expr = self.parse_expression()
                finally:
                    self.in_print_context = saved_context
                
                # Now check for redirection operators
                if self.current().type in [TokenType.GT, TokenType.REDIRECT_APPEND]:
                    redirect_type = ">" if self.current().type == TokenType.GT else ">>"
                    self.advance()
                    # Parse redirect target with full expression parser
                    saved_context2 = self.in_print_context
                    self.in_print_context = False
                    try:
                        redirect_target = self.parse_expression()
                    finally:
                        self.in_print_context = saved_context2
                    
                    # Convert to appropriate statement with redirection
                    if func_name == 'printf':
                        from fawk_ast import PrintfStmt
                        self.skip_statement_terminator()
                        return PrintfStmt(expr.args, redirect_type, redirect_target)
                    else:  # print
                        self.skip_statement_terminator()
                        return PrintStmt(expr.args, redirect_type, redirect_target)
                
                self.skip_statement_terminator()
                return ExprStmt(expr)
            else:
                # Not a function call, reset and parse normally
                self.pos = saved_pos
        
        # Normal expression statement
        expr = self.parse_expression()
        self.skip_statement_terminator()
        return ExprStmt(expr)
    
    def skip_statement_terminator(self):
        while self.current().type in [TokenType.NEWLINE, TokenType.SEMICOLON]:
            self.advance()
    
    def parse_expression(self) -> ASTNode:
        return self.parse_piped_getline()
    
    def parse_piped_getline(self) -> ASTNode:
        """Parse piped getline: cmd | getline var"""
        left = self.parse_pipeline()
        
        # Check for | getline
        if self.current().type == TokenType.PIPE:
            self.advance()
            if self.current().type == TokenType.GETLINE:
                self.advance()
                # Get target variable (optional)
                target = None
                if self.current().type == TokenType.IDENTIFIER:
                    target = self.current().value
                    self.advance()
                from fawk_ast import PipedGetline
                return PipedGetline(left, target)
            else:
                self.error("Expected 'getline' after '|'")
        
        return left
    
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
        # Check if this is a destructuring pattern: [identifier, ...]
        # We need to look ahead to see if we have [ followed by identifier(s) and then =
        if self.current().type == TokenType.LBRACKET:
            # Try to parse as destructuring pattern
            saved_pos = self.pos
            try:
                pattern = self.parse_destructure_pattern()
                if self.current().type == TokenType.ASSIGN:
                    # This is a destructuring assignment
                    self.advance()
                    value = self.parse_expression()
                    return Assignment(pattern, value)
                else:
                    # Not an assignment, backtrack
                    self.pos = saved_pos
            except:
                # Not a valid destructuring pattern, backtrack
                self.pos = saved_pos
        
        # Normal assignment parsing
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
        left = self.parse_in()
        
        while self.current().type in [TokenType.EQ, TokenType.NE, TokenType.MATCH, TokenType.NOT_MATCH]:
            op = self.advance().value
            right = self.parse_in()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_in(self) -> ASTNode:
        """Parse 'in' operator for array membership checks"""
        from fawk_ast import InOp, CommaExpr
        left = self.parse_comparison()
        
        # Check for 'in' operator
        if self.current().type == TokenType.IN:
            self.advance()
            right = self.parse_comparison()
            
            # If left is a CommaExpr, extract its expressions as indices
            if isinstance(left, CommaExpr):
                return InOp(left.exprs, right)
            else:
                return InOp([left], right)
        
        return left
    
    def parse_comparison(self) -> ASTNode:
        left = self.parse_concatenation()
        
        # In print context, don't parse > as comparison (reserved for redirection)
        # but >= is still allowed since it's not a redirection operator
        allowed_ops = [TokenType.LT, TokenType.LE, TokenType.GE]
        if not self.in_print_context:
            allowed_ops.append(TokenType.GT)
        
        while self.current().type in allowed_ops:
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
        left = self.parse_power()
        
        while self.current().type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            op = self.advance().value
            right = self.parse_power()
            left = BinaryOp(op, left, right)
        
        return left
    
    def parse_power(self) -> ASTNode:
        left = self.parse_unary()
        
        # Power is right-associative: 2^3^2 = 2^(3^2)
        if self.current().type == TokenType.POWER:
            op = self.advance().value
            right = self.parse_power()  # Right-associative recursion
            return BinaryOp(op, left, right)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        if self.current().type == TokenType.INCREMENT:
            self.advance()
            operand = self.parse_unary()
            from fawk_ast import PrefixIncrement
            return PrefixIncrement(operand)
        
        if self.current().type == TokenType.DECREMENT:
            self.advance()
            operand = self.parse_unary()
            from fawk_ast import PrefixDecrement
            return PrefixDecrement(operand)
        
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
                # Array access - support multi-dimensional: arr[i,j,k]
                self.advance()
                indices = [self.parse_expression()]
                
                # Check for additional indices separated by commas
                while self.current().type == TokenType.COMMA:
                    self.advance()
                    indices.append(self.parse_expression())
                
                self.expect(TokenType.RBRACKET)
                expr = ArrayAccess(expr, indices)
            
            elif self.current().type == TokenType.INCREMENT:
                # Postfix increment: x++
                self.advance()
                from fawk_ast import PostfixIncrement
                expr = PostfixIncrement(expr)
            
            elif self.current().type == TokenType.DECREMENT:
                # Postfix decrement: x--
                self.advance()
                from fawk_ast import PostfixDecrement
                expr = PostfixDecrement(expr)
            
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
            # Could be grouped expression, comma expression, or lambda
            if self.is_lambda():
                return self.parse_lambda()
            else:
                self.advance()
                # Inside parentheses, disable print context (> is always comparison, not redirection)
                saved = self.in_print_context
                self.in_print_context = False
                try:
                    # Check if this is a comma expression (i,j) for multi-dimensional array key
                    exprs = [self.parse_expression()]
                    
                    # If we see a comma, this is a comma expression
                    if self.current().type == TokenType.COMMA:
                        while self.current().type == TokenType.COMMA:
                            self.advance()
                            exprs.append(self.parse_expression())
                        self.expect(TokenType.RPAREN)
                        # Return a CommaExpr node
                        from fawk_ast import CommaExpr
                        return CommaExpr(exprs)
                    else:
                        self.expect(TokenType.RPAREN)
                        return exprs[0]
                finally:
                    self.in_print_context = saved
        
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
    
    def parse_destructure_pattern(self) -> ASTNode:
        """Parse a destructuring pattern: [x, y] or [[x, y], [z, w]]"""
        from fawk_ast import DestructurePattern, Identifier
        
        self.expect(TokenType.LBRACKET)
        patterns = []
        
        if self.current().type != TokenType.RBRACKET:
            # Parse first pattern element
            if self.current().type == TokenType.LBRACKET:
                # Nested destructuring pattern
                patterns.append(self.parse_destructure_pattern())
            elif self.current().type == TokenType.IDENTIFIER:
                # Simple identifier
                patterns.append(Identifier(self.advance().value))
            else:
                self.error("Destructuring pattern must contain identifiers or nested patterns")
            
            # Parse remaining elements
            while self.current().type == TokenType.COMMA:
                self.advance()
                if self.current().type == TokenType.RBRACKET:
                    break
                
                if self.current().type == TokenType.LBRACKET:
                    # Nested destructuring pattern
                    patterns.append(self.parse_destructure_pattern())
                elif self.current().type == TokenType.IDENTIFIER:
                    # Simple identifier
                    patterns.append(Identifier(self.advance().value))
                else:
                    self.error("Destructuring pattern must contain identifiers or nested patterns")
        
        self.expect(TokenType.RBRACKET)
        return DestructurePattern(patterns)
    
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
