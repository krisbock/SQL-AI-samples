# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from promptflow.core import tool
from promptflow.connections import CustomConnection
import requests
import json
from openai import AzureOpenAI
import pyodbc
import pandas as pd


def generate_embeddings(text, conn: CustomConnection):
    # initiate client
    client = AzureOpenAI(
        azure_endpoint = conn['AZURE_OPENAI_API_EMB_BASE'],
        api_key = conn['AZURE_OPENAI_API_EMB_KEY'],
        api_version = conn['AZURE_OPENAI_API_EMB_VERSION'],
    )

    response = client.embeddings.create(input=text, model=conn['AZURE_OPENAI_API_EMB_DEPLOYMENT'])
    embeddings = response.data[0].embedding
    return embeddings

def execute_sql(sql_query: str, conn_db: CustomConnection):

    conn_string = conn_db['CONNECTION-STRING']
    with pyodbc.connect(conn_string,autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            query_out = cursor.fetchall()

    toReturn = pd.DataFrame((tuple(t) for t in query_out)) 
    toReturn.columns = [column[0] for column in cursor.description]

    return toReturn

@tool
def get_product(search_text: str, sql_query_prep: dict, conn: CustomConnection, conn_db: CustomConnection, top_k:int) -> str:
    search_service = conn['AZURE_SEARCH_ENDPOINT']#"sqldricopilot"
    index_name =  conn['AZURE_SEARCH_INDEX']#"promptflow-demo-product-description"
    search_key = conn['ACS-SEARCH-KEY']
    api_version = conn['AZURE_SEARCH_API_VERSION']

    headers = {
            'Content-Type': 'application/json',
            'api-key': search_key,
        }
    params = {
        'api-version': api_version,
    }
    body = {
        "vectorQueries": [
            {
            "kind": "vector",
            "vector": generate_embeddings(text = search_text, conn = conn),
            "fields": "ProductCategoryNameVector, DescriptionVector",
            "k": top_k
            },
        ],
        "search": search_text,
        "select": "ProductId, ProductCategoryName, Name, ProductNumber, Color, ListPrice, Size, ProductCategoryID, ProductModelID, ProductDescriptionID, Description",
        "top": top_k,
    }
    response = requests.post(
        f"{search_service}/indexes/{index_name}/docs/search", headers=headers, params=params, json=body)
    response_json = response.json()['value']

    list_prod_id = list(map(lambda x: x['ProductId'], response_json))
    list_prod_id = str(tuple(list_prod_id)).replace(",)", ")")
    query_product = sql_query_prep['query_prod_byID'].replace("{list_product}", list_prod_id)

    try:
        out_df = execute_sql(sql_query=query_product, conn_db=conn_db)
        out_json = out_df.to_json(orient="records")
        out_dict = json.loads(out_json)
    except:
        out_dict = {}

    return out_dict