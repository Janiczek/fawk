"""
FAWK Interpreter
Executes the Abstract Syntax Tree
"""

import re
from typing import Any, List, Callable
from fawk_ast import *


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}
    
    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        elif self.parent:
            return self.parent.get(name)
        else:
            return 0  # AWK default for undefined variables
    
    def set(self, name: str, value: Any):
        self.vars[name] = value
    
    def set_local(self, name: str, value: Any):
        self.vars[name] = value
    
    def has(self, name: str) -> bool:
        if name in self.vars:
            return True
        elif self.parent:
            return self.parent.has(name)
        return False


class FawkArray:
    """Represents a FAWK array (can be regular or associative)"""
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        # Convert key to appropriate type
        if isinstance(key, (int, float)):
            key = int(key)
        else:
            key = str(key)
        return self.data.get(key, 0)
    
    def set(self, key, value):
        if isinstance(key, (int, float)):
            key = int(key)
        else:
            key = str(key)
        self.data[key] = value
    
    def keys(self):
        return list(self.data.keys())
    
    def values(self):
        return list(self.data.values())
    
    def length(self):
        return len(self.data)
    
    def copy(self):
        """Create a deep copy of this array"""
        new_arr = FawkArray()
        for key, value in self.data.items():
            if isinstance(value, FawkArray):
                new_arr.data[key] = value.copy()
            else:
                new_arr.data[key] = value
        return new_arr
    
    def __repr__(self):
        # Display as array-like for regular indices, dict-like for assoc
        if all(isinstance(k, int) for k in self.data.keys()):
            # Try to display as regular array
            if not self.data:
                return "[]"
            max_idx = max(self.data.keys())
            if all(i in self.data for i in range(max_idx + 1)):
                return "[" + ", ".join(str(self.data[i]) for i in range(max_idx + 1)) + "]"
        
        # Display as associative array
        items = [f"{k} => {v}" for k, v in self.data.items()]
        return "[" + ", ".join(items) + "]"


class UserFunction:
    def __init__(self, params: List[str], body: Block, closure_env: Environment):
        self.params = params
        self.body = body
        self.closure_env = closure_env


class Interpreter:
    def __init__(self, argc=0, argv=None):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
        self.globals_declared = set()
        
        # AWK built-in variables
        self.ARGC = argc
        self.ARGV = FawkArray()
        if argv:
            for i, arg in enumerate(argv):
                self.ARGV.set(i, arg)
        
        self.CONVFMT = "%.6g"
        
        # ENVIRON - environment variables
        import os
        self.ENVIRON = FawkArray()
        for key, value in os.environ.items():
            self.ENVIRON.set(key, value)
        
        self.FILENAME = ""
        self.FNR = 0  # File number of records
        self.FS = " "  # Field separator
        self.NF = 0    # Number of fields
        self.NR = 0    # Number of records
        self.OFMT = "%.6g"
        self.OFS = " "  # Output field separator
        self.ORS = "\n" # Output record separator
        self.RLENGTH = -1  # Length of string matched by match()
        self.RS = "\n"     # Record separator
        self.RSTART = 0    # Start of string matched by match()
        self.RT = ""       # Record terminator (matched text)
        self.SUBSEP = "\034"  # Subscript separator
        
        self.fields = []  # Current line fields
        self.current_line = ""  # Original line ($0)
        
        # Built-in functions - single source of truth
        self.builtin_functions = {
            'length': lambda arr: arr.length() if isinstance(arr, FawkArray) else len(str(arr)),
            'map': self.builtin_map,
            'filter': self.builtin_filter,
            'reduce': self.builtin_reduce,
            'sum_array': self.builtin_sum_array,
            'match': self.builtin_match,
            'split': self.builtin_split,
        }
        
        # Register built-in functions
        self.register_builtins()
    
    def register_builtins(self):
        """Register all built-in functions"""
        for name, func in self.builtin_functions.items():
            self.functions[name] = func
    
    def builtin_map(self, func, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("map requires an array")
        
        result = FawkArray()
        for key in arr.keys():
            value = arr.get(key)
            result.set(key, self.call_function(func, [value]))
        return result
    
    def builtin_filter(self, pred, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("filter requires an array")
        
        result = FawkArray()
        for key in arr.keys():
            value = arr.get(key)
            if self.is_truthy(self.call_function(pred, [value])):
                result.set(key, value)
        return result
    
    def builtin_reduce(self, func, initial, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("reduce requires an array")
        
        acc = initial
        for key in arr.keys():
            value = arr.get(key)
            acc = self.call_function(func, [acc, value])
        return acc
    
    def builtin_sum_array(self, arr):
        if not isinstance(arr, FawkArray):
            return 0
        total = 0
        for key in arr.keys():
            value = arr.get(key)
            total += value if isinstance(value, (int, float)) else 0
        return total
    
    def builtin_match(self, pattern, text):
        """Match a regex pattern and return array with full match and groups"""
        text_str = str(text)
        match = re.search(pattern, text_str)
        
        result = FawkArray()
        if match:
            # Set RSTART and RLENGTH
            self.RSTART = match.start() + 1  # AWK uses 1-based indexing
            self.RLENGTH = len(match.group(0))
            
            # Index 0: full match
            result.set(0, match.group(0))
            # Index 1+: captured groups
            for i, group in enumerate(match.groups(), 1):
                result.set(i, group if group is not None else "")
        else:
            # No match
            self.RSTART = 0
            self.RLENGTH = -1
        
        return result
    
    def builtin_split(self, separator, text):
        """Split text by separator and return array"""
        text_str = str(text)
        sep_str = str(separator)
        
        parts = text_str.split(sep_str)
        
        result = FawkArray()
        for i, part in enumerate(parts):
            result.set(i, part)
        
        return result
    
    def error(self, msg: str):
        raise RuntimeError(f"Runtime error: {msg}")
    
    def is_truthy(self, value) -> bool:
        if isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value != 0
        elif isinstance(value, str):
            return value != ""
        elif isinstance(value, FawkArray):
            return value.length() > 0
        elif value is None:
            return False
        return True
    
    def to_number(self, value):
        """Convert value to number (like AWK does)"""
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            # Try to parse as number
            try:
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, AttributeError):
                return 0  # AWK default for non-numeric strings
        return 0
    
    def eval(self, node: ASTNode) -> Any:
        method_name = f'eval_{node.__class__.__name__}'
        method = getattr(self, method_name, None)
        if method:
            return method(node)
        else:
            self.error(f"No eval method for {node.__class__.__name__}")
    
    def eval_Program(self, node: Program) -> None:
        # Program evaluation is handled by run() method
        pass
    
    def eval_Block(self, node: Block) -> Any:
        result = None
        for stmt in node.statements:
            result = self.eval(stmt)
        return result
    
    def eval_GlobalDecl(self, node: GlobalDecl) -> None:
        for name in node.names:
            self.globals_declared.add(name)
            if name not in self.global_env.vars:
                self.global_env.set(name, 0)
    
    def eval_IfStmt(self, node: IfStmt) -> Any:
        condition = self.eval(node.condition)
        if self.is_truthy(condition):
            return self.eval(node.then_block)
        elif node.else_block:
            return self.eval(node.else_block)
        return None
    
    def eval_ForInStmt(self, node: ForInStmt) -> None:
        iterable = self.eval(node.iterable)
        
        if not isinstance(iterable, FawkArray):
            self.error("for-in requires an array")
        
        for key in iterable.keys():
            self.current_env.set_local(node.var, key)
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                continue
    
    def eval_WhileStmt(self, node: WhileStmt) -> None:
        while self.is_truthy(self.eval(node.condition)):
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                continue
    
    def eval_ReturnStmt(self, node: ReturnStmt) -> None:
        value = self.eval(node.value) if node.value else None
        raise ReturnException(value)
    
    def eval_BreakStmt(self, node: BreakStmt) -> None:
        raise BreakException()
    
    def eval_ContinueStmt(self, node: ContinueStmt) -> None:
        raise ContinueException()
    
    def eval_PrintStmt(self, node: PrintStmt) -> None:
        if not node.args:
            print(end=self.ORS)
        else:
            values = [self.value_to_string(self.eval(arg)) for arg in node.args]
            print(self.OFS.join(values), end=self.ORS)
    
    def value_to_string(self, value) -> str:
        if isinstance(value, FawkArray):
            return str(value)
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, float):
            # Format floats nicely
            if value == int(value):
                return str(int(value))
            return str(value)
        elif value is None:
            return ""
        return str(value)
    
    def eval_ExprStmt(self, node: ExprStmt) -> Any:
        return self.eval(node.expr)
    
    def eval_BinaryOp(self, node: BinaryOp) -> Any:
        left = self.eval(node.left)
        right = self.eval(node.right)
        
        op = node.op
        
        # String concatenation
        if op == 'concat':
            return self.value_to_string(left) + self.value_to_string(right)
        # Arithmetic operations - convert to numbers
        elif op == '+':
            return self.to_number(left) + self.to_number(right)
        elif op == '-':
            return self.to_number(left) - self.to_number(right)
        elif op == '*':
            return self.to_number(left) * self.to_number(right)
        elif op == '/':
            right_num = self.to_number(right)
            if right_num == 0:
                self.error("Division by zero")
            return self.to_number(left) / right_num
        elif op == '%':
            return self.to_number(left) % self.to_number(right)
        # Comparison operations - use as-is for now
        elif op == '==':
            return left == right
        elif op == '!=':
            return left != right
        elif op == '<':
            return self.to_number(left) < self.to_number(right)
        elif op == '<=':
            return self.to_number(left) <= self.to_number(right)
        elif op == '>':
            return self.to_number(left) > self.to_number(right)
        elif op == '>=':
            return self.to_number(left) >= self.to_number(right)
        # Logical operations
        elif op == '&&':
            return self.is_truthy(left) and self.is_truthy(right)
        elif op == '||':
            return self.is_truthy(left) or self.is_truthy(right)
        # Match operations
        elif op == '~':
            # String ~ pattern: check if string contains/matches pattern
            text = self.value_to_string(left)
            pattern = self.value_to_string(right)
            try:
                return bool(re.search(pattern, text))
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")
        elif op == '!~':
            # String !~ pattern: check if string does not match pattern
            text = self.value_to_string(left)
            pattern = self.value_to_string(right)
            try:
                return not bool(re.search(pattern, text))
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")
        else:
            self.error(f"Unknown binary operator: {op}")
    
    def eval_UnaryOp(self, node: UnaryOp) -> Any:
        operand = self.eval(node.operand)
        
        if node.op == '-':
            return -self.to_number(operand)
        elif node.op == '!':
            return not self.is_truthy(operand)
        else:
            self.error(f"Unknown unary operator: {node.op}")
    
    def eval_Assignment(self, node: Assignment) -> Any:
        value = self.eval(node.value)
        
        if isinstance(node.target, Identifier):
            name = node.target.name
            
            # Check if it's a built-in variable
            if name == 'FS':
                self.FS = str(value)
            elif name == 'OFS':
                self.OFS = str(value)
            elif name == 'ORS':
                self.ORS = str(value)
            elif name == 'RS':
                self.RS = str(value)
            elif name == 'OFMT':
                self.OFMT = str(value)
            elif name == 'CONVFMT':
                self.CONVFMT = str(value)
            elif name == 'SUBSEP':
                self.SUBSEP = str(value)
            elif name == 'FILENAME':
                self.FILENAME = str(value)
            # Check if it's a global
            elif name in self.globals_declared:
                self.global_env.set(name, value)
            else:
                self.current_env.set_local(name, value)
        
        elif isinstance(node.target, ArrayAccess):
            array = self.eval(node.target.array)
            if not isinstance(array, FawkArray):
                # Auto-vivify array
                array = FawkArray()
                if isinstance(node.target.array, Identifier):
                    name = node.target.array.name
                    if name in self.globals_declared:
                        self.global_env.set(name, array)
                    else:
                        self.current_env.set_local(name, array)
            
            index = self.eval(node.target.index)
            array.set(index, value)
        
        else:
            self.error("Invalid assignment target")
        
        return value
    
    def eval_ArrayLiteral(self, node: ArrayLiteral) -> FawkArray:
        arr = FawkArray()
        for i, elem in enumerate(node.elements):
            arr.set(i, self.eval(elem))
        return arr
    
    def eval_AssocArray(self, node: AssocArray) -> FawkArray:
        arr = FawkArray()
        for key_expr, value_expr in node.pairs:
            key = self.eval(key_expr)
            value = self.eval(value_expr)
            arr.set(key, value)
        return arr
    
    def eval_ArrayAccess(self, node: ArrayAccess) -> Any:
        array = self.eval(node.array)
        if not isinstance(array, FawkArray):
            return 0  # AWK behavior
        
        index = self.eval(node.index)
        return array.get(index)
    
    def eval_FunctionCall(self, node: FunctionCall) -> Any:
        func = self.eval(node.func)
        args = [self.eval(arg) for arg in node.args]
        
        return self.call_function(func, args)
    
    def call_function(self, func, args):
        if callable(func) and not isinstance(func, UserFunction):
            # Built-in function
            return func(*args)
        elif isinstance(func, UserFunction):
            # User-defined function
            if len(args) != len(func.params):
                self.error(f"Function expects {len(func.params)} arguments, got {len(args)}")
            
            # Create new environment for function
            func_env = Environment(func.closure_env)
            for param, arg in zip(func.params, args):
                # Copy arrays when passing as arguments (pass by value)
                if isinstance(arg, FawkArray):
                    func_env.set_local(param, arg.copy())
                else:
                    func_env.set_local(param, arg)
            
            # Execute function body
            saved_env = self.current_env
            self.current_env = func_env
            
            try:
                result = self.eval(func.body)
                # For lambdas with single expression, implicitly return the value
                if isinstance(func.body, Block) and len(func.body.statements) == 1:
                    stmt = func.body.statements[0]
                    if isinstance(stmt, ExprStmt):
                        # Implicit return for single-expression lambdas
                        result = self.eval(stmt.expr)
            except ReturnException as e:
                result = e.value
            finally:
                self.current_env = saved_env
            
            return result
        else:
            self.error(f"Not a function: {func}")
    
    def eval_Lambda(self, node: Lambda) -> UserFunction:
        return UserFunction(node.params, node.body, self.current_env)
    
    def eval_Pipeline(self, node: Pipeline) -> Any:
        left_value = self.eval(node.left)
        
        # The right side should be a function call
        # We append the left value as the last argument
        if isinstance(node.right, FunctionCall):
            func = self.eval(node.right.func)
            args = [self.eval(arg) for arg in node.right.args]
            args.append(left_value)  # Add piped value as last argument
            return self.call_function(func, args)
        else:
            self.error("Pipeline right side must be a function call")
    
    def eval_Identifier(self, node: Identifier) -> Any:
        name = node.name
        
        # Check for built-in variables
        if name == 'ARGC':
            return self.ARGC
        elif name == 'ARGV':
            return self.ARGV
        elif name == 'CONVFMT':
            return self.CONVFMT
        elif name == 'ENVIRON':
            return self.ENVIRON
        elif name == 'FILENAME':
            return self.FILENAME
        elif name == 'FNR':
            return self.FNR
        elif name == 'FS':
            return self.FS
        elif name == 'NF':
            return self.NF
        elif name == 'NR':
            return self.NR
        elif name == 'OFMT':
            return self.OFMT
        elif name == 'OFS':
            return self.OFS
        elif name == 'ORS':
            return self.ORS
        elif name == 'RLENGTH':
            return self.RLENGTH
        elif name == 'RS':
            return self.RS
        elif name == 'RSTART':
            return self.RSTART
        elif name == 'RT':
            return self.RT
        elif name == 'SUBSEP':
            return self.SUBSEP
        
        # Check for functions
        if name in self.functions:
            return self.functions[name]
        
        # Check for variables
        return self.current_env.get(name)
    
    def eval_Number(self, node: Number) -> float:
        return node.value
    
    def eval_String(self, node: String) -> str:
        return node.value
    
    def eval_Regex(self, node: Regex) -> bool:
        """Evaluate regex pattern against current line ($0)"""
        line = self.current_line
        flags = 0
        if 'i' in node.flags:
            flags |= re.IGNORECASE
        try:
            return bool(re.search(node.pattern, line, flags))
        except re.error as e:
            self.error(f"Invalid regex pattern: {e}")
    
    def eval_FieldAccess(self, node: FieldAccess) -> Any:
        index = self.eval(node.index)
        index = int(index)
        
        if index == 0:
            return self.current_line
        elif 1 <= index <= len(self.fields):
            return self.fields[index - 1]
        else:
            return ""
    
    def split_into_records(self, input_text: str) -> List[tuple]:
        """
        Split input text into records based on RS value.
        Returns a list of tuples: (record_text, record_terminator)
        """
        if not input_text:
            return []
        
        records = []
        rs = self.RS
        
        if rs == "\n":
            # Default: each line is a record
            lines = input_text.split('\n')
            for i, line in enumerate(lines):
                if i < len(lines) - 1:
                    # Not the last line, has newline terminator
                    records.append((line, "\n"))
                elif line:
                    # Last line with content but no trailing newline
                    records.append((line, ""))
        
        elif rs == "":
            # Empty string: records separated by blank lines
            # Leading newlines are ignored, trailing newline after last record is removed
            
            # Strip leading newlines
            text = input_text.lstrip('\n')
            if not text:
                return []
            
            # Split by one or more blank lines (two or more consecutive newlines)
            # We need to track what was matched as the separator
            parts = re.split(r'(\n\n+)', text)
            
            for i in range(0, len(parts), 2):
                if i < len(parts):
                    record = parts[i]
                    # Remove trailing newline from record if present
                    if record.endswith('\n'):
                        record = record[:-1]
                    
                    # Get terminator (the blank lines that follow)
                    if i + 1 < len(parts):
                        terminator = parts[i + 1]
                    else:
                        # Last record - check if original text ended with newlines
                        terminator = ""
                    
                    if record:  # Only add non-empty records
                        records.append((record, terminator))
        
        elif len(rs) == 1:
            # Single character: split by that character
            parts = input_text.split(rs)
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    # Not the last part, has separator
                    records.append((part, rs))
                elif part:
                    # Last part with content but no trailing separator
                    records.append((part, ""))
        
        else:
            # Regex pattern: split by pattern matches
            try:
                # Use split with capturing group to get both parts and separators
                parts = re.split(f'({rs})', input_text)
                
                # parts will be [text, sep, text, sep, text, ...]
                for i in range(0, len(parts), 2):
                    if i < len(parts):
                        record = parts[i]
                        # Get terminator (the matched separator)
                        if i + 1 < len(parts):
                            terminator = parts[i + 1]
                        else:
                            terminator = ""
                        
                        # Include even empty records (leading/trailing matches)
                        records.append((record, terminator))
            except re.error:
                # Invalid regex, treat as literal string
                parts = input_text.split(rs)
                for i, part in enumerate(parts):
                    if i < len(parts) - 1:
                        records.append((part, rs))
                    elif part:
                        records.append((part, ""))
        
        return records
    
    def split_fields(self, record: str) -> List[str]:
        """
        Split a record into fields based on FS and RS.
        When RS == "" and FS is a single character, newlines also act as field separators.
        """
        fs = self.FS
        rs = self.RS
        
        # Special case: RS == "" and FS is a single character
        if rs == "" and len(fs) == 1 and fs != "":
            # Newline always acts as field separator in addition to FS
            # First split by newlines, then by FS
            lines = record.split('\n')
            fields = []
            for line in lines:
                if fs == " ":
                    # Special case: space means any whitespace
                    fields.extend(line.split())
                else:
                    fields.extend(line.split(fs))
            return fields
        else:
            # Normal field splitting
            if fs == " ":
                # Special case: space means any whitespace
                return record.split()
            else:
                return record.split(fs)
    
    def run(self, program: Program, input_text: str = None):
        # Register user-defined functions (protect built-ins)
        for func_def in program.functions:
            if func_def.name in self.builtin_functions:
                raise RuntimeError(f"Cannot redefine built-in function '{func_def.name}'")
            self.functions[func_def.name] = UserFunction(
                func_def.params, func_def.body, self.global_env
            )
        
        # Execute BEGIN block with its own local environment
        if program.begin_block:
            begin_env = Environment(self.global_env)
            saved_env = self.current_env
            self.current_env = begin_env
            try:
                self.eval(program.begin_block)
            finally:
                self.current_env = saved_env
        
        # Process input with pattern-action blocks
        if input_text:
            # Split input into records based on RS
            records = self.split_into_records(input_text)
            
            for record, terminator in records:
                self.NR += 1
                self.FNR += 1
                self.RT = terminator
                
                # Split record into fields
                self.current_line = record  # Store original record for $0
                self.fields = self.split_fields(record)
                self.NF = len(self.fields)
                
                # Execute pattern-action blocks
                for pattern_action in program.patterns:
                    # Check if pattern matches (or no pattern)
                    should_execute = False
                    if pattern_action.pattern is None:
                        should_execute = True
                    else:
                        # Evaluate pattern
                        should_execute = self.is_truthy(self.eval(pattern_action.pattern))
                    
                    if should_execute:
                        action_env = Environment(self.global_env)
                        saved_env = self.current_env
                        self.current_env = action_env
                        try:
                            self.eval(pattern_action.action)
                        finally:
                            self.current_env = saved_env
        else:
            # No input, just execute pattern-less actions
            for pattern_action in program.patterns:
                if pattern_action.pattern is None:
                    action_env = Environment(self.global_env)
                    saved_env = self.current_env
                    self.current_env = action_env
                    try:
                        self.eval(pattern_action.action)
                    finally:
                        self.current_env = saved_env
        
        # Execute END block with its own local environment
        if program.end_block:
            end_env = Environment(self.global_env)
            saved_env = self.current_env
            self.current_env = end_env
            try:
                self.eval(program.end_block)
            finally:
                self.current_env = saved_env
