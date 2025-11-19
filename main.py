import os
# from typing import Dict
import httpx

from mcp.server.fastmcp import FastMCP
import json
import logging

import asyncio

# constants
# API_BASE_URL = 'https://api.reliefweb.int/v2'
API_BASE_URL = "http://localhost:8080/v2"

# Initialise FastMCP server
mcp = FastMCP("reliefweb")


def get_config() -> dict[str, str]:
    return {
        "appname": os.environ.get("appname", "")        
    }


def make_queryapi(query: str, country_name: str, start_date: str) -> str : 

    query_api = ""

    if query != "":
        query_api +=  query

    if country_name:
        query_api += (" AND " if query else "") + f"country.name:{country_name}"

    if start_date:
        query_api += (" AND " if query_api else "") + f"date.created:>={start_date}"

    return query_api

def parse_result_getdocs(result: str) -> list:
    json_result = json.loads(result)

    if "data" in json_result : 
        disasters = json_result["data"]
        documents: list= []
        for disaster in disasters :
            documents.append(disaster.get("href"))

    return documents

async def make_request(url: str, params: dict) -> str:
    
    logging.info(f"Parameters: {params}")
    print(f"Parameters: {params}")

    async with httpx.AsyncClient() as client:

        try:
            if params:
                response = await client.get(url, params=params, timeout=30.0, follow_redirects=True)
            else:
                response = await client.get(url, timeout=30.0, follow_redirects=True)

            logging.info(f"Response status: {response.raise_for_status()}")
            logging.debug(response.json())
            text = response.text
            logging.info(text)
            return text
        except Exception:
            return json.dumps({"error": "request failed"})




@mcp.tool(
    name="search_disasters",
    description="get disaster information from the United Nations Emergency Events"
                "Classification")
async def search_disasters(query: str, country_name: str, start_date: str) -> str: 
    url = f"{API_BASE_URL}/disasters"
    query_api = make_queryapi(query, country_name, start_date)

    config = get_config()
    params = {
        "appname": config["appname"],        
        "query[value]": query_api,
        "query[operator]": "AND",
        "preset": "latest",
        "profile": "minimal",
        "limit": 5,
    }
    # get the documents list result
    result = await make_request(url, params)


    # get the documents href
    doc_refs = parse_result_getdocs(result)

    documents: list= []
    for href in doc_refs :
        json_doc = await make_request(href, None)
        documents.append(json_doc)
    
    result = "[" + ','.join(documents) + "]"

    return result

@mcp.tool(
    name="search_reports",
    description="get report and update from ReliefWeb (United Nations emergency reports).")
async def search_reports(query: str, country_name: str, start_date: str) -> str: 
    url = f"{API_BASE_URL}/reports"
    query_api = make_queryapi(query, country_name, start_date)

    config = get_config()
    params = {
        "appname": config["appname"],        
        "query[value]": query_api,
        "query[operator]": "AND",
        "preset": "latest",
        "profile": "minimal",
        "limit": 5,
    }
    result = await make_request(url, params)
    
    # get the documents href
    doc_refs = parse_result_getdocs(result)

    documents: list= []
    for href in doc_refs :
        json_doc = await make_request(href, None)
        documents.append(json_doc)

    result = "[" + ','.join(documents) + "]"
  
    return result


def main(): 

    # check config from environment variables
    config = get_config()
    req_config = ["appname"]
    missing = [k for k in req_config if not config.get(k)]

    if missing:
        logging.error(f"Error: missing config: {', '.join(missing)}")
        exit(1)

    # Initialise and run the server
    mcp.run(transport="stdio")

 
    # result = asyncio.run(search_reports("earthquake", "Sudan", "2023-01-01"))
    # print (result)


if __name__ == "__main__":
    main()
    
    
