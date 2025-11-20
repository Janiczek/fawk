{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE FlexibleContexts #-}

module Main where

import AST
import Parser
import Eval
import System.Environment (getArgs)
import System.IO
import Control.Monad
import Control.Monad.State
import Control.Monad.Except
import qualified Data.Map.Strict as Map

-- | Parse input line into fields
parseFields :: String -> Map.Map Int String
parseFields line = Map.fromList $ zip [0..] (line : words line)

-- | Execute a program
executeProgram :: Program -> [String] -> IO ()
executeProgram prog inputLines = do
  -- Initialize state with built-in functions
  let initState = initialState { esGlobals = builtins }
  
  -- Register user-defined functions
  let funcEnv = Map.fromList [(funcName f, VFunction (funcParams f) (funcBody f) Map.empty) | f <- progFunctions prog]
  let stateWithFuncs = initState { esGlobals = Map.union funcEnv (esGlobals initState) }
  
  -- Run BEGIN blocks
  result1 <- runEval (runBeginBlocks (progActions prog)) stateWithFuncs
  case result1 of
    Left err -> hPutStrLn stderr $ "Error in BEGIN: " ++ err
    Right (_, state1) -> do
      -- Process input lines
      result2 <- runEval (processLines (progActions prog) inputLines) state1
      case result2 of
        Left err -> hPutStrLn stderr $ "Error processing lines: " ++ err
        Right (_, state2) -> do
          -- Run END blocks
          result3 <- runEval (runEndBlocks (progActions prog)) state2
          case result3 of
            Left err -> hPutStrLn stderr $ "Error in END: " ++ err
            Right _ -> return ()

-- | Run BEGIN blocks
runBeginBlocks :: [Action] -> EvalM ()
runBeginBlocks actions = do
  forM_ actions $ \(Action pat body) ->
    case pat of
      PBegin -> do
        _ <- evalStmts body
        return ()
      _ -> return ()

-- | Process input lines
processLines :: [Action] -> [String] -> EvalM ()
processLines actions lines_ = do
  forM_ (zip [1..] lines_) $ \(lineNum, line) -> do
    -- Update state with current line info
    modify $ \st -> st 
      { esNR = lineNum
      , esCurrentLine = line
      , esFields = parseFields line
      }
    
    -- Run pattern-action blocks
    forM_ actions $ \(Action pat body) ->
      case pat of
        PAll -> do
          _ <- evalStmts body
          return ()
        PExpr expr -> do
          val <- evalExpr expr
          when (isTruthy val) $ do
            _ <- evalStmts body
            return ()
        _ -> return ()

-- | Run END blocks
runEndBlocks :: [Action] -> EvalM ()
runEndBlocks actions = do
  forM_ actions $ \(Action pat body) ->
    case pat of
      PEnd -> do
        _ <- evalStmts body
        return ()
      _ -> return ()

-- | Main entry point
main :: IO ()
main = do
  args <- getArgs
  case args of
    [] -> do
      hPutStrLn stderr "Usage: fawk <script.fawk> [input.txt]"
      hPutStrLn stderr "   or: fawk -e '<script>' [input.txt]"
    ["-e", script] -> do
      case parseFawk script of
        Left err -> hPutStrLn stderr $ "Parse error: " ++ err
        Right prog -> do
          input <- getContents
          executeProgram prog (lines input)
    [scriptFile] -> do
      script <- readFile scriptFile
      case parseFawk script of
        Left err -> hPutStrLn stderr $ "Parse error: " ++ err
        Right prog -> do
          input <- getContents
          executeProgram prog (lines input)
    ["-e", script, inputFile] -> do
      case parseFawk script of
        Left err -> hPutStrLn stderr $ "Parse error: " ++ err
        Right prog -> do
          input <- readFile inputFile
          executeProgram prog (lines input)
    [scriptFile, inputFile] -> do
      script <- readFile scriptFile
      case parseFawk script of
        Left err -> hPutStrLn stderr $ "Parse error: " ++ err
        Right prog -> do
          input <- readFile inputFile
          executeProgram prog (lines input)
    _ -> hPutStrLn stderr "Usage: fawk <script.fawk> [input.txt]"
