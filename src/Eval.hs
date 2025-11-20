{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE FlexibleContexts #-}

module Eval where

import AST
import Control.Monad.State
import Control.Monad.Except
import qualified Data.Map.Strict as Map
import Data.List (intercalate)

-- | Evaluation monad with state and error handling
type EvalM = StateT EvalState (ExceptT String IO)

-- | Evaluation state
data EvalState = EvalState
  { esGlobals :: Env            -- Global variables
  , esLocals :: [Env]           -- Stack of local environments
  , esFields :: Map.Map Int String  -- Current line fields
  , esNR :: Int                 -- Current line number
  , esCurrentLine :: String     -- Current input line
  } deriving (Show)

-- | Initial evaluation state
initialState :: EvalState
initialState = EvalState
  { esGlobals = Map.empty
  , esLocals = []
  , esFields = Map.empty
  , esNR = 0
  , esCurrentLine = ""
  }

-- | Run evaluation
runEval :: EvalM a -> EvalState -> IO (Either String (a, EvalState))
runEval m s = runExceptT (runStateT m s)

-- | Lookup a variable in the environment
lookupVar :: String -> EvalM (Maybe Value)
lookupVar name = do
  st <- get
  -- First check locals (from innermost to outermost)
  case findInLocals (esLocals st) of
    Just val -> return (Just val)
    Nothing -> return (Map.lookup name (esGlobals st))
  where
    findInLocals [] = Nothing
    findInLocals (env:envs) =
      case Map.lookup name env of
        Just val -> Just val
        Nothing -> findInLocals envs

-- | Set a variable in the current scope
setVar :: String -> Value -> EvalM ()
setVar name val = do
  st <- get
  case esLocals st of
    -- If we have local scopes, set in the innermost one
    (env:envs) -> put st { esLocals = Map.insert name val env : envs }
    -- Otherwise, set in globals
    [] -> put st { esGlobals = Map.insert name val (esGlobals st) }

-- | Declare global variables (initialized to 0 like AWK)
declareGlobals :: [String] -> EvalM ()
declareGlobals names = do
  st <- get
  let globals' = foldr (\name acc -> Map.insert name (VInt 0) acc) (esGlobals st) names
  put st { esGlobals = globals' }

-- | Push a new local scope
pushScope :: Env -> EvalM ()
pushScope env = modify $ \st -> st { esLocals = env : esLocals st }

-- | Pop a local scope
popScope :: EvalM ()
popScope = modify $ \st -> st { esLocals = drop 1 (esLocals st) }

-- | Get field value
getField :: Int -> EvalM Value
getField n = do
  st <- get
  case Map.lookup n (esFields st) of
    Just str -> return (VString str)
    Nothing -> return (VString "")

-- | Evaluate an expression
evalExpr :: Expr -> EvalM Value
evalExpr = \case
  EInt n -> return (VInt n)
  EDouble d -> return (VDouble d)
  EString s -> return (VString s)
  
  EVar name -> do
    mval <- lookupVar name
    case mval of
      Just val -> return val
      Nothing -> return VNull
  
  EArray elems -> do
    arr <- foldM insertElem Map.empty (zip [0..] elems)
    return (VArray arr)
    where
      insertElem acc (idx, AEValue e) = do
        val <- evalExpr e
        return (Map.insert (VInt idx) val acc)
      insertElem acc (_, AEKeyValue ke ve) = do
        key <- evalExpr ke
        val <- evalExpr ve
        return (Map.insert key val acc)
  
  EIndex arr idx -> do
    arrVal <- evalExpr arr
    idxVal <- evalExpr idx
    case arrVal of
      VArray m -> return (Map.findWithDefault VNull idxVal m)
      _ -> throwError "Cannot index non-array value"
  
  EBinOp op e1 e2 -> do
    v1 <- evalExpr e1
    v2 <- evalExpr e2
    evalBinOp op v1 v2
  
  EUnOp op e -> do
    v <- evalExpr e
    evalUnOp op v
  
  ECall func args -> do
    funcVal <- evalExpr func
    argVals <- mapM evalExpr args
    callFunction funcVal argVals
  
  ELambda params body -> do
    -- Capture current environment
    st <- get
    let capturedEnv = case esLocals st of
          [] -> esGlobals st
          (env:_) -> env
    return (VFunction params body capturedEnv)
  
  EPipeline left right -> do
    leftVal <- evalExpr left
    -- Handle the right side specially for function calls
    case right of
      ECall func args -> do
        -- Evaluate function and arguments, then add piped value as last argument
        funcVal <- evalExpr func
        argVals <- mapM evalExpr args
        callFunction funcVal (argVals ++ [leftVal])
      _ -> do
        -- Otherwise, treat right side as a unary function
        rightVal <- evalExpr right
        callFunction rightVal [leftVal]
  
  EField n -> getField n

-- | Evaluate binary operator
evalBinOp :: BinOp -> Value -> Value -> EvalM Value
evalBinOp op v1 v2 = case op of
  Add -> numOp (+) v1 v2
  Sub -> numOp (-) v1 v2
  Mul -> numOp (*) v1 v2
  Div -> numOp (/) v1 v2
  Mod -> intOp mod v1 v2
  Eq -> return $ VInt (if v1 == v2 then 1 else 0)
  Neq -> return $ VInt (if v1 /= v2 then 1 else 0)
  Lt -> cmpOp "lt" v1 v2
  Gt -> cmpOp "gt" v1 v2
  Lte -> cmpOp "lte" v1 v2
  Gte -> cmpOp "gte" v1 v2
  And -> return $ VInt (if isTruthy v1 && isTruthy v2 then 1 else 0)
  Or -> return $ VInt (if isTruthy v1 || isTruthy v2 then 1 else 0)
  where
    numOp f (VInt a) (VInt b) = return (VInt (truncate (f (fromIntegral a) (fromIntegral b))))
    numOp f (VDouble a) (VDouble b) = return (VDouble (f a b))
    numOp f (VInt a) (VDouble b) = return (VDouble (f (fromIntegral a) b))
    numOp f (VDouble a) (VInt b) = return (VDouble (f a (fromIntegral b)))
    numOp f VNull b = numOp f (VInt 0) b  -- AWK: treat null as 0
    numOp f a VNull = numOp f a (VInt 0)
    numOp f (VString s) b = numOp f (stringToNum s) b  -- AWK: convert strings to numbers
    numOp f a (VString s) = numOp f a (stringToNum s)
    numOp _ _ _ = throwError "Type error in numeric operation"
    
    intOp f (VInt a) (VInt b) = return (VInt (f a b))
    intOp _ _ _ = throwError "Type error in integer operation"
    
    stringToNum s = case reads s of
      [(n, "")] -> VInt n
      _ -> case reads s of
        [(d, "")] -> VDouble d
        _ -> VInt 0
    
    cmpOp opName (VInt a) (VInt b) = return $ VInt (if doCmp opName (fromIntegral a) (fromIntegral b) then 1 else 0)
    cmpOp opName (VDouble a) (VDouble b) = return $ VInt (if doCmp opName a b then 1 else 0)
    cmpOp opName (VInt a) (VDouble b) = return $ VInt (if doCmp opName (fromIntegral a) b then 1 else 0)
    cmpOp opName (VDouble a) (VInt b) = return $ VInt (if doCmp opName a (fromIntegral b) then 1 else 0)
    cmpOp opName (VString s) b = cmpOp opName (stringToNum s) b
    cmpOp opName a (VString s) = cmpOp opName a (stringToNum s)
    cmpOp opName VNull b = cmpOp opName (VInt 0) b
    cmpOp opName a VNull = cmpOp opName a (VInt 0)
    cmpOp _ _ _ = return $ VInt 0
    
    doCmp :: String -> Double -> Double -> Bool
    doCmp "lt" a b = a < b
    doCmp "gt" a b = a > b
    doCmp "lte" a b = a <= b
    doCmp "gte" a b = a >= b
    doCmp _ _ _ = False

-- | Evaluate unary operator
evalUnOp :: UnOp -> Value -> EvalM Value
evalUnOp Neg (VInt n) = return (VInt (-n))
evalUnOp Neg (VDouble d) = return (VDouble (-d))
evalUnOp Not v = return (VInt (if isTruthy v then 0 else 1))
evalUnOp _ _ = throwError "Type error in unary operation"

-- | Check if a value is truthy
isTruthy :: Value -> Bool
isTruthy VNull = False
isTruthy (VInt 0) = False
isTruthy (VDouble 0.0) = False
isTruthy (VString "") = False
isTruthy _ = True

-- | Call a function
callFunction :: Value -> [Value] -> EvalM Value
callFunction (VFunction params body capturedEnv) args = do
  -- Create new local environment with parameters bound to arguments
  let paramEnv = Map.fromList (zip params args)
  -- Merge captured environment with parameter bindings
  let newEnv = Map.union paramEnv capturedEnv
  
  -- Push new scope and evaluate body
  pushScope newEnv
  stmtResult <- evalStmts body
  popScope
  case stmtResult of
    SRReturn val -> return val
    SRNormal val -> return val

callFunction (VBuiltin _ f) args = liftIO (f args)
callFunction _ _ = throwError "Cannot call non-function value"

-- | Execute statements
evalStmts :: [Stmt] -> EvalM StmtResult
evalStmts [] = return (SRNormal VNull)
evalStmts (s:ss) = do
  result <- evalStmt s
  case result of
    SRReturn v -> return (SRReturn v)
    SRNormal v -> 
      if null ss
        then return (SRNormal v)
        else evalStmts ss

-- | Execute a single statement
evalStmt :: Stmt -> EvalM StmtResult
evalStmt = \case
  SExpr e -> SRNormal <$> evalExpr e
  
  SAssign name e -> do
    val <- evalExpr e
    setVar name val
    return (SRNormal val)
  
  SIndexAssign arr idx val -> do
    arrVal <- evalExpr arr
    idxVal <- evalExpr idx
    valVal <- evalExpr val
    case arrVal of
      VArray m -> do
        let newArray = VArray (Map.insert idxVal valVal m)
        -- Update the array variable
        case arr of
          EVar name -> setVar name newArray
          _ -> throwError "Cannot assign to non-variable array"
        return (SRNormal valVal)
      _ -> throwError "Cannot index assign to non-array"
  
  SReturn e -> do
    val <- evalExpr e
    return (SRReturn val)
  
  SIf cond thenStmts elseStmts -> do
    condVal <- evalExpr cond
    if isTruthy condVal
      then evalStmts thenStmts
      else evalStmts elseStmts
  
  SFor var arr body -> do
    arrVal <- evalExpr arr
    case arrVal of
      VArray m -> do
        let loop [] = return (SRNormal VNull)
            loop (key:keys) = do
              setVar var key
              result <- evalStmts body
              case result of
                SRReturn v -> return (SRReturn v)
                SRNormal _ -> loop keys
        loop (Map.keys m)
      _ -> throwError "Cannot iterate over non-array"
  
  SWhile cond body -> do
    let loop = do
          condVal <- evalExpr cond
          if isTruthy condVal
            then do
              result <- evalStmts body
              case result of
                SRReturn v -> return (SRReturn v)
                SRNormal _ -> loop
            else return (SRNormal VNull)
    loop
  
  SBlock stmts -> evalStmts stmts
  
  SGlobal names -> do
    declareGlobals names
    return (SRNormal VNull)

-- | Value to string for printing
valueToString :: Value -> String
valueToString = \case
  VInt n -> show n
  VDouble d -> show d
  VString s -> s
  VNull -> ""
  VArray m -> 
    "[" ++ intercalate ", " (map valStr (Map.elems m)) ++ "]"
    where valStr v = valueToString v
  VFunction{} -> "<function>"
  VBuiltin name _ -> "<builtin:" ++ name ++ ">"

-- | Setup built-in functions
builtins :: Env
builtins = Map.fromList
  [ ("print", VBuiltin "print" printBuiltin)
  , ("length", VBuiltin "length" lengthBuiltin)
  , ("map", VBuiltin "map" mapBuiltin)
  , ("filter", VBuiltin "filter" filterBuiltin)
  , ("reduce", VBuiltin "reduce" reduceBuiltin)
  ]

-- | Print builtin
printBuiltin :: [Value] -> IO Value
printBuiltin vals = do
  putStrLn $ unwords (map valueToString vals)
  return VNull

-- | Length builtin
lengthBuiltin :: [Value] -> IO Value
lengthBuiltin [VArray m] = return (VInt (Map.size m))
lengthBuiltin [VString s] = return (VInt (length s))
lengthBuiltin _ = return (VInt 0)

-- | Map builtin
mapBuiltin :: [Value] -> IO Value
mapBuiltin [func, VArray arr] = do
  let initSt = initialState { esGlobals = builtins }
  result <- runEval (mapArray func arr) initSt
  case result of
    Right (val, _) -> return val
    Left err -> error err
  where
    mapArray f m = do
      results <- forM (Map.toList m) $ \(key, val) -> do
        newVal <- callFunction f [val]
        return (key, newVal)
      return (VArray (Map.fromList results))
mapBuiltin _ = return VNull

-- | Filter builtin
filterBuiltin :: [Value] -> IO Value
filterBuiltin [pred_, VArray arr] = do
  let initSt = initialState { esGlobals = builtins }
  result <- runEval (filterArray pred_ arr) initSt
  case result of
    Right (val, _) -> return val
    Left err -> error err
  where
    filterArray p m = do
      results <- filterM (\(_, val) -> do
        result <- callFunction p [val]
        return (isTruthy result)) (Map.toList m)
      return (VArray (Map.fromList results))
filterBuiltin _ = return VNull

-- | Reduce builtin
reduceBuiltin :: [Value] -> IO Value
reduceBuiltin [func, initial, VArray arr] = do
  let initSt = initialState { esGlobals = builtins }
  result <- runEval (foldArray func initial arr) initSt
  case result of
    Right (val, _) -> return val
    Left err -> error err
  where
    foldArray f acc m = do
      foldM (\a v -> callFunction f [a, v]) acc (Map.elems m)
reduceBuiltin _ = return VNull
