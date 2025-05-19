# Module for Azure Cosmos DB operations:
# - Manage singleton client, database, and container
# - Configure container with vector index for embeddings
# - Upsert and retrieve code snippet documents with embeddings
# - Perform vector similarity search using DiskANN index

import os
import logging
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants for Cosmos DB configuration
COSMOS_DATABASE_NAME = os.environ.get("COSMOS_DATABASE_NAME", "dev-snippet-db")
COSMOS_CONTAINER_NAME = os.environ.get("COSMOS_CONTAINER_NAME", "code-snippets")
COSMOS_VECTOR_TOP_K = int(os.environ.get("COSMOS_VECTOR_TOP_K", "30"))

# Singleton references for client, database, and container caching
# This ensures we reuse connections across calls
_cosmos_client = None
_database = None
_container = None

# Gets or creates the singleton Cosmos client, caching it for reuse
async def get_cosmos_client():
    """
    Gets or creates the singleton Cosmos client.
    """
    global _cosmos_client
    if _cosmos_client is None:
        logger.debug("Creating Cosmos client")
        _cosmos_client = CosmosClient(
            url=os.environ["COSMOS_ENDPOINT"],
            credential=DefaultAzureCredential()
        )
    return _cosmos_client

# Gets or creates the singleton Cosmos database reference
async def get_database():
    """
    Gets or creates the singleton database.
    """
    global _database
    if _database is None:
        client = await get_cosmos_client()
        _database = await client.create_database_if_not_exists(COSMOS_DATABASE_NAME)
    return _database

# Gets or creates the Cosmos DB container with proper partition key and vector index configuration
# The container is set up with a partition on /name and a vectorEmbeddingPolicy on /embedding
async def get_container():
    """
    Gets or creates the Cosmos DB container with proper partition key and vector index configuration.
    
    The container is configured with:
    - Partition key: /name (for now, will be migrated to /projectId later)
    - Vector embedding policy: int8, 1536 dimensions, cosine distance
    - Excluded path: /embedding/* (to avoid regular indexing of vector data)
    
    Returns:
        The container client
        
    Raises:
        Exception: If container creation or configuration fails
    """
    global _container
    if _container is None:
        try:
            logger.info(f"Getting container '{COSMOS_CONTAINER_NAME}' from database '{COSMOS_DATABASE_NAME}'")
            
            database = await get_database()
            
            # Create container with vector index configuration
            logger.debug("Creating container with vector index configuration")
            _container = await database.create_container_if_not_exists(
                id=COSMOS_CONTAINER_NAME,
                partition_key=PartitionKey(path="/name"),
                indexing_policy={
                    "indexingMode": "consistent",
                    "automatic": True,
                    "includedPaths": [
                        {
                            "path": "/*"
                        }
                    ],
                    "excludedPaths": [
                        {
                            "path": "/embedding/*"
                        }
                    ],
                    "vectorEmbeddingPolicy": {
                        "vectorEmbeddings": [
                            {
                                "path": "/embedding",
                                "dataType": "int8",
                                "dimensions": 1536,
                                "distanceFunction": "cosine"
                            }
                        ]
                    }
                }
            )
            
            logger.info("Successfully configured container with vector index")
        except Exception as e:
            logger.error(f"Error configuring Cosmos container: {str(e)}", exc_info=True)
            raise
    return _container

# Closes all Cosmos DB connections and resets cached client, database, and container
async def close_connections():
    """
    Closes all Cosmos DB connections.
    """
    global _cosmos_client, _database, _container
    if _cosmos_client is not None:
        await _cosmos_client.close()
        _cosmos_client = None
        _database = None
        _container = None
        logger.info("Closed Cosmos DB connections")

# Upserts a document into Cosmos DB with vector embeddings
# The document includes id, name, projectId, code, type, and embedding fields
async def upsert_document(name: str, project_id: str, code: str, embedding: list) -> dict:
    """
    Upserts a document into Cosmos DB with vector embeddings.
    
    The document structure:
    {
        "id": name,
        "name": name,  # partition key
        "projectId": project_id,
        "code": code,
        "type": "code-snippet",
        "embedding": embedding  # int8 quantized vector
    }
    
    Args:
        name: The name of the snippet (used as id and partition key)
        project_id: The project ID
        code: The code content
        embedding: The int8 quantized embedding vector
        
    Returns:
        The created/updated document
        
    Raises:
        Exception: If document upsert fails
    """
    try:
        logger.info(f"Upserting document '{name}' in project '{project_id}'")
        logger.debug(f"Code length: {len(code)} chars, embedding length: {len(embedding)}")
        
        container = await get_container()
        
        # Prepare the document
        document = {
            "id": name,
            "name": name,  # This field is used for partition key
            "projectId": project_id,
            "code": code,
            "type": "code-snippet",
            "embedding": embedding  # Store the embedding vector
        }
        
        # Upsert the document
        logger.debug("Executing upsert operation")
        result = await container.upsert_item(body=document)
        
        logger.info(f"Successfully upserted document with id '{name}'")
        return result
    except Exception as e:
        logger.error(f"Error upserting document: {str(e)}", exc_info=True)
        raise

# Retrieves a snippet by its id (partition key) from Cosmos DB
# Returns the document or None if not found
async def get_snippet_by_id(name: str) -> dict:
    """
    Gets a snippet from Cosmos DB by id.
    
    Args:
        name: The name (id) of the snippet to retrieve
        
    Returns:
        The retrieved document or None if not found
        
    Raises:
        Exception: If document retrieval fails
    """
    try:
        logger.info(f"Retrieving snippet with id '{name}'")
        
        container = await get_container()
        
        try:
            result = await container.read_item(
                item=name,
                partition_key=name
            )
            logger.info(f"Successfully retrieved snippet with id '{name}'")
            return result
        except CosmosResourceNotFoundError:
            logger.info(f"No snippet found with id '{name}'")
            return None
                
    except Exception as e:
        logger.error(f"Error retrieving snippet: {str(e)}", exc_info=True)
        raise

# Performs vector similarity search using Cosmos DB's DiskANN index
# Returns the top-k similar snippet documents with their distance scores
async def query_similar_snippets(
    query_vector: list[float], *, project_id: str, k: int = COSMOS_VECTOR_TOP_K
) -> list[dict]:
    """
    Performs vector similarity search using Cosmos DB's DiskANN index.
    
    The query:
    ```sql
    SELECT TOP @k c.id, c.code, 
    VectorDistance(c.embedding, @vec) AS score 
    FROM c WHERE c.projectId = @pid 
    ORDER BY VectorDistance(c.embedding, @vec)
    ```
    
    Args:
        query_vector: The query embedding vector
        project_id: The project ID to search within
        k: Number of results to return
        
    Returns:
        List of matching documents with their scores:
        [
            {"id": "snippet-1", "code": "...", "score": 0.95},
            {"id": "snippet-2", "code": "...", "score": 0.92},
            ...
        ]
        
    Raises:
        Exception: If query execution fails
    """
    try:
        logger.info(f"Executing vector similarity search (k={k}, project_id={project_id})")
        logger.debug(f"Query vector length: {len(query_vector)}")
        
        container = await get_container()

        params = [
            {"name": "@vec", "value": query_vector},
            {"name": "@k", "value": k},
            {"name": "@pid", "value": project_id},
        ]

        sql = (
            "SELECT TOP @k c.id, c.code, "
            "VectorDistance(c.embedding, @vec) AS score "
            "FROM c WHERE c.projectId = @pid "
            "ORDER BY VectorDistance(c.embedding, @vec)"
        )

        logger.debug(f"Executing SQL query: {sql}")
        items_iterable = container.query_items(
            query=sql,
            parameters=params
        )
        
        results = [item async for item in items_iterable]
        logger.info(f"Found {len(results)} similar snippets")
        
        return results
    except Exception as e:
        logger.error(f"Error in vector similarity search: {str(e)}", exc_info=True)
        raise 