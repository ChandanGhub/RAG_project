
# python components/test.py


from __future__ import annotations

import os
import sqlite3
import tempfile
from typing import Annotated, Any, Dict, Optional, TypedDict
from dotenv import load_dotenv

# pypdf loader ok
from langchain_community.document_loaders import PyPDFLoader 

# Text splitter ok
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ollama model ok
from langchain_ollama import ChatOllama, OllamaEmbeddings

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
import requests

loader = PyPDFLoader("sample-folder/Introduction to Machine Learning with Python.pdf")
documents = loader.load()
print(len(documents))
print(documents[55].page_content)




''' git add .
git commit -m "comment""
git push -u origin main'''