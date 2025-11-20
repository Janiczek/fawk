use std::collections::HashMap;
use std::rc::Rc;
use crate::ast::*;
use crate::value::*;

pub struct Interpreter {
    globals: HashMap<String, Value>,
    scopes: Vec<HashMap<String, Value>>,
    current_fields: Vec<String>,
    nr: usize,
    break_flag: bool,
    continue_flag: bool,
    return_value: Option<Value>,
}

impl Interpreter {
    pub fn new() -> Self {
        let mut globals = HashMap::new();
        
        // Register built-in functions
        globals.insert("length".to_string(), Value::Builtin(builtin_length));
        // map, filter, reduce are handled as special builtins that need interpreter context
        
        Interpreter {
            globals,
            scopes: vec![HashMap::new()],
            current_fields: Vec::new(),
            nr: 0,
            break_flag: false,
            continue_flag: false,
            return_value: None,
        }
    }
    
    fn push_scope(&mut self) {
        self.scopes.push(HashMap::new());
    }
    
    fn pop_scope(&mut self) {
        self.scopes.pop();
    }
    
    fn get_var(&self, name: &str) -> Value {
        // Check local scopes from innermost to outermost
        for scope in self.scopes.iter().rev() {
            if let Some(val) = scope.get(name) {
                return val.clone();
            }
        }
        
        // Check globals
        if let Some(val) = self.globals.get(name) {
            return val.clone();
        }
        
        // Special variables
        match name {
            "NR" => Value::Number(self.nr as f64),
            _ => Value::Nil,
        }
    }
    
    fn set_var(&mut self, name: String, value: Value) {
        // Check if it's a global
        if self.globals.contains_key(&name) {
            self.globals.insert(name, value);
            return;
        }
        
        // Set in the current (innermost) scope
        if let Some(scope) = self.scopes.last_mut() {
            scope.insert(name, value);
        }
    }
    
    fn declare_global(&mut self, name: String) {
        if !self.globals.contains_key(&name) {
            self.globals.insert(name, Value::Nil);
        }
    }
    
    pub fn run(&mut self, program: Program, input_lines: Vec<String>) {
        // First pass: register all top-level functions
        for item in &program.items {
            if let Item::Function(func) = item {
                let func_val = Value::Function(Rc::new(FunctionValue::User {
                    params: func.params.clone(),
                    body: func.body.clone(),
                    closure: HashMap::new(),
                }));
                self.globals.insert(func.name.clone(), func_val);
            }
        }
        
        // Execute BEGIN blocks
        for item in &program.items {
            if let Item::Rule(rule) = item {
                if let Some(Pattern::Begin) = rule.pattern {
                    self.execute_block(&rule.action);
                }
            }
        }
        
        // Execute pattern-action rules for each input line
        for line in input_lines {
            self.nr += 1;
            self.current_fields = split_line(&line);
            
            for item in &program.items {
                if let Item::Rule(rule) = item {
                    match &rule.pattern {
                        Some(Pattern::Begin) | Some(Pattern::End) => continue,
                        Some(Pattern::Expression(expr)) => {
                            let result = self.eval_expr(expr);
                            if result.to_bool() {
                                self.execute_block(&rule.action);
                            }
                        }
                        None => {
                            self.execute_block(&rule.action);
                        }
                    }
                }
            }
        }
        
        // Execute END blocks
        for item in &program.items {
            if let Item::Rule(rule) = item {
                if let Some(Pattern::End) = rule.pattern {
                    self.execute_block(&rule.action);
                }
            }
        }
    }
    
    fn execute_block(&mut self, stmts: &[Stmt]) {
        for stmt in stmts {
            self.execute_stmt(stmt);
            
            if self.break_flag || self.continue_flag || self.return_value.is_some() {
                break;
            }
        }
    }
    
    fn execute_stmt(&mut self, stmt: &Stmt) {
        match stmt {
            Stmt::Print { args } => {
                let values: Vec<Value> = args.iter().map(|e| self.eval_expr(e)).collect();
                let output: Vec<String> = values.iter().map(|v| format!("{}", v)).collect();
                println!("{}", output.join(" "));
            }
            Stmt::Expr(expr) => {
                self.eval_expr(expr);
            }
            Stmt::VarDecl { name, value } => {
                let val = if let Some(v) = value {
                    self.eval_expr(v)
                } else {
                    Value::Nil
                };
                self.set_var(name.clone(), val);
            }
            Stmt::GlobalDecl { names } => {
                for name in names {
                    self.declare_global(name.clone());
                }
            }
            Stmt::Assign { target, value } => {
                let val = self.eval_expr(value);
                self.assign_target(target, val);
            }
            Stmt::Return(expr) => {
                self.return_value = Some(if let Some(e) = expr {
                    self.eval_expr(e)
                } else {
                    Value::Nil
                });
            }
            Stmt::If { condition, then_branch, else_branch } => {
                let cond_val = self.eval_expr(condition);
                if cond_val.to_bool() {
                    self.execute_block(then_branch);
                } else if let Some(else_stmts) = else_branch {
                    self.execute_block(else_stmts);
                }
            }
            Stmt::While { condition, body } => {
                while self.eval_expr(condition).to_bool() {
                    self.execute_block(body);
                    
                    if self.break_flag {
                        self.break_flag = false;
                        break;
                    }
                    
                    if self.continue_flag {
                        self.continue_flag = false;
                        continue;
                    }
                    
                    if self.return_value.is_some() {
                        break;
                    }
                }
            }
            Stmt::For { var, iterable, body } => {
                let iter_val = self.eval_expr(iterable);
                
                if let Value::Array(arr) = iter_val {
                    let keys = arr.keys();
                    
                    for key in keys {
                        self.push_scope();
                        self.set_var(var.clone(), key);
                        self.execute_block(body);
                        self.pop_scope();
                        
                        if self.break_flag {
                            self.break_flag = false;
                            break;
                        }
                        
                        if self.continue_flag {
                            self.continue_flag = false;
                            continue;
                        }
                        
                        if self.return_value.is_some() {
                            break;
                        }
                    }
                }
            }
            Stmt::Break => {
                self.break_flag = true;
            }
            Stmt::Continue => {
                self.continue_flag = true;
            }
        }
    }
    
    fn assign_target(&mut self, target: &Expr, value: Value) {
        match target {
            Expr::Ident(name) => {
                self.set_var(name.clone(), value);
            }
            Expr::Index { array, index } => {
                let arr_val = self.eval_expr(array);
                let idx_val = self.eval_expr(index);
                
                if let Value::Array(arr) = arr_val {
                    // Need mutable access, so we clone and update
                    let mut new_arr = (*arr).clone();
                    new_arr.set(idx_val, value);
                    
                    // Now update the original variable
                    if let Expr::Ident(name) = array.as_ref() {
                        self.set_var(name.clone(), Value::Array(Rc::new(new_arr)));
                    }
                }
            }
            _ => {}
        }
    }
    
    pub fn eval_expr(&mut self, expr: &Expr) -> Value {
        match expr {
            Expr::Number(n) => Value::Number(*n),
            Expr::String(s) => Value::String(s.clone()),
            Expr::Ident(name) => self.get_var(name),
            Expr::Array(elements) => {
                let mut arr = ArrayValue::new();
                let mut auto_index = 0i64;
                
                for elem in elements {
                    match elem {
                        ArrayElement::Value(v) => {
                            let val = self.eval_expr(v);
                            arr.indexed.insert(auto_index, val);
                            auto_index += 1;
                        }
                        ArrayElement::KeyValue { key, value } => {
                            let key_val = self.eval_expr(key);
                            let val = self.eval_expr(value);
                            arr.set(key_val, val);
                        }
                    }
                }
                
                Value::Array(Rc::new(arr))
            }
            Expr::Index { array, index } => {
                let arr_val = self.eval_expr(array);
                let idx_val = self.eval_expr(index);
                
                match arr_val {
                    Value::Array(arr) => arr.get(&idx_val),
                    _ => Value::Nil,
                }
            }
            Expr::Call { func, args } => {
                // Check if it's a special built-in that needs interpreter context
                if let Expr::Ident(name) = func.as_ref() {
                    match name.as_str() {
                        "map" => return self.builtin_map(args),
                        "filter" => return self.builtin_filter(args),
                        "reduce" => return self.builtin_reduce(args),
                        _ => {}
                    }
                }
                
                let func_val = self.eval_expr(func);
                let arg_vals: Vec<Value> = args.iter().map(|a| self.eval_expr(a)).collect();
                
                self.call_function(func_val, arg_vals)
            }
            Expr::Lambda { params, body } => {
                // Capture current scope for closure
                let mut closure = HashMap::new();
                for scope in &self.scopes {
                    closure.extend(scope.clone());
                }
                
                Value::Function(Rc::new(FunctionValue::User {
                    params: params.clone(),
                    body: body.clone(),
                    closure,
                }))
            }
            Expr::Binary { left, op, right } => {
                let left_val = self.eval_expr(left);
                let right_val = self.eval_expr(right);
                
                match op {
                    BinOp::Add => {
                        Value::Number(left_val.to_number() + right_val.to_number())
                    }
                    BinOp::Sub => {
                        Value::Number(left_val.to_number() - right_val.to_number())
                    }
                    BinOp::Mul => {
                        Value::Number(left_val.to_number() * right_val.to_number())
                    }
                    BinOp::Div => {
                        Value::Number(left_val.to_number() / right_val.to_number())
                    }
                    BinOp::Mod => {
                        Value::Number(left_val.to_number() % right_val.to_number())
                    }
                    BinOp::Equal => {
                        Value::Number(if values_equal(&left_val, &right_val) { 1.0 } else { 0.0 })
                    }
                    BinOp::NotEqual => {
                        Value::Number(if !values_equal(&left_val, &right_val) { 1.0 } else { 0.0 })
                    }
                    BinOp::Less => {
                        Value::Number(if left_val.to_number() < right_val.to_number() { 1.0 } else { 0.0 })
                    }
                    BinOp::LessEqual => {
                        Value::Number(if left_val.to_number() <= right_val.to_number() { 1.0 } else { 0.0 })
                    }
                    BinOp::Greater => {
                        Value::Number(if left_val.to_number() > right_val.to_number() { 1.0 } else { 0.0 })
                    }
                    BinOp::GreaterEqual => {
                        Value::Number(if left_val.to_number() >= right_val.to_number() { 1.0 } else { 0.0 })
                    }
                    BinOp::And => {
                        Value::Number(if left_val.to_bool() && right_val.to_bool() { 1.0 } else { 0.0 })
                    }
                    BinOp::Or => {
                        Value::Number(if left_val.to_bool() || right_val.to_bool() { 1.0 } else { 0.0 })
                    }
                }
            }
            Expr::Unary { op, expr } => {
                let val = self.eval_expr(expr);
                
                match op {
                    UnOp::Neg => Value::Number(-val.to_number()),
                    UnOp::Not => Value::Number(if !val.to_bool() { 1.0 } else { 0.0 }),
                }
            }
            Expr::Field(expr) => {
                let idx_val = self.eval_expr(expr);
                let idx = idx_val.to_number() as usize;
                
                if idx == 0 {
                    // $0 is the whole line
                    Value::String(self.current_fields.join(" "))
                } else if idx <= self.current_fields.len() {
                    Value::String(self.current_fields[idx - 1].clone())
                } else {
                    Value::String(String::new())
                }
            }
            Expr::Pipeline { left, right } => {
                let left_val = self.eval_expr(left);
                
                // right should be a function call
                // We need to append left_val as the last argument
                match right.as_ref() {
                    Expr::Call { func, args } => {
                        // Check if it's a special built-in that needs interpreter context
                        if let Expr::Ident(name) = func.as_ref() {
                            match name.as_str() {
                                "map" => {
                                    // Create temp expr for the left value
                                    let mut pipeline_args = args.clone();
                                    pipeline_args.push(Expr::Ident("__pipeline_tmp__".to_string()));
                                    
                                    // Set a temporary variable for the pipeline value
                                    self.set_var("__pipeline_tmp__".to_string(), left_val.clone());
                                    
                                    let result = self.builtin_map(&pipeline_args);
                                    
                                    // Clean up the temporary variable
                                    self.set_var("__pipeline_tmp__".to_string(), Value::Nil);
                                    
                                    return result;
                                }
                                "filter" => {
                                    // Create temp expr for the left value
                                    let mut pipeline_args = args.clone();
                                    pipeline_args.push(Expr::Ident("__pipeline_tmp__".to_string()));
                                    
                                    // Set a temporary variable for the pipeline value
                                    self.set_var("__pipeline_tmp__".to_string(), left_val.clone());
                                    
                                    let result = self.builtin_filter(&pipeline_args);
                                    
                                    // Clean up the temporary variable
                                    self.set_var("__pipeline_tmp__".to_string(), Value::Nil);
                                    
                                    return result;
                                }
                                "reduce" => {
                                    // Create temp expr for the left value
                                    let mut pipeline_args = args.clone();
                                    pipeline_args.push(Expr::Ident("__pipeline_tmp__".to_string()));
                                    
                                    // Set a temporary variable for the pipeline value
                                    self.set_var("__pipeline_tmp__".to_string(), left_val.clone());
                                    
                                    let result = self.builtin_reduce(&pipeline_args);
                                    
                                    // Clean up the temporary variable
                                    self.set_var("__pipeline_tmp__".to_string(), Value::Nil);
                                    
                                    return result;
                                }
                                _ => {}
                            }
                        }
                        
                        let func_val = self.eval_expr(func);
                        let mut arg_vals: Vec<Value> = args.iter().map(|a| self.eval_expr(a)).collect();
                        arg_vals.push(left_val);
                        
                        self.call_function(func_val, arg_vals)
                    }
                    _ => {
                        // Treat as function with single argument
                        let func_val = self.eval_expr(right);
                        self.call_function(func_val, vec![left_val])
                    }
                }
            }
        }
    }
    
    fn builtin_map(&mut self, args: &[Expr]) -> Value {
        if args.len() < 2 {
            return Value::Nil;
        }
        
        let func_val = self.eval_expr(&args[0]);
        let arr_val = self.eval_expr(&args[1]);
        
        if let Value::Array(input_arr) = arr_val {
            let mut result = ArrayValue::new();
            
            // Map over indexed elements
            for (key, val) in &input_arr.indexed {
                let mapped = self.call_function(func_val.clone(), vec![val.clone()]);
                result.indexed.insert(*key, mapped);
            }
            
            // Map over associative elements
            for (key, val) in &input_arr.assoc {
                let mapped = self.call_function(func_val.clone(), vec![val.clone()]);
                result.assoc.insert(key.clone(), mapped);
            }
            
            Value::Array(Rc::new(result))
        } else {
            Value::Nil
        }
    }
    
    fn builtin_filter(&mut self, args: &[Expr]) -> Value {
        if args.len() < 2 {
            return Value::Nil;
        }
        
        let pred_val = self.eval_expr(&args[0]);
        let arr_val = self.eval_expr(&args[1]);
        
        if let Value::Array(input_arr) = arr_val {
            let mut result = ArrayValue::new();
            
            // Filter indexed elements
            for (key, val) in &input_arr.indexed {
                let test = self.call_function(pred_val.clone(), vec![val.clone()]);
                if test.to_bool() {
                    result.indexed.insert(*key, val.clone());
                }
            }
            
            // Filter associative elements
            for (key, val) in &input_arr.assoc {
                let test = self.call_function(pred_val.clone(), vec![val.clone()]);
                if test.to_bool() {
                    result.assoc.insert(key.clone(), val.clone());
                }
            }
            
            Value::Array(Rc::new(result))
        } else {
            Value::Nil
        }
    }
    
    fn builtin_reduce(&mut self, args: &[Expr]) -> Value {
        if args.len() < 3 {
            return Value::Nil;
        }
        
        let func_val = self.eval_expr(&args[0]);
        let init_val = self.eval_expr(&args[1]);
        let arr_val = self.eval_expr(&args[2]);
        
        if let Value::Array(input_arr) = arr_val {
            let mut acc = init_val;
            
            // Reduce over indexed elements (in order)
            let mut keys: Vec<_> = input_arr.indexed.keys().collect();
            keys.sort();
            
            for key in keys {
                if let Some(val) = input_arr.indexed.get(key) {
                    acc = self.call_function(func_val.clone(), vec![acc, val.clone()]);
                }
            }
            
            // Reduce over associative elements
            for val in input_arr.assoc.values() {
                acc = self.call_function(func_val.clone(), vec![acc.clone(), val.clone()]);
            }
            
            acc
        } else {
            init_val
        }
    }
    
    fn call_function(&mut self, func: Value, args: Vec<Value>) -> Value {
        match func {
            Value::Function(f) => {
                match &*f {
                    FunctionValue::User { params, body, closure } => {
                        // Create new scope with closure variables
                        self.push_scope();
                        
                        // Add closure variables
                        for (name, val) in closure {
                            self.set_var(name.clone(), val.clone());
                        }
                        
                        // Bind parameters
                        for (i, param) in params.iter().enumerate() {
                            let val = args.get(i).cloned().unwrap_or(Value::Nil);
                            self.set_var(param.clone(), val);
                        }
                        
                        // Execute body
                        // If the last statement is an expression, use its value as the return value
                        let mut result = Value::Nil;
                        for (i, stmt) in body.iter().enumerate() {
                            if i == body.len() - 1 {
                                // Last statement
                                if let Stmt::Expr(expr) = stmt {
                                    result = self.eval_expr(expr);
                                } else {
                                    self.execute_stmt(stmt);
                                    result = self.return_value.take().unwrap_or(Value::Nil);
                                }
                            } else {
                                self.execute_stmt(stmt);
                                if self.return_value.is_some() {
                                    result = self.return_value.take().unwrap();
                                    break;
                                }
                            }
                        }
                        
                        // Check if there was an explicit return
                        if self.return_value.is_some() {
                            result = self.return_value.take().unwrap();
                        }
                        
                        self.pop_scope();
                        
                        result
                    }
                    FunctionValue::Builtin { func } => {
                        func(&args)
                    }
                }
            }
            Value::Builtin(f) => {
                f(&args)
            }
            _ => Value::Nil,
        }
    }
}

fn split_line(line: &str) -> Vec<String> {
    line.split_whitespace().map(|s| s.to_string()).collect()
}

fn values_equal(a: &Value, b: &Value) -> bool {
    match (a, b) {
        (Value::Number(x), Value::Number(y)) => x == y,
        (Value::String(x), Value::String(y)) => x == y,
        _ => false,
    }
}

// Built-in functions
fn builtin_length(args: &[Value]) -> Value {
    if args.is_empty() {
        return Value::Number(0.0);
    }
    
    match &args[0] {
        Value::Array(arr) => Value::Number(arr.len() as f64),
        Value::String(s) => Value::Number(s.len() as f64),
        _ => Value::Number(0.0),
    }
}

