{-# LANGUAGE OverloadedStrings #-}

module Parser where

import AST
import Control.Monad.Combinators.Expr
import Data.Void
import Text.Megaparsec
import Text.Megaparsec.Char
import qualified Text.Megaparsec.Char.Lexer as L

type Parser = Parsec Void String

-- | Space consumer that handles comments and whitespace
sc :: Parser ()
sc = L.space
  space1
  (L.skipLineComment "#")
  empty

-- | Lexeme parser that consumes trailing whitespace
lexeme :: Parser a -> Parser a
lexeme = L.lexeme sc

-- | Symbol parser
symbol :: String -> Parser String
symbol = L.symbol sc

-- | Parse a keyword
keyword :: String -> Parser ()
keyword w = lexeme (string w *> notFollowedBy alphaNumChar)

-- | Parse an identifier
identifier :: Parser String
identifier = lexeme ((:) <$> letterChar <*> many (alphaNumChar <|> char '_'))
  <?> "identifier"

-- | Reserved words
reserved :: [String]
reserved = ["function", "return", "if", "else", "for", "in", "while", 
            "BEGIN", "END", "global", "NR"]

-- | Parse a non-reserved identifier
varName :: Parser String
varName = try $ do
  name <- identifier
  if name `elem` reserved
    then fail $ "keyword " ++ show name ++ " cannot be used as identifier"
    else return name

-- | Parse an integer
integer :: Parser Int
integer = lexeme L.decimal

-- | Parse a floating point number
double :: Parser Double
double = lexeme L.float

-- | Parse a number (int or double)
number :: Parser Expr
number = try (EDouble <$> double) <|> (EInt <$> integer)

-- | Parse a string literal
stringLit :: Parser String
stringLit = lexeme (char '"' >> manyTill L.charLiteral (char '"'))

-- | Parse parenthesized expression
parens :: Parser a -> Parser a
parens = between (symbol "(") (symbol ")")

-- | Parse braces
braces :: Parser a -> Parser a
braces = between (symbol "{") (symbol "}")

-- | Parse brackets
brackets :: Parser a -> Parser a
brackets = between (symbol "[") (symbol "]")

-- | Parse an expression
expr :: Parser Expr
expr = makeExprParser term operatorTable

-- | Expression term (primary expressions)
term :: Parser Expr
term = choice
  [ try lambda
  , try number
  , EString <$> stringLit
  , try fieldVar
  , try arrayLiteral
  , try functionCall
  , EVar <$> varName
  , parens expr
  ] >>= postfix

-- | Postfix operators (array indexing)
postfix :: Expr -> Parser Expr
postfix e = (do
    idx <- brackets expr
    postfix (EIndex e idx)
  ) <|> return e

-- | Field variable ($1, $2, etc.)
fieldVar :: Parser Expr
fieldVar = do
  _ <- symbol "$"
  n <- integer
  return (EField n)

-- | Array literal
arrayLiteral :: Parser Expr
arrayLiteral = EArray <$> brackets (arrayElem `sepBy` symbol ",")

-- | Array element (regular or key=>value)
arrayElem :: Parser ArrayElem
arrayElem = try keyValue <|> (AEValue <$> expr)
  where
    keyValue = do
      key <- expr
      _ <- symbol "=>"
      val <- expr
      return (AEKeyValue key val)

-- | Lambda/arrow function
lambda :: Parser Expr
lambda = do
  params <- parens (varName `sepBy` symbol ",")
  _ <- symbol "=>"
  body <- braces (many stmt)
  return (ELambda params body)

-- | Function call
functionCall :: Parser Expr
functionCall = do
  name <- try $ do
    n <- varName
    _ <- lookAhead (symbol "(")
    return n
  args <- parens (expr `sepBy` symbol ",")
  return (ECall (EVar name) args)

-- | Operator table for expression parsing
operatorTable :: [[Operator Parser Expr]]
operatorTable =
  [ [ Prefix (EUnOp Neg <$ symbol "-")
    , Prefix (EUnOp Not <$ symbol "!")
    ]
  , [ InfixL (EBinOp Mul <$ symbol "*")
    , InfixL (EBinOp Div <$ symbol "/")
    , InfixL (EBinOp Mod <$ symbol "%")
    ]
  , [ InfixL (EBinOp Add <$ symbol "+")
    , InfixL (EBinOp Sub <$ symbol "-")
    ]
  , [ InfixN (EBinOp Lte <$ symbol "<=")
    , InfixN (EBinOp Gte <$ symbol ">=")
    , InfixN (EBinOp Lt <$ symbol "<")
    , InfixN (EBinOp Gt <$ symbol ">")
    ]
  , [ InfixN (EBinOp Eq <$ symbol "==")
    , InfixN (EBinOp Neq <$ symbol "!=")
    ]
  , [ InfixL (EBinOp And <$ symbol "&&")
    ]
  , [ InfixL (EBinOp Or <$ symbol "||")
    ]
  , [ InfixL (EPipeline <$ symbol "|>")
    ]
  ]

-- | Parse a statement
stmt :: Parser Stmt
stmt = choice
  [ try returnStmt
  , try ifStmt
  , try forStmt
  , try whileStmt
  , try globalStmt
  , try printStmt
  , try indexAssign
  , try assignStmt
  , exprStmt
  ]

-- | Print statement (special case, can omit parentheses)
printStmt :: Parser Stmt
printStmt = do
  name <- try $ do
    n <- identifier
    if n == "print"
      then return n
      else fail "not print"
  args <- (try (parens (expr `sepBy` symbol ","))) <|> ((:[]) <$> expr)
  return (SExpr (ECall (EVar name) args))

-- | Expression statement
exprStmt :: Parser Stmt
exprStmt = SExpr <$> expr

-- | Assignment statement
assignStmt :: Parser Stmt
assignStmt = do
  var <- varName
  _ <- symbol "="
  val <- expr
  return (SAssign var val)

-- | Array index assignment
indexAssign :: Parser Stmt
indexAssign = do
  arr <- varName
  idx <- brackets expr
  _ <- symbol "="
  val <- expr
  return (SIndexAssign (EVar arr) idx val)

-- | Return statement
returnStmt :: Parser Stmt
returnStmt = do
  keyword "return"
  SReturn <$> expr

-- | If statement
ifStmt :: Parser Stmt
ifStmt = do
  keyword "if"
  cond <- parens expr
  thenBlock <- braces (many stmt)
  elseBlock <- option [] (keyword "else" >> braces (many stmt))
  return (SIf cond thenBlock elseBlock)

-- | For-in loop
forStmt :: Parser Stmt
forStmt = do
  keyword "for"
  _ <- symbol "("
  var <- varName
  keyword "in"
  arr <- expr
  _ <- symbol ")"
  body <- braces (many stmt)
  return (SFor var arr body)

-- | While loop
whileStmt :: Parser Stmt
whileStmt = do
  keyword "while"
  cond <- parens expr
  body <- braces (many stmt)
  return (SWhile cond body)

-- | Global declaration
globalStmt :: Parser Stmt
globalStmt = do
  keyword "global"
  vars <- varName `sepBy` symbol ","
  return (SGlobal vars)

-- | Parse a function definition
funcDef :: Parser FuncDef
funcDef = do
  keyword "function"
  name <- varName
  params <- parens (varName `sepBy` symbol ",")
  body <- braces (many stmt)
  return (FuncDef name params body)

-- | Parse a pattern
pattern_ :: Parser Pattern
pattern_ = choice
  [ PBegin <$ keyword "BEGIN"
  , PEnd <$ keyword "END"
  , PExpr <$> expr
  ]

-- | Parse an action block
action :: Parser Action
action = do
  pat <- option PAll (try pattern_)
  body <- braces (many stmt)
  return (Action pat body)

-- | Parse a complete program
program :: Parser Program
program = do
  sc
  funcs <- many funcDef
  actions <- many action
  eof
  return (Program funcs actions)

-- | Parse a FAWK program from a string
parseFawk :: String -> Either String Program
parseFawk input =
  case parse program "" input of
    Left err -> Left (errorBundlePretty err)
    Right prog -> Right prog
