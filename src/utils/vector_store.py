"""Vector store utility for RAG capabilities."""
import os
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.config.env import config

class VectorStore:
    """Vector store for document retrieval."""

    def __init__(self, persist_directory: str = "data/chroma_db"):
        """Initialize vector store.

        Args:
            persist_directory: Directory to persist vector store
        """
        self.persist_directory = persist_directory
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize embeddings with Google's embedding model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=config.GOOGLE_API_KEY,
            model_name="models/embedding-001"
        )

        # Initialize vector store
        self._init_vector_store()

    def _init_vector_store(self):
        """Initialize or load the vector store."""
        # Check if the directory contains Chroma files
        is_empty = not any(f.startswith('chroma-') for f in os.listdir(self.persist_directory)) if os.path.exists(self.persist_directory) else True

        if not is_empty:
            print(f"Loading existing Chroma DB from {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            print(f"Creating new Chroma DB in {self.persist_directory}")
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )

    def add_documents_from_directory(self, directory_path: str):
        """Add all documents from a directory to the vector store.

        Args:
            directory_path: Path to directory containing documents
        """
        if not os.path.isdir(directory_path):
            raise ValueError(f"Directory not found: {directory_path}")

        print(f"Loading documents from directory: {directory_path}")

        # Create loaders for PDF and text files
        pdf_loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader
        )

        text_loader = DirectoryLoader(
            directory_path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )

        # Load documents
        pdf_documents = pdf_loader.load()
        text_documents = text_loader.load()
        documents = pdf_documents + text_documents

        if not documents:
            print(f"No documents found in {directory_path}")
            return

        print(f"Loaded {len(documents)} documents: {len(pdf_documents)} PDFs and {len(text_documents)} text files")

        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )

        # Split documents into chunks
        splits = text_splitter.split_documents(documents)

        # Add to vector store
        self.vectorstore.add_documents(splits)
        self.vectorstore.persist()

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
        self.vectorstore.persist()

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