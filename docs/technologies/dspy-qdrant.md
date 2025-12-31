# DSPy-Qdrant

## Overview

**DSPy-Qdrant** is a Qdrant-powered custom retriever module for DSPy that enables semantic search capabilities within the DSPy framework. It allows developers to retrieve the top-k most relevant documents from a Qdrant collection using sentence embedding models for vectorization.

- **Package Name**: DSPY-QDRANT
- **Latest Version**: 0.1.4
- **Release Date**: December 19, 2025
- **License**: Apache License Version 2.0
- **Author/Maintainer**: Anush008
- **Python Requirement**: >=3.11

## Installation

To install DSPy-Qdrant, use pip:

```bash
pip install dspy-qdrant
```

## Features

- Qdrant-powered custom retriever module for DSPy
- Enables semantic search capabilities
- Retrieves top-k most relevant documents from a Qdrant collection
- Uses sentence embedding models for vectorization
- Integrates with DSPy framework for language model programming
- Compatible with Qdrant vector database

## Usage

### Basic Usage

```python
from dspy_qdrant import QdrantRM
```

### Implementation in a Module

```python
import dspy
from qdrant_client import QdrantClient
from dspy_qdrant import QdrantRM

qdrant_client = QdrantClient()

class MyModule(dspy.Module):
    def __init__(self, num_passages: int = 5):
        super().__init__()
        self.num_passages = num_passages

    def forward(self, question: str):
        retrieve = QdrantRM(
            qdrant_collection_name="my_collection_name",
            qdrant_client=qdrant_client,
            k=self.num_passages
        )
        # Do something with results...
```

## Parameters for QdrantRM Class

| Parameter | Type | Description | Default |
| ----------- | ------ | ------------- | --------- |
| qdrant_collection_name | str | Name of the Qdrant collection used for retrieval | Required |
| qdrant_client | QdrantClient | An initialized instance of qdrant_client.QdrantClient | Required |
| k | int | Number of top documents to retrieve per query | 3 |
| document_field | str | Field in the Qdrant payload that contains the raw document content | "document" |
| vectorizer | BaseSentenceVectorizer | Embedding model for vectorizing queries | Uses FastEmbedVectorizer if not provided |
| vector_name | str | Name of the vector field in Qdrant collection to use for search | Defaults to the first found |

## Integration Capabilities

- Works with DSPy (framework for programming language models)
- Integrates with Qdrant vector database
- Uses sentence embedding models for semantic search
- Compatible with QdrantClient for connecting to Qdrant instances
- Enables seamless document retrieval in language model applications

## Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [DSPy GitHub repository](https://github.com/stanfordnlp/dspy)

## Package Details

- Source Distribution: dspy_qdrant-0.1.4.tar.gz (120.6 kB)
- Built Distribution: dspy_qdrant-0.1.4-py3-none-any.whl (12.9 kB)

The package provides a semantic search retriever that works within the DSPy framework, allowing developers to leverage Qdrant's vector search capabilities for document retrieval in language model applications.
