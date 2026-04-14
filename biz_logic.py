import os
from dotenv import load_dotenv
from pinecone import Pinecone

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.llms.groq import Groq
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings

load_dotenv()

class BizSearchEngine:
    def __init__(self):
        # 1. Setup the AI Models
        self.llm = Groq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=os.getenv("GROQ_API_KEY"))
        self.embed_model = OllamaEmbedding(model_name="mxbai-embed-large")
        
        # ==========================================
        # 2. APPLY GLOBAL SETTINGS 
        # ==========================================
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        
        # Restrict the chunk size so it safely fits inside the mxbai-embed-large limit
        Settings.chunk_size = 384 
        
        # Allow a slight overlap so sentences at the edge of chunks don't lose context
        Settings.chunk_overlap = 50 
        # ==========================================

        # 3. Connect to Pinecone Cloud
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=pinecone_api_key)
        
        self.pinecone_index = self.pc.Index("bizsearch-index")
        
        # 4. Setup Vector Store
        self.vector_store = PineconeVectorStore(pinecone_index=self.pinecone_index)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # 5. Load Index
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model
            )
        except Exception:
            self.index = None

    def ingest_and_sync(self, file_path):
        """Reads a file and pushes the vectors straight to Pinecone."""
        try:
            print("📄 Reading document...")
            documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
            
            print("☁️ Generating embeddings and uploading to Pinecone...")
            self.index = VectorStoreIndex.from_documents(
                documents, 
                storage_context=self.storage_context,
                show_progress=True
            )
            return "✅ Report Successfully Synced to Cloud Vector DB!"
        except Exception as e:
            raise Exception(f"Failed to ingest: {str(e)}")

    def ask(self, search_query):
        # Safety check: ensure a document has been uploaded or an index exists
        if not self.index:
            return "⚠️ Please upload and sync a document before asking questions."

        # 1. Wrap the user's query in a strict formatting wrapper
        structured_prompt = f"""
        You are an expert business analyst. Answer the user's question based ONLY on the provided document context.

        CRITICAL FORMATTING RULES:
        1. Structure your answer professionally.
        2. Always use short, readable paragraphs.
        3. Use bullet points or numbered lists when explaining multiple items, steps, or features.
        4. Use **bold text** to highlight key metrics, important names, or core concepts.
        5. NEVER return a single, massive wall of text.

        User Question: {search_query}
        """
        
        # 2. Convert the index into a query engine and send the prompt!
        response = self.index.as_query_engine().query(structured_prompt)
        return str(response)

    def clear_data(self):
        """Instantly wipes all data from the Pinecone index."""
        try:
            # Tell Pinecone to delete all vectors
            self.pinecone_index.delete(delete_all=True)
            
            # Re-initialize the empty vector store
            self.vector_store = PineconeVectorStore(pinecone_index=self.pinecone_index)
            self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
            self.index = None
            return True
        except Exception as e:
            print(f"Clear Error: {str(e)}")
            return False