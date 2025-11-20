#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>

// ============================================================================
// TOKEN DEFINITIONS
// ============================================================================

typedef enum {
    TOK_EOF, TOK_NUMBER, TOK_STRING, TOK_IDENT,
    TOK_LPAREN, TOK_RPAREN, TOK_LBRACE, TOK_RBRACE, TOK_LBRACKET, TOK_RBRACKET,
    TOK_COMMA, TOK_SEMICOLON,
    TOK_PLUS, TOK_MINUS, TOK_STAR, TOK_SLASH, TOK_PERCENT,
    TOK_EQ, TOK_NE, TOK_LT, TOK_LE, TOK_GT, TOK_GE,
    TOK_AND, TOK_OR, TOK_NOT,
    TOK_ASSIGN, TOK_ARROW, TOK_PIPE_GT,
    TOK_FUNCTION, TOK_RETURN, TOK_IF, TOK_ELSE, TOK_FOR, TOK_IN, TOK_WHILE,
    TOK_BEGIN, TOK_END, TOK_GLOBAL,
    TOK_NEWLINE
} TokenType;

typedef struct {
    TokenType type;
    char *text;
    double number;
    int line;
} Token;

typedef struct {
    char *source;
    int pos;
    int line;
    Token current;
} Lexer;

// ============================================================================
// VALUE SYSTEM
// ============================================================================

typedef enum {
    VAL_NUMBER, VAL_STRING, VAL_ARRAY, VAL_FUNCTION, VAL_BUILTIN, VAL_NULL
} ValueType;

struct Value;
struct Env;

typedef struct Value (*BuiltinFunc)(struct Env*, struct Value*, int);

typedef struct ASTNode ASTNode;

typedef struct {
    char **params;
    int param_count;
    ASTNode *body;
    struct Env *closure;
} FunctionValue;

typedef struct ArrayEntry {
    char *key;
    struct Value *value;
    struct ArrayEntry *next;
} ArrayEntry;

typedef struct {
    ArrayEntry **buckets;
    int size;
    int capacity;
} ArrayValue;

typedef struct Value {
    ValueType type;
    union {
        double number;
        char *string;
        ArrayValue *array;
        FunctionValue *function;
        BuiltinFunc builtin;
    } as;
} Value;

// ============================================================================
// ENVIRONMENT (SCOPE)
// ============================================================================

typedef struct EnvEntry {
    char *name;
    Value *value;
    struct EnvEntry *next;
} EnvEntry;

typedef struct Env {
    EnvEntry **buckets;
    int capacity;
    struct Env *parent;
} Env;

// ============================================================================
// AST NODES
// ============================================================================

typedef enum {
    AST_NUMBER, AST_STRING, AST_IDENT, AST_ARRAY_LITERAL,
    AST_BINARY, AST_UNARY, AST_CALL, AST_INDEX, AST_ASSIGN,
    AST_BLOCK, AST_IF, AST_FOR_IN, AST_WHILE, AST_RETURN,
    AST_FUNCTION_DEF, AST_LAMBDA, AST_GLOBAL_DECL,
    AST_PATTERN_ACTION, AST_PROGRAM
} ASTNodeType;

struct ASTNode {
    ASTNodeType type;
    union {
        double number;
        char *string;
        struct {
            char *name;
        } ident;
        struct {
            ASTNode **elements;
            int count;
        } array_literal;
        struct {
            char *op;
            ASTNode *left;
            ASTNode *right;
        } binary;
        struct {
            char *op;
            ASTNode *operand;
        } unary;
        struct {
            ASTNode *func;
            ASTNode **args;
            int arg_count;
        } call;
        struct {
            ASTNode *array;
            ASTNode *index;
        } index;
        struct {
            ASTNode *target;
            ASTNode *value;
        } assign;
        struct {
            ASTNode **stmts;
            int count;
        } block;
        struct {
            ASTNode *condition;
            ASTNode *then_branch;
            ASTNode *else_branch;
        } if_stmt;
        struct {
            char *var;
            ASTNode *array;
            ASTNode *body;
        } for_in;
        struct {
            ASTNode *condition;
            ASTNode *body;
        } while_stmt;
        struct {
            ASTNode *value;
        } return_stmt;
        struct {
            char *name;
            char **params;
            int param_count;
            ASTNode *body;
        } function_def;
        struct {
            char **params;
            int param_count;
            ASTNode *body;
        } lambda;
        struct {
            char **names;
            int count;
        } global_decl;
        struct {
            ASTNode *pattern;
            ASTNode *action;
        } pattern_action;
        struct {
            ASTNode **items;
            int count;
        } program;
    } as;
};

// ============================================================================
// FORWARD DECLARATIONS
// ============================================================================

void lexer_init(Lexer *lex, char *source);
void lexer_next(Lexer *lex);
ASTNode *parse(Lexer *lex);
Value eval(Env *env, ASTNode *node);
Env *env_new(Env *parent);
void env_set(Env *env, char *name, Value *val);
Value *env_get(Env *env, char *name);
Value value_null();
Value value_number(double n);
Value value_string(char *s);
Value value_array();
void array_set(ArrayValue *arr, char *key, Value *val);
Value *array_get(ArrayValue *arr, char *key);
Value builtin_print(Env *env, Value *args, int argc);
Value builtin_length(Env *env, Value *args, int argc);
Value builtin_map(Env *env, Value *args, int argc);
Value builtin_filter(Env *env, Value *args, int argc);
Value builtin_reduce(Env *env, Value *args, int argc);
void error(const char *fmt, ...);

// ============================================================================
// GLOBALS
// ============================================================================

Env *global_env;
int NR = 0;
char **fields = NULL;
int field_count = 0;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

void error(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "Error: ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");
    va_end(args);
    exit(1);
}

char *str_dup(const char *s) {
    if (!s) return NULL;
    char *dup = malloc(strlen(s) + 1);
    strcpy(dup, s);
    return dup;
}

unsigned int hash_string(const char *str) {
    unsigned int hash = 5381;
    int c;
    while ((c = *str++))
        hash = ((hash << 5) + hash) + c;
    return hash;
}

// ============================================================================
// VALUE FUNCTIONS
// ============================================================================

Value value_null() {
    Value v;
    v.type = VAL_NULL;
    return v;
}

Value value_number(double n) {
    Value v;
    v.type = VAL_NUMBER;
    v.as.number = n;
    return v;
}

Value value_string(char *s) {
    Value v;
    v.type = VAL_STRING;
    v.as.string = str_dup(s);
    return v;
}

Value value_array() {
    Value v;
    v.type = VAL_ARRAY;
    v.as.array = malloc(sizeof(ArrayValue));
    v.as.array->capacity = 16;
    v.as.array->size = 0;
    v.as.array->buckets = calloc(v.as.array->capacity, sizeof(ArrayEntry*));
    return v;
}

Value value_function(char **params, int param_count, ASTNode *body, Env *closure) {
    Value v;
    v.type = VAL_FUNCTION;
    v.as.function = malloc(sizeof(FunctionValue));
    v.as.function->params = params;
    v.as.function->param_count = param_count;
    v.as.function->body = body;
    v.as.function->closure = closure;
    return v;
}

Value value_builtin(BuiltinFunc func) {
    Value v;
    v.type = VAL_BUILTIN;
    v.as.builtin = func;
    return v;
}

double value_to_number(Value *v) {
    if (v->type == VAL_NUMBER) return v->as.number;
    if (v->type == VAL_STRING) return atof(v->as.string);
    return 0;
}

char *value_to_string(Value *v) {
    if (v->type == VAL_STRING) return v->as.string;
    if (v->type == VAL_NUMBER) {
        char *buf = malloc(64);
        sprintf(buf, "%g", v->as.number);
        return buf;
    }
    return "";
}

int value_to_bool(Value *v) {
    if (v->type == VAL_NULL) return 0;
    if (v->type == VAL_NUMBER) return v->as.number != 0;
    if (v->type == VAL_STRING) return strlen(v->as.string) > 0;
    return 1;
}

// ============================================================================
// ARRAY FUNCTIONS
// ============================================================================

void array_set(ArrayValue *arr, char *key, Value *val) {
    unsigned int h = hash_string(key) % arr->capacity;
    ArrayEntry *entry = arr->buckets[h];
    
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            entry->value = val;
            return;
        }
        entry = entry->next;
    }
    
    ArrayEntry *new_entry = malloc(sizeof(ArrayEntry));
    new_entry->key = str_dup(key);
    new_entry->value = val;
    new_entry->next = arr->buckets[h];
    arr->buckets[h] = new_entry;
    arr->size++;
}

Value *array_get(ArrayValue *arr, char *key) {
    unsigned int h = hash_string(key) % arr->capacity;
    ArrayEntry *entry = arr->buckets[h];
    
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            return entry->value;
        }
        entry = entry->next;
    }
    
    Value *null_val = malloc(sizeof(Value));
    *null_val = value_null();
    return null_val;
}

int array_has(ArrayValue *arr, char *key) {
    unsigned int h = hash_string(key) % arr->capacity;
    ArrayEntry *entry = arr->buckets[h];
    
    while (entry) {
        if (strcmp(entry->key, key) == 0) {
            return 1;
        }
        entry = entry->next;
    }
    return 0;
}

// ============================================================================
// ENVIRONMENT FUNCTIONS
// ============================================================================

Env *env_new(Env *parent) {
    Env *env = malloc(sizeof(Env));
    env->capacity = 32;
    env->buckets = calloc(env->capacity, sizeof(EnvEntry*));
    env->parent = parent;
    return env;
}

void env_set(Env *env, char *name, Value *val) {
    unsigned int h = hash_string(name) % env->capacity;
    EnvEntry *entry = env->buckets[h];
    
    while (entry) {
        if (strcmp(entry->name, name) == 0) {
            entry->value = val;
            return;
        }
        entry = entry->next;
    }
    
    EnvEntry *new_entry = malloc(sizeof(EnvEntry));
    new_entry->name = str_dup(name);
    new_entry->value = val;
    new_entry->next = env->buckets[h];
    env->buckets[h] = new_entry;
}

Value *env_get(Env *env, char *name) {
    while (env) {
        unsigned int h = hash_string(name) % env->capacity;
        EnvEntry *entry = env->buckets[h];
        
        while (entry) {
            if (strcmp(entry->name, name) == 0) {
                return entry->value;
            }
            entry = entry->next;
        }
        
        env = env->parent;
    }
    return NULL;
}

// ============================================================================
// LEXER
// ============================================================================

void lexer_init(Lexer *lex, char *source) {
    lex->source = source;
    lex->pos = 0;
    lex->line = 1;
    lexer_next(lex);
}

char lexer_peek(Lexer *lex) {
    return lex->source[lex->pos];
}

char lexer_advance(Lexer *lex) {
    return lex->source[lex->pos++];
}

void lexer_skip_whitespace(Lexer *lex) {
    while (1) {
        char c = lexer_peek(lex);
        if (c == ' ' || c == '\t' || c == '\r') {
            lexer_advance(lex);
        } else if (c == '#') {
            while (lexer_peek(lex) != '\n' && lexer_peek(lex) != '\0') {
                lexer_advance(lex);
            }
        } else {
            break;
        }
    }
}

int is_keyword(const char *text, const char *keyword) {
    return strcmp(text, keyword) == 0;
}

void lexer_next(Lexer *lex) {
    lexer_skip_whitespace(lex);
    
    char c = lexer_peek(lex);
    
    if (c == '\0') {
        lex->current.type = TOK_EOF;
        return;
    }
    
    if (c == '\n') {
        lexer_advance(lex);
        lex->line++;
        lex->current.type = TOK_NEWLINE;
        return;
    }
    
    // Single character tokens
    if (c == '(') { lexer_advance(lex); lex->current.type = TOK_LPAREN; return; }
    if (c == ')') { lexer_advance(lex); lex->current.type = TOK_RPAREN; return; }
    if (c == '{') { lexer_advance(lex); lex->current.type = TOK_LBRACE; return; }
    if (c == '}') { lexer_advance(lex); lex->current.type = TOK_RBRACE; return; }
    if (c == '[') { lexer_advance(lex); lex->current.type = TOK_LBRACKET; return; }
    if (c == ']') { lexer_advance(lex); lex->current.type = TOK_RBRACKET; return; }
    if (c == ',') { lexer_advance(lex); lex->current.type = TOK_COMMA; return; }
    if (c == ';') { lexer_advance(lex); lex->current.type = TOK_SEMICOLON; return; }
    if (c == '+') { lexer_advance(lex); lex->current.type = TOK_PLUS; return; }
    if (c == '-') { lexer_advance(lex); lex->current.type = TOK_MINUS; return; }
    if (c == '*') { lexer_advance(lex); lex->current.type = TOK_STAR; return; }
    if (c == '/') { lexer_advance(lex); lex->current.type = TOK_SLASH; return; }
    if (c == '%') { lexer_advance(lex); lex->current.type = TOK_PERCENT; return; }
    
    // Two character tokens
    if (c == '=') {
        lexer_advance(lex);
        if (lexer_peek(lex) == '=') {
            lexer_advance(lex);
            lex->current.type = TOK_EQ;
        } else if (lexer_peek(lex) == '>') {
            lexer_advance(lex);
            lex->current.type = TOK_ARROW;
        } else {
            lex->current.type = TOK_ASSIGN;
        }
        return;
    }
    
    if (c == '!') {
        lexer_advance(lex);
        if (lexer_peek(lex) == '=') {
            lexer_advance(lex);
            lex->current.type = TOK_NE;
        } else {
            lex->current.type = TOK_NOT;
        }
        return;
    }
    
    if (c == '<') {
        lexer_advance(lex);
        if (lexer_peek(lex) == '=') {
            lexer_advance(lex);
            lex->current.type = TOK_LE;
        } else {
            lex->current.type = TOK_LT;
        }
        return;
    }
    
    if (c == '>') {
        lexer_advance(lex);
        if (lexer_peek(lex) == '=') {
            lexer_advance(lex);
            lex->current.type = TOK_GE;
        } else {
            lex->current.type = TOK_GT;
        }
        return;
    }
    
    if (c == '&' && lex->source[lex->pos + 1] == '&') {
        lexer_advance(lex);
        lexer_advance(lex);
        lex->current.type = TOK_AND;
        return;
    }
    
    if (c == '|') {
        lexer_advance(lex);
        if (lexer_peek(lex) == '|') {
            lexer_advance(lex);
            lex->current.type = TOK_OR;
        } else if (lexer_peek(lex) == '>') {
            lexer_advance(lex);
            lex->current.type = TOK_PIPE_GT;
        } else {
            error("Unexpected character: |");
        }
        return;
    }
    
    // Strings
    if (c == '"') {
        lexer_advance(lex);
        int start = lex->pos;
        while (lexer_peek(lex) != '"' && lexer_peek(lex) != '\0') {
            lexer_advance(lex);
        }
        int len = lex->pos - start;
        lex->current.text = malloc(len + 1);
        strncpy(lex->current.text, &lex->source[start], len);
        lex->current.text[len] = '\0';
        lexer_advance(lex);
        lex->current.type = TOK_STRING;
        return;
    }
    
    // Numbers
    if (isdigit(c)) {
        int start = lex->pos;
        while (isdigit(lexer_peek(lex)) || lexer_peek(lex) == '.') {
            lexer_advance(lex);
        }
        int len = lex->pos - start;
        char *num_str = malloc(len + 1);
        strncpy(num_str, &lex->source[start], len);
        num_str[len] = '\0';
        lex->current.number = atof(num_str);
        free(num_str);
        lex->current.type = TOK_NUMBER;
        return;
    }
    
    // Identifiers and keywords
    if (isalpha(c) || c == '_' || c == '$') {
        int start = lex->pos;
        while (isalnum(lexer_peek(lex)) || lexer_peek(lex) == '_' || lexer_peek(lex) == '$') {
            lexer_advance(lex);
        }
        int len = lex->pos - start;
        lex->current.text = malloc(len + 1);
        strncpy(lex->current.text, &lex->source[start], len);
        lex->current.text[len] = '\0';
        
        if (is_keyword(lex->current.text, "function")) lex->current.type = TOK_FUNCTION;
        else if (is_keyword(lex->current.text, "return")) lex->current.type = TOK_RETURN;
        else if (is_keyword(lex->current.text, "if")) lex->current.type = TOK_IF;
        else if (is_keyword(lex->current.text, "else")) lex->current.type = TOK_ELSE;
        else if (is_keyword(lex->current.text, "for")) lex->current.type = TOK_FOR;
        else if (is_keyword(lex->current.text, "in")) lex->current.type = TOK_IN;
        else if (is_keyword(lex->current.text, "while")) lex->current.type = TOK_WHILE;
        else if (is_keyword(lex->current.text, "BEGIN")) lex->current.type = TOK_BEGIN;
        else if (is_keyword(lex->current.text, "END")) lex->current.type = TOK_END;
        else if (is_keyword(lex->current.text, "global")) lex->current.type = TOK_GLOBAL;
        else lex->current.type = TOK_IDENT;
        return;
    }
    
    error("Unexpected character: %c", c);
}

// ============================================================================
// PARSER
// ============================================================================

Token parser_peek(Lexer *lex) {
    return lex->current;
}

void parser_expect(Lexer *lex, TokenType type) {
    if (lex->current.type != type) {
        error("Expected token type %d but got %d", type, lex->current.type);
    }
    lexer_next(lex);
}

void parser_skip_newlines(Lexer *lex) {
    while (lex->current.type == TOK_NEWLINE) {
        lexer_next(lex);
    }
}

ASTNode *new_node(ASTNodeType type) {
    ASTNode *node = malloc(sizeof(ASTNode));
    node->type = type;
    return node;
}

ASTNode *parse_primary(Lexer *lex);
ASTNode *parse_expression(Lexer *lex);
ASTNode *parse_statement(Lexer *lex);

ASTNode *parse_primary(Lexer *lex) {
    parser_skip_newlines(lex);
    Token tok = parser_peek(lex);
    
    if (tok.type == TOK_NUMBER) {
        lexer_next(lex);
        ASTNode *node = new_node(AST_NUMBER);
        node->as.number = tok.number;
        return node;
    }
    
    if (tok.type == TOK_STRING) {
        lexer_next(lex);
        ASTNode *node = new_node(AST_STRING);
        node->as.string = tok.text;
        return node;
    }
    
    if (tok.type == TOK_IDENT) {
        lexer_next(lex);
        ASTNode *node = new_node(AST_IDENT);
        node->as.ident.name = tok.text;
        return node;
    }
    
    if (tok.type == TOK_LPAREN) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        
        // Try to parse as lambda parameters first
        char **params = NULL;
        int param_count = 0;
        int might_be_lambda = 1;
        
        if (lex->current.type == TOK_RPAREN) {
            // Empty params - definitely a lambda if followed by =>
            lexer_next(lex);
            parser_skip_newlines(lex);
            if (lex->current.type == TOK_ARROW) {
                // It's a lambda with no parameters
                lexer_next(lex);
                parser_skip_newlines(lex);
                ASTNode *body = parse_statement(lex);
                ASTNode *node = new_node(AST_LAMBDA);
                node->as.lambda.params = NULL;
                node->as.lambda.param_count = 0;
                node->as.lambda.body = body;
                return node;
            } else {
                // It's (), which is a syntax error, but let's handle it as empty expr
                error("Empty parentheses without arrow");
            }
        }
        
        // Check if first token is an identifier
        if (lex->current.type == TOK_IDENT) {
            // Could be lambda params or grouped expression
            // Save first identifier
            params = malloc(sizeof(char*) * 10);
            params[param_count++] = lex->current.text;
            lexer_next(lex);
            parser_skip_newlines(lex);
            
            // Check what follows
            if (lex->current.type == TOK_COMMA) {
                // Multiple parameters - definitely a lambda
                while (lex->current.type == TOK_COMMA) {
                    lexer_next(lex);
                    parser_skip_newlines(lex);
                    if (lex->current.type != TOK_IDENT) {
                        error("Expected parameter name in lambda");
                    }
                    params[param_count++] = lex->current.text;
                    lexer_next(lex);
                    parser_skip_newlines(lex);
                }
                parser_expect(lex, TOK_RPAREN);
                parser_skip_newlines(lex);
                parser_expect(lex, TOK_ARROW);
                parser_skip_newlines(lex);
                ASTNode *body = parse_statement(lex);
                ASTNode *node = new_node(AST_LAMBDA);
                node->as.lambda.params = params;
                node->as.lambda.param_count = param_count;
                node->as.lambda.body = body;
                return node;
            } else if (lex->current.type == TOK_RPAREN) {
                // Single parameter
                lexer_next(lex);
                parser_skip_newlines(lex);
                if (lex->current.type == TOK_ARROW) {
                    // It's a lambda
                    lexer_next(lex);
                    parser_skip_newlines(lex);
                    ASTNode *body = parse_statement(lex);
                    ASTNode *node = new_node(AST_LAMBDA);
                    node->as.lambda.params = params;
                    node->as.lambda.param_count = param_count;
                    node->as.lambda.body = body;
                    return node;
                } else {
                    // It's (ident) which is just a grouped identifier
                    ASTNode *node = new_node(AST_IDENT);
                    node->as.ident.name = params[0];
                    free(params);
                    return node;
                }
            } else {
                // Something else follows - not a lambda param list
                // This must be a grouped expression starting with an identifier
                // We need to create an identifier node and continue parsing
                error("Unexpected token after identifier in parentheses");
            }
        }
        
        // Otherwise, parse as grouped expression
        ASTNode *expr = parse_expression(lex);
        parser_expect(lex, TOK_RPAREN);
        return expr;
    }
    
    if (tok.type == TOK_LBRACKET) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        
        ASTNode **elements = malloc(sizeof(ASTNode*) * 100);
        int count = 0;
        
        if (lex->current.type != TOK_RBRACKET) {
            while (1) {
                parser_skip_newlines(lex);
                ASTNode *elem = parse_expression(lex);
                
                // Check for => (associative array)
                parser_skip_newlines(lex);
                if (lex->current.type == TOK_ARROW) {
                    lexer_next(lex);
                    parser_skip_newlines(lex);
                    ASTNode *value = parse_expression(lex);
                    
                    // Create a key-value pair
                    ASTNode *pair = new_node(AST_BINARY);
                    pair->as.binary.op = "=>";
                    pair->as.binary.left = elem;
                    pair->as.binary.right = value;
                    elements[count++] = pair;
                } else {
                    elements[count++] = elem;
                }
                
                parser_skip_newlines(lex);
                if (lex->current.type != TOK_COMMA) break;
                lexer_next(lex);
            }
        }
        
        parser_expect(lex, TOK_RBRACKET);
        
        ASTNode *node = new_node(AST_ARRAY_LITERAL);
        node->as.array_literal.elements = elements;
        node->as.array_literal.count = count;
        return node;
    }
    
    error("Unexpected token in primary expression");
    return NULL;
}

ASTNode *parse_postfix(Lexer *lex) {
    ASTNode *node = parse_primary(lex);
    
    while (1) {
        if (lex->current.type == TOK_LPAREN) {
            lexer_next(lex);
            parser_skip_newlines(lex);
            
            ASTNode **args = malloc(sizeof(ASTNode*) * 20);
            int arg_count = 0;
            
            if (lex->current.type != TOK_RPAREN) {
                while (1) {
                    parser_skip_newlines(lex);
                    args[arg_count++] = parse_expression(lex);
                    parser_skip_newlines(lex);
                    if (lex->current.type != TOK_COMMA) break;
                    lexer_next(lex);
                }
            }
            
            parser_expect(lex, TOK_RPAREN);
            
            ASTNode *call = new_node(AST_CALL);
            call->as.call.func = node;
            call->as.call.args = args;
            call->as.call.arg_count = arg_count;
            node = call;
        } else if (lex->current.type == TOK_LBRACKET) {
            lexer_next(lex);
            parser_skip_newlines(lex);
            ASTNode *index = parse_expression(lex);
            parser_expect(lex, TOK_RBRACKET);
            
            ASTNode *idx = new_node(AST_INDEX);
            idx->as.index.array = node;
            idx->as.index.index = index;
            node = idx;
        } else {
            break;
        }
    }
    
    return node;
}

ASTNode *parse_unary(Lexer *lex) {
    if (lex->current.type == TOK_MINUS || lex->current.type == TOK_NOT) {
        TokenType op = lex->current.type;
        lexer_next(lex);
        ASTNode *operand = parse_unary(lex);
        ASTNode *node = new_node(AST_UNARY);
        node->as.unary.op = (op == TOK_MINUS) ? "-" : "!";
        node->as.unary.operand = operand;
        return node;
    }
    return parse_postfix(lex);
}

ASTNode *parse_multiplicative(Lexer *lex) {
    ASTNode *left = parse_unary(lex);
    
    while (lex->current.type == TOK_STAR || lex->current.type == TOK_SLASH || 
           lex->current.type == TOK_PERCENT) {
        char *op;
        if (lex->current.type == TOK_STAR) op = "*";
        else if (lex->current.type == TOK_SLASH) op = "/";
        else op = "%";
        
        lexer_next(lex);
        ASTNode *right = parse_unary(lex);
        
        ASTNode *node = new_node(AST_BINARY);
        node->as.binary.op = op;
        node->as.binary.left = left;
        node->as.binary.right = right;
        left = node;
    }
    
    return left;
}

ASTNode *parse_additive(Lexer *lex) {
    ASTNode *left = parse_multiplicative(lex);
    
    while (lex->current.type == TOK_PLUS || lex->current.type == TOK_MINUS) {
        char *op = (lex->current.type == TOK_PLUS) ? "+" : "-";
        lexer_next(lex);
        ASTNode *right = parse_multiplicative(lex);
        
        ASTNode *node = new_node(AST_BINARY);
        node->as.binary.op = op;
        node->as.binary.left = left;
        node->as.binary.right = right;
        left = node;
    }
    
    return left;
}

ASTNode *parse_comparison(Lexer *lex) {
    ASTNode *left = parse_additive(lex);
    
    while (lex->current.type == TOK_LT || lex->current.type == TOK_LE ||
           lex->current.type == TOK_GT || lex->current.type == TOK_GE) {
        char *op;
        if (lex->current.type == TOK_LT) op = "<";
        else if (lex->current.type == TOK_LE) op = "<=";
        else if (lex->current.type == TOK_GT) op = ">";
        else op = ">=";
        
        lexer_next(lex);
        ASTNode *right = parse_additive(lex);
        
        ASTNode *node = new_node(AST_BINARY);
        node->as.binary.op = op;
        node->as.binary.left = left;
        node->as.binary.right = right;
        left = node;
    }
    
    return left;
}

ASTNode *parse_equality(Lexer *lex) {
    ASTNode *left = parse_comparison(lex);
    
    while (lex->current.type == TOK_EQ || lex->current.type == TOK_NE) {
        char *op = (lex->current.type == TOK_EQ) ? "==" : "!=";
        lexer_next(lex);
        ASTNode *right = parse_comparison(lex);
        
        ASTNode *node = new_node(AST_BINARY);
        node->as.binary.op = op;
        node->as.binary.left = left;
        node->as.binary.right = right;
        left = node;
    }
    
    return left;
}

ASTNode *parse_logical_and(Lexer *lex) {
    ASTNode *left = parse_equality(lex);
    
    while (lex->current.type == TOK_AND) {
        lexer_next(lex);
        ASTNode *right = parse_equality(lex);
        
        ASTNode *node = new_node(AST_BINARY);
        node->as.binary.op = "&&";
        node->as.binary.left = left;
        node->as.binary.right = right;
        left = node;
    }
    
    return left;
}

ASTNode *parse_logical_or(Lexer *lex) {
    ASTNode *left = parse_logical_and(lex);
    
    while (lex->current.type == TOK_OR) {
        lexer_next(lex);
        ASTNode *right = parse_logical_and(lex);
        
        ASTNode *node = new_node(AST_BINARY);
        node->as.binary.op = "||";
        node->as.binary.left = left;
        node->as.binary.right = right;
        left = node;
    }
    
    return left;
}

ASTNode *parse_pipeline(Lexer *lex) {
    ASTNode *left = parse_logical_or(lex);
    
    while (lex->current.type == TOK_PIPE_GT) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        ASTNode *right = parse_logical_or(lex);
        
        // Transform: left |> right into right(left) or right(...args, left)
        if (right->type == AST_CALL) {
            // Add left as last argument
            ASTNode **new_args = malloc(sizeof(ASTNode*) * (right->as.call.arg_count + 1));
            for (int i = 0; i < right->as.call.arg_count; i++) {
                new_args[i] = right->as.call.args[i];
            }
            new_args[right->as.call.arg_count] = left;
            right->as.call.args = new_args;
            right->as.call.arg_count++;
            left = right;
        } else {
            // Create call: right(left)
            ASTNode *call = new_node(AST_CALL);
            call->as.call.func = right;
            call->as.call.args = malloc(sizeof(ASTNode*));
            call->as.call.args[0] = left;
            call->as.call.arg_count = 1;
            left = call;
        }
    }
    
    return left;
}

ASTNode *parse_assignment(Lexer *lex) {
    ASTNode *left = parse_pipeline(lex);
    
    if (lex->current.type == TOK_ASSIGN) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        ASTNode *right = parse_assignment(lex);
        
        ASTNode *node = new_node(AST_ASSIGN);
        node->as.assign.target = left;
        node->as.assign.value = right;
        return node;
    }
    
    return left;
}

ASTNode *parse_expression(Lexer *lex) {
    return parse_assignment(lex);
}

ASTNode *parse_block(Lexer *lex) {
    parser_expect(lex, TOK_LBRACE);
    parser_skip_newlines(lex);
    
    ASTNode **stmts = malloc(sizeof(ASTNode*) * 100);
    int count = 0;
    
    while (lex->current.type != TOK_RBRACE && lex->current.type != TOK_EOF) {
        parser_skip_newlines(lex);
        if (lex->current.type == TOK_RBRACE) break;
        stmts[count++] = parse_statement(lex);
        parser_skip_newlines(lex);
    }
    
    parser_expect(lex, TOK_RBRACE);
    
    ASTNode *node = new_node(AST_BLOCK);
    node->as.block.stmts = stmts;
    node->as.block.count = count;
    return node;
}

ASTNode *parse_statement(Lexer *lex) {
    parser_skip_newlines(lex);
    
    if (lex->current.type == TOK_LBRACE) {
        return parse_block(lex);
    }
    
    if (lex->current.type == TOK_IF) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_LPAREN);
        parser_skip_newlines(lex);
        ASTNode *condition = parse_expression(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_RPAREN);
        parser_skip_newlines(lex);
        ASTNode *then_branch = parse_statement(lex);
        ASTNode *else_branch = NULL;
        
        parser_skip_newlines(lex);
        if (lex->current.type == TOK_ELSE) {
            lexer_next(lex);
            parser_skip_newlines(lex);
            else_branch = parse_statement(lex);
        }
        
        ASTNode *node = new_node(AST_IF);
        node->as.if_stmt.condition = condition;
        node->as.if_stmt.then_branch = then_branch;
        node->as.if_stmt.else_branch = else_branch;
        return node;
    }
    
    if (lex->current.type == TOK_FOR) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_LPAREN);
        parser_skip_newlines(lex);
        
        if (lex->current.type != TOK_IDENT) {
            error("Expected identifier in for loop");
        }
        char *var = lex->current.text;
        lexer_next(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_IN);
        parser_skip_newlines(lex);
        ASTNode *array = parse_expression(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_RPAREN);
        parser_skip_newlines(lex);
        ASTNode *body = parse_statement(lex);
        
        ASTNode *node = new_node(AST_FOR_IN);
        node->as.for_in.var = var;
        node->as.for_in.array = array;
        node->as.for_in.body = body;
        return node;
    }
    
    if (lex->current.type == TOK_WHILE) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_LPAREN);
        parser_skip_newlines(lex);
        ASTNode *condition = parse_expression(lex);
        parser_skip_newlines(lex);
        parser_expect(lex, TOK_RPAREN);
        parser_skip_newlines(lex);
        ASTNode *body = parse_statement(lex);
        
        ASTNode *node = new_node(AST_WHILE);
        node->as.while_stmt.condition = condition;
        node->as.while_stmt.body = body;
        return node;
    }
    
    if (lex->current.type == TOK_RETURN) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        ASTNode *value = NULL;
        if (lex->current.type != TOK_NEWLINE && lex->current.type != TOK_RBRACE && 
            lex->current.type != TOK_EOF) {
            value = parse_expression(lex);
        }
        
        ASTNode *node = new_node(AST_RETURN);
        node->as.return_stmt.value = value;
        return node;
    }
    
    if (lex->current.type == TOK_GLOBAL) {
        lexer_next(lex);
        parser_skip_newlines(lex);
        
        char **names = malloc(sizeof(char*) * 20);
        int count = 0;
        
        while (1) {
            parser_skip_newlines(lex);
            if (lex->current.type != TOK_IDENT) break;
            names[count++] = lex->current.text;
            lexer_next(lex);
            parser_skip_newlines(lex);
            if (lex->current.type != TOK_COMMA) break;
            lexer_next(lex);
        }
        
        ASTNode *node = new_node(AST_GLOBAL_DECL);
        node->as.global_decl.names = names;
        node->as.global_decl.count = count;
        return node;
    }
    
    ASTNode *expr = parse_expression(lex);
    return expr;
}

ASTNode *parse_function_def(Lexer *lex) {
    parser_expect(lex, TOK_FUNCTION);
    parser_skip_newlines(lex);
    
    if (lex->current.type != TOK_IDENT) {
        error("Expected function name");
    }
    char *name = lex->current.text;
    lexer_next(lex);
    parser_skip_newlines(lex);
    
    parser_expect(lex, TOK_LPAREN);
    parser_skip_newlines(lex);
    
    char **params = malloc(sizeof(char*) * 20);
    int param_count = 0;
    
    if (lex->current.type != TOK_RPAREN) {
        while (1) {
            parser_skip_newlines(lex);
            if (lex->current.type != TOK_IDENT) break;
            params[param_count++] = lex->current.text;
            lexer_next(lex);
            parser_skip_newlines(lex);
            if (lex->current.type != TOK_COMMA) break;
            lexer_next(lex);
        }
    }
    
    parser_expect(lex, TOK_RPAREN);
    parser_skip_newlines(lex);
    
    ASTNode *body = parse_block(lex);
    
    ASTNode *node = new_node(AST_FUNCTION_DEF);
    node->as.function_def.name = name;
    node->as.function_def.params = params;
    node->as.function_def.param_count = param_count;
    node->as.function_def.body = body;
    return node;
}

ASTNode *parse_pattern_action(Lexer *lex) {
    parser_skip_newlines(lex);
    
    ASTNode *pattern = NULL;
    ASTNode *action = NULL;
    
    if (lex->current.type == TOK_BEGIN || lex->current.type == TOK_END) {
        pattern = new_node(AST_IDENT);
        pattern->as.ident.name = (lex->current.type == TOK_BEGIN) ? "BEGIN" : "END";
        lexer_next(lex);
        parser_skip_newlines(lex);
        action = parse_block(lex);
    } else if (lex->current.type == TOK_LBRACE) {
        // Just an action, no pattern
        action = parse_block(lex);
    } else {
        // General pattern followed by action
        pattern = parse_expression(lex);
        parser_skip_newlines(lex);
        action = parse_block(lex);
    }
    
    ASTNode *node = new_node(AST_PATTERN_ACTION);
    node->as.pattern_action.pattern = pattern;
    node->as.pattern_action.action = action;
    return node;
}

ASTNode *parse(Lexer *lex) {
    ASTNode **items = malloc(sizeof(ASTNode*) * 100);
    int count = 0;
    
    parser_skip_newlines(lex);
    
    while (lex->current.type != TOK_EOF) {
        parser_skip_newlines(lex);
        if (lex->current.type == TOK_EOF) break;
        
        if (lex->current.type == TOK_FUNCTION) {
            items[count++] = parse_function_def(lex);
        } else {
            // Everything else is a pattern-action
            items[count++] = parse_pattern_action(lex);
        }
        
        parser_skip_newlines(lex);
    }
    
    ASTNode *node = new_node(AST_PROGRAM);
    node->as.program.items = items;
    node->as.program.count = count;
    return node;
}

// ============================================================================
// EVALUATOR
// ============================================================================

int in_return = 0;
Value return_value;

Value eval(Env *env, ASTNode *node) {
    if (!node) return value_null();
    
    if (in_return) return return_value;
    
    switch (node->type) {
        case AST_NUMBER:
            return value_number(node->as.number);
        
        case AST_STRING:
            return value_string(node->as.string);
        
        case AST_IDENT: {
            char *name = node->as.ident.name;
            
            // Check for special variables
            if (strcmp(name, "NR") == 0) {
                return value_number(NR);
            }
            
            // Check for field variables ($1, $2, etc.)
            if (name[0] == '$') {
                int field_num = atoi(name + 1);
                if (field_num >= 0 && field_num < field_count) {
                    return value_string(fields[field_num]);
                }
                return value_string("");
            }
            
            Value *val = env_get(env, name);
            if (!val) {
                // Return null for undefined variables
                Value *null_val = malloc(sizeof(Value));
                *null_val = value_null();
                return *null_val;
            }
            return *val;
        }
        
        case AST_ARRAY_LITERAL: {
            Value arr = value_array();
            for (int i = 0; i < node->as.array_literal.count; i++) {
                ASTNode *elem = node->as.array_literal.elements[i];
                
                if (elem->type == AST_BINARY && strcmp(elem->as.binary.op, "=>") == 0) {
                    // Associative array entry
                    Value key_val = eval(env, elem->as.binary.left);
                    char *key = value_to_string(&key_val);
                    Value val = eval(env, elem->as.binary.right);
                    Value *val_ptr = malloc(sizeof(Value));
                    *val_ptr = val;
                    array_set(arr.as.array, key, val_ptr);
                } else {
                    // Regular array entry
                    char key[32];
                    sprintf(key, "%d", i);
                    Value val = eval(env, elem);
                    Value *val_ptr = malloc(sizeof(Value));
                    *val_ptr = val;
                    array_set(arr.as.array, key, val_ptr);
                }
            }
            return arr;
        }
        
        case AST_BINARY: {
            char *op = node->as.binary.op;
            Value left = eval(env, node->as.binary.left);
            
            // Short-circuit evaluation for logical operators
            if (strcmp(op, "&&") == 0) {
                if (!value_to_bool(&left)) return value_number(0);
                Value right = eval(env, node->as.binary.right);
                return value_number(value_to_bool(&right));
            }
            if (strcmp(op, "||") == 0) {
                if (value_to_bool(&left)) return value_number(1);
                Value right = eval(env, node->as.binary.right);
                return value_number(value_to_bool(&right));
            }
            
            Value right = eval(env, node->as.binary.right);
            
            if (strcmp(op, "+") == 0) {
                return value_number(value_to_number(&left) + value_to_number(&right));
            } else if (strcmp(op, "-") == 0) {
                return value_number(value_to_number(&left) - value_to_number(&right));
            } else if (strcmp(op, "*") == 0) {
                return value_number(value_to_number(&left) * value_to_number(&right));
            } else if (strcmp(op, "/") == 0) {
                return value_number(value_to_number(&left) / value_to_number(&right));
            } else if (strcmp(op, "%") == 0) {
                return value_number((int)value_to_number(&left) % (int)value_to_number(&right));
            } else if (strcmp(op, "==") == 0) {
                return value_number(value_to_number(&left) == value_to_number(&right));
            } else if (strcmp(op, "!=") == 0) {
                return value_number(value_to_number(&left) != value_to_number(&right));
            } else if (strcmp(op, "<") == 0) {
                return value_number(value_to_number(&left) < value_to_number(&right));
            } else if (strcmp(op, "<=") == 0) {
                return value_number(value_to_number(&left) <= value_to_number(&right));
            } else if (strcmp(op, ">") == 0) {
                return value_number(value_to_number(&left) > value_to_number(&right));
            } else if (strcmp(op, ">=") == 0) {
                return value_number(value_to_number(&left) >= value_to_number(&right));
            }
            break;
        }
        
        case AST_UNARY: {
            Value operand = eval(env, node->as.unary.operand);
            if (strcmp(node->as.unary.op, "-") == 0) {
                return value_number(-value_to_number(&operand));
            } else if (strcmp(node->as.unary.op, "!") == 0) {
                return value_number(!value_to_bool(&operand));
            }
            break;
        }
        
        case AST_CALL: {
            Value func = eval(env, node->as.call.func);
            
            if (func.type == VAL_BUILTIN) {
                Value *args = malloc(sizeof(Value) * node->as.call.arg_count);
                for (int i = 0; i < node->as.call.arg_count; i++) {
                    args[i] = eval(env, node->as.call.args[i]);
                }
                return func.as.builtin(env, args, node->as.call.arg_count);
            } else if (func.type == VAL_FUNCTION) {
                FunctionValue *fn = func.as.function;
                Env *call_env = env_new(fn->closure);
                
                for (int i = 0; i < fn->param_count; i++) {
                    Value arg = (i < node->as.call.arg_count) ? 
                                eval(env, node->as.call.args[i]) : value_null();
                    Value *arg_ptr = malloc(sizeof(Value));
                    *arg_ptr = arg;
                    env_set(call_env, fn->params[i], arg_ptr);
                }
                
                int saved_in_return = in_return;
                in_return = 0;
                
                Value result = eval(call_env, fn->body);
                
                if (in_return) {
                    result = return_value;
                    in_return = saved_in_return;
                }
                
                return result;
            }
            break;
        }
        
        case AST_INDEX: {
            Value array = eval(env, node->as.index.array);
            Value index = eval(env, node->as.index.index);
            
            if (array.type == VAL_ARRAY) {
                char *key = value_to_string(&index);
                return *array_get(array.as.array, key);
            }
            break;
        }
        
        case AST_ASSIGN: {
            Value val = eval(env, node->as.assign.value);
            Value *val_ptr = malloc(sizeof(Value));
            *val_ptr = val;
            
            if (node->as.assign.target->type == AST_IDENT) {
                env_set(env, node->as.assign.target->as.ident.name, val_ptr);
            } else if (node->as.assign.target->type == AST_INDEX) {
                Value array = eval(env, node->as.assign.target->as.index.array);
                Value index = eval(env, node->as.assign.target->as.index.index);
                
                if (array.type == VAL_ARRAY) {
                    char *key = value_to_string(&index);
                    array_set(array.as.array, key, val_ptr);
                }
            }
            
            return val;
        }
        
        case AST_BLOCK: {
            Value result = value_null();
            for (int i = 0; i < node->as.block.count; i++) {
                result = eval(env, node->as.block.stmts[i]);
                if (in_return) break;
            }
            return result;
        }
        
        case AST_IF: {
            Value condition = eval(env, node->as.if_stmt.condition);
            if (value_to_bool(&condition)) {
                return eval(env, node->as.if_stmt.then_branch);
            } else if (node->as.if_stmt.else_branch) {
                return eval(env, node->as.if_stmt.else_branch);
            }
            return value_null();
        }
        
        case AST_FOR_IN: {
            Value array = eval(env, node->as.for_in.array);
            Value result = value_null();
            
            if (array.type == VAL_ARRAY) {
                for (int i = 0; i < array.as.array->capacity; i++) {
                    ArrayEntry *entry = array.as.array->buckets[i];
                    while (entry) {
                        Value *key_val = malloc(sizeof(Value));
                        *key_val = value_string(entry->key);
                        env_set(env, node->as.for_in.var, key_val);
                        result = eval(env, node->as.for_in.body);
                        if (in_return) break;
                        entry = entry->next;
                    }
                    if (in_return) break;
                }
            }
            
            return result;
        }
        
        case AST_WHILE: {
            Value result = value_null();
            while (1) {
                Value condition = eval(env, node->as.while_stmt.condition);
                if (!value_to_bool(&condition)) break;
                result = eval(env, node->as.while_stmt.body);
                if (in_return) break;
            }
            return result;
        }
        
        case AST_RETURN: {
            if (node->as.return_stmt.value) {
                return_value = eval(env, node->as.return_stmt.value);
            } else {
                return_value = value_null();
            }
            in_return = 1;
            return return_value;
        }
        
        case AST_LAMBDA: {
            return value_function(node->as.lambda.params, node->as.lambda.param_count,
                                 node->as.lambda.body, env);
        }
        
        case AST_GLOBAL_DECL: {
            // Global declarations don't do anything at runtime in the current scope
            // They just mark variables that should be accessed from global scope
            return value_null();
        }
        
        default:
            break;
    }
    
    return value_null();
}

// ============================================================================
// BUILT-IN FUNCTIONS
// ============================================================================

Value builtin_print(Env *env, Value *args, int argc) {
    for (int i = 0; i < argc; i++) {
        if (i > 0) printf(" ");
        
        if (args[i].type == VAL_NUMBER) {
            printf("%g", args[i].as.number);
        } else if (args[i].type == VAL_STRING) {
            printf("%s", args[i].as.string);
        } else if (args[i].type == VAL_ARRAY) {
            printf("[");
            int first = 1;
            ArrayValue *arr = args[i].as.array;
            
            // Check if it's a regular numeric array (0, 1, 2, ...)
            int is_regular = 1;
            int max_index = -1;
            for (int j = 0; j < arr->capacity; j++) {
                ArrayEntry *entry = arr->buckets[j];
                while (entry) {
                    char *endptr;
                    int idx = strtol(entry->key, &endptr, 10);
                    if (*endptr != '\0' || idx < 0) {
                        is_regular = 0;
                    } else if (idx > max_index) {
                        max_index = idx;
                    }
                    entry = entry->next;
                }
            }
            
            if (is_regular && max_index >= 0) {
                // Print as regular array in order
                for (int j = 0; j <= max_index; j++) {
                    char key[32];
                    sprintf(key, "%d", j);
                    if (array_has(arr, key)) {
                        if (!first) printf(", ");
                        Value *val = array_get(arr, key);
                        if (val->type == VAL_NUMBER) {
                            printf("%g", val->as.number);
                        } else if (val->type == VAL_STRING) {
                            printf("%s", val->as.string);
                        }
                        first = 0;
                    }
                }
            } else {
                // Print as associative array (just values)
                for (int j = 0; j < arr->capacity; j++) {
                    ArrayEntry *entry = arr->buckets[j];
                    while (entry) {
                        if (!first) printf(", ");
                        Value *val = entry->value;
                        if (val->type == VAL_NUMBER) {
                            printf("%g", val->as.number);
                        } else if (val->type == VAL_STRING) {
                            printf("%s", val->as.string);
                        }
                        first = 0;
                        entry = entry->next;
                    }
                }
            }
            printf("]");
        }
    }
    printf("\n");
    return value_null();
}

Value builtin_length(Env *env, Value *args, int argc) {
    if (argc < 1) return value_number(0);
    
    if (args[0].type == VAL_ARRAY) {
        return value_number(args[0].as.array->size);
    } else if (args[0].type == VAL_STRING) {
        return value_number(strlen(args[0].as.string));
    }
    
    return value_number(0);
}

Value builtin_map(Env *env, Value *args, int argc) {
    if (argc < 2) return value_null();
    
    Value func = args[0];
    Value array = args[1];
    
    if (array.type != VAL_ARRAY) return value_null();
    
    Value result = value_array();
    
    for (int i = 0; i < array.as.array->capacity; i++) {
        ArrayEntry *entry = array.as.array->buckets[i];
        while (entry) {
            // Call function with array element
            if (func.type == VAL_FUNCTION) {
                FunctionValue *fn = func.as.function;
                Env *call_env = env_new(fn->closure);
                
                Value *arg_ptr = malloc(sizeof(Value));
                *arg_ptr = *entry->value;
                env_set(call_env, fn->params[0], arg_ptr);
                
                int saved_in_return = in_return;
                in_return = 0;
                
                Value mapped = eval(call_env, fn->body);
                
                if (in_return) {
                    mapped = return_value;
                    in_return = saved_in_return;
                }
                
                Value *mapped_ptr = malloc(sizeof(Value));
                *mapped_ptr = mapped;
                array_set(result.as.array, entry->key, mapped_ptr);
            }
            
            entry = entry->next;
        }
    }
    
    return result;
}

Value builtin_filter(Env *env, Value *args, int argc) {
    if (argc < 2) return value_null();
    
    Value func = args[0];
    Value array = args[1];
    
    if (array.type != VAL_ARRAY) return value_null();
    
    Value result = value_array();
    
    for (int i = 0; i < array.as.array->capacity; i++) {
        ArrayEntry *entry = array.as.array->buckets[i];
        while (entry) {
            // Call function with array element
            if (func.type == VAL_FUNCTION) {
                FunctionValue *fn = func.as.function;
                Env *call_env = env_new(fn->closure);
                
                Value *arg_ptr = malloc(sizeof(Value));
                *arg_ptr = *entry->value;
                env_set(call_env, fn->params[0], arg_ptr);
                
                int saved_in_return = in_return;
                in_return = 0;
                
                Value predicate = eval(call_env, fn->body);
                
                if (in_return) {
                    predicate = return_value;
                    in_return = saved_in_return;
                }
                
                if (value_to_bool(&predicate)) {
                    array_set(result.as.array, entry->key, entry->value);
                }
            }
            
            entry = entry->next;
        }
    }
    
    return result;
}

Value builtin_reduce(Env *env, Value *args, int argc) {
    if (argc < 3) return value_null();
    
    Value func = args[0];
    Value initial = args[1];
    Value array = args[2];
    
    if (array.type != VAL_ARRAY) return initial;
    
    Value accumulator = initial;
    
    for (int i = 0; i < array.as.array->capacity; i++) {
        ArrayEntry *entry = array.as.array->buckets[i];
        while (entry) {
            // Call function with accumulator and array element
            if (func.type == VAL_FUNCTION) {
                FunctionValue *fn = func.as.function;
                Env *call_env = env_new(fn->closure);
                
                Value *acc_ptr = malloc(sizeof(Value));
                *acc_ptr = accumulator;
                env_set(call_env, fn->params[0], acc_ptr);
                
                Value *elem_ptr = malloc(sizeof(Value));
                *elem_ptr = *entry->value;
                env_set(call_env, fn->params[1], elem_ptr);
                
                int saved_in_return = in_return;
                in_return = 0;
                
                accumulator = eval(call_env, fn->body);
                
                if (in_return) {
                    accumulator = return_value;
                    in_return = saved_in_return;
                }
            }
            
            entry = entry->next;
        }
    }
    
    return accumulator;
}

Value builtin_sum(Env *env, Value *args, int argc) {
    if (argc < 1 || args[0].type != VAL_ARRAY) return value_number(0);
    
    double total = 0;
    ArrayValue *arr = args[0].as.array;
    
    for (int i = 0; i < arr->capacity; i++) {
        ArrayEntry *entry = arr->buckets[i];
        while (entry) {
            total += value_to_number(entry->value);
            entry = entry->next;
        }
    }
    
    return value_number(total);
}

Value builtin_avg(Env *env, Value *args, int argc) {
    if (argc < 1 || args[0].type != VAL_ARRAY) return value_number(0);
    
    Value sum = builtin_sum(env, args, argc);
    Value len = builtin_length(env, args, argc);
    
    if (len.as.number == 0) return value_number(0);
    return value_number(sum.as.number / len.as.number);
}

// ============================================================================
// MAIN
// ============================================================================

void split_fields(char *line) {
    if (fields) {
        for (int i = 0; i < field_count; i++) {
            free(fields[i]);
        }
        free(fields);
    }
    
    fields = malloc(sizeof(char*) * 100);
    field_count = 0;
    
    // $0 is the whole line
    fields[field_count++] = str_dup(line);
    
    // Split by whitespace or comma
    char *token = strtok(line, " ,\t");
    while (token) {
        fields[field_count++] = str_dup(token);
        token = strtok(NULL, " ,\t");
    }
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <script.fawk> [input.txt]\n", argv[0]);
        return 1;
    }
    
    // Read script
    FILE *script_file = fopen(argv[1], "r");
    if (!script_file) {
        error("Cannot open script file: %s", argv[1]);
    }
    
    fseek(script_file, 0, SEEK_END);
    long script_size = ftell(script_file);
    fseek(script_file, 0, SEEK_SET);
    
    char *script = malloc(script_size + 1);
    fread(script, 1, script_size, script_file);
    script[script_size] = '\0';
    fclose(script_file);
    
    // Parse script
    Lexer lex;
    lexer_init(&lex, script);
    ASTNode *program = parse(&lex);
    
    // Initialize global environment
    global_env = env_new(NULL);
    
    // Add built-in functions
    Value *print_val = malloc(sizeof(Value));
    *print_val = value_builtin(builtin_print);
    env_set(global_env, "print", print_val);
    
    Value *length_val = malloc(sizeof(Value));
    *length_val = value_builtin(builtin_length);
    env_set(global_env, "length", length_val);
    
    Value *map_val = malloc(sizeof(Value));
    *map_val = value_builtin(builtin_map);
    env_set(global_env, "map", map_val);
    
    Value *filter_val = malloc(sizeof(Value));
    *filter_val = value_builtin(builtin_filter);
    env_set(global_env, "filter", filter_val);
    
    Value *reduce_val = malloc(sizeof(Value));
    *reduce_val = value_builtin(builtin_reduce);
    env_set(global_env, "reduce", reduce_val);
    
    Value *sum_val = malloc(sizeof(Value));
    *sum_val = value_builtin(builtin_sum);
    env_set(global_env, "sum", sum_val);
    
    Value *avg_val = malloc(sizeof(Value));
    *avg_val = value_builtin(builtin_avg);
    env_set(global_env, "avg", avg_val);
    
    // Execute program
    ASTNode *begin_action = NULL;
    ASTNode *end_action = NULL;
    ASTNode **pattern_actions = malloc(sizeof(ASTNode*) * 100);
    int pattern_action_count = 0;
    
    // First pass: register functions and find BEGIN/END blocks
    for (int i = 0; i < program->as.program.count; i++) {
        ASTNode *item = program->as.program.items[i];
        
        if (item->type == AST_FUNCTION_DEF) {
            Value func = value_function(item->as.function_def.params,
                                       item->as.function_def.param_count,
                                       item->as.function_def.body,
                                       global_env);
            Value *func_ptr = malloc(sizeof(Value));
            *func_ptr = func;
            env_set(global_env, item->as.function_def.name, func_ptr);
        } else if (item->type == AST_PATTERN_ACTION) {
            if (item->as.pattern_action.pattern &&
                item->as.pattern_action.pattern->type == AST_IDENT) {
                if (strcmp(item->as.pattern_action.pattern->as.ident.name, "BEGIN") == 0) {
                    begin_action = item->as.pattern_action.action;
                } else if (strcmp(item->as.pattern_action.pattern->as.ident.name, "END") == 0) {
                    end_action = item->as.pattern_action.action;
                } else {
                    pattern_actions[pattern_action_count++] = item;
                }
            } else {
                pattern_actions[pattern_action_count++] = item;
            }
        }
    }
    
    // Execute BEGIN block
    if (begin_action) {
        eval(global_env, begin_action);
    }
    
    // Process input lines
    if (pattern_action_count > 0 && argc >= 3) {
        FILE *input_file = fopen(argv[2], "r");
        if (input_file) {
            char line[4096];
            while (fgets(line, sizeof(line), input_file)) {
                NR++;
                // Remove newline
                line[strcspn(line, "\n")] = 0;
                split_fields(line);
                
                // Evaluate each pattern-action
                for (int i = 0; i < pattern_action_count; i++) {
                    ASTNode *pa = pattern_actions[i];
                    int should_execute = 1;
                    
                    if (pa->as.pattern_action.pattern) {
                        Value pattern_result = eval(global_env, pa->as.pattern_action.pattern);
                        should_execute = value_to_bool(&pattern_result);
                    }
                    
                    if (should_execute) {
                        eval(global_env, pa->as.pattern_action.action);
                    }
                }
            }
            fclose(input_file);
        }
    }
    
    // Execute END block
    if (end_action) {
        eval(global_env, end_action);
    }
    
    return 0;
}
