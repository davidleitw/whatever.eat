import os
from typing import Annotated, Optional
from contextlib import contextmanager

from typing_extensions import TypedDict
from src.config.settings import config

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from langchain.chat_models import init_chat_model


class State(TypedDict):
    """State definition for the chat bot graph."""
    messages: Annotated[list, add_messages]


class ChatBotManager:
    """
    Manages the lifecycle of the chat bot components including LLM initialization
    and graph setup with proper resource management.
    """
    
    def __init__(self, model_name: str = "openai:gpt-4.1"):
        """
        Initialize the ChatBotManager.
        
        Args:
            model_name: The model identifier for the LLM
        """
        self.model_name = model_name
        self._llm = None
        self._graph_builder = None
        self._graph = None
        self._initialized = False
    
    def _ensure_api_key(self) -> None:
        """Ensure OpenAI API key is set in environment variables."""
        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = config.OPENAI_API_KEY
    
    def initialize(self) -> None:
        """Initialize the chat bot components."""
        if self._initialized:
            return
            
        self._ensure_api_key()
        self._llm = init_chat_model(model=self.model_name)
        self._graph_builder = self._setup_graph()
        self._initialized = True
    
    def _setup_graph(self) -> StateGraph:
        """
        Set up the state graph with chat bot node.
        
        Returns:
            Configured StateGraph instance
        """
        graph_builder = StateGraph(State)
        graph_builder.add_node("chat_bot", self._chat_bot_handler)
        graph_builder.add_edge(START, "chat_bot")
        return graph_builder
    
    def _chat_bot_handler(self, state: State) -> dict:
        """
        Handle chat bot processing for a given state.
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with new messages
        """
        if not self._initialized:
            raise RuntimeError("ChatBotManager must be initialized before use")
        return {"messages": [self._llm.invoke(state["messages"])]}
    
    def get_graph_builder(self) -> StateGraph:
        """
        Get the configured graph builder.
        
        Returns:
            StateGraph instance
            
        Raises:
            RuntimeError: If manager is not initialized
        """
        if not self._initialized:
            raise RuntimeError("ChatBotManager must be initialized before use")
        return self._graph_builder
    
    def build_graph(self) -> StateGraph:
        """
        Build and return the complete graph.
        
        Returns:
            Compiled StateGraph
        """
        if not self._graph:
            graph_builder = self.get_graph_builder()
            # Add any additional graph configuration here
            self._graph = graph_builder.compile()
        return self._graph
    
    def cleanup(self) -> None:
        """Clean up resources and reset state."""
        self._llm = None
        self._graph_builder = None
        self._graph = None
        self._initialized = False

    def event_loop(self) -> None:
        if not self._initialized:
            raise RuntimeError("ChatBotManager must be initialized before use")

        graph = self._graph_builder.compile()


    @contextmanager
    def managed_session(self):
        """
        Context manager for automatic resource management.
        
        Usage:
            with ChatBotManager().managed_session() as manager:
                graph = manager.build_graph()
                # Use the graph...
        """
        try:
            self.initialize()
            yield self
        finally:
            self.cleanup()


# Factory function for creating manager instances
def create_chat_bot_manager(model_name: str = "openai:gpt-4.1") -> ChatBotManager:
    """
    Factory function to create a ChatBotManager instance.
    
    Args:
        model_name: The model identifier for the LLM
        
    Returns:
        ChatBotManager instance
    """
    return ChatBotManager(model_name=model_name)


# Convenience function for backward compatibility
def setup_graph() -> StateGraph:
    """
    Legacy function for backward compatibility.
    Creates and initializes a ChatBotManager to return a graph builder.
    
    Returns:
        StateGraph instance
        
    Note:
        This function is provided for backward compatibility.
        Consider using ChatBotManager directly for better resource management.
    """
    manager = create_chat_bot_manager()
    manager.initialize()
    return manager.get_graph_builder()





