from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
import os
import json
from llama_index.core import StorageContext, load_index_from_storage, VectorStoreIndex, SimpleDirectoryReader
from openai import OpenAI
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
CONFIG_FILE = 'rag_config.json'
DEFAULT_RAGS = {
    'ng911': 'NG911',
    'arlington_zoning': 'Arlington Zoning RAG'
}

def load_rag_config():
    """Load RAG configuration from file, ensuring default RAGs exist."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Merge with default RAGs to ensure they exist
            for rag_id, rag_name in DEFAULT_RAGS.items():
                if rag_id not in config:
                    config[rag_id] = rag_name
            return config
    return DEFAULT_RAGS.copy()

def save_rag_config(config):
    """Save RAG configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=OPENAI_API_KEY)

# Load RAG configuration
RAGS = load_rag_config()

def get_rag_paths(rag_name):
    """Get the data and storage paths for a specific RAG"""
    base_path = os.path.join(os.getcwd(), rag_name)
    return {
        'data': os.path.join(base_path, 'data'),
        'storage': os.path.join(base_path, 'storage')
    }

def ensure_rag_directories(rag_name):
    """Create necessary directories for a RAG if they don't exist"""
    paths = get_rag_paths(rag_name)
    os.makedirs(paths['data'], exist_ok=True)
    os.makedirs(paths['storage'], exist_ok=True)
    return paths

def get_rag_index(rag_name):
    """Load or create the index for a specific RAG"""
    paths = get_rag_paths(rag_name)
    storage_path = paths['storage']
    
    if os.path.exists(os.path.join(storage_path, 'docstore.json')):
        storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        return load_index_from_storage(storage_context=storage_context)
    else:
        return None

def build_rag_index(rag_name):
    """Build or rebuild the index for a specific RAG."""
    paths = get_rag_paths(rag_name)
    try:
        # Load existing documents if any
        existing_docs = []
        if os.path.exists(os.path.join(paths['storage'], 'docstore.json')):
            storage_context = StorageContext.from_defaults(persist_dir=paths['storage'])
            existing_index = load_index_from_storage(storage_context)
            if existing_index:
                existing_docs = existing_index.docstore.docs

        # Load all documents from data directory
        documents = SimpleDirectoryReader(paths['data']).load_data()
        
        # Create new index with all documents
        index = VectorStoreIndex.from_documents(documents)
        
        # Persist the new index
        index.storage_context.persist(persist_dir=paths['storage'])
        
        # Log the operation
        print(f"Index built for {rag_name}:")
        print(f"- Total documents: {len(documents)}")
        print(f"- Existing documents: {len(existing_docs)}")
        print(f"- New documents: {len(documents) - len(existing_docs)}")
        
        return True, f"Index built successfully with {len(documents)} documents"
    except Exception as e:
        print(f"Error building index for {rag_name}: {str(e)}")
        return False, str(e)

@app.route('/')
def index():
    """Display the main page with all RAGs."""
    rags = load_rag_config()
    return render_template('index.html', rags=rags)

@app.route('/rag/<rag_id>')
def rag_interface(rag_id):
    """Display the interface for a specific RAG."""
    rags = load_rag_config()
    if rag_id not in rags:
        return "RAG not found", 404
    return render_template('rag_interface.html', rag_id=rag_id, rag_name=rags[rag_id])

@app.route('/create_rag', methods=['POST'])
def create_rag():
    """Create a new RAG."""
    data = request.get_json()
    rag_id = data.get('rag_id')
    rag_name = data.get('rag_name')
    
    if not rag_id or not rag_name:
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    config = load_rag_config()
    if rag_id in config:
        return jsonify({'success': False, 'error': 'RAG ID already exists'})
    
    # Create necessary directories
    os.makedirs(f'storage/{rag_id}', exist_ok=True)
    os.makedirs(f'data/{rag_id}', exist_ok=True)
    
    # Update configuration
    config[rag_id] = rag_name
    save_rag_config(config)
    
    return jsonify({'success': True})

@app.route('/delete_rag', methods=['POST'])
def delete_rag():
    """Delete a RAG."""
    data = request.get_json()
    rag_id = data.get('rag_id')
    
    if not rag_id:
        return jsonify({'success': False, 'error': 'Missing RAG ID'})
    
    if rag_id in DEFAULT_RAGS:
        return jsonify({'success': False, 'error': 'Cannot delete default RAG'})
    
    config = load_rag_config()
    if rag_id not in config:
        return jsonify({'success': False, 'error': 'RAG not found'})
    
    # Remove directories
    import shutil
    if os.path.exists(f'storage/{rag_id}'):
        shutil.rmtree(f'storage/{rag_id}')
    if os.path.exists(f'data/{rag_id}'):
        shutil.rmtree(f'data/{rag_id}')
    
    # Update configuration
    del config[rag_id]
    save_rag_config(config)
    
    return jsonify({'success': True})

@app.route('/query', methods=['POST'])
def query():
    """Handle queries for any RAG."""
    data = request.get_json()
    rag_id = data.get('rag_id')
    query_text = data.get('query')
    
    if not rag_id or not query_text:
        return jsonify({'error': 'Missing required fields'})
    
    try:
        # Load the appropriate RAG index
        paths = get_rag_paths(rag_id)
        storage_path = paths['storage']
        
        if not os.path.exists(os.path.join(storage_path, 'docstore.json')):
            return jsonify({'error': 'RAG index not found. Please upload and index documents first.'})
        
        storage_context = StorageContext.from_defaults(persist_dir=storage_path)
        index = load_index_from_storage(storage_context)
        
        # Query the index
        query_engine = index.as_query_engine()
        response = query_engine.query(query_text)
        
        return jsonify({'response': str(response)})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/<rag_name>/files', methods=['GET'])
def list_files(rag_name):
    """List files in the RAG's data directory."""
    if rag_name not in RAGS:
        return jsonify({'error': 'RAG not found'}), 404
    
    paths = get_rag_paths(rag_name)
    data_path = paths['data']
    
    if not os.path.exists(data_path):
        return jsonify({'success': True, 'files': []})
    
    files = []
    for filename in os.listdir(data_path):
        file_path = os.path.join(data_path, filename)
        if os.path.isfile(file_path):
            files.append({
                'name': filename,
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path)
            })
    return jsonify({'success': True, 'files': files})

@app.route('/api/<rag_name>/files', methods=['POST'])
def upload_file(rag_name):
    """Upload a file to the RAG's data directory."""
    if rag_name not in RAGS:
        return jsonify({'success': False, 'error': 'RAG not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    paths = ensure_rag_directories(rag_name)
    filename = secure_filename(file.filename)
    file_path = os.path.join(paths['data'], filename)
    file.save(file_path)
    
    return jsonify({'success': True, 'message': 'File uploaded successfully'})

@app.route('/api/<rag_name>/files/<filename>', methods=['DELETE'])
def delete_file(rag_name, filename):
    """Delete a file from the RAG's data directory."""
    if rag_name not in RAGS:
        return jsonify({'success': False, 'error': 'RAG not found'}), 404
    
    paths = get_rag_paths(rag_name)
    file_path = os.path.join(paths['data'], secure_filename(filename))
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    try:
        os.remove(file_path)
        return jsonify({'success': True, 'message': 'File deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to delete file: {str(e)}'}), 500

@app.route('/api/<rag_name>/index', methods=['POST'])
def build_index(rag_name):
    """Build or rebuild the index for a specific RAG."""
    if rag_name not in RAGS:
        return jsonify({'success': False, 'error': 'RAG not found'}), 404
    
    success, message = build_rag_index(rag_name)
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 500

@app.route('/api/<rag_name>/storage_status')
def check_storage_status(rag_name):
    """Check if a RAG has an index."""
    if rag_name not in RAGS:
        return jsonify({'error': 'RAG not found'}), 404
    
    paths = get_rag_paths(rag_name)
    storage_path = paths['storage']
    
    has_storage = os.path.exists(os.path.join(storage_path, 'docstore.json'))
    return jsonify({'has_storage': has_storage})

if __name__ == '__main__':
    # Ensure all RAG directories exist
    for rag_name in RAGS:
        ensure_rag_directories(rag_name)
    app.run(host='0.0.0.0', port=8000, debug=True)
