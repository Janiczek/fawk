{-# LANGUAGE LambdaCase #-}

module AST where

import qualified Data.Map.Strict as Map

-- | FAWK Value types
data Value
  = VInt Int
  | VDouble Double
  | VString String
  | VArray (Map.Map Value Value)  -- Arrays (regular and associative)
  | VFunction [String] [Stmt] Env  -- Function with parameters, body, and captured environment
  | VBuiltin String ([Value] -> IO Value)  -- Built-in functions
  | VNull

instance Show Value where
  show (VInt n) = "VInt " ++ show n
  show (VDouble d) = "VDouble " ++ show d
  show (VString s) = "VString " ++ show s
  show (VArray m) = "VArray " ++ show m
  show (VFunction params _ _) = "VFunction " ++ show params ++ " <body> <env>"
  show (VBuiltin name _) = "VBuiltin " ++ show name
  show VNull = "VNull"

instance Eq Value where
  VInt a == VInt b = a == b
  VDouble a == VDouble b = a == b
  VString a == VString b = a == b
  VNull == VNull = True
  VInt a == VDouble b = fromIntegral a == b
  VDouble a == VInt b = a == fromIntegral b
  _ == _ = False

instance Ord Value where
  compare (VInt a) (VInt b) = compare a b
  compare (VDouble a) (VDouble b) = compare a b
  compare (VString a) (VString b) = compare a b
  compare (VInt a) (VDouble b) = compare (fromIntegral a) b
  compare (VDouble a) (VInt b) = compare a (fromIntegral b)
  compare VNull VNull = EQ
  compare _ _ = EQ

-- | Environment for variable bindings
type Env = Map.Map String Value

-- | Result of statement execution (for early returns)
data StmtResult
  = SRNormal Value      -- Normal completion
  | SRReturn Value      -- Early return
  deriving (Show, Eq)

-- | Expression AST
data Expr
  = EInt Int
  | EDouble Double
  | EString String
  | EVar String
  | EArray [ArrayElem]  -- Array literal
  | EIndex Expr Expr    -- Array indexing
  | EBinOp BinOp Expr Expr
  | EUnOp UnOp Expr
  | ECall Expr [Expr]   -- Function call
  | ELambda [String] [Stmt]  -- Anonymous function (arrow syntax)
  | EPipeline Expr Expr  -- Pipeline operator |>
  | EField Int          -- Field variable $1, $2, etc.
  deriving (Show, Eq)

-- | Array element (for literals)
data ArrayElem
  = AEValue Expr         -- Regular array element
  | AEKeyValue Expr Expr -- Associative array element (key => value)
  deriving (Show, Eq)

-- | Binary operators
data BinOp
  = Add | Sub | Mul | Div | Mod
  | Eq | Neq | Lt | Gt | Lte | Gte
  | And | Or
  deriving (Show, Eq)

-- | Unary operators
data UnOp
  = Neg | Not
  deriving (Show, Eq)

-- | Statement AST
data Stmt
  = SExpr Expr                    -- Expression statement
  | SAssign String Expr           -- Variable assignment
  | SIndexAssign Expr Expr Expr   -- Array index assignment
  | SReturn Expr                  -- Return statement
  | SIf Expr [Stmt] [Stmt]        -- If-else statement
  | SFor String Expr [Stmt]       -- For-in loop
  | SWhile Expr [Stmt]            -- While loop
  | SBlock [Stmt]                 -- Block of statements
  | SGlobal [String]              -- Global declaration
  deriving (Show, Eq)

-- | Function definition
data FuncDef = FuncDef
  { funcName :: String
  , funcParams :: [String]
  , funcBody :: [Stmt]
  } deriving (Show, Eq)

-- | Pattern for AWK-style pattern-action blocks
data Pattern
  = PBegin                  -- BEGIN pattern
  | PEnd                    -- END pattern
  | PExpr Expr              -- Expression pattern
  | PAll                    -- Match all (no pattern specified)
  deriving (Show, Eq)

-- | Action block
data Action = Action
  { actionPattern :: Pattern
  , actionBody :: [Stmt]
  } deriving (Show, Eq)

-- | Top-level program structure
data Program = Program
  { progFunctions :: [FuncDef]
  , progActions :: [Action]
  } deriving (Show, Eq)
