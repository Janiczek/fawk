#!/usr/bin/env python3
"""
FAWK - Functional AWK Interpreter
A functional AWK dialect with first-class functions and arrays.
"""

import sys
from fawk_lexer import Lexer
from fawk_parser import Parser
from fawk_interpreter import Interpreter


def main():
    if len(sys.argv) < 2:
        print("Usage: fawk <script.fawk> [input_file]", file=sys.stderr)
        sys.exit(1)
    
    script_file = sys.argv[1]
    
    # Read source code
    try:
        with open(script_file, 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: Script file '{script_file}' not found", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading script file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Tokenize
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
    except SyntaxError as e:
        print(f"Lexer error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Parse
    try:
        parser = Parser(tokens)
        program = parser.parse()
    except SyntaxError as e:
        print(f"Parser error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Interpret
    # Prepare ARGC and ARGV (mimicking AWK behavior)
    argc = len(sys.argv)
    argv = sys.argv  # [fawk.py, script.fawk, input_file, ...]
    interpreter = Interpreter(argc, argv)
    
    # Read input if provided
    input_lines = []
    input_file = None
    if len(sys.argv) > 2:
        input_file = sys.argv[2]
        interpreter.FILENAME = input_file
        try:
            with open(input_file, 'r') as f:
                input_lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Run
    try:
        interpreter.run(program, input_lines)
    except RuntimeError as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
