import os
import sys
import shutil
import tempfile
import json
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)

from src.query_generator_app import GraphQLQueryGeneratorApp
from src.utils.schema_utils import load_schema_from_file

app = FastAPI(title="AutoGraphQL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCHEMAS_DIR = os.path.join(root_dir, 'schemas')

@app.get("/api/schemas")
def list_schemas():
    schemas = []
    if os.path.exists(SCHEMAS_DIR):
        for item in os.listdir(SCHEMAS_DIR):
            item_path = os.path.join(SCHEMAS_DIR, item)
            if os.path.isdir(item_path):
                schema_file = os.path.join(item_path, 'index.graphql')
                if os.path.exists(schema_file):
                    schemas.append(item)
    return {"schemas": sorted(schemas)}

@app.post("/api/generate")
def generate_dataset(
    schema_names: str = Form(""),
    schema_file: Optional[UploadFile] = File(None),
    categories: str = Form(""),
    count: int = Form(3),
    max_hops: int = Form(2)
):
    selected_schemas = [s.strip() for s in schema_names.split(",")] if schema_names else []
    selected_categories = [c.strip() for c in categories.split(",")] if categories else []
    
    tmp_dir = tempfile.mkdtemp()
    custom_schema_path = None
    
    if schema_file and schema_file.filename.endswith('.graphql'):
        custom_schema_dir = os.path.join(tmp_dir, 'custom_schemas', 'custom')
        os.makedirs(custom_schema_dir, exist_ok=True)
        custom_schema_path = os.path.join(custom_schema_dir, 'index.graphql')
        
        content = schema_file.file.read()
        with open(custom_schema_path, 'wb') as f:
            f.write(content)
            
        selected_schemas.append('custom')
    
    dataset = []
    data_id = 1
    
    generator_app = GraphQLQueryGeneratorApp()
    queries_output_dir = os.path.join(tmp_dir, 'queries')
    os.makedirs(queries_output_dir, exist_ok=True)

    for schema_name in selected_schemas:
        if schema_name == 'custom':
            schema_path = custom_schema_path
        else:
            schema_path = os.path.join(SCHEMAS_DIR, schema_name, 'index.graphql')
            
        if not schema_path or not os.path.exists(schema_path):
            continue
            
        try:
            schema_content = load_schema_from_file(schema_path)
        except Exception:
            continue
            
        for category in selected_categories:
            generator_app.generate_queries_for_schema(
                schema_file=schema_path,
                category=category,
                count=count,
                max_hops=max_hops,
                output_dir=queries_output_dir
            )
            
            query_dir = os.path.join(queries_output_dir, schema_name)
            if not os.path.exists(query_dir):
                continue
                
            query_files = [f for f in os.listdir(query_dir) if f.endswith('.graphql') and category in f]
            for query_file in sorted(query_files):
                query_path = os.path.join(query_dir, query_file)
                variables_file = query_file.replace('_query_', '_variables_').replace('.graphql', '.json')
                variables_path = os.path.join(query_dir, variables_file)
                
                try:
                    with open(query_path, 'r') as f:
                        query_content = f.read()
                except Exception:
                    continue
                    
                variables_content = "{}"
                if os.path.exists(variables_path):
                    try:
                        with open(variables_path, 'r') as f:
                            variables_content = f.read()
                    except Exception:
                        pass
                
                query_sub_category = ""
                mutation_type = ""
                
                if category == 'mutations':
                    ql = query_content.lower()
                    if ('mutation create' in ql or 'mutation insert' in ql or 'mutation add' in ql):
                        mutation_type = "insert"
                    elif ('mutation delete' in ql or 'mutation remove' in ql):
                        mutation_type = "delete"
                    else:
                        mutation_type = "unknown"
                        
                if category in ['external_fragments', 'inline_fragments', 'aliases']:
                    if any(term in variables_content.lower() for term in ['filter', 'where', 'condition']):
                        query_sub_category = "filters"
                    elif any(d in variables_content for d in ['includeDetails', 'skipOptionalFields']):
                        query_sub_category = "directives"
                    elif '@include' in query_content or '@skip' in query_content:
                        query_sub_category = "directives"

                query_category_list = category + (", " + query_sub_category if query_sub_category else "")

                dataset.append({
                    'DataID': data_id,
                    'GraphQLSchemaName': schema_name,
                    'GraphQLQuery': query_content,
                    'GraphQLQueryVariables': variables_content,
                    'QueryCategory': category,
                    '_mutation_type': mutation_type
                })
                data_id += 1
                
    df = pd.DataFrame(dataset)
    if '_mutation_type' in df.columns:
        df = df.drop(columns=['_mutation_type'])
        
    output_excel = os.path.join(tmp_dir, 'generated_dataset.xlsx')
    if len(df) > 0:
        df.to_excel(output_excel, index=False)
    else:
        df = pd.DataFrame(columns=['DataID', 'GraphQLSchemaName', 'GraphQLQuery', 'GraphQLQueryVariables', 'QueryCategory'])
        df.to_excel(output_excel, index=False)
        
    return FileResponse(output_excel, filename="autographql_dataset.xlsx")

@app.get("/api/datasets/train")
def download_train_dataset():
    file_path = os.path.join(root_dir, "datasets", "train_data.xlsx")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="train_data.xlsx")
    return {"error": "Training dataset not found."}

@app.get("/api/datasets/test")
def download_test_dataset():
    file_path = os.path.join(root_dir, "datasets", "test_data.xlsx")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="test_data.xlsx")
    return {"error": "Testing dataset not found."}

@app.get("/api/paper")
def download_paper():
    file_path = os.path.join(root_dir, "docs", "autographql.pdf")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename="autographql.pdf")
    return {"error": "Paper PDF not found."}
