"""
FAWK Interpreter
Executes the Abstract Syntax Tree
"""

import re
import math
from decimal import Decimal, getcontext
from typing import Any, List, Callable
from .fawk_ast import *


class BreakException(Exception):
    pass


class ContinueException(Exception):
    pass


class ReturnException(Exception):
    def __init__(self, value):
        self.value = value


class TailCallException(Exception):
    """Exception raised when a tail call is detected"""
    def __init__(self, func_call_node):
        self.func_call_node = func_call_node


class ExitException(Exception):
    def __init__(self, code):
        self.code = code


class NextException(Exception):
    pass


class NextFileException(Exception):
    pass


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
    def __init__(self, shared_data=None, parent=None):
        """
        Initialize a FawkArray.
        
        Args:
            shared_data: If provided, this array shares data with another array (copy-on-write)
            parent: The parent array this array shares data with (for COW)
        """
        if shared_data is not None:
            # Copy-on-write: share the data dictionary
            self.data = shared_data
            self._shared = True
            self._parent = parent
        else:
            self.data = {}
            self._shared = False
            self._parent = None
    
    def _ensure_unique(self):
        """Ensure this array has its own copy of data (copy-on-write)"""
        if self._shared:
            # Copy the data
            new_data = {}
            for key, value in self.data.items():
                # Optimized: use type() for exact match (faster than isinstance)
                if type(value) is FawkArray:
                    # Recursively ensure nested arrays are unique too
                    new_data[key] = value._ensure_unique_copy()
                else:
                    new_data[key] = value
            self.data = new_data
            self._shared = False
            self._parent = None
    
    def _ensure_unique_copy(self):
        """Create a unique copy of this array (used when copying nested arrays)"""
        if self._shared:
            new_arr = FawkArray()
            for key, value in self.data.items():
                # Optimized: use type() for exact match (faster than isinstance)
                if type(value) is FawkArray:
                    new_arr.data[key] = value._ensure_unique_copy()
                else:
                    new_arr.data[key] = value
            return new_arr
        else:
            # Already unique, create a deep copy
            new_arr = FawkArray()
            for key, value in self.data.items():
                # Optimized: use type() for exact match (faster than isinstance)
                if type(value) is FawkArray:
                    new_arr.data[key] = value._ensure_unique_copy()
                else:
                    new_arr.data[key] = value
            return new_arr
    
    def get(self, key):
        # Convert key to appropriate type (optimized: use type() for faster checks)
        # Fast path: already int
        if type(key) is int:
            pass  # no conversion needed
        elif type(key) is float:
            key = int(key)
        else:
            # Try to convert to int, fallback to string
            try:
                key = int(key)
            except (ValueError, TypeError):
                key = str(key)
        # GAWK behavior: deleted array elements return empty string, not 0
        # Check if key exists in data (not just if it has a value)
        if key in self.data:
            return self.data[key]
        else:
            return ""  # GAWK returns empty string for non-existent/deleted elements
    
    def set(self, key, value):
        # Copy-on-write: ensure we have our own copy before modifying
        self._ensure_unique()
        
        # Optimized: use type() for faster checks
        if type(key) is int:
            pass  # no conversion needed
        elif type(key) is float:
            key = int(key)
        else:
            # Try to convert to int, fallback to string
            try:
                key = int(key)
            except (ValueError, TypeError):
                key = str(key)
        self.data[key] = value
    
    def delete(self, key):
        """Delete an element from the array (with COW)"""
        # Copy-on-write: ensure we have our own copy before modifying
        self._ensure_unique()
        
        # Optimized: use type() for faster checks
        if type(key) is int:
            pass  # no conversion needed
        elif type(key) is float:
            key = int(key)
        else:
            # Try to convert to int, fallback to string
            try:
                key = int(key)
            except (ValueError, TypeError):
                key = str(key)
        
        if key in self.data:
            del self.data[key]
    
    def clear(self):
        """Clear all elements from the array (with COW)"""
        # Copy-on-write: ensure we have our own copy before modifying
        self._ensure_unique()
        self.data.clear()
    
    def keys(self):
        """Return keys in GAWK-compatible order: numeric keys sorted numerically, string keys lexicographically"""
        # Fast path: if data is empty, return empty list
        if not self.data:
            return []
        
        keys_list = list(self.data.keys())
        
        # Separate numeric and non-numeric keys
        numeric_keys = []
        string_keys = []
        
        for key in keys_list:
            # Optimized: use type() for faster checks
            key_type = type(key)
            if key_type is int:
                numeric_keys.append((key, key))
            elif key_type is str:
                # Try to parse as number
                try:
                    # Check if string looks like a number
                    num_val = float(key)
                    # In AWK, numeric strings are sorted numerically
                    numeric_keys.append((num_val, key))
                except (ValueError, TypeError):
                    # Not a number, treat as string
                    string_keys.append(key)
            else:
                string_keys.append(key)
        
        # Sort numeric keys by their numeric value, string keys lexicographically
        numeric_keys.sort(key=lambda x: x[0])
        string_keys.sort()
        
        # Return original keys in sorted order
        result = [key for _, key in numeric_keys] + string_keys
        return result
    
    def values(self):
        return list(self.data.values())
    
    def length(self):
        return len(self.data)
    
    def cow_copy(self):
        """Create a copy-on-write copy (shared reference) of this array"""
        # Create a new FawkArray that shares the same data dictionary
        return FawkArray(shared_data=self.data, parent=self)
    
    def copy(self):
        """Create a deep copy of this array (for when we actually need a full copy)"""
        # Ensure we're working with unique data
        if self._shared:
            # If shared, create a unique copy
            return self._ensure_unique_copy()
        else:
            # Already unique, create a deep copy
            # Optimized: use type() for faster checks
            new_arr = FawkArray()
            for key, value in self.data.items():
                if type(value) is FawkArray:
                    new_arr.data[key] = value.copy()
                else:
                    new_arr.data[key] = value
            return new_arr
    
    def is_associative(self) -> bool:
        """Check if array is associative (not a regular array with consecutive indexes starting from 1)"""
        if not self.data:
            return False  # Empty array is considered regular
        
        # Check if all keys are integers
        if not all(isinstance(k, int) for k in self.data.keys()):
            return True  # Has non-integer keys, so associative
        
        # Check if it's a dense array starting from 1 (AWK standard for regular arrays)
        max_idx = max(self.data.keys())
        min_idx = min(self.data.keys())
        
        # Regular array: starts at 1 and has consecutive indexes
        if min_idx == 1 and all(i in self.data for i in range(1, max_idx + 1)):
            return False  # Regular array
        
        # Everything else (0-based, sparse, etc.) is associative
        return True
    
    def __repr__(self):
        # Display as array-like for regular indices (1-based consecutive), dict-like for assoc
        if not self.data:
            return "[]"
        
        def format_value(v):
            """Format value with double quotes if it's a string, escaping quotes inside"""
            if isinstance(v, str):
                # Escape double quotes by replacing " with \"
                escaped = v.replace('"', '\\"')
                return f'"{escaped}"'
            return str(v)
        
        # Check if it's a regular array (1-based consecutive indexes)
        if not self.is_associative():
            # Regular array: starts at 1 and has consecutive indexes
            max_idx = max(self.data.keys())
            return "[" + ", ".join(format_value(self.data[i]) for i in range(1, max_idx + 1)) + "]"
        
        # Display as associative array
        def format_key(k):
            """Format key with double quotes if it's a string, escaping quotes inside"""
            if isinstance(k, str):
                # Escape double quotes by replacing " with \"
                escaped = k.replace('"', '\\"')
                return f'"{escaped}"'
            return str(k)
        
        items = [f"{format_key(k)} => {format_value(v)}" for k, v in self.data.items()]
        return "[" + ", ".join(items) + "]"
    
    def __eq__(self, other):
        """Structural comparison of arrays"""
        # Optimized: use type() for faster checks
        if type(other) is not FawkArray:
            return False
        
        # Compare keys
        if set(self.data.keys()) != set(other.data.keys()):
            return False
        
        # Compare values recursively
        for key in self.data.keys():
            self_val = self.data[key]
            other_val = other.data[key]
            
            # Recursive comparison for nested arrays
            # Optimized: use type() for faster checks
            self_val_type = type(self_val)
            other_val_type = type(other_val)
            if self_val_type is FawkArray and other_val_type is FawkArray:
                if self_val != other_val:
                    return False
            else:
                # For non-array values, use standard comparison
                # Handle numeric comparison (1 == 1.0 should be True)
                if isinstance(self_val, (int, float)) and isinstance(other_val, (int, float)):
                    if self_val != other_val:
                        return False
                elif self_val != other_val:
                    return False
        
        return True
    
    def __ne__(self, other):
        """Structural inequality comparison"""
        return not self.__eq__(other)


class UserFunction:
    def __init__(self, params: List[str], body: Block, closure_env: Environment, is_lambda: bool = False):
        self.params = params
        self.body = body
        self.closure_env = closure_env
        self.is_lambda = is_lambda


class Interpreter:
    # Built-in function signatures - single source of truth
    # Format: category -> [(name, args_string, return_hint), ...]
    BUILTIN_FUNCTION_SIGNATURES = {
        'Array functions': [
            ('length', '[value]', 'int'),
            ('map', 'func, array', 'array'),
            ('filter', 'pred, array', 'array'),
            ('reduce', 'func, initial, array', 'value'),
            ('sum', 'array', 'number'),
            ('is_associative', 'array', '0|1'),
            ('keys', 'array', 'array'),
            ('set_union', 'set1, set2', 'array'),
            ('set_intersection', 'set1, set2', 'array'),
            ('set_diff', 'set1, set2', 'array'),
        ],
        'String functions': [
            ('match', 'pattern, text', 'array'),
            ('split', 'separator, text', 'array'),
            ('substr', 'string, start, [length]', 'string'),
            ('tolower', 'string', 'string'),
            ('toupper', 'string', 'string'),
            ('gsub', 'pattern, replacement, [target]', 'number'),
            ('sub', 'pattern, replacement, [target]', 'number'),
        ],
        'Math functions': [
            ('atan2', 'y, x', 'number'),
            ('cos', 'x', 'number'),
            ('sin', 'x', 'number'),
            ('exp', 'x', 'number'),
            ('log', 'x', 'number'),
            ('sqrt', 'x', 'number'),
            ('int', 'x', 'int'),
            ('rand', '', '0.0...1.0'),
            ('srand', '[seed]', 'seed'),
        ],
        'I/O functions': [
            ('printf', 'fmt, ...', 'int'),
            ('sprintf', 'fmt, ...', 'string'),
            ('close', 'filename_or_cmd', 'number'),
            ('fflush', '[filename]', 'number'),
        ],
        'Utility functions': [
            ('hash', 'value', 'int'),
        ],
    }
    
    @classmethod
    def get_builtin_function_names(cls):
        """Return list of built-in function names"""
        names = []
        for category_functions in cls.BUILTIN_FUNCTION_SIGNATURES.values():
            for name, _, _ in category_functions:
                names.append(name)
        return names
    
    @classmethod
    def get_builtin_function_signatures(cls):
        """Return dictionary mapping function names to (args, return_hint) tuples"""
        result = {}
        for category_functions in cls.BUILTIN_FUNCTION_SIGNATURES.values():
            for name, args, return_hint in category_functions:
                result[name] = (args, return_hint)
        return result
    
    @classmethod
    def get_builtin_function_signatures_by_category(cls):
        """Return dictionary mapping categories to lists of (name, args, return_hint) tuples"""
        return cls.BUILTIN_FUNCTION_SIGNATURES
    
    def __init__(self, argc=0, argv=None):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.functions = {}
        self.globals_declared = set()
        self.in_function = False  # Track if we're inside a user function
        self.current_closure_env = None  # Track the closure environment of the current function
        self.current_function = None  # Track the current UserFunction being executed (for tail recursion)
        self.current_function_name = None  # Track the name of the current function (for tail recursion)
        
        # AWK built-in variables
        self.ARGC = argc
        self.ARGV = FawkArray()
        if argv:
            for i, arg in enumerate(argv):
                self.ARGV.set(i, arg)
        
        self.CONVFMT = "%.6g"
        self.PREC = 53  # Default precision (like gawk, similar to IEEE 754 double)
        self._use_high_precision = False  # Cached result of use_high_precision()
        
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
        
        # File handles for print redirection
        self.redirect_files = {}  # filename -> file handle
        
        # Command pipes for getline
        self.open_pipes = {}  # command string -> subprocess.Popen object
        
        # Built-in functions - single source of truth
        # Build dictionary from BUILTIN_FUNCTION_SIGNATURES
        self.builtin_functions = {}
        for category_functions in self.BUILTIN_FUNCTION_SIGNATURES.values():
            for name, _, _ in category_functions:
                method_name = f'builtin_{name}'
                if hasattr(self, method_name):
                    self.builtin_functions[name] = getattr(self, method_name)
        
        # Random number generator seed
        import random
        self.random = random.Random()
        
        # Register built-in functions
        self.register_builtins()
        
        # Build eval dispatch dictionary for fast method lookup (optimization)
        # Import AST classes for dispatch table
        from . import fawk_ast
        self._eval_dispatch = {
            fawk_ast.Program: self.eval_Program,
            fawk_ast.Block: self.eval_Block,
            fawk_ast.GlobalDecl: self.eval_GlobalDecl,
            fawk_ast.IfStmt: self.eval_IfStmt,
            fawk_ast.ForInStmt: self.eval_ForInStmt,
            fawk_ast.ForStmt: self.eval_ForStmt,
            fawk_ast.WhileStmt: self.eval_WhileStmt,
            fawk_ast.DoWhileStmt: self.eval_DoWhileStmt,
            fawk_ast.SwitchStmt: self.eval_SwitchStmt,
            fawk_ast.ReturnStmt: self.eval_ReturnStmt,
            fawk_ast.ExitStmt: self.eval_ExitStmt,
            fawk_ast.NextStmt: self.eval_NextStmt,
            fawk_ast.NextFileStmt: self.eval_NextFileStmt,
            fawk_ast.BreakStmt: self.eval_BreakStmt,
            fawk_ast.ContinueStmt: self.eval_ContinueStmt,
            fawk_ast.DeleteStmt: self.eval_DeleteStmt,
            fawk_ast.DelarrayStmt: self.eval_DelarrayStmt,
            fawk_ast.PrintStmt: self.eval_PrintStmt,
            fawk_ast.PrintfStmt: self.eval_PrintfStmt,
            fawk_ast.ExprStmt: self.eval_ExprStmt,
            fawk_ast.BinaryOp: self.eval_BinaryOp,
            fawk_ast.UnaryOp: self.eval_UnaryOp,
            fawk_ast.TernaryOp: self.eval_TernaryOp,
            fawk_ast.PrefixIncrement: self.eval_PrefixIncrement,
            fawk_ast.PrefixDecrement: self.eval_PrefixDecrement,
            fawk_ast.PostfixIncrement: self.eval_PostfixIncrement,
            fawk_ast.PostfixDecrement: self.eval_PostfixDecrement,
            fawk_ast.Assignment: self.eval_Assignment,
            fawk_ast.ArrayLiteral: self.eval_ArrayLiteral,
            fawk_ast.AssocArray: self.eval_AssocArray,
            fawk_ast.ArrayAccess: self.eval_ArrayAccess,
            fawk_ast.FunctionCall: self.eval_FunctionCall,
            fawk_ast.Lambda: self.eval_Lambda,
            fawk_ast.Pipeline: self.eval_Pipeline,
            fawk_ast.Identifier: self.eval_Identifier,
            fawk_ast.Number: self.eval_Number,
            fawk_ast.String: self.eval_String,
            fawk_ast.Regex: self.eval_Regex,
            fawk_ast.FieldAccess: self.eval_FieldAccess,
            fawk_ast.InOp: self.eval_InOp,
            fawk_ast.CommaExpr: self.eval_CommaExpr,
            fawk_ast.PipedGetline: self.eval_PipedGetline,
            fawk_ast.DestructurePattern: self.eval_DestructurePattern,
        }
        
        # Cache for compiled regex patterns (optimization)
        self._regex_cache = {}
        
        # Cache for built-in variable lookups (optimization)
        self._builtin_vars = {
            'ARGC': lambda: self.ARGC,
            'ARGV': lambda: self.ARGV,
            'CONVFMT': lambda: self.CONVFMT,
            'ENVIRON': lambda: self.ENVIRON,
            'FILENAME': lambda: self.FILENAME,
            'FNR': lambda: self.FNR,
            'FS': lambda: self.FS,
            'NF': lambda: self.NF,
            'NR': lambda: self.NR,
            'OFMT': lambda: self.OFMT,
            'OFS': lambda: self.OFS,
            'ORS': lambda: self.ORS,
            'PREC': lambda: self.PREC,
            'RLENGTH': lambda: self.RLENGTH,
            'RS': lambda: self.RS,
            'RSTART': lambda: self.RSTART,
            'RT': lambda: self.RT,
            'SUBSEP': lambda: self.SUBSEP,
        }
    
    def register_builtins(self):
        """Register all built-in functions"""
        for name, func in self.builtin_functions.items():
            self.functions[name] = func
    
    def set_variable(self, name: str, value: Any):
        """Set a variable in the global environment (used for -v flags)"""
        if name == 'PREC':
            self.PREC = int(self.to_number(value))
            self._use_high_precision = self.PREC > 53  # Update cache
        else:
            self.global_env.set(name, value)
    
    def builtin_length(self, value=None):
        """Return length of array or string"""
        if value is None:
            # No argument: return length of $0
            value = self.current_line
        
        if isinstance(value, FawkArray):
            return value.length()
        else:
            # Convert to string and get length
            # Handle large integers by temporarily increasing limit
            import sys
            old_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0)  # 0 means no limit
                return len(str(value))
            finally:
                sys.set_int_max_str_digits(old_limit)
    
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
        is_assoc = arr.is_associative()
        new_index = 1  # For regular arrays, start reindexing from 1 (AWK convention)
        
        for key in arr.keys():
            value = arr.get(key)
            if self.is_truthy(self.call_function(pred, [value])):
                if is_assoc:
                    # For associative arrays, preserve original keys
                    result.set(key, value)
                else:
                    # For regular arrays, reindex starting from 1
                    result.set(new_index, value)
                    new_index += 1
        return result
    
    def builtin_reduce(self, func, initial, arr):
        if not isinstance(arr, FawkArray):
            raise RuntimeError("reduce requires an array")
        
        acc = initial
        for key in arr.keys():
            value = arr.get(key)
            acc = self.call_function(func, [acc, value])
        return acc
    
    def builtin_sum(self, arr):
        if not isinstance(arr, FawkArray):
            return 0
        total = 0
        for key in arr.keys():
            value = arr.get(key)
            total += value if isinstance(value, (int, float)) else 0
        return total
    
    def builtin_is_associative(self, arr):
        """Check if an array is associative (not a regular array with consecutive indexes starting from 1)"""
        if not isinstance(arr, FawkArray):
            return 0  # Not an array, so not associative (but also not regular)
        return 1 if arr.is_associative() else 0
    
    def builtin_keys(self, arr):
        """Return a new array containing all keys from the given array (1-indexed)"""
        if not isinstance(arr, FawkArray):
            raise RuntimeError("keys() requires an array as argument")
        
        result = FawkArray()
        # Get keys in sorted order (numeric first, then string)
        keys_list = arr.keys()
        # Store keys as values in a 1-indexed array
        for i, key in enumerate(keys_list, 1):
            result.set(i, key)
        return result
    
    def builtin_set_union(self, set1, set2):
        """Return a new set containing all elements from both set1 and set2"""
        if not isinstance(set1, FawkArray):
            raise RuntimeError("set_union requires arrays as arguments")
        if not isinstance(set2, FawkArray):
            raise RuntimeError("set_union requires arrays as arguments")
        
        result = FawkArray()
        # Add all elements from set1
        for key in set1.keys():
            result.set(key, 1)
        # Add all elements from set2
        for key in set2.keys():
            result.set(key, 1)
        return result
    
    def builtin_set_intersection(self, set1, set2):
        """Return a new set containing only elements that are in both set1 and set2"""
        if not isinstance(set1, FawkArray):
            raise RuntimeError("set_intersection requires arrays as arguments")
        if not isinstance(set2, FawkArray):
            raise RuntimeError("set_intersection requires arrays as arguments")
        
        result = FawkArray()
        # Only add elements that are in both sets
        for key in set1.keys():
            if key in set2.data:
                result.set(key, 1)
        return result
    
    def builtin_set_diff(self, set1, set2):
        """Return a new set containing elements in set1 but not in set2"""
        if not isinstance(set1, FawkArray):
            raise RuntimeError("set_diff requires arrays as arguments")
        if not isinstance(set2, FawkArray):
            raise RuntimeError("set_diff requires arrays as arguments")
        
        result = FawkArray()
        # Add elements from set1 that are not in set2
        for key in set1.keys():
            if key not in set2.data:
                result.set(key, 1)
        return result
    
    def builtin_match(self, pattern, text):
        """Match a regex pattern and return array with full match and groups"""
        text_str = str(text)
        # Cache compiled regex patterns for better performance
        if pattern not in self._regex_cache:
            try:
                self._regex_cache[pattern] = re.compile(pattern)
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")
        compiled_pattern = self._regex_cache[pattern]
        match = compiled_pattern.search(text_str)
        
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
        # AWK uses 1-based indexing for split() results
        for i, part in enumerate(parts, 1):
            result.set(i, part)
        
        return result
    
    def use_high_precision(self):
        """Check if we should use high precision arithmetic (cached for performance)"""
        return self._use_high_precision
    
    def to_decimal(self, value):
        """Convert value to Decimal for high precision arithmetic"""
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, int):
            return Decimal(value)
        elif isinstance(value, float):
            # Convert float to string to avoid precision loss
            return Decimal(str(value))
        elif isinstance(value, str):
            try:
                return Decimal(value)
            except:
                return Decimal(0)
        return Decimal(0)
    
    def from_decimal(self, value):
        """Convert Decimal back to regular number if not in high precision mode"""
        if self.use_high_precision():
            return value
        else:
            return float(value)
    
    def builtin_atan2(self, y, x):
        """Arctangent of y/x in radians"""
        if self.use_high_precision():
            import mpmath
            mpmath.mp.dps = self.PREC  # decimal places of precision
            result = mpmath.atan2(mpmath.mpf(str(y)), mpmath.mpf(str(x)))
            return Decimal(str(result))
        else:
            return math.atan2(self.to_number(y), self.to_number(x))
    
    def builtin_cos(self, x):
        """Cosine of x (in radians)"""
        if self.use_high_precision():
            import mpmath
            mpmath.mp.dps = self.PREC
            result = mpmath.cos(mpmath.mpf(str(x)))
            return Decimal(str(result))
        else:
            return math.cos(self.to_number(x))
    
    def builtin_sin(self, x):
        """Sine of x (in radians)"""
        if self.use_high_precision():
            import mpmath
            mpmath.mp.dps = self.PREC
            result = mpmath.sin(mpmath.mpf(str(x)))
            return Decimal(str(result))
        else:
            return math.sin(self.to_number(x))
    
    def builtin_exp(self, x):
        """Exponential function (e^x)"""
        if self.use_high_precision():
            import mpmath
            mpmath.mp.dps = self.PREC
            result = mpmath.exp(mpmath.mpf(str(x)))
            return Decimal(str(result))
        else:
            return math.exp(self.to_number(x))
    
    def builtin_log(self, x):
        """Natural logarithm"""
        if self.use_high_precision():
            import mpmath
            mpmath.mp.dps = self.PREC
            result = mpmath.log(mpmath.mpf(str(x)))
            return Decimal(str(result))
        else:
            return math.log(self.to_number(x))
    
    def builtin_sqrt(self, x):
        """Square root"""
        if self.use_high_precision():
            import mpmath
            mpmath.mp.dps = self.PREC
            result = mpmath.sqrt(mpmath.mpf(str(x)))
            return Decimal(str(result))
        else:
            return math.sqrt(self.to_number(x))
    
    def builtin_int(self, x):
        """Integer part of x"""
        num = self.to_number(x)
        # If it's a float, convert to int (truncates towards zero)
        if isinstance(num, float):
            return int(num)
        return int(num)
    
    def builtin_rand(self):
        """Random number between 0 and 1"""
        return self.random.random()
    
    def builtin_srand(self, seed=None):
        """Seed the random number generator"""
        if seed is None:
            import time
            seed = int(time.time())
        else:
            seed = int(self.to_number(seed))
        self.random.seed(seed)
        return seed
    
    def builtin_printf(self, fmt, *args):
        """Print formatted output"""
        output = self.format_string(fmt, args)
        print(output, end='')
        return len(output)
    
    def builtin_sprintf(self, fmt, *args):
        """Return formatted string"""
        return self.format_string(fmt, args)
    
    def _format_decimal(self, value, format_spec, conv):
        """Format a Decimal value with high precision"""
        import re
        from decimal import ROUND_HALF_UP
        
        # Parse the format spec to extract precision
        match = re.match(r'%([+-]?)(\d*)\.?(\d*)([fFeEgG])', format_spec)
        if not match:
            return str(value)
        
        sign_flag, width, precision, conversion = match.groups()
        
        if not precision:
            precision = 6  # default precision
        else:
            precision = int(precision)
        
        # Format the decimal number
        if conversion in 'fF':
            # Fixed-point notation
            # Round to the specified precision using ROUND_HALF_UP (like C printf)
            getcontext().prec = self.PREC
            quantize_exp = Decimal(10) ** -precision
            rounded = value.quantize(quantize_exp, rounding=ROUND_HALF_UP)
            result = format(rounded, f'.{precision}f')
        elif conversion in 'eE':
            # Scientific notation
            result = format(float(value), format_spec.replace('%', ''))
        else:  # 'gG'
            # General format
            result = format(float(value), format_spec.replace('%', ''))
        
        return result
    
    def format_string(self, fmt, args):
        """Format string with printf-style formatting"""
        fmt_str = self.value_to_string(fmt)
        arg_list = list(args)
        arg_idx = 0
        result = []
        i = 0
        
        while i < len(fmt_str):
            if fmt_str[i] == '%':
                if i + 1 < len(fmt_str) and fmt_str[i + 1] == '%':
                    result.append('%')
                    i += 2
                    continue
                
                # Parse format specifier
                i += 1
                spec_start = i
                
                # Skip flags
                while i < len(fmt_str) and fmt_str[i] in '-+ 0#':
                    i += 1
                
                # Parse width
                while i < len(fmt_str) and fmt_str[i].isdigit():
                    i += 1
                
                # Parse precision
                if i < len(fmt_str) and fmt_str[i] == '.':
                    i += 1
                    while i < len(fmt_str) and fmt_str[i].isdigit():
                        i += 1
                
                # Parse conversion specifier
                if i < len(fmt_str):
                    conv = fmt_str[i]
                    format_spec = fmt_str[spec_start-1:i+1]
                    
                    if arg_idx < len(arg_list):
                        arg = arg_list[arg_idx]
                        arg_idx += 1
                        
                        try:
                            if conv in 'dioxX':
                                # Integer conversion
                                result.append(format_spec % int(self.to_number(arg)))
                            elif conv in 'eEfFgG':
                                # Float conversion
                                if self.use_high_precision() and isinstance(arg, Decimal):
                                    # For high precision, format Decimal with custom precision
                                    result.append(self._format_decimal(arg, format_spec, conv))
                                else:
                                    result.append(format_spec % float(self.to_number(arg)))
                            elif conv in 'sc':
                                # String/char conversion
                                result.append(format_spec % self.value_to_string(arg))
                            else:
                                result.append(format_spec)
                        except (ValueError, TypeError) as e:
                            # If formatting fails, just append the value
                            result.append(str(arg))
                    else:
                        # Not enough arguments - append format specifier as-is (matches some AWK behavior)
                        # But actually, we should probably error like gawk does, but for now just append it
                        result.append(format_spec)
                    i += 1
                else:
                    break
            else:
                result.append(fmt_str[i])
                i += 1
        
        return ''.join(result)
    
    def builtin_substr(self, string, start, length=None):
        """Extract substring"""
        # Handle large integers by temporarily increasing limit
        import sys
        old_limit = sys.get_int_max_str_digits()
        try:
            sys.set_int_max_str_digits(0)  # 0 means no limit
            s = self.value_to_string(string)
            start_idx = int(self.to_number(start)) - 1  # AWK uses 1-based indexing
            if start_idx < 0:
                start_idx = 0
            
            if length is None:
                return s[start_idx:]
            else:
                length_val = int(self.to_number(length))
                return s[start_idx:start_idx + length_val]
        finally:
            sys.set_int_max_str_digits(old_limit)
    
    def builtin_tolower(self, string):
        """Convert string to lowercase"""
        return self.value_to_string(string).lower()
    
    def builtin_toupper(self, string):
        """Convert string to uppercase"""
        return self.value_to_string(string).upper()
    
    def builtin_gsub(self, pattern, replacement, target=None):
        """Global substitution (replace all occurrences) - returns new string, does not mutate"""
        if target is None:
            target = self.current_line
        
        target_str = self.value_to_string(target)
        pattern_str = self.value_to_string(pattern)
        replacement_str = self.value_to_string(replacement)
        
        # Cache compiled regex patterns
        if pattern_str not in self._regex_cache:
            try:
                self._regex_cache[pattern_str] = re.compile(pattern_str)
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")
        compiled_pattern = self._regex_cache[pattern_str]
        
        # Return the new string (immutable behavior)
        result = compiled_pattern.sub(replacement_str, target_str)
        return result
    
    def builtin_sub(self, pattern, replacement, target=None):
        """Substitution (replace first occurrence) - returns new string, does not mutate"""
        if target is None:
            target = self.current_line
        
        target_str = self.value_to_string(target)
        pattern_str = self.value_to_string(pattern)
        replacement_str = self.value_to_string(replacement)
        
        # Cache compiled regex patterns
        if pattern_str not in self._regex_cache:
            try:
                self._regex_cache[pattern_str] = re.compile(pattern_str)
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")
        compiled_pattern = self._regex_cache[pattern_str]
        
        # Replace only first occurrence and return the new string (immutable behavior)
        result, count = compiled_pattern.subn(replacement_str, target_str, count=1)
        return result
    
    def builtin_close(self, filename_or_cmd):
        """Close a file or command pipe"""
        key = self.value_to_string(filename_or_cmd)
        
        # Check if it's a command pipe
        if key in self.open_pipes:
            pipe = self.open_pipes[key]
            try:
                pipe.stdout.close()
                pipe.wait()
            except:
                pass
            del self.open_pipes[key]
            return 0
        
        # Check if it's a redirect file
        if key in self.redirect_files:
            try:
                self.redirect_files[key].close()
            except:
                pass
            del self.redirect_files[key]
            return 0
        
        # File/command not open
        return -1
    
    def builtin_fflush(self, filename=None):
        """
        Flush any buffered output associated with filename.
        If no argument or empty string, flush all open output files and pipes.
        Returns 0 on success, -1 on failure.
        """
        import sys
        
        # Handle no argument or empty string - flush all open output files and pipes
        if filename is None:
            filename_str = ""
        else:
            filename_str = self.value_to_string(filename)
        
        if filename_str == "":
            # Flush all open output files and pipes
            all_success = True
            failed_files = []
            
            # Flush all redirect files
            for fname, file_handle in list(self.redirect_files.items()):
                try:
                    file_handle.flush()
                except (IOError, OSError) as e:
                    all_success = False
                    failed_files.append(fname)
            
            # Flush stdout and stderr
            try:
                sys.stdout.flush()
            except (IOError, OSError):
                all_success = False
                failed_files.append("/dev/stdout")
            
            try:
                sys.stderr.flush()
            except (IOError, OSError):
                all_success = False
                failed_files.append("/dev/stderr")
            
            # Issue warnings for failed files
            if failed_files:
                for fname in failed_files:
                    print(f"fawk: warning: fflush: failed to flush '{fname}'", file=sys.stderr)
                return -1
            
            return 0 if all_success else -1
        
        # Handle specific filename
        # Special handling for /dev/stdout and /dev/stderr
        if filename_str == "/dev/stdout":
            try:
                sys.stdout.flush()
                return 0
            except (IOError, OSError):
                print(f"fawk: warning: fflush: failed to flush '/dev/stdout'", file=sys.stderr)
                return -1
        
        if filename_str == "/dev/stderr":
            try:
                sys.stderr.flush()
                return 0
            except (IOError, OSError):
                print(f"fawk: warning: fflush: failed to flush '/dev/stderr'", file=sys.stderr)
                return -1
        
        # Check if it's a redirect file (output file)
        if filename_str in self.redirect_files:
            try:
                self.redirect_files[filename_str].flush()
                return 0
            except (IOError, OSError) as e:
                print(f"fawk: warning: fflush: failed to flush '{filename_str}': {e}", file=sys.stderr)
                return -1
        
        # Check if it's an input pipe (read-only) - issue warning
        if filename_str in self.open_pipes:
            print(f"fawk: warning: fflush: cannot flush file or pipe '{filename_str}' opened for reading", file=sys.stderr)
            return -1
        
        # File/pipe not open - issue warning
        print(f"fawk: warning: fflush: '{filename_str}' is not an open file, pipe, or coprocess", file=sys.stderr)
        return -1
    
    def builtin_hash(self, value):
        """Return a hash integer for any AWK value"""
        return self._hash_value(value)
    
    def _deterministic_hash(self, data):
        """Create a deterministic hash from bytes or string"""
        # Use a simple deterministic hash algorithm (FNV-1a variant)
        if isinstance(data, str):
            data = data.encode('utf-8')
        hash_val = 2166136261  # FNV offset basis
        for byte in data:
            hash_val ^= byte
            hash_val = (hash_val * 16777619) & 0xffffffffffffffff  # 64-bit mask
        # Convert to signed 64-bit integer (Python int, but in range)
        if hash_val > 0x7fffffffffffffff:
            hash_val = hash_val - 0x10000000000000000
        return hash_val
    
    def _hash_value(self, value):
        """Recursively hash an AWK value with deterministic results"""
        # Optimized: use type() for faster checks
        value_type = type(value)
        if value_type is FawkArray:
            # For arrays, create a deterministic hash by sorting keys
            # and recursively hashing key-value pairs
            # Optimized: iterate over data.items() directly instead of calling keys()
            sorted_items = []
            # Get all items and sort them
            for key, val in value.data.items():
                # Sort key: strings come after numbers, both sorted within their group
                if type(key) is int:
                    sort_key = (0, key)  # 0 = numeric
                elif type(key) is str:
                    # Try to parse as number for sorting
                    try:
                        num_val = float(key)
                        sort_key = (0, num_val)  # 0 = numeric
                    except (ValueError, TypeError):
                        sort_key = (1, key)  # 1 = string
                else:
                    sort_key = (1, str(key))  # 1 = string
                sorted_items.append((sort_key, key, val))
            
            # Sort by sort_key
            sorted_items.sort(key=lambda x: x[0])
            
            # Hash the sorted items
            hashed_items = []
            for _, key, val in sorted_items:
                hashed_key = self._hash_value(key)
                hashed_val = self._hash_value(val)
                hashed_items.append((hashed_key, hashed_val))
            
            # Create deterministic hash from tuple representation
            items_str = str(hashed_items)
            return self._deterministic_hash(items_str)
        elif value_type is bool:
            return 1 if value else 0
        elif value_type is int:
            # For integers, return the value itself (deterministic)
            return value
        elif value_type is float:
            # For floats, use deterministic hash of string representation
            return self._deterministic_hash(str(value))
        elif value_type is str:
            return self._deterministic_hash(value)
        elif value is None:
            return 0
        elif isinstance(value, UserFunction):
            # For user functions, create hash from params and a hash of the body
            # Use params as string and body representation
            params_str = ",".join(value.params)
            body_str = str(value.body)
            func_str = f"UserFunction({params_str}):{body_str}"
            return self._deterministic_hash(func_str)
        elif callable(value):
            # For built-in functions, try to find the function name
            func_name = None
            for name, builtin_func in self.builtin_functions.items():
                if value is builtin_func:
                    func_name = name
                    break
            if func_name:
                # Use function name for deterministic hash
                return self._deterministic_hash(f"builtin:{func_name}")
            else:
                # Unknown callable - use id() which is consistent within a run
                # Convert to signed 64-bit integer
                obj_id = id(value)
                if obj_id > 0x7fffffffffffffff:
                    obj_id = obj_id - 0x10000000000000000
                return obj_id
        else:
            # Fallback for any other type - use deterministic hash of string representation
            return self._deterministic_hash(str(value))
    
    def error(self, msg: str):
        raise RuntimeError(msg)
    
    def is_truthy(self, value) -> bool:
        # Optimized: use type() for faster checks
        value_type = type(value)
        if value_type is bool:
            return value
        elif value_type is int or value_type is float:
            return value != 0
        elif value_type is str:
            return value != ""
        elif value_type is FawkArray:
            return value.length() > 0
        elif value is None:
            return False
        return True
    
    def to_number(self, value):
        """Convert value to number (like AWK does)"""
        # Fast path for common types - optimized: use type() for faster checks
        value_type = type(value)
        if value_type is int:
            return value
        if value_type is float:
            return value
        if value_type is str:
            # Try to parse as number
            # Optimize: check if string looks numeric before parsing
            if not value:
                return 0
            try:
                # Fast path for integers (most common case)
                if value.isdigit() or (value[0] == '-' and value[1:].isdigit()):
                    return int(value)
                # Try to parse beginning number (e.g., "123abc" -> 123, "123.45abc" -> 123.45)
                # This matches AWK behavior where int("123abc") = 123
                import re
                # Match: optional sign, digits, optional decimal point and digits, optional exponent
                match = re.match(r'^([+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)', value)
                if match:
                    num_str = match.group(1)
                    if '.' in num_str or 'e' in num_str.lower() or 'E' in num_str:
                        return float(num_str)
                    return int(num_str)
                # If no match, try direct conversion (for pure numeric strings)
                if '.' in value or 'e' in value.lower():
                    return float(value)
                return int(value)
            except (ValueError, AttributeError):
                return 0  # AWK default for non-numeric strings
        return 0
    
    def eval(self, node: ASTNode) -> Any:
        # Optimized dispatch: fast-path for most common node types using if/elif
        # This avoids dictionary lookup overhead for hot paths
        # Based on profiling: Identifier (4.3M), BinaryOp (1M), ExprStmt (702K), etc.
        node_type = type(node)
        
        # Fast path: check most common types first (ordered by frequency)
        if node_type is Identifier:
            return self.eval_Identifier(node)
        elif node_type is BinaryOp:
            return self.eval_BinaryOp(node)
        elif node_type is ExprStmt:
            return self.eval_ExprStmt(node)
        elif node_type is Assignment:
            return self.eval_Assignment(node)
        elif node_type is ArrayAccess:
            return self.eval_ArrayAccess(node)
        elif node_type is ArrayLiteral:
            return self.eval_ArrayLiteral(node)
        elif node_type is Block:
            return self.eval_Block(node)
        elif node_type is IfStmt:
            return self.eval_IfStmt(node)
        elif node_type is Number:
            return self.eval_Number(node)
        elif node_type is FunctionCall:
            return self.eval_FunctionCall(node)
        elif node_type is ReturnStmt:
            return self.eval_ReturnStmt(node)
        elif node_type is ForInStmt:
            return self.eval_ForInStmt(node)
        elif node_type is String:
            return self.eval_String(node)
        elif node_type is UnaryOp:
            return self.eval_UnaryOp(node)
        elif node_type is FieldAccess:
            return self.eval_FieldAccess(node)
        elif node_type is Pipeline:
            return self.eval_Pipeline(node)
        elif node_type is PrefixIncrement:
            return self.eval_PrefixIncrement(node)
        elif node_type is PrefixDecrement:
            return self.eval_PrefixDecrement(node)
        elif node_type is PostfixIncrement:
            return self.eval_PostfixIncrement(node)
        elif node_type is PostfixDecrement:
            return self.eval_PostfixDecrement(node)
        elif node_type is TernaryOp:
            return self.eval_TernaryOp(node)
        elif node_type is AssocArray:
            return self.eval_AssocArray(node)
        elif node_type is Lambda:
            return self.eval_Lambda(node)
        elif node_type is Regex:
            return self.eval_Regex(node)
        elif node_type is InOp:
            return self.eval_InOp(node)
        elif node_type is CommaExpr:
            return self.eval_CommaExpr(node)
        elif node_type is PipedGetline:
            return self.eval_PipedGetline(node)
        elif node_type is DestructurePattern:
            return self.eval_DestructurePattern(node)
        else:
            # Fallback to dictionary for less common types
            method = self._eval_dispatch.get(node_type)
            if method:
                return method(node)
            else:
                self.error(f"No eval method for {node_type.__name__}")
    
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
        
        # Optimized: use type() for exact match (faster than isinstance)
        if type(iterable) is not FawkArray:
            self.error("for-in requires an array")
        
        # Optimized: cache keys() result if array is not being modified
        # For read-only iteration, we can use keys() once
        keys_list = iterable.keys()
        for key in keys_list:
            # Use set() instead of set_local() to ensure it updates the variable
            # even if it already exists in the environment
            self.current_env.set(node.var, key)
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                continue
    
    def eval_ForStmt(self, node: ForStmt) -> None:
        # C-style for loop: for (init; condition; update) body
        # Initialize
        if node.init:
            self.eval(node.init)
        
        # Loop
        while True:
            # Check condition
            if node.condition:
                if not self.is_truthy(self.eval(node.condition)):
                    break
            # If no condition, loop forever (or until break)
            
            # Execute body
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                pass  # Continue to update
            
            # Update
            if node.update:
                self.eval(node.update)
    
    def eval_WhileStmt(self, node: WhileStmt) -> None:
        while self.is_truthy(self.eval(node.condition)):
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                continue
    
    def eval_DoWhileStmt(self, node: DoWhileStmt) -> None:
        while True:
            try:
                self.eval(node.body)
            except BreakException:
                break
            except ContinueException:
                pass  # Continue to condition check
            
            if not self.is_truthy(self.eval(node.condition)):
                break
    
    def eval_SwitchStmt(self, node: SwitchStmt) -> None:
        switch_value = self.eval(node.expr)
        
        # Find matching case or default
        matched = False
        default_case = None
        
        for case in node.cases:
            if case.value is None:
                # Default case
                default_case = case
            elif not matched:
                # Check if this case matches
                case_value = self.eval(case.value)
                if switch_value == case_value:
                    matched = True
                    # Execute this case's statements
                    try:
                        for stmt in case.statements:
                            self.eval(stmt)
                    except BreakException:
                        return  # Break out of switch
        
        # If no case matched, execute default if it exists
        if not matched and default_case:
            try:
                for stmt in default_case.statements:
                    self.eval(stmt)
            except BreakException:
                return  # Break out of switch
    
    def eval_ReturnStmt(self, node: ReturnStmt) -> None:
        # Check for tail recursion: if returning a function call to the same function
        if (node.value and 
            isinstance(node.value, FunctionCall) and 
            isinstance(node.value.func, Identifier) and
            self.current_function_name and
            node.value.func.name == self.current_function_name):
            # This is a tail call - raise special exception
            raise TailCallException(node.value)
        
        value = self.eval(node.value) if node.value else None
        raise ReturnException(value)
    
    def eval_ExitStmt(self, node: ExitStmt) -> None:
        code = 0
        if node.code:
            code = int(self.to_number(self.eval(node.code)))
        raise ExitException(code)
    
    def eval_NextStmt(self, node: NextStmt) -> None:
        raise NextException()
    
    def eval_NextFileStmt(self, node: NextFileStmt) -> None:
        raise NextFileException()
    
    def eval_BreakStmt(self, node: BreakStmt) -> None:
        raise BreakException()
    
    def eval_ContinueStmt(self, node: ContinueStmt) -> None:
        raise ContinueException()
    
    def eval_DeleteStmt(self, node) -> None:
        """Delete an array element, field, or entire array/variable"""
        from .fawk_ast import DeleteStmt, Identifier, ArrayAccess, FieldAccess
        
        if isinstance(node.target, Identifier):
            # Delete entire array or variable
            name = node.target.name
            if name in self.current_env.vars:
                del self.current_env.vars[name]
            elif name in self.global_env.vars:
                del self.global_env.vars[name]
        
        elif isinstance(node.target, ArrayAccess):
            # Delete array element
            array = self.eval(node.target.array)
            if isinstance(array, FawkArray):
                # Compute the index
                if len(node.target.indices) == 1:
                    index = self.eval(node.target.indices[0])
                else:
                    # Multiple indices: concatenate with SUBSEP
                    index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.target.indices]
                    index = self.SUBSEP.join(index_values)
                
                # Convert index to the right type
                if isinstance(index, (int, float)):
                    index = int(index)
                else:
                    index = str(index)
                
                # Delete the key if it exists (using COW-aware method)
                array.delete(index)
        
        elif isinstance(node.target, FieldAccess):
            # Delete field: delete $3
            index = self.eval(node.target.index)
            index = int(index)
            
            if index <= 0:
                # Can't delete $0 or negative fields
                return
            
            if index > self.NF:
                # Field doesn't exist, nothing to delete
                return
            
            # Delete the field by shifting subsequent fields left
            # Remove field at index (1-based, convert to 0-based)
            field_idx = index - 1
            
            # Shift all fields after this one to the left
            for i in range(field_idx, len(self.fields) - 1):
                self.fields[i] = self.fields[i + 1]
            
            # Remove the last field (now duplicate)
            if len(self.fields) > 0:
                self.fields.pop()
            
            # Update NF
            self.NF = len(self.fields)
            
            # Reconstruct $0 by joining fields with OFS
            if self.NF > 0:
                self.current_line = self.OFS.join(self.fields)
            else:
                # All fields deleted, $0 is empty
                self.current_line = ""
    
    def eval_DelarrayStmt(self, node) -> None:
        """Delete all elements from an array"""
        from .fawk_ast import DelarrayStmt, Identifier
        
        if not isinstance(node.target, Identifier):
            self.error("delarray target must be an array variable name")
        
        name = node.target.name
        
        # Get the array from the appropriate environment
        array = None
        if name in self.current_env.vars:
            array = self.current_env.vars[name]
        elif name in self.global_env.vars:
            array = self.global_env.vars[name]
        else:
            # Array doesn't exist, nothing to do (GAWK behavior)
            return
        
        # Check if it's actually an array
        if isinstance(array, FawkArray):
            # Delete all elements (using COW-aware method)
            array.clear()
        else:
            # Not an array, delete the variable entirely
            if name in self.current_env.vars:
                del self.current_env.vars[name]
            elif name in self.global_env.vars:
                del self.global_env.vars[name]
    
    def eval_PrintStmt(self, node: PrintStmt) -> None:
        # Prepare output string
        if not node.args:
            output = ""
        else:
            values = [self.value_to_string(self.eval(arg)) for arg in node.args]
            output = self.OFS.join(values)
        
        # Handle redirection
        if node.redirect_type and node.redirect_target:
            self._write_redirected(output + self.ORS, node.redirect_type, node.redirect_target)
        else:
            # No redirection, print to stdout
            print(output, end=self.ORS)
    
    def eval_PrintfStmt(self, node: 'PrintfStmt') -> None:
        from .fawk_ast import PrintfStmt
        
        # Printf requires at least a format string
        if not node.args:
            self.error("printf requires at least a format string")
        
        # Evaluate arguments
        args = [self.eval(arg) for arg in node.args]
        
        # First arg is format string, rest are values to format
        fmt = args[0]
        values = args[1:] if len(args) > 1 else []
        
        # Format the output
        output = self.format_string(fmt, values)
        
        # Handle redirection
        if node.redirect_type and node.redirect_target:
            self._write_redirected(output, node.redirect_type, node.redirect_target)
        else:
            # No redirection, print to stdout (no ORS for printf)
            print(output, end='')
    
    def _write_redirected(self, output: str, redirect_type: str, redirect_target) -> None:
        """Helper method to write output to a redirected file or stream"""
        import sys
        
        # Evaluate redirect target to get filename
        filename = self.value_to_string(self.eval(redirect_target))
        
        # Special handling for /dev/stderr and /dev/stdout
        if filename == "/dev/stderr":
            print(output, end='', file=sys.stderr)
        elif filename == "/dev/stdout":
            print(output, end='', file=sys.stdout)
        else:
            # Handle file redirection
            if redirect_type == ">":
                # Overwrite mode - close existing file if open and reopen
                if filename in self.redirect_files:
                    self.redirect_files[filename].close()
                    del self.redirect_files[filename]
                
                # Open file in write mode
                try:
                    self.redirect_files[filename] = open(filename, 'w')
                except IOError as e:
                    self.error(f"Cannot open file '{filename}' for writing: {e}")
                
                # Write to file
                print(output, end='', file=self.redirect_files[filename])
                self.redirect_files[filename].flush()
            
            elif redirect_type == ">>":
                # Append mode - open if not already open
                if filename not in self.redirect_files:
                    try:
                        self.redirect_files[filename] = open(filename, 'a')
                    except IOError as e:
                        self.error(f"Cannot open file '{filename}' for appending: {e}")
                
                # Write to file
                print(output, end='', file=self.redirect_files[filename])
                self.redirect_files[filename].flush()
    
    def value_to_string(self, value) -> str:
        """Convert value to string for print statements (uses OFMT)"""
        if isinstance(value, FawkArray):
            return str(value)
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, UserFunction):
            return "<function>"
        elif callable(value):
            # Check if it's a built-in function by comparing with known built-ins
            for builtin_func in self.builtin_functions.values():
                if value is builtin_func:
                    return "<function>"
            # If it's callable but not a known built-in, still treat as function
            # (could be a lambda or other callable passed from outside)
            return "<function>"
        elif isinstance(value, Decimal):
            # Format Decimal values using OFMT
            try:
                return self.OFMT % float(value)
            except:
                return str(value)
        elif isinstance(value, int):
            # For arbitrary precision integers, convert directly to string
            # without using OFMT (which would try to format as float)
            import sys
            # Temporarily increase the limit for large integers
            old_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0)  # 0 means no limit
                return str(value)
            finally:
                sys.set_int_max_str_digits(old_limit)
        elif isinstance(value, float):
            # Format floats using OFMT
            try:
                # Check if it's actually an integer value
                if value == int(value):
                    return str(int(value))
                return self.OFMT % value
            except:
                return str(value)
        elif value is None:
            return ""
        return str(value)
    
    def value_to_string_convert(self, value) -> str:
        """Convert value to string for conversions (uses CONVFMT for numbers)"""
        if isinstance(value, FawkArray):
            return str(value)
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, Decimal):
            # Format Decimal values using CONVFMT
            try:
                return self.CONVFMT % float(value)
            except:
                return str(value)
        elif isinstance(value, int):
            # For arbitrary precision integers, convert directly to string
            # without using CONVFMT (which would try to format as float)
            import sys
            old_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0)  # 0 means no limit
                return str(value)
            finally:
                sys.set_int_max_str_digits(old_limit)
        elif isinstance(value, float):
            # Format floats using CONVFMT
            try:
                # Check if it's actually an integer value
                if value == int(value):
                    return str(int(value))
                return self.CONVFMT % value
            except:
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
        
        # String concatenation (uses CONVFMT for number conversions)
        if op == 'concat':
            return self.value_to_string_convert(left) + self.value_to_string_convert(right)
        # Arithmetic operations - convert to numbers
        elif op == '+':
            if self.use_high_precision():
                getcontext().prec = self.PREC
                return self.to_decimal(left) + self.to_decimal(right)
            return self.to_number(left) + self.to_number(right)
        elif op == '-':
            if self.use_high_precision():
                getcontext().prec = self.PREC
                return self.to_decimal(left) - self.to_decimal(right)
            return self.to_number(left) - self.to_number(right)
        elif op == '*':
            if self.use_high_precision():
                getcontext().prec = self.PREC
                return self.to_decimal(left) * self.to_decimal(right)
            return self.to_number(left) * self.to_number(right)
        elif op == '/':
            if self.use_high_precision():
                getcontext().prec = self.PREC
                right_dec = self.to_decimal(right)
                if right_dec == 0:
                    self.error("Division by zero")
                return self.to_decimal(left) / right_dec
            else:
                right_num = self.to_number(right)
                if right_num == 0:
                    self.error("Division by zero")
                return self.to_number(left) / right_num
        elif op == '%':
            if self.use_high_precision():
                getcontext().prec = self.PREC
                return self.to_decimal(left) % self.to_decimal(right)
            return self.to_number(left) % self.to_number(right)
        elif op == '^':
            # Power operation with arbitrary precision support for integers
            left_num = self.to_number(left)
            right_num = self.to_number(right)
            
            # Check if both operands are integers (or integer-valued floats)
            # Optimized: use type() for faster checks
            left_is_int = type(left_num) is int or (type(left_num) is float and left_num == int(left_num))
            right_is_int = type(right_num) is int or (type(right_num) is float and right_num == int(right_num))
            
            if left_is_int and right_is_int and right_num >= 0:
                # Use Python's arbitrary precision integer arithmetic
                base = int(left_num)
                exponent = int(right_num)
                return base ** exponent
            elif self.use_high_precision():
                # High precision floating point
                import mpmath
                mpmath.mp.dps = self.PREC
                result = mpmath.power(mpmath.mpf(str(left_num)), mpmath.mpf(str(right_num)))
                return Decimal(str(result))
            else:
                # Standard floating point
                return left_num ** right_num
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
            # If right is a Regex node, get its pattern
            # Optimized: use type() for faster checks
            if type(node.right) is Regex:
                pattern = node.right.pattern
                flags = 0
                if 'i' in node.right.flags:
                    flags |= re.IGNORECASE
                # Cache compiled regex patterns
                cache_key = (pattern, flags)
                if cache_key not in self._regex_cache:
                    try:
                        self._regex_cache[cache_key] = re.compile(pattern, flags)
                    except re.error as e:
                        self.error(f"Invalid regex pattern: {e}")
                compiled_pattern = self._regex_cache[cache_key]
                return bool(compiled_pattern.search(text))
            else:
                pattern = self.value_to_string(right)
                # Cache compiled regex patterns
                if pattern not in self._regex_cache:
                    try:
                        self._regex_cache[pattern] = re.compile(pattern)
                    except re.error as e:
                        self.error(f"Invalid regex pattern: {e}")
                compiled_pattern = self._regex_cache[pattern]
                return bool(compiled_pattern.search(text))
        elif op == '!~':
            # String !~ pattern: check if string does not match pattern
            text = self.value_to_string(left)
            # If right is a Regex node, get its pattern
            if isinstance(node.right, Regex):
                pattern = node.right.pattern
                flags = 0
                if 'i' in node.right.flags:
                    flags |= re.IGNORECASE
                # Cache compiled regex patterns
                cache_key = (pattern, flags)
                if cache_key not in self._regex_cache:
                    try:
                        self._regex_cache[cache_key] = re.compile(pattern, flags)
                    except re.error as e:
                        self.error(f"Invalid regex pattern: {e}")
                compiled_pattern = self._regex_cache[cache_key]
                return not bool(compiled_pattern.search(text))
            else:
                pattern = self.value_to_string(right)
                # Cache compiled regex patterns
                if pattern not in self._regex_cache:
                    try:
                        self._regex_cache[pattern] = re.compile(pattern)
                    except re.error as e:
                        self.error(f"Invalid regex pattern: {e}")
                compiled_pattern = self._regex_cache[pattern]
                return not bool(compiled_pattern.search(text))
        else:
            self.error(f"Unknown binary operator: {op}")
    
    def eval_UnaryOp(self, node: UnaryOp) -> Any:
        operand = self.eval(node.operand)
        
        if node.op == '-':
            if self.use_high_precision():
                getcontext().prec = self.PREC
                return -self.to_decimal(operand)
            return -self.to_number(operand)
        elif node.op == '!':
            return not self.is_truthy(operand)
        else:
            self.error(f"Unknown unary operator: {node.op}")
    
    def eval_TernaryOp(self, node: TernaryOp) -> Any:
        """Evaluate ternary operator: condition ? true_expr : false_expr"""
        condition_value = self.eval(node.condition)
        if self.is_truthy(condition_value):
            return self.eval(node.true_expr)
        else:
            return self.eval(node.false_expr)
    
    def eval_PrefixIncrement(self, node) -> Any:
        """Prefix increment: ++x - increment and return new value"""
        from .fawk_ast import PrefixIncrement, Identifier, ArrayAccess
        
        # Get current value
        current_value = self.eval(node.operand)
        new_value = self.to_number(current_value) + 1
        
        # Update the variable/array element
        if isinstance(node.operand, Identifier):
            name = node.operand.name
            if name in self.globals_declared:
                self.global_env.set(name, new_value)
            elif self.in_function:
                self.current_env.set_local(name, new_value)
            else:
                self.global_env.set(name, new_value)
        elif isinstance(node.operand, ArrayAccess):
            array = self.eval(node.operand.array)
            if not isinstance(array, FawkArray):
                array = FawkArray()
                if isinstance(node.operand.array, Identifier):
                    name = node.operand.array.name
                    if name in self.globals_declared:
                        self.global_env.set(name, array)
                    else:
                        self.current_env.set_local(name, array)
            
            if len(node.operand.indices) == 1:
                index = self.eval(node.operand.indices[0])
            else:
                index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.operand.indices]
                index = self.SUBSEP.join(index_values)
            
            array.set(index, new_value)
        else:
            self.error("Prefix increment operand must be a variable or array element")
        
        return new_value
    
    def eval_PrefixDecrement(self, node) -> Any:
        """Prefix decrement: --x - decrement and return new value"""
        from .fawk_ast import PrefixDecrement, Identifier, ArrayAccess
        
        # Get current value
        current_value = self.eval(node.operand)
        new_value = self.to_number(current_value) - 1
        
        # Update the variable/array element
        if isinstance(node.operand, Identifier):
            name = node.operand.name
            if name in self.globals_declared:
                self.global_env.set(name, new_value)
            elif self.in_function:
                self.current_env.set_local(name, new_value)
            else:
                self.global_env.set(name, new_value)
        elif isinstance(node.operand, ArrayAccess):
            array = self.eval(node.operand.array)
            if not isinstance(array, FawkArray):
                array = FawkArray()
                if isinstance(node.operand.array, Identifier):
                    name = node.operand.array.name
                    if name in self.globals_declared:
                        self.global_env.set(name, array)
                    else:
                        self.current_env.set_local(name, array)
            
            if len(node.operand.indices) == 1:
                index = self.eval(node.operand.indices[0])
            else:
                index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.operand.indices]
                index = self.SUBSEP.join(index_values)
            
            array.set(index, new_value)
        else:
            self.error("Prefix decrement operand must be a variable or array element")
        
        return new_value
    
    def eval_PostfixIncrement(self, node) -> Any:
        """Postfix increment: x++ - return old value, then increment"""
        from .fawk_ast import PostfixIncrement, Identifier, ArrayAccess
        
        # Get current value (this is what we'll return)
        old_value = self.eval(node.operand)
        new_value = self.to_number(old_value) + 1
        
        # Update the variable/array element
        if isinstance(node.operand, Identifier):
            name = node.operand.name
            if name in self.globals_declared:
                self.global_env.set(name, new_value)
            elif self.in_function:
                self.current_env.set_local(name, new_value)
            else:
                self.global_env.set(name, new_value)
        elif isinstance(node.operand, ArrayAccess):
            array = self.eval(node.operand.array)
            if not isinstance(array, FawkArray):
                array = FawkArray()
                if isinstance(node.operand.array, Identifier):
                    name = node.operand.array.name
                    if name in self.globals_declared:
                        self.global_env.set(name, array)
                    else:
                        self.current_env.set_local(name, array)
            
            if len(node.operand.indices) == 1:
                index = self.eval(node.operand.indices[0])
            else:
                index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.operand.indices]
                index = self.SUBSEP.join(index_values)
            
            array.set(index, new_value)
        else:
            self.error("Postfix increment operand must be a variable or array element")
        
        return old_value
    
    def eval_PostfixDecrement(self, node) -> Any:
        """Postfix decrement: x-- - return old value, then decrement"""
        from .fawk_ast import PostfixDecrement, Identifier, ArrayAccess
        
        # Get current value (this is what we'll return)
        old_value = self.eval(node.operand)
        new_value = self.to_number(old_value) - 1
        
        # Update the variable/array element
        if isinstance(node.operand, Identifier):
            name = node.operand.name
            if name in self.globals_declared:
                self.global_env.set(name, new_value)
            elif self.in_function:
                self.current_env.set_local(name, new_value)
            else:
                self.global_env.set(name, new_value)
        elif isinstance(node.operand, ArrayAccess):
            array = self.eval(node.operand.array)
            if not isinstance(array, FawkArray):
                array = FawkArray()
                if isinstance(node.operand.array, Identifier):
                    name = node.operand.array.name
                    if name in self.globals_declared:
                        self.global_env.set(name, array)
                    else:
                        self.current_env.set_local(name, array)
            
            if len(node.operand.indices) == 1:
                index = self.eval(node.operand.indices[0])
            else:
                index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.operand.indices]
                index = self.SUBSEP.join(index_values)
            
            array.set(index, new_value)
        else:
            self.error("Postfix decrement operand must be a variable or array element")
        
        return old_value
    
    def eval_Assignment(self, node: Assignment) -> Any:
        value = self.eval(node.value)
        
        if isinstance(node.target, Identifier):
            # Create a deep copy of arrays when assigning to variables
            # Optimized: use type() for exact match (faster than isinstance)
            if type(value) is FawkArray:
                value = value.copy()
            
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
            elif name == 'PREC':
                self.PREC = int(self.to_number(value))
                self._use_high_precision = self.PREC > 53  # Update cache
            # FAWK scoping rules:
            # - Variables declared with 'global' keyword are always global
            # - Variables assigned in functions (not declared global) are local
            # - Variables assigned outside functions are global
            # - BUT: if a variable already exists in current environment (e.g., from for-in loop),
            #   update it there to maintain proper scoping
            elif name in self.globals_declared:
                # Explicitly declared global
                self.global_env.set(name, value)
            elif self.in_function:
                # Inside function, not declared global: local variable
                self.current_env.set_local(name, value)
            elif name in self.current_env.vars:
                # Variable already exists in current environment (e.g., from for-in loop)
                # Update it there to maintain proper scoping
                self.current_env.set_local(name, value)
            else:
                # Outside function: global by default
                self.global_env.set(name, value)
        
        elif isinstance(node.target, ArrayAccess):
            # Handle nested array access: grid[x][y] = value
            # We need to ensure that grid[x] is a FawkArray before we can set grid[x][y]
            array = self._get_or_create_nested_array(node.target.array)
            
            # Special case: arr[] = value (array append syntax)
            if len(node.target.indices) == 0:
                # Find the next unused numeric index
                # Start from length(arr) + 1
                start_index = array.length() + 1
                
                # Get all keys from the array
                keys_list = array.keys()
                
                # Find the next unused numeric index
                # Check if start_index is already used, if so, find the next gap
                index = start_index
                while True:
                    # Check if this index is already in use
                    # Convert index to the type used in the array (int or str)
                    if isinstance(index, (int, float)):
                        key = int(index)
                    else:
                        key = str(index)
                    
                    if key not in array.data:
                        # Found an unused index
                        break
                    
                    # This index is used, try the next one
                    index += 1
                
                # Convert to the appropriate type for storage
                if isinstance(index, (int, float)):
                    index = int(index)
                else:
                    index = str(index)
            elif len(node.target.indices) == 1:
                index = self.eval(node.target.indices[0])
            else:
                # Multiple indices: concatenate with SUBSEP
                index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.target.indices]
                index = self.SUBSEP.join(index_values)
            
            array.set(index, value)
        
        elif isinstance(node.target, FieldAccess):
            # Field assignment: $2 = value or $0 = value
            index = self.eval(node.target.index)
            index = int(index)
            
            # Convert value to string (fields are strings in AWK)
            value_str = self.value_to_string(value)
            
            if index == 0:
                # Assigning to $0: update the whole record and re-split fields
                self.current_line = value_str
                self.fields = self.split_fields(value_str)
                self.NF = len(self.fields)
            elif index > 0:
                # Assigning to $1, $2, etc.
                # Extend fields array if necessary
                while len(self.fields) < index:
                    self.fields.append("")
                
                # Update the field (1-based to 0-based index)
                self.fields[index - 1] = value_str
                
                # Update NF if we extended beyond current NF
                if index > self.NF:
                    self.NF = index
                
                # Reconstruct $0 by joining fields with OFS
                self.current_line = self.OFS.join(self.fields)
            # Negative indices are ignored (AWK behavior)
        
        elif isinstance(node.target, DestructurePattern):
            # Destructuring assignment: [x, y] = arr or [[x, y], [z, w]] = nested_arr
            if not isinstance(value, FawkArray):
                self.error("Destructuring assignment requires an array")
            
            self._destructure_assign(node.target, value)
        
        else:
            self.error("Invalid assignment target")
        
        return value
    
    def _get_or_create_nested_array(self, node) -> FawkArray:
        """Helper method to get or create a nested array for assignment.
        Handles cases like grid[x][y] = value where grid[x] needs to be a FawkArray."""
        from .fawk_ast import Identifier, ArrayAccess
        
        if isinstance(node, Identifier):
            # Simple variable: get or create the array
            name = node.name
            array = self.eval(node)
            if not isinstance(array, FawkArray):
                array = FawkArray()
                # Store it back
                if name in self.globals_declared:
                    self.global_env.set(name, array)
                elif self.in_function:
                    self.current_env.set_local(name, array)
                elif name in self.current_env.vars:
                    self.current_env.set_local(name, array)
                else:
                    self.global_env.set(name, array)
            return array
        
        elif isinstance(node, ArrayAccess):
            # Nested access: get or create parent, then get or create nested array
            parent_array = self._get_or_create_nested_array(node.array)
            
            # Get the index for accessing the nested array
            if len(node.indices) == 1:
                index = self.eval(node.indices[0])
            else:
                index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.indices]
                index = self.SUBSEP.join(index_values)
            
            # Convert index to the right type
            if isinstance(index, (int, float)):
                index = int(index)
            else:
                index = str(index)
            
            # Get the nested array, or create it if it doesn't exist or isn't an array
            nested_value = parent_array.get(index)
            if not isinstance(nested_value, FawkArray):
                # Create a new nested array and store it
                nested_array = FawkArray()
                parent_array.set(index, nested_array)
                return nested_array
            else:
                return nested_value
        
        else:
            # For other node types, just evaluate and check
            result = self.eval(node)
            if not isinstance(result, FawkArray):
                self.error(f"Expected array, got {type(result).__name__}")
            return result
    
    def _destructure_assign(self, pattern, array: FawkArray) -> None:
        """Helper method to perform destructuring assignment"""
        from .fawk_ast import DestructurePattern, Identifier
        
        # Check if array has enough elements
        # Convert index to appropriate type for checking
        num_patterns = len(pattern.patterns)
        
        # AWK uses 1-based indexing for destructuring, even for match() results
        # (match() results have [0]=full_match, but destructuring starts from [1])
        start_idx = 1
        
        # Check if we're trying to destructure more items than available
        # We need to check if the key exists in the array, not just if get() returns 0
        for i in range(start_idx, start_idx + num_patterns):
            # Convert index to the type used in the array
            if isinstance(i, (int, float)):
                key = int(i)
            else:
                key = str(i)
            
            # Check if this index exists in the array
            if key not in array.data:
                available = i - start_idx
                element_word = "element" if available == 1 else "elements"
                self.error(f"Destructuring pattern has {num_patterns} elements but array has only {available} {element_word}")
        
        # Destructure using 1-based indexing (AWK standard)
        for i, pattern_elem in enumerate(pattern.patterns):
            # Get the value from the array at index (1 + i)
            array_index = start_idx + i
            array_value = array.get(array_index)
            
            if isinstance(pattern_elem, Identifier):
                # Simple identifier: assign the value
                name = pattern_elem.name
                
                # Create a deep copy of arrays when assigning (same as regular assignment)
                if isinstance(array_value, FawkArray):
                    array_value = array_value.copy()
                
                # Use same scoping rules as regular assignment
                if name in self.globals_declared:
                    self.global_env.set(name, array_value)
                elif self.in_function:
                    self.current_env.set_local(name, array_value)
                elif name in self.current_env.vars:
                    self.current_env.set_local(name, array_value)
                else:
                    self.global_env.set(name, array_value)
            
            elif isinstance(pattern_elem, DestructurePattern):
                # Nested destructuring: recursively destructure
                if not isinstance(array_value, FawkArray):
                    self.error(f"Destructuring pattern expects array at index {i}, got {type(array_value).__name__}")
                self._destructure_assign(pattern_elem, array_value)
            
            else:
                self.error(f"Invalid pattern element in destructuring: {type(pattern_elem).__name__}")
    
    def eval_DestructurePattern(self, node) -> Any:
        """DestructurePattern should not be evaluated directly, only used in assignments"""
        from .fawk_ast import DestructurePattern
        self.error("DestructurePattern should only appear as assignment target")
    
    def eval_ArrayLiteral(self, node: ArrayLiteral) -> FawkArray:
        arr = FawkArray()
        # AWK uses 1-based indexing for arrays
        for i, elem in enumerate(node.elements, 1):
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
        # Optimized: use type() for exact match (faster than isinstance)
        if type(array) is not FawkArray:
            return ""  # AWK behavior: return empty string for non-array
        
        # Handle multi-dimensional array access
        if len(node.indices) == 1:
            index = self.eval(node.indices[0])
        else:
            # Multiple indices: concatenate with SUBSEP
            index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.indices]
            index = self.SUBSEP.join(index_values)
        
        # GAWK behavior: accessing an array element auto-creates it if it doesn't exist
        # Convert index to the right type (optimized: use type() for faster checks)
        index_type = type(index)
        if index_type is int:
            pass  # no conversion needed
        elif index_type is float:
            index = int(index)
        else:
            # Try to convert to int, fallback to string
            try:
                index = int(index)
            except (ValueError, TypeError):
                index = str(index)
        
        # Optimized: direct access to data dict, avoiding COW overhead for reads
        # If key doesn't exist, auto-create it with empty string (GAWK behavior)
        if index not in array.data:
            # Need to ensure unique before modifying
            array._ensure_unique()
            array.data[index] = ""
        
        # Direct dict access is faster than get() method
        return array.data.get(index, "")
    
    def eval_FunctionCall(self, node: FunctionCall) -> Any:
        func = self.eval(node.func)
        
        # Check if function was not found (returns 0 for undefined identifiers)
        # Only check this if the function expression was an Identifier
        # We need to distinguish between:
        # 1. Identifier doesn't exist (undefined function) -> "Function 'x' is not defined"
        # 2. Identifier exists but is not callable (e.g., variable with value 0) -> "Not a function: x"
        if func == 0 and isinstance(node.func, Identifier):
            name = node.func.name
            # Check if this identifier exists as a variable
            variable_exists = False
            if self.in_function:
                if name in self.globals_declared:
                    variable_exists = name in self.global_env.vars
                elif name in self.current_env.vars:
                    variable_exists = True
                elif self.current_closure_env != self.global_env:
                    variable_exists = self.current_env.has(name)
            else:
                variable_exists = (name in self.current_env.vars or name in self.global_env.vars)
            
            # Also check if it exists as a function
            function_exists = name in self.functions
            
            # If neither variable nor function exists, it's an undefined function
            if not variable_exists and not function_exists:
                self.error(f"Function '{name}' is not defined")
        
        # Check for old-style split() and match() calls BEFORE checking for undefined arguments
        # This ensures the old-style error message takes precedence
        if callable(func) and not isinstance(func, UserFunction):
            if func == self.builtin_match:
                if len(node.args) == 3:
                    self.error("match() in fawk takes 2 arguments (pattern, text), not 3.\n"
                              "Old AWK style: match(string, regexp, array)\n"
                              "fawk style: result = match(pattern, text)\n"
                              "The result is an array with [0]=full match, [1]=first group, etc.")
            elif func == self.builtin_split:
                if len(node.args) == 3:
                    self.error("split() in fawk takes 2 arguments (separator, text), not 3.\n"
                              "Old AWK style: split(string, array, separator)\n"
                              "fawk style: result = split(separator, text)\n"
                              "The result is an array with the split parts.")
        
        # Special handling for match() and split() - if first argument is a Regex node,
        # extract the pattern string instead of evaluating it to a boolean
        args = []
        for i, arg_node in enumerate(node.args):
            # Check if argument is an undefined identifier
            if isinstance(arg_node, Identifier):
                if not self.identifier_exists(arg_node.name):
                    self.error(f"Undefined variable '{arg_node.name}' used as function argument")
            
            # Check if this is match() and first arg is a Regex
            if (func == self.builtin_match and i == 0 and isinstance(arg_node, Regex)):
                # Extract pattern string from Regex node
                args.append(arg_node.pattern)
            else:
                args.append(self.eval(arg_node))
        
        return self.call_function(func, args, node.func)
    
    def call_function(self, func, args, func_node=None):
        if callable(func) and not isinstance(func, UserFunction):
            # Built-in function
            # Check for common AWK-style function calls that need better error messages
            if func == self.builtin_match:
                if len(args) == 3:
                    self.error("match() in fawk takes 2 arguments (pattern, text), not 3.\n"
                              "Old AWK style: match(string, regexp, array)\n"
                              "fawk style: result = match(pattern, text)\n"
                              "The result is an array with [0]=full match, [1]=first group, etc.")
                elif len(args) != 2:
                    self.error(f"match() expects 2 arguments (pattern, text), got {len(args)}")
            elif func == self.builtin_split:
                if len(args) == 3:
                    self.error("split() in fawk takes 2 arguments (separator, text), not 3.\n"
                              "Old AWK style: split(string, array, separator)\n"
                              "fawk style: result = split(separator, text)\n"
                              "The result is an array with the split parts.")
                elif len(args) != 2:
                    self.error(f"split() expects 2 arguments (separator, text), got {len(args)}")
            
            try:
                return func(*args)
            except TypeError as e:
                # Check if it's an argument count error for match or split
                if "positional arguments" in str(e) and (func == self.builtin_match or func == self.builtin_split):
                    # This shouldn't happen now due to checks above, but just in case
                    if func == self.builtin_match:
                        self.error("match() in fawk takes 2 arguments (pattern, text), not 3.\n"
                                  "Old AWK style: match(string, regexp, array)\n"
                                  "fawk style: result = match(pattern, text)")
                    elif func == self.builtin_split:
                        self.error("split() in fawk takes 2 arguments (separator, text), not 3.\n"
                                  "Old AWK style: split(string, array, separator)\n"
                                  "fawk style: result = split(separator, text)")
                raise
        elif isinstance(func, UserFunction):
            # User-defined function
            if len(args) != len(func.params):
                # Extract function name if available
                if func_node and isinstance(func_node, Identifier):
                    func_name = f"'{func_node.name}'"
                    self.error(f"Function {func_name} expects {len(func.params)} arguments, got {len(args)}")
                else:
                    self.error(f"Function expects {len(func.params)} arguments, got {len(args)}")
            
            # Get function name for tail recursion detection
            func_name = None
            if func_node and isinstance(func_node, Identifier):
                func_name = func_node.name
            
            # Save current state
            saved_env = self.current_env
            saved_in_function = self.in_function
            saved_closure_env = self.current_closure_env
            saved_current_function = self.current_function
            saved_current_function_name = self.current_function_name
            
            # Create initial environment for function
            func_env = Environment(func.closure_env)
            for param, arg in zip(func.params, args):
                # Use copy-on-write for arrays when passing as arguments (pass by value)
                if isinstance(arg, FawkArray):
                    func_env.set_local(param, arg.cow_copy())
                else:
                    func_env.set_local(param, arg)
            
            # Set up function execution context
            self.current_env = func_env
            self.in_function = True
            self.current_closure_env = func.closure_env
            self.current_function = func
            self.current_function_name = func_name
            
            # Execute function body with tail recursion support
            # Use a loop to handle tail calls without growing the stack
            result = None
            try:
                while True:
                    try:
                        result = self.eval(func.body)
                        # For lambdas with single expression, implicitly return the value
                        if func.is_lambda and isinstance(func.body, Block) and len(func.body.statements) == 1:
                            stmt = func.body.statements[0]
                            if isinstance(stmt, ExprStmt):
                                # Implicit return for single-expression lambdas
                                result = self.eval(stmt.expr)
                        break  # Normal return, exit loop
                    except ReturnException as e:
                        result = e.value
                        break  # Return statement, exit loop
                    except TailCallException as e:
                        # Tail call detected - update parameters and continue loop
                        tail_call_node = e.func_call_node
                        # Evaluate new arguments
                        new_args = []
                        for arg_node in tail_call_node.args:
                            # Check if argument is an undefined identifier
                            if isinstance(arg_node, Identifier):
                                if not self.identifier_exists(arg_node.name):
                                    self.error(f"Undefined variable '{arg_node.name}' used as function argument")
                            new_args.append(self.eval(arg_node))
                        
                        # Validate argument count
                        if len(new_args) != len(func.params):
                            if func_name:
                                self.error(f"Function '{func_name}' expects {len(func.params)} arguments, got {len(new_args)}")
                            else:
                                self.error(f"Function expects {len(func.params)} arguments, got {len(new_args)}")
                        
                        # Update function environment with new arguments
                        for param, arg in zip(func.params, new_args):
                            # Use copy-on-write for arrays when passing as arguments (pass by value)
                            if isinstance(arg, FawkArray):
                                func_env.set_local(param, arg.cow_copy())
                            else:
                                func_env.set_local(param, arg)
                        
                        # Continue loop to execute function body again with new parameters
                        continue
            finally:
                # Restore previous state
                self.current_env = saved_env
                self.in_function = saved_in_function
                self.current_closure_env = saved_closure_env
                self.current_function = saved_current_function
                self.current_function_name = saved_current_function_name
            
            return result
        else:
            # Provide better error message if we know the function name
            if func_node and isinstance(func_node, Identifier):
                self.error(f"Not a function: {func_node.name}")
            else:
                self.error(f"Not a function: {func}")
    
    def eval_Lambda(self, node: Lambda) -> UserFunction:
        return UserFunction(node.params, node.body, self.current_env, is_lambda=True)
    
    def eval_Pipeline(self, node: Pipeline) -> Any:
        left_value = self.eval(node.left)
        
        # The right side should be a function call
        # We append the left value as the last argument
        if isinstance(node.right, FunctionCall):
            func = self.eval(node.right.func)
            # Special handling for match() and split() - if first argument is a Regex node,
            # extract the pattern string instead of evaluating it to a boolean
            args = []
            for i, arg_node in enumerate(node.right.args):
                # Check if this is match() and first arg is a Regex
                if (func == self.builtin_match and i == 0 and isinstance(arg_node, Regex)):
                    # Extract pattern string from Regex node
                    args.append(arg_node.pattern)
                else:
                    args.append(self.eval(arg_node))
            args.append(left_value)  # Add piped value as last argument
            return self.call_function(func, args)
        else:
            self.error("Pipeline right side must be a function call")
    
    def identifier_exists(self, name: str) -> bool:
        """Check if an identifier exists as a variable or function (without evaluating it)"""
        # Check for built-in variables
        if name in self._builtin_vars:
            return True
        
        # Check for variables first (variables can shadow functions)
        # FAWK scoping: inside functions, only access local vars or explicitly global vars
        if self.in_function:
            if name in self.globals_declared:
                # Explicitly global variable
                if name in self.global_env.vars:
                    return True
            elif name in self.current_env.vars:
                # Local variable
                return True
            else:
                # Search up the closure chain for captured variables
                # But if this is a regular function (closure_env is global_env),
                # only look for explicitly declared globals, not all globals
                if self.current_closure_env == self.global_env:
                    # Regular function: only look for explicitly declared globals
                    # Don't search global_env for non-declared variables (isolation)
                    pass
                else:
                    # Lambda: search full closure chain to capture outer variables
                    if self.current_env.has(name):
                        return True
        else:
            # Outside function: check if variable exists
            # First check current_env.vars (for for-in loop variables)
            # Then check global_env.vars (for regular assignments)
            if name in self.current_env.vars:
                return True
            elif name in self.global_env.vars:
                return True
        
        # Check for functions (only if no variable was found)
        if name in self.functions:
            return True
        
        # Identifier doesn't exist
        return False
    
    def eval_Identifier(self, node: Identifier) -> Any:
        name = node.name
        
        # Check for built-in variables using cached lookup (optimization)
        # Built-in variables cannot be shadowed
        if name in self._builtin_vars:
            return self._builtin_vars[name]()
        
        # Check for variables first (variables can shadow functions)
        # FAWK scoping: inside functions, only access local vars or explicitly global vars
        variable_value = None
        if self.in_function:
            if name in self.globals_declared:
                # Explicitly global variable
                if name in self.global_env.vars:
                    variable_value = self.global_env.vars[name]
            elif name in self.current_env.vars:
                # Local variable - fast path, no need to call get()
                variable_value = self.current_env.vars[name]
            else:
                # Search up the closure chain for captured variables
                # But if this is a regular function (closure_env is global_env),
                # only look for explicitly declared globals, not all globals
                if self.current_closure_env == self.global_env:
                    # Regular function: only look for explicitly declared globals
                    # Don't search global_env for non-declared variables (isolation)
                    pass
                else:
                    # Lambda: search full closure chain to capture outer variables
                    if self.current_env.has(name):
                        variable_value = self.current_env.get(name)
        else:
            # Outside function: check if variable exists
            # First check current_env.vars (for for-in loop variables)
            # Then check global_env.vars (for regular assignments)
            if name in self.current_env.vars:
                variable_value = self.current_env.vars[name]
            elif name in self.global_env.vars:
                variable_value = self.global_env.vars[name]
        
        # If variable exists, return it (this shadows any function with the same name)
        if variable_value is not None:
            return variable_value
        
        # Check for functions (only if no variable was found)
        if name in self.functions:
            return self.functions[name]
        
        # No variable or function found - return default (0 for undefined variables)
        if self.in_function:
            if self.current_closure_env == self.global_env:
                return 0
            else:
                return self.current_env.get(name)
        else:
            return self.current_env.get(name)
    
    def eval_Number(self, node: Number):
        if self.use_high_precision():
            getcontext().prec = self.PREC
            return self.to_decimal(node.value)
        return node.value
    
    def eval_String(self, node: String) -> str:
        return node.value
    
    def eval_Regex(self, node: Regex) -> bool:
        """Evaluate regex pattern against current line ($0)"""
        line = self.current_line
        flags = 0
        if 'i' in node.flags:
            flags |= re.IGNORECASE
        # Cache compiled regex patterns
        cache_key = (node.pattern, flags)
        if cache_key not in self._regex_cache:
            try:
                self._regex_cache[cache_key] = re.compile(node.pattern, flags)
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")
        compiled_pattern = self._regex_cache[cache_key]
        return bool(compiled_pattern.search(line))
    
    def eval_FieldAccess(self, node: FieldAccess) -> Any:
        index = self.eval(node.index)
        index = int(index)
        
        if index == 0:
            return self.current_line
        elif 1 <= index <= len(self.fields):
            return self.fields[index - 1]
        else:
            return ""
    
    def eval_InOp(self, node) -> bool:
        """Evaluate 'in' operator for array membership"""
        from .fawk_ast import InOp
        
        array = self.eval(node.array)
        if not isinstance(array, FawkArray):
            return False
        
        # Compute the index from the indices
        if len(node.indices) == 1:
            index = self.eval(node.indices[0])
        else:
            # Multiple indices: concatenate with SUBSEP
            index_values = [self.value_to_string_convert(self.eval(idx)) for idx in node.indices]
            index = self.SUBSEP.join(index_values)
        
        # Convert index to the right type for lookup
        if isinstance(index, (int, float)):
            index = int(index)
        else:
            index = str(index)
        
        return index in array.data
    
    def eval_CommaExpr(self, node) -> str:
        """Evaluate comma expression - concatenates values with SUBSEP"""
        from .fawk_ast import CommaExpr
        
        # Evaluate all expressions and concatenate with SUBSEP
        values = [self.value_to_string_convert(self.eval(expr)) for expr in node.exprs]
        return self.SUBSEP.join(values)
    
    def eval_PipedGetline(self, node) -> int:
        """Evaluate piped getline: cmd | getline var"""
        from .fawk_ast import PipedGetline
        import subprocess
        
        # Get the command string
        cmd = self.value_to_string(self.eval(node.command))
        
        # Open pipe if not already open
        if cmd not in self.open_pipes:
            try:
                pipe = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.open_pipes[cmd] = pipe
            except Exception as e:
                # Error opening command
                return -1
        
        pipe = self.open_pipes[cmd]
        
        # Read one line from the pipe
        try:
            line = pipe.stdout.readline()
            if line:
                # Remove trailing newline if present
                if line.endswith('\n'):
                    line = line[:-1]
                
                # Store in target variable or $0
                if node.target:
                    # Store in variable
                    self.current_env.set_local(node.target, line)
                else:
                    # Store in $0 and update fields
                    self.current_line = line
                    self.fields = self.split_fields(line)
                    self.NF = len(self.fields)
                
                return 1  # Success
            else:
                # EOF
                return 0
        except Exception as e:
            # Error reading
            return -1
    
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
                        
                        # Skip trailing empty records (GAWK compatibility)
                        # Only skip if this is the last record and it's empty
                        is_last = (i + 1 >= len(parts))
                        if is_last and not record:
                            # Trailing empty record - skip it (GAWK behavior)
                            continue
                        
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
        
        # Special case: empty record has no fields (AWK compatibility)
        if record == "":
            return []
        
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
    
    def run(self, program: Program, input_files: list = None):
        """
        Run the FAWK program.
        
        Args:
            program: The parsed Program AST
            input_files: List of tuples (filename, content) or None for no input
        """
        # Register user-defined functions (protect built-ins)
        for func_def in program.functions:
            if func_def.name in self.builtin_functions:
                raise RuntimeError(f"Cannot redefine built-in function '{func_def.name}'")
            self.functions[func_def.name] = UserFunction(
                func_def.params, func_def.body, self.global_env
            )
        
        # Execute all BEGIN blocks in order with their own local environments
        for begin_block in program.begin_blocks:
            begin_env = Environment(self.global_env)
            saved_env = self.current_env
            self.current_env = begin_env
            try:
                self.eval(begin_block)
            except ExitException as e:
                # Exit during BEGIN
                import sys
                sys.exit(e.code)
            finally:
                self.current_env = saved_env
        
        # Process input files
        exit_code = None
        if input_files:
            try:
                for filename, file_content in input_files:
                    # Set FILENAME and reset FNR for this file
                    self.FILENAME = filename
                    self.FNR = 0
                    
                    # Track if we should skip record processing (but still run ENDFILE)
                    skip_file = False
                    
                    # Execute all BEGINFILE blocks in order
                    for beginfile_block in program.beginfile_blocks:
                        beginfile_env = Environment(self.global_env)
                        saved_env = self.current_env
                        self.current_env = beginfile_env
                        try:
                            self.eval(beginfile_block)
                        except NextFileException:
                            # Skip this file's records but still run ENDFILE
                            skip_file = True
                        except ExitException as e:
                            # Exit during BEGINFILE
                            exit_code = e.code
                            self.current_env = saved_env
                            break
                        finally:
                            if self.current_env == beginfile_env:
                                self.current_env = saved_env
                        if exit_code is not None:
                            break
                    
                    # Process this file's records (unless skipped by nextfile in BEGINFILE)
                    if not skip_file:
                        try:
                            records = self.split_into_records(file_content)
                            
                            for record, terminator in records:
                                self.NR += 1
                                self.FNR += 1
                                self.RT = terminator
                                
                                # Split record into fields
                                self.current_line = record  # Store original record for $0
                                self.fields = self.split_fields(record)
                                self.NF = len(self.fields)
                                
                                # Execute pattern-action blocks
                                try:
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
                                            except NextException:
                                                # Skip to next record
                                                break
                                            finally:
                                                self.current_env = saved_env
                                except NextFileException:
                                    # Skip to next file
                                    break
                        except NextFileException:
                            # Skip remaining records in this file
                            pass
                        except ExitException as e:
                            # Exit during pattern-action - save exit code and jump to ENDFILE
                            exit_code = e.code
                    
                    # Execute all ENDFILE blocks in order
                    for endfile_block in program.endfile_blocks:
                        endfile_env = Environment(self.global_env)
                        saved_env = self.current_env
                        self.current_env = endfile_env
                        try:
                            self.eval(endfile_block)
                        except ExitException as e:
                            # Exit during ENDFILE
                            exit_code = e.code
                        finally:
                            self.current_env = saved_env
                        if exit_code is not None:
                            break
                    
                    # If exit was called, stop processing files
                    if exit_code is not None:
                        break
                        
            except ExitException as e:
                # Exit during file processing
                exit_code = e.code
        else:
            # No input, just execute pattern-less actions
            try:
                for pattern_action in program.patterns:
                    if pattern_action.pattern is None:
                        action_env = Environment(self.global_env)
                        saved_env = self.current_env
                        self.current_env = action_env
                        try:
                            self.eval(pattern_action.action)
                        except NextException:
                            # Skip to next record (no effect when no input)
                            pass
                        finally:
                            self.current_env = saved_env
            except ExitException as e:
                # Exit during pattern-action - save exit code and jump to END
                exit_code = e.code
        
        # Execute all END blocks in order with their own local environments
        for end_block in program.end_blocks:
            end_env = Environment(self.global_env)
            saved_env = self.current_env
            self.current_env = end_env
            try:
                self.eval(end_block)
            except ExitException as e:
                # Exit during END - update exit code
                exit_code = e.code
            finally:
                self.current_env = saved_env
        
        # Close all redirect files
        for file_handle in self.redirect_files.values():
            try:
                file_handle.close()
            except:
                pass
        self.redirect_files.clear()
        
        # Close all open pipes
        for pipe in self.open_pipes.values():
            try:
                pipe.stdout.close()
                pipe.wait()
            except:
                pass
        self.open_pipes.clear()
        
        # Exit with saved code if exit was called
        if exit_code is not None:
            import sys
            sys.exit(exit_code)
