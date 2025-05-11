"""Vector store utility for RAG capabilities with Vertex AI."""
import os
import shutil
from typing import List, Dict, Any
import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.utils.embeddings_adapter import get_langchain_compatible_embeddings
from src.config.env import config

class VectorStore:
    """Vector store for document retrieval using Vertex AI embeddings."""
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        """Initialize vector store.
        
        Args:
            persist_directory: Directory to persist vector store
        """
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize embeddings with our adapter
        print(f"[DEBUG] VectorStore: Initializing embeddings adapter")
        print(f"[DEBUG] VectorStore: Embedding model = {config.EMBEDDING_MODEL}")
        try:
            self.embeddings = get_langchain_compatible_embeddings()
            print(f"[DEBUG] VectorStore: Successfully initialized embeddings adapter")
        except Exception as e:
            print(f"[ERROR] VectorStore: Failed to initialize embeddings adapter: {e}")
            print(f"[ERROR] VectorStore: Error type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] VectorStore: {traceback.format_exc()}")
            raise
        
        # Initialize vector store
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize or load the vector store."""
        # Clean up old Chroma DB if it exists but is from an incompatible version
        if os.path.exists(self.persist_directory):
            chroma_sqlite = os.path.join(self.persist_directory, "chroma.sqlite3")
            if os.path.exists(chroma_sqlite):
                try:
                    # Try to initialize with existing DB
                    client = chromadb.PersistentClient(path=self.persist_directory)
                    collection_names = client.list_collections()
                    print(f"Found existing Chroma DB with collections: {[c.name for c in collection_names]}")
                except Exception as e:
                    print(f"Found incompatible Chroma DB, recreating: {e}")
                    # Backup the old DB
                    backup_dir = f"{self.persist_directory}_backup"
                    if os.path.exists(backup_dir):
                        shutil.rmtree(backup_dir)
                    shutil.copytree(self.persist_directory, backup_dir)
                    print(f"Backed up old DB to {backup_dir}")
                    # Remove the old DB
                    shutil.rmtree(self.persist_directory)
                    os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize or create the Chroma client
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Get or create collection
        try:
            collection_name = "documents"
            collections = self.client.list_collections()
            collection_exists = any(c.name == collection_name for c in collections)

            if collection_exists:
                print(f"Loading existing Chroma collection '{collection_name}'")
            else:
                print(f"Creating new Chroma collection '{collection_name}'")

            # Create Chroma collection wrapper for LangChain
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=collection_name,
                embedding_function=self.embeddings
            )
        except Exception as e:
            print(f"Error initializing Chroma: {e}")
            import traceback
            print(traceback.format_exc())
            raise
    
    def add_documents_from_directory(self, directory_path: str):
        """Add all documents from a directory to the vector store.

        Args:
            directory_path: Path to directory containing documents
        """
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        print(f"Loading documents from directory: {directory_path}")

        # Get list of PDF and text files directly
        pdf_files = []
        txt_files = []

        # Use os.walk() for more control over which files are processed
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.pdf'):
                    pdf_files.append(file_path)
                elif file.lower().endswith('.txt'):
                    txt_files.append(file_path)

        # Deduplicate files (in case there are any duplicates)
        pdf_files = list(set(pdf_files))
        txt_files = list(set(txt_files))

        print(f"Found {len(pdf_files)} PDF files and {len(txt_files)} text files")

        # Load documents manually
        pdf_documents = []
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(pdf_file)
                pdf_documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading PDF {pdf_file}: {e}")

        text_documents = []
        for txt_file in txt_files:
            try:
                loader = TextLoader(txt_file)
                text_documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading text file {txt_file}: {e}")

        documents = pdf_documents + text_documents

        if not documents:
            print(f"No documents found in {directory_path}")
            return

        print(f"Loaded {len(documents)} documents: {len(pdf_documents)} pages from PDFs and {len(text_documents)} text files")
        
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        
        # Split documents into chunks
        splits = text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vectorstore.add_documents(splits)
        # No need to call persist() with newer Chroma versions
        # as they persist automatically

        print(f"Added {len(splits)} document chunks to vector store")
    
    def add_document(self, file_path: str):
        """Add a single document to the vector store.
        
        Args:
            file_path: Path to document file
        """
        if not os.path.isfile(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100
        )
        
        # Load document
        documents = []
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif file_path.endswith('.txt'):
            loader = TextLoader(file_path)
            documents = loader.load()
        else:
            print(f"Unsupported file format: {file_path}")
            return
        
        # Split document into chunks
        splits = text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vectorstore.add_documents(splits)
        # No need to call persist() with newer Chroma versions
        # as they persist automatically

        print(f"Added {len(splits)} chunks from {file_path} to vector store")
    
    def similarity_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of documents with content and metadata
        """
        docs = self.vectorstore.similarity_search(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return results