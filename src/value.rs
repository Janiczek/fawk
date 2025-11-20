use std::collections::HashMap;
use std::fmt;
use std::rc::Rc;
use crate::ast::Stmt;

#[derive(Clone)]
pub enum Value {
    Number(f64),
    String(String),
    Array(Rc<ArrayValue>),
    Function(Rc<FunctionValue>),
    Builtin(fn(&[Value]) -> Value),
    Nil,
}

#[derive(Debug, Clone)]
pub struct ArrayValue {
    pub indexed: HashMap<i64, Value>,
    pub assoc: HashMap<String, Value>,
}

impl ArrayValue {
    pub fn new() -> Self {
        ArrayValue {
            indexed: HashMap::new(),
            assoc: HashMap::new(),
        }
    }
    
    pub fn get(&self, key: &Value) -> Value {
        match key {
            Value::Number(n) => {
                let idx = *n as i64;
                self.indexed.get(&idx).cloned().unwrap_or(Value::Nil)
            }
            Value::String(s) => {
                self.assoc.get(s).cloned().unwrap_or(Value::Nil)
            }
            _ => Value::Nil,
        }
    }
    
    pub fn set(&mut self, key: Value, value: Value) {
        match key {
            Value::Number(n) => {
                let idx = n as i64;
                self.indexed.insert(idx, value);
            }
            Value::String(s) => {
                self.assoc.insert(s, value);
            }
            _ => {}
        }
    }
    
    pub fn keys(&self) -> Vec<Value> {
        let mut keys = Vec::new();
        
        for k in self.indexed.keys() {
            keys.push(Value::Number(*k as f64));
        }
        
        for k in self.assoc.keys() {
            keys.push(Value::String(k.clone()));
        }
        
        keys
    }
    
    pub fn len(&self) -> usize {
        self.indexed.len() + self.assoc.len()
    }
}

#[derive(Clone)]
pub enum FunctionValue {
    User {
        params: Vec<String>,
        body: Vec<Stmt>,
        closure: HashMap<String, Value>,
    },
    Builtin {
        func: fn(&[Value]) -> Value,
    },
}

impl fmt::Debug for Value {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Value::Number(n) => write!(f, "{}", n),
            Value::String(s) => write!(f, "\"{}\"", s),
            Value::Array(arr) => {
                write!(f, "[")?;
                let mut first = true;
                
                // Sort indexed keys for consistent output
                let mut indexed_keys: Vec<_> = arr.indexed.keys().collect();
                indexed_keys.sort();
                
                for key in indexed_keys {
                    if !first {
                        write!(f, ", ")?;
                    }
                    first = false;
                    write!(f, "{:?}", arr.indexed.get(key).unwrap())?;
                }
                
                for (key, val) in &arr.assoc {
                    if !first {
                        write!(f, ", ")?;
                    }
                    first = false;
                    write!(f, "\"{}\" => {:?}", key, val)?;
                }
                
                write!(f, "]")
            }
            Value::Function(_) => write!(f, "<function>"),
            Value::Builtin(_) => write!(f, "<builtin>"),
            Value::Nil => write!(f, "nil"),
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Value::Number(n) => {
                // Format numbers nicely
                if n.fract() == 0.0 {
                    write!(f, "{}", *n as i64)
                } else {
                    write!(f, "{}", n)
                }
            }
            Value::String(s) => write!(f, "{}", s),
            Value::Array(arr) => {
                write!(f, "[")?;
                let mut first = true;
                
                // Sort indexed keys for consistent output
                let mut indexed_keys: Vec<_> = arr.indexed.keys().collect();
                indexed_keys.sort();
                
                for key in indexed_keys {
                    if !first {
                        write!(f, ", ")?;
                    }
                    first = false;
                    write!(f, "{}", arr.indexed.get(key).unwrap())?;
                }
                
                for (_key, val) in &arr.assoc {
                    if !first {
                        write!(f, ", ")?;
                    }
                    first = false;
                    write!(f, "{}", val)?;
                }
                
                write!(f, "]")
            }
            Value::Function(_) => write!(f, "<function>"),
            Value::Builtin(_) => write!(f, "<builtin>"),
            Value::Nil => write!(f, ""),
        }
    }
}

impl Value {
    pub fn to_bool(&self) -> bool {
        match self {
            Value::Number(n) => *n != 0.0,
            Value::String(s) => !s.is_empty(),
            Value::Array(_) => true,
            Value::Function(_) => true,
            Value::Builtin(_) => true,
            Value::Nil => false,
        }
    }
    
    pub fn to_number(&self) -> f64 {
        match self {
            Value::Number(n) => *n,
            Value::String(s) => s.parse().unwrap_or(0.0),
            _ => 0.0,
        }
    }
    
    pub fn to_string(&self) -> String {
        match self {
            Value::String(s) => s.clone(),
            _ => format!("{}", self),
        }
    }
}
