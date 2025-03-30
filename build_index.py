from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core import Settings
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create storage directory if it doesn't exist
os.makedirs("storage", exist_ok=True)

# Load documents from the data directory
documents = SimpleDirectoryReader("data").load_data()

# Create and store the index
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist(persist_dir="storage/rag_vector_index")

print("Index built and stored successfully!") 