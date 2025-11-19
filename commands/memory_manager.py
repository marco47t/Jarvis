# commands/memory_manager.py
import chromadb
import uuid
import logging
from config import DATA_DIR

logger = logging.getLogger(__name__)

class MemoryManager:
    """Handles the agent's long-term memory using a vector database."""
    def __init__(self):
        try:
            # Setup a persistent client. Data will be stored in the 'data/chroma_db' directory.
            self.client = chromadb.PersistentClient(path=f"{DATA_DIR}/chroma_db")
            
            # Get or create the collection. This is like a table in a traditional DB.
            # We'll use two collections: one for task memories, one for user preferences.
            self.memory_collection = self.client.get_or_create_collection(name="agent_memories")
            self.profile_collection = self.client.get_or_create_collection(name="user_profile")
            
            logger.info("MemoryManager initialized successfully with ChromaDB.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB. Long-term memory will be disabled. Error: {e}", exc_info=True)
            self.client = None

    def add_memory(self, task_summary: str, tools_used: list, final_result: str):
        """Adds a memory of a completed task to the database."""
        if not self.client:
            return

        try:
            unique_id = str(uuid.uuid4())
            document_content = (
                f"Task Summary: {task_summary}\n"
                f"Tools Used: {', '.join(tools_used)}\n"
                f"Final Result: {final_result}"
            )
            
            self.memory_collection.add(
                documents=[document_content],
                metadatas=[{"tools_used": ', '.join(tools_used)}],
                ids=[unique_id]
            )
            logger.info(f"Added new memory to collection: {unique_id}")
        except Exception as e:
            logger.error(f"Failed to add memory to ChromaDB: {e}", exc_info=True)

    def retrieve_relevant_memories(self, query: str, n_results: int = 3) -> list[str]:
        """Retrieves the most relevant memories for a given query."""
        if not self.client:
            return ["Long-term memory is currently offline."]

        try:
            results = self.memory_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results['documents'][0] if results and results['documents'] else []
        except Exception as e:
            logger.error(f"Failed to query memories from ChromaDB: {e}", exc_info=True)
            return [f"Error retrieving memories: {e}"]
            
    def save_user_preference(self, key: str, value: str):
        """Saves or updates a user preference."""
        if not self.client:
            return
            
        try:
            # Use the key as the ID to ensure it's overwritable (upsert)
            self.profile_collection.upsert(
                documents=[value],
                metadatas=[{"type": "user_preference"}],
                ids=[key]
            )
            logger.info(f"Saved/Updated user preference: {key} = {value}")
        except Exception as e:
            logger.error(f"Failed to save preference to ChromaDB: {e}", exc_info=True)

    def get_all_preferences(self) -> dict:
        """Retrieves all stored user preferences."""
        if not self.client:
            return {}
        try:
            # We get all items and format them as a dictionary.
            prefs = self.profile_collection.get()
            return {
                pref_id: doc 
                for pref_id, doc in zip(prefs['ids'], prefs['documents'])
            } if prefs else {}
        except Exception as e:
            logger.error(f"Failed to get preferences from ChromaDB: {e}", exc_info=True)
            return {}