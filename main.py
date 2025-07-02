import os
from typing import Annotated

from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch

os.environ["TAVILY_API_KEY"] = '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'

tool = TavilySearch(max_results=2)
tools = [tool]
tool.invoke("What's a 'node' in LangGraph?")


class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


llm = init_chat_model("openai:gpt-4.1")
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

def stream(user_message: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_message}]}):
       for value in event.values():
           print(value)

if __name__ == "__main__":
   while True:
       try:
           user_message = input("User: ")
           if user_message.lower() in ["quit", "exit", "q"]:
               print("Goodbye!")
               break
           stream(user_message)
       except:
           # fallback if input() is not available
           user_message = "What do you know about LangGraph?"
           print("User: " + user_message)
           stream(user_message)
           break