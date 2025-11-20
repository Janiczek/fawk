use crate::ast::*;
use crate::lexer::Token;

pub struct Parser {
    tokens: Vec<Token>,
    current: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Parser { tokens, current: 0 }
    }
    
    fn current_token(&self) -> &Token {
        self.tokens.get(self.current).unwrap_or(&Token::Eof)
    }
    
    fn peek(&self, offset: usize) -> &Token {
        self.tokens.get(self.current + offset).unwrap_or(&Token::Eof)
    }
    
    fn advance(&mut self) -> Token {
        let token = self.current_token().clone();
        if self.current < self.tokens.len() {
            self.current += 1;
        }
        token
    }
    
    fn skip_newlines(&mut self) {
        while matches!(self.current_token(), Token::Newline) {
            self.advance();
        }
    }
    
    fn expect(&mut self, expected: Token) {
        let token = self.advance();
        if token != expected {
            panic!("Expected {:?}, got {:?}", expected, token);
        }
    }
    
    fn check(&self, token: &Token) -> bool {
        std::mem::discriminant(self.current_token()) == std::mem::discriminant(token)
    }
    
    pub fn parse(&mut self) -> Program {
        let mut items = Vec::new();
        
        self.skip_newlines();
        
        while !matches!(self.current_token(), Token::Eof) {
            self.skip_newlines();
            if matches!(self.current_token(), Token::Eof) {
                break;
            }
            
            if matches!(self.current_token(), Token::Function) {
                items.push(Item::Function(self.parse_function()));
            } else {
                items.push(Item::Rule(self.parse_rule()));
            }
            
            self.skip_newlines();
        }
        
        Program { items }
    }
    
    fn parse_function(&mut self) -> Function {
        self.expect(Token::Function);
        
        let name = match self.advance() {
            Token::Ident(n) => n,
            t => panic!("Expected function name, got {:?}", t),
        };
        
        self.expect(Token::LeftParen);
        
        let mut params = Vec::new();
        while !matches!(self.current_token(), Token::RightParen) {
            match self.advance() {
                Token::Ident(p) => params.push(p),
                t => panic!("Expected parameter name, got {:?}", t),
            }
            
            if matches!(self.current_token(), Token::Comma) {
                self.advance();
            }
        }
        
        self.expect(Token::RightParen);
        self.skip_newlines();
        self.expect(Token::LeftBrace);
        
        let body = self.parse_block();
        
        self.expect(Token::RightBrace);
        
        Function { name, params, body }
    }
    
    fn parse_rule(&mut self) -> Rule {
        let pattern = if matches!(self.current_token(), Token::Begin) {
            self.advance();
            Some(Pattern::Begin)
        } else if matches!(self.current_token(), Token::End) {
            self.advance();
            Some(Pattern::End)
        } else if matches!(self.current_token(), Token::LeftBrace) {
            None
        } else {
            Some(Pattern::Expression(self.parse_expression()))
        };
        
        self.skip_newlines();
        self.expect(Token::LeftBrace);
        
        let action = self.parse_block();
        
        self.expect(Token::RightBrace);
        
        Rule { pattern, action }
    }
    
    fn parse_block(&mut self) -> Vec<Stmt> {
        let mut stmts = Vec::new();
        
        self.skip_newlines();
        
        while !matches!(self.current_token(), Token::RightBrace | Token::Eof) {
            self.skip_newlines();
            if matches!(self.current_token(), Token::RightBrace | Token::Eof) {
                break;
            }
            
            stmts.push(self.parse_statement());
            
            // Optional semicolon or newline
            if matches!(self.current_token(), Token::Semicolon | Token::Newline) {
                self.advance();
            }
            
            self.skip_newlines();
        }
        
        stmts
    }
    
    fn parse_statement(&mut self) -> Stmt {
        self.skip_newlines();
        
        match self.current_token() {
            Token::Print => {
                self.advance();
                let mut args = Vec::new();
                
                // Parse print arguments (comma-separated expressions)
                if !matches!(self.current_token(), Token::Newline | Token::Semicolon | Token::RightBrace) {
                    loop {
                        args.push(self.parse_expression());
                        
                        if matches!(self.current_token(), Token::Comma) {
                            self.advance();
                        } else {
                            break;
                        }
                    }
                }
                
                Stmt::Print { args }
            }
            Token::Return => {
                self.advance();
                if matches!(self.current_token(), Token::Newline | Token::Semicolon | Token::RightBrace) {
                    Stmt::Return(None)
                } else {
                    let expr = self.parse_expression();
                    Stmt::Return(Some(expr))
                }
            }
            Token::If => self.parse_if(),
            Token::While => self.parse_while(),
            Token::For => self.parse_for(),
            Token::Break => {
                self.advance();
                Stmt::Break
            }
            Token::Continue => {
                self.advance();
                Stmt::Continue
            }
            Token::Global => {
                self.advance();
                let mut names = Vec::new();
                loop {
                    match self.advance() {
                        Token::Ident(n) => names.push(n),
                        t => panic!("Expected identifier, got {:?}", t),
                    }
                    if matches!(self.current_token(), Token::Comma) {
                        self.advance();
                    } else {
                        break;
                    }
                }
                Stmt::GlobalDecl { names }
            }
            _ => {
                // Try to parse assignment or expression
                let expr = self.parse_expression();
                
                if matches!(self.current_token(), Token::Equal) {
                    self.advance();
                    let value = self.parse_expression();
                    Stmt::Assign { target: expr, value }
                } else {
                    Stmt::Expr(expr)
                }
            }
        }
    }
    
    fn parse_if(&mut self) -> Stmt {
        self.expect(Token::If);
        
        self.expect(Token::LeftParen);
        let condition = self.parse_expression();
        self.expect(Token::RightParen);
        
        self.skip_newlines();
        self.expect(Token::LeftBrace);
        let then_branch = self.parse_block();
        self.expect(Token::RightBrace);
        
        self.skip_newlines();
        
        let else_branch = if matches!(self.current_token(), Token::Else) {
            self.advance();
            self.skip_newlines();
            self.expect(Token::LeftBrace);
            let else_stmts = self.parse_block();
            self.expect(Token::RightBrace);
            Some(else_stmts)
        } else {
            None
        };
        
        Stmt::If { condition, then_branch, else_branch }
    }
    
    fn parse_while(&mut self) -> Stmt {
        self.expect(Token::While);
        
        self.expect(Token::LeftParen);
        let condition = self.parse_expression();
        self.expect(Token::RightParen);
        
        self.skip_newlines();
        self.expect(Token::LeftBrace);
        let body = self.parse_block();
        self.expect(Token::RightBrace);
        
        Stmt::While { condition, body }
    }
    
    fn parse_for(&mut self) -> Stmt {
        self.expect(Token::For);
        
        self.expect(Token::LeftParen);
        let var = match self.advance() {
            Token::Ident(v) => v,
            t => panic!("Expected identifier in for loop, got {:?}", t),
        };
        
        self.expect(Token::In);
        let iterable = self.parse_expression();
        self.expect(Token::RightParen);
        
        self.skip_newlines();
        self.expect(Token::LeftBrace);
        let body = self.parse_block();
        self.expect(Token::RightBrace);
        
        Stmt::For { var, iterable, body }
    }
    
    fn parse_expression(&mut self) -> Expr {
        self.parse_pipeline()
    }
    
    fn parse_pipeline(&mut self) -> Expr {
        let mut expr = self.parse_or();
        
        loop {
            self.skip_newlines();  // Allow newlines before |>
            
            if matches!(self.current_token(), Token::PipeGreater) {
                self.advance();
                self.skip_newlines();  // Allow newlines after |>
                let right = self.parse_or();
                expr = Expr::Pipeline {
                    left: Box::new(expr),
                    right: Box::new(right),
                };
            } else {
                break;
            }
        }
        
        expr
    }
    
    fn parse_or(&mut self) -> Expr {
        let mut expr = self.parse_and();
        
        while matches!(self.current_token(), Token::PipePipe) {
            self.advance();
            let right = self.parse_and();
            expr = Expr::Binary {
                left: Box::new(expr),
                op: BinOp::Or,
                right: Box::new(right),
            };
        }
        
        expr
    }
    
    fn parse_and(&mut self) -> Expr {
        let mut expr = self.parse_equality();
        
        while matches!(self.current_token(), Token::AmpAmp) {
            self.advance();
            let right = self.parse_equality();
            expr = Expr::Binary {
                left: Box::new(expr),
                op: BinOp::And,
                right: Box::new(right),
            };
        }
        
        expr
    }
    
    fn parse_equality(&mut self) -> Expr {
        let mut expr = self.parse_comparison();
        
        while let Token::EqualEqual | Token::BangEqual = self.current_token() {
            let op = match self.advance() {
                Token::EqualEqual => BinOp::Equal,
                Token::BangEqual => BinOp::NotEqual,
                _ => unreachable!(),
            };
            
            let right = self.parse_comparison();
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
            };
        }
        
        expr
    }
    
    fn parse_comparison(&mut self) -> Expr {
        let mut expr = self.parse_term();
        
        while let Token::Less | Token::LessEqual | Token::Greater | Token::GreaterEqual = self.current_token() {
            let op = match self.advance() {
                Token::Less => BinOp::Less,
                Token::LessEqual => BinOp::LessEqual,
                Token::Greater => BinOp::Greater,
                Token::GreaterEqual => BinOp::GreaterEqual,
                _ => unreachable!(),
            };
            
            let right = self.parse_term();
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
            };
        }
        
        expr
    }
    
    fn parse_term(&mut self) -> Expr {
        let mut expr = self.parse_factor();
        
        while let Token::Plus | Token::Minus = self.current_token() {
            let op = match self.advance() {
                Token::Plus => BinOp::Add,
                Token::Minus => BinOp::Sub,
                _ => unreachable!(),
            };
            
            let right = self.parse_factor();
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
            };
        }
        
        expr
    }
    
    fn parse_factor(&mut self) -> Expr {
        let mut expr = self.parse_unary();
        
        while let Token::Star | Token::Slash | Token::Percent = self.current_token() {
            let op = match self.advance() {
                Token::Star => BinOp::Mul,
                Token::Slash => BinOp::Div,
                Token::Percent => BinOp::Mod,
                _ => unreachable!(),
            };
            
            let right = self.parse_unary();
            expr = Expr::Binary {
                left: Box::new(expr),
                op,
                right: Box::new(right),
            };
        }
        
        expr
    }
    
    fn parse_unary(&mut self) -> Expr {
        match self.current_token() {
            Token::Minus => {
                self.advance();
                let expr = self.parse_unary();
                Expr::Unary {
                    op: UnOp::Neg,
                    expr: Box::new(expr),
                }
            }
            Token::Bang => {
                self.advance();
                let expr = self.parse_unary();
                Expr::Unary {
                    op: UnOp::Not,
                    expr: Box::new(expr),
                }
            }
            Token::Dollar => {
                self.advance();
                let expr = self.parse_postfix();
                Expr::Field(Box::new(expr))
            }
            _ => self.parse_postfix(),
        }
    }
    
    fn parse_postfix(&mut self) -> Expr {
        let mut expr = self.parse_primary();
        
        loop {
            match self.current_token() {
                Token::LeftParen => {
                    self.advance();
                    let mut args = Vec::new();
                    
                    while !matches!(self.current_token(), Token::RightParen) {
                        args.push(self.parse_expression());
                        if matches!(self.current_token(), Token::Comma) {
                            self.advance();
                        }
                    }
                    
                    self.expect(Token::RightParen);
                    
                    expr = Expr::Call {
                        func: Box::new(expr),
                        args,
                    };
                }
                Token::LeftBracket => {
                    self.advance();
                    let index = self.parse_expression();
                    self.expect(Token::RightBracket);
                    
                    expr = Expr::Index {
                        array: Box::new(expr),
                        index: Box::new(index),
                    };
                }
                _ => break,
            }
        }
        
        expr
    }
    
    fn parse_primary(&mut self) -> Expr {
        match self.current_token().clone() {
            Token::Number(n) => {
                self.advance();
                Expr::Number(n)
            }
            Token::String(s) => {
                self.advance();
                Expr::String(s)
            }
            Token::Ident(name) => {
                self.advance();
                Expr::Ident(name)
            }
            Token::LeftParen => {
                self.advance();
                
                // Check if it's a lambda
                if self.check(&Token::RightParen) || self.check(&Token::Ident(String::new())) {
                    // Peek ahead to see if there's an arrow
                    let mut lookahead = 1;
                    let mut paren_count = 1;
                    let mut is_lambda = false;
                    
                    loop {
                        match self.peek(lookahead) {
                            Token::RightParen => {
                                paren_count -= 1;
                                if paren_count == 0 {
                                    // Check if next is arrow
                                    if matches!(self.peek(lookahead + 1), Token::Arrow) {
                                        is_lambda = true;
                                    }
                                    break;
                                }
                            }
                            Token::LeftParen => paren_count += 1,
                            Token::Eof => break,
                            _ => {}
                        }
                        lookahead += 1;
                    }
                    
                    if is_lambda {
                        return self.parse_lambda();
                    }
                }
                
                // Regular parenthesized expression
                let expr = self.parse_expression();
                self.expect(Token::RightParen);
                expr
            }
            Token::LeftBracket => {
                self.advance();
                self.parse_array()
            }
            t => panic!("Unexpected token in expression: {:?}", t),
        }
    }
    
    fn parse_lambda(&mut self) -> Expr {
        // Already consumed the '('
        let mut params = Vec::new();
        
        while !matches!(self.current_token(), Token::RightParen) {
            match self.advance() {
                Token::Ident(p) => params.push(p),
                t => panic!("Expected parameter name in lambda, got {:?}", t),
            }
            
            if matches!(self.current_token(), Token::Comma) {
                self.advance();
            }
        }
        
        self.expect(Token::RightParen);
        self.expect(Token::Arrow);
        self.skip_newlines();
        self.expect(Token::LeftBrace);
        
        let body = self.parse_block();
        
        self.expect(Token::RightBrace);
        
        Expr::Lambda { params, body }
    }
    
    fn parse_array(&mut self) -> Expr {
        // Already consumed the '['
        let mut elements = Vec::new();
        
        while !matches!(self.current_token(), Token::RightBracket) {
            let first_expr = self.parse_expression();
            
            if matches!(self.current_token(), Token::Arrow) {
                // Key-value pair
                self.advance();
                let value_expr = self.parse_expression();
                elements.push(ArrayElement::KeyValue {
                    key: first_expr,
                    value: value_expr,
                });
            } else {
                // Regular value
                elements.push(ArrayElement::Value(first_expr));
            }
            
            if matches!(self.current_token(), Token::Comma) {
                self.advance();
            }
        }
        
        self.expect(Token::RightBracket);
        
        Expr::Array(elements)
    }
}
