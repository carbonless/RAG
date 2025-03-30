# Multi-RAG Management System

A Flask-based web application for managing multiple Retrieval-Augmented Generation (RAG) systems. This application allows you to create, manage, and query multiple RAGs, each with its own document collection and vector index.

## Features

- Create and manage multiple RAGs
- Upload and manage documents for each RAG
- Build and update vector indexes
- Interactive chat interface for querying RAGs
- REST API for programmatic access
- File management system for each RAG
- Storage status monitoring

## Prerequisites

- Python 3.8+
- OpenAI API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multi-rag-manager.git
cd multi-rag-manager
```

2. Create and activate a virtual environment:
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the server:
```bash
python main.py
```

2. Access the web interface at `http://localhost:8000`

3. Create a new RAG or use existing ones:
   - Click "Create New RAG" to add a new RAG
   - Upload documents to the RAG
   - Build the index
   - Use the chat interface to query the RAG

## API Endpoints

### Query a RAG
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"rag_id": "your_rag_id", "query": "your question"}'
```

### List Files
```bash
curl http://localhost:8000/api/your_rag_id/files
```

### Upload File
```bash
curl -X POST http://localhost:8000/api/your_rag_id/files \
  -F "file=@/path/to/your/file.pdf"
```

### Build Index
```bash
curl -X POST http://localhost:8000/api/your_rag_id/index
```

### Check Storage Status
```bash
curl http://localhost:8000/api/your_rag_id/storage_status
```

## Project Structure

```
multi-rag-manager/
├── main.py              # Main Flask application
├── requirements.txt     # Python dependencies
├── .env                # Environment variables
├── templates/          # HTML templates
│   ├── index.html     # Main page
│   └── rag_interface.html  # RAG interface
├── data/              # Document storage
│   └── your_rag_id/   # RAG-specific documents
└── storage/           # Vector index storage
    └── your_rag_id/   # RAG-specific indexes
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 