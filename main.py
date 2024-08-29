import os
import warnings
from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.converters.txt import TextFileToDocument
from haystack.components.embedders import OpenAIDocumentEmbedder, OpenAITextEmbedder
from haystack.components.generators import OpenAIGenerator
from haystack.components.preprocessors.document_splitter import DocumentSplitter
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.routers import ConditionalRouter
from haystack.components.websearch.serper_dev import SerperDevWebSearch
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore

warnings.filterwarnings("ignore")

os.environ['OPENAI_API_KEY'] = "REPLACE_THIS_WITH_YOUR_OPENAI_API_KEY"
os.environ['SERPERDEV_API_KEY'] = "REPLACE_THIS_WITH_YOUR_SERPERDEV_API_KEY"

# Initialise an in-memory document store
document_store = InMemoryDocumentStore()

# Create ingestion pipeline to write embedded documents into the document store
converter = TextFileToDocument()
splitter = DocumentSplitter(split_by="passage", split_length=1, split_overlap=0)
embedder = OpenAIDocumentEmbedder()
writer = DocumentWriter(document_store=document_store)
ingestion_pipeline = Pipeline()
ingestion_pipeline.add_component("converter", converter)
ingestion_pipeline.add_component("splitter", splitter)
ingestion_pipeline.add_component("embedder", embedder)
ingestion_pipeline.add_component("writer", writer)

# Connect components of ingestion pipeline
ingestion_pipeline.connect("converter", "splitter")
ingestion_pipeline.connect("splitter", "embedder")
ingestion_pipeline.connect("embedder", "writer")

# Run ingestion pipeline
ingestion_pipeline.run({"converter": {"sources": ['data/novusmundus23.txt']}})

# Creae a prompt for RAG (the PromptBuilder component uses Jinja templating)
prompt_for_rag = """
You will be provided some context, followed by the file path and the page number that this context comes from.
Answer the question based on the context.
Add the file path and the page number to your answer.
If the answer is not in the content, reply with 'n/a'.
Context:
{% for doc in documents %}
   {{doc.content}} 
   file path: {{doc.meta['file_path']}}
   page number: {{doc.meta['page_number']}}
{% endfor %}
Question: {{query}}
Answer:
"""

# Create a prompt for websearch (used if RAG cannot generate a meaningful answer)
prompt_for_websearch = """
Answer the following query given the documents retrieved from the web.
Your answer should indicate that your answer was generated from websearch.
Add the sources to your answer.
Query: {{query}}
Documents:
{% for doc in documents %}
  {{doc.content}}
{% endfor %}
"""

# If RAG answer contains "n/a" then do websearch, otherwise RAG answer is final
routes = [
    {
        "condition": "{{'n/a' in replies[0]|lower}}",
        "output": "{{query}}",
        "output_name": "go_to_websearch",
        "output_type": str,
    },
    {
        "condition": "{{'n/a' not in replies[0]|lower}}",
        "output": "{{replies[0]}}",
        "output_name": "go_to_answer",
        "output_type": str,
    },
]

# Build a RAG pipeline with websearch as fall-back, if the answer cannot be provided by RAG
query_embedder = OpenAITextEmbedder()
retriever = InMemoryEmbeddingRetriever(document_store=document_store)
prompt_builder_for_rag = PromptBuilder(template=prompt_for_rag)
llm_for_rag = OpenAIGenerator(model="gpt-3.5-turbo")
websearch = SerperDevWebSearch()
prompt_builder_for_websearch = PromptBuilder(template=prompt_for_websearch)
llm_for_websearch = OpenAIGenerator(model="gpt-3.5-turbo")
rag_or_websearch = Pipeline()
rag_or_websearch.add_component("query_embedder", query_embedder)
rag_or_websearch.add_component("retriever", retriever)
rag_or_websearch.add_component("prompt_builder_for_rag", prompt_builder_for_rag)
rag_or_websearch.add_component("llm_for_rag", llm_for_rag)
rag_or_websearch.add_component("router", ConditionalRouter(routes=routes))
rag_or_websearch.add_component("websearch", websearch)
rag_or_websearch.add_component("prompt_builder_for_websearch", prompt_builder_for_websearch)
rag_or_websearch.add_component("llm_for_websearch", llm_for_websearch)
rag_or_websearch.connect("query_embedder.embedding", "retriever.query_embedding")
rag_or_websearch.connect("retriever.documents", "prompt_builder_for_rag.documents")
rag_or_websearch.connect("prompt_builder_for_rag", "llm_for_rag")
rag_or_websearch.connect("llm_for_rag.replies", "router.replies")
rag_or_websearch.connect("router.go_to_websearch", "websearch.query")
rag_or_websearch.connect("router.go_to_websearch", "prompt_builder_for_websearch.query")
rag_or_websearch.connect("websearch.documents", "prompt_builder_for_websearch.documents")
rag_or_websearch.connect("prompt_builder_for_websearch", "llm_for_websearch")

def run_rag_or_websearch_pipeline(question):
    result = rag_or_websearch.run(
        {
            "query_embedder": {"text": question},
            "retriever": {"top_k": 1},
            "prompt_builder_for_rag": {"query": question},
            "router": {"query": question},
        }
    )
    print()
    # Result comes from websearch, because the router decided to use the route 
    # output_name "go_to_websearch", instead of the route output_name "go_to_answer"
    if "llm_for_websearch" in result:
        print("Question: " + question)
        print("Answer: " + result["llm_for_websearch"]["replies"][0])
    # Result comes from RAG, because the router decided to use the route 
    # output_name "go_to_answer", instead of the route output_name "go_to_websearch"
    else:
        print("Question: " + question)
        print("Answer: " + result["router"]["go_to_answer"])
    print()

# Example 1: Run the rag_or_websearch pipeline with answer from RAG
question = "What Alien Life Forms exisit on planet Novusmundus23?"
run_rag_or_websearch_pipeline(question)

# Example 2: Run the rag_or_websearch pipeline with answer from websearch
question = "What is the current USA effective federal funds rate?"
run_rag_or_websearch_pipeline(question)
