#!/usr/bin/env python3
"""
FAWK - Functional AWK Interpreter
A functional AWK dialect with first-class functions and arrays.
"""

import sys
import argparse
from .fawk_lexer import Lexer
from .fawk_parser import Parser
from .fawk_interpreter import Interpreter

def main():
    # Get builtin function signatures grouped by category from the interpreter (single source of truth)
    builtin_signatures_by_category = Interpreter.get_builtin_function_signatures_by_category()
    
    # Format builtin functions for help output, grouped by category
    builtin_functions_lines = []
    for category in sorted(builtin_signatures_by_category.keys()):
        builtin_functions_lines.append(f'\n{category}:')
        functions = builtin_signatures_by_category[category]
        for name, args, return_hint in sorted(functions, key=lambda x: x[0]):
            builtin_functions_lines.append(f'  - {name}({args}) -> {return_hint}')
    builtin_functions_str = '\n'.join(builtin_functions_lines)
    
    # Parse command line arguments AWK-style
    parser = argparse.ArgumentParser(
        description='FAWK - Functional AWK Interpreter',
        usage='%(prog)s [-F fs] [-v var=value] [-f script_file] [-e program] [script_string] [input_file ...]',
        epilog='Examples:\n'
               '  %(prog)s -f script.fawk input.txt     # script from file\n'
               '  %(prog)s \'{ print $1 }\' input.txt     # inline script\n'
               '  %(prog)s -e \'{ print $1 }\' input.txt  # program from -e flag\n'
               '  %(prog)s -f script.fawk f1.txt f2.txt # multiple inputs\n'
               '  cat file.txt | %(prog)s \'{ print $1 }\' # piped input\n'
               '  %(prog)s -v PREC=100 \'BEGIN {printf("%%.50f\\n", 4*atan2(1,1))}\' # arbitrary precision\n'
               '\n'
               'Built-in functions:\n'
               f'{builtin_functions_str}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-F', '--field-separator', dest='field_separator', metavar='fs',
                        help='set field separator (FS variable)')
    parser.add_argument('-f', '--file', dest='script_file', metavar='script_file',
                        help='read script from file')
    parser.add_argument('-e', dest='programs', action='append', metavar='program',
                        help='program text (can be used multiple times, programs are concatenated)')
    parser.add_argument('-v', dest='variables', action='append', metavar='var=value',
                        help='set variable before execution (can be used multiple times)')
    parser.add_argument('args', nargs='*', help='script string or input files')
    
    args = parser.parse_args()
    
    # Determine source of script and input files
    # Priority: -e flag > -f flag > positional arg
    if args.programs:
        # Script from -e flag(s): fawk -e 'BEGIN { print "hello" }' input.txt
        # Multiple -e flags are concatenated
        source = '\n'.join(args.programs)
        # All remaining args are input files
        input_files = args.args
    elif args.script_file:
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
        # Treat first arg as inline script: fawk 'BEGIN { print "hello" }' input.txt
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
    
    # Set field separator from -F flag
    if args.field_separator is not None:
        interpreter.FS = args.field_separator
    
    # Set variables from -v flags
    if args.variables:
        for var_assignment in args.variables:
            if '=' in var_assignment:
                var_name, var_value = var_assignment.split('=', 1)
                # Try to parse as number, otherwise use as string
                try:
                    if '.' in var_value:
                        value = float(var_value)
                    else:
                        value = int(var_value)
                except ValueError:
                    value = var_value
                interpreter.set_variable(var_name, value)
            else:
                print(f"Warning: Invalid variable assignment: {var_assignment}", file=sys.stderr)
    
    # Read input from files if provided, or from stdin
    file_list = []
    if input_files:
        for input_file in input_files:
            # Support "-" as explicit stdin
            if input_file == "-":
                try:
                    content = sys.stdin.read()
                    file_list.append(("-", content))
                except IOError as e:
                    print(f"Error reading from stdin: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                try:
                    with open(input_file, 'r') as f:
                        content = f.read()
                    file_list.append((input_file, content))
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
            try:
                content = sys.stdin.read()
                file_list.append(("-", content))
            except IOError as e:
                print(f"Error reading from stdin: {e}", file=sys.stderr)
                sys.exit(1)
    
    # Run
    try:
        interpreter.run(program, file_list if file_list else None)
    except RuntimeError as e:
        print(f"Runtime error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)


if __name__ == '__main__':
    main()
