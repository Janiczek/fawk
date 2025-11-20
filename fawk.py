#!/usr/bin/env python3
"""
FAWK - Functional AWK Interpreter
A functional AWK dialect with first-class functions and arrays.
"""

import sys
import argparse
from fawk_lexer import Lexer
from fawk_parser import Parser
from fawk_interpreter import Interpreter


def main():
    # Parse command line arguments AWK-style
    parser = argparse.ArgumentParser(
        description='FAWK - Functional AWK Interpreter',
        usage='%(prog)s [-f script_file] [script_string] [input_file ...]',
        epilog='Examples:\n'
               '  %(prog)s script.fawk input.txt        # script from file\n'
               '  %(prog)s -f script.fawk input.txt     # explicit -f flag\n'
               '  %(prog)s \'{ print $1 }\' input.txt     # inline script\n'
               '  %(prog)s -f script.fawk f1.txt f2.txt # multiple inputs\n'
               '  cat file.txt | %(prog)s \'{ print $1 }\' # piped input',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-f', '--file', dest='script_file', metavar='script_file',
                        help='read script from file')
    parser.add_argument('args', nargs='*', help='script string or input files')
    
    args = parser.parse_args()
    
    # Determine source of script and input files
    if args.script_file:
        # Script from file: fawk -f script.fawk input.txt
        try:
            with open(args.script_file, 'r') as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: Script file '{args.script_file}' not found", file=sys.stderr)
            sys.exit(1)
        except IOError as e:
            print(f"Error reading script file: {e}", file=sys.stderr)
            sys.exit(1)
        # All remaining args are input files
        input_files = args.args
    elif args.args:
        # First arg could be either a script file or inline script
        # Check if it's a file first (backward compatibility)
        import os
        if os.path.isfile(args.args[0]):
            # Treat as script file: fawk script.fawk input.txt
            try:
                with open(args.args[0], 'r') as f:
                    source = f.read()
            except FileNotFoundError:
                print(f"Error: Script file '{args.args[0]}' not found", file=sys.stderr)
                sys.exit(1)
            except IOError as e:
                print(f"Error reading script file: {e}", file=sys.stderr)
                sys.exit(1)
            input_files = args.args[1:]
        else:
            # Treat as inline script: fawk 'BEGIN { print "hello" }' input.txt
            source = args.args[0]
            input_files = args.args[1:]
    else:
        parser.print_help(file=sys.stderr)
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
        parser_obj = Parser(tokens)
        program = parser_obj.parse()
    except SyntaxError as e:
        print(f"Parser error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Prepare ARGC and ARGV (mimicking AWK behavior)
    # ARGV[0] is the program name, ARGV[1..n] are input files
    argv = ['fawk'] + input_files
    argc = len(argv)
    interpreter = Interpreter(argc, argv)
    
    # Read input from files if provided, or from stdin
    input_text = ""
    if input_files:
        for input_file in input_files:
            interpreter.FILENAME = input_file
            interpreter.FNR = 0  # Reset file record counter for each file
            try:
                with open(input_file, 'r') as f:
                    input_text += f.read()
            except FileNotFoundError:
                print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
                sys.exit(1)
            except IOError as e:
                print(f"Error reading input file: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        # No input files specified - check if stdin has data
        # This allows piping: cat file.txt | fawk '{ print $1 }'
        if not sys.stdin.isatty():
            interpreter.FILENAME = "-"
            try:
                input_text = sys.stdin.read()
            except IOError as e:
                print(f"Error reading from stdin: {e}", file=sys.stderr)
                sys.exit(1)
    
    # Run
    try:
        interpreter.run(program, input_text)
    except RuntimeError as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
