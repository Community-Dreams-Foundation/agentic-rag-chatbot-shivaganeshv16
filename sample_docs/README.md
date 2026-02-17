# Sample Documents

This folder contains sample documents for testing the RAG pipeline.

## Files

- `sample_technical_doc.md` - A sample technical document about microservices architecture

## Usage

Upload these files through the web UI (drag and drop) or use the API:

```bash
curl -X POST http://localhost:8001/api/upload \
  -F "file=@sample_docs/sample_technical_doc.md"
```
