mod ast;
mod lexer;
mod parser;
mod value;
mod interpreter;

use std::env;
use std::fs;
use std::io::{self, BufRead};

use lexer::Lexer;
use parser::Parser;
use interpreter::Interpreter;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: fawk <script.fawk> [input_file]");
        std::process::exit(1);
    }
    
    let script_path = &args[1];
    
    // Read the FAWK script
    let script = fs::read_to_string(script_path)
        .unwrap_or_else(|e| {
            eprintln!("Error reading script file '{}': {}", script_path, e);
            std::process::exit(1);
        });
    
    // Tokenize
    let mut lexer = Lexer::new(&script);
    let tokens = lexer.tokenize();
    
    // Parse
    let mut parser = Parser::new(tokens);
    let program = parser.parse();
    
    // Read input
    let input_lines: Vec<String> = if args.len() > 2 {
        // Read from file
        let input_path = &args[2];
        fs::read_to_string(input_path)
            .unwrap_or_else(|e| {
                eprintln!("Error reading input file '{}': {}", input_path, e);
                std::process::exit(1);
            })
            .lines()
            .map(|s| s.to_string())
            .collect()
    } else {
        // Read from stdin
        let stdin = io::stdin();
        stdin.lock().lines()
            .filter_map(|line| line.ok())
            .collect()
    };
    
    // Interpret
    let mut interpreter = Interpreter::new();
    interpreter.run(program, input_lines);
}
