#!/usr/bin/env python3
import json
import os
import hashlib
import re
from typing import Dict, Any, List, Tuple, Set

def save_variables_to_json(variables: Dict[str, Any], output_file: str) -> None:
    """Save variables to a JSON file with proper formatting."""
    simplified = {}
    for var_name, var_value in variables.items():
        simplified[var_name] = var_value['value'] if isinstance(var_value, dict) and 'value' in var_value else var_value
    
    with open(output_file, 'w') as f:
        json.dump(simplified, f, indent=2)

def format_query_with_closing_braces(query: str, needed_braces: int) -> str:
    """Format a GraphQL query with proper indentation for closing braces."""
    lines = [line for line in query.split('\n') if not line.strip().startswith('#')]
    formatted_lines = []
    indent_level = 0
    
    for line in lines:
        if not line.strip():
            formatted_lines.append(line)
            continue
            
        open_count = line.count('{')
        close_count = line.count('}')
        
        this_indent = max(0, (indent_level - close_count) * 2) if close_count > 0 else indent_level * 2
        formatted_lines.append(' ' * this_indent + line.strip())
        indent_level += open_count - close_count
    
    for _ in range(needed_braces):
        indent_level -= 1
        formatted_lines.append(' ' * max(0, indent_level * 2) + '}')
    
    if indent_level > 0:
        for i in range(indent_level):
            formatted_lines.append(' ' * max(0, (indent_level - i - 1) * 2) + '}')
    
    return '\n'.join(formatted_lines)

def ensure_closing_braces(file_path: str) -> None:
    """Make sure the file has balanced opening and closing braces."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        open_count = content.count('{')
        close_count = content.count('}')
        
        if open_count > close_count:
            with open(file_path, 'w') as f:
                f.write(content.rstrip() + '\n' + '}' * (open_count - close_count) + '\n')
        elif open_count < close_count:
            lines = content.split('\n')
            result_lines = []
            excess = close_count - open_count
            
            for line in reversed(lines):
                if excess > 0:
                    count = min(line.count('}'), excess)
                    if count > 0:
                        for _ in range(count):
                            pos = line.rfind('}')
                            if pos >= 0:
                                line = line[:pos] + line[pos+1:]
                        excess -= count
                result_lines.insert(0, line)
            
            with open(file_path, 'w') as f:
                f.write('\n'.join(result_lines))
    except Exception as e:
        print(f"Error ensuring closing braces in {file_path}: {e}")

def save_query_results(queries: List[Tuple[str, Dict[str, Any]]], output_dir: str, 
                       schema_name: str, category: str) -> None:
    """Save query results to separate query and variable files."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    if category == 'mutations':
        pair_counter = 1
        for i in range(0, len(queries), 2):
            if i < len(queries):
                insert_query, insert_variables = queries[i]
                query_lines = [line for line in insert_query.split('\n') if not line.strip().startswith('#')]
                clean_query = format_query_properly('\n'.join(query_lines))
                
                query_file = os.path.join(output_dir, f"{schema_name}_{category}_insert_{pair_counter}.graphql")
                variables_file = os.path.join(output_dir, f"{schema_name}_{category}_insert_{pair_counter}.json")
                
                with open(query_file, 'w') as f:
                    f.write(clean_query)
                
                save_variables_to_json(insert_variables, variables_file)
                ensure_closing_braces(query_file)
                ensure_closing_braces(variables_file)
            
            if i + 1 < len(queries):
                delete_query, delete_variables = queries[i + 1]
                query_lines = [line for line in delete_query.split('\n') if not line.strip().startswith('#')]
                clean_query = format_query_properly('\n'.join(query_lines))
                
                query_file = os.path.join(output_dir, f"{schema_name}_{category}_delete_{pair_counter}_after_insert_{pair_counter}.graphql")
                variables_file = os.path.join(output_dir, f"{schema_name}_{category}_delete_{pair_counter}_after_insert_{pair_counter}.json")
                
                with open(query_file, 'w') as f:
                    f.write(clean_query)
                
                save_variables_to_json(delete_variables, variables_file)
                ensure_closing_braces(query_file)
                ensure_closing_braces(variables_file)
            
            pair_counter += 1
    else:
        for i, (query, variables) in enumerate(queries, 1):
            query_lines = [line for line in query.split('\n') if not line.strip().startswith('#')]
            clean_query = format_query_properly('\n'.join(query_lines))
            
            query_file = os.path.join(output_dir, f"{schema_name}_{category}_query_{i}.graphql")
            variables_file = os.path.join(output_dir, f"{schema_name}_{category}_variables_{i}.json")
            
            with open(query_file, 'w') as f:
                f.write(clean_query)
            
            save_variables_to_json(variables, variables_file)
            ensure_closing_braces(query_file)
            ensure_closing_braces(variables_file)

def format_query_properly(query: str) -> str:
    """Format a GraphQL query properly with balanced braces and proper indentation."""
    query = query.strip()
    
    open_braces = query.count('{')
    close_braces = query.count('}')
    
    if open_braces > close_braces:
        query = format_query_with_closing_braces(query, open_braces - close_braces)
    elif open_braces < close_braces:
        excess = close_braces - open_braces
        lines = query.split('\n')
        result_lines = []
        
        for line in reversed(lines):
            while excess > 0 and '}' in line:
                pos = line.rfind('}')
                if pos >= 0:
                    line = line[:pos] + line[pos+1:]
                    excess -= 1
            result_lines.insert(0, line)
        
        query = '\n'.join(result_lines)
    
    lines = query.split('\n')
    formatted_lines = []
    indent = 0
    
    for line in lines:
        if not line.strip():
            continue
        
        open_count = line.count('{')
        close_count = line.count('}')
        
        current_indent = max(0, indent - 1) if line.strip().startswith('}') else indent
        formatted_lines.append('  ' * current_indent + line.strip())
        
        indent += open_count - close_count
        indent = max(0, indent)
    
    return '\n'.join(formatted_lines)

def generate_query_signature(query: str) -> str:
    """Generate a hash signature for a query to detect duplicates."""
    if not query or query.strip() == '':
        return ''
    
    query = re.sub(r'#.*', '', query)
    query = ' '.join(query.split())
    
    return hashlib.md5(query.encode()).hexdigest()

def validate_query_uniqueness(queries: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
    """Validate query uniqueness and filter out duplicates and invalid queries."""
    seen_signatures: Set[str] = set()
    unique_queries: List[Tuple[str, Dict[str, Any]]] = []
    
    for query, variables in queries:
        if not query or not query.strip():
            continue
            
        query_lines = [line.strip() for line in query.split('\n') if line.strip()]
        if len(query_lines) <= 2 or len(query.strip()) < 10:
            continue
            
        signature = generate_query_signature(query)
        
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_queries.append((query, variables))
    
    return unique_queries 