# Haystack Retrieval-Augmented Generation (RAG) with web search fall-back

[Haystack](https://haystack.deepset.ai/) is an open source framework for building Large Language Model (LLM) applications, Retrieval-Augmented Generation (RAG) pipelines, and search systems. Haystack is an excellent alternative to the LangChain and LlamaIndex frameworks.

Haystack uses pipelines and components as core concepts. Pipelines are chains of components. Components are building blocks (functions).

Pipelines are composed by connecting components.

Components can have one or multiple inputs and one or multiple outputs. For example: An "Embedder" component might expect a list of documents as input and produce both a list of the same documents with embeddings and a dictionary of metadata about the documents as output.

Haystack has many ready-made components, such as Generators, Embedders, Retrievers, Converters, Rankers, Routers, PreProcessors etc.

Haystack also makes it easy to build and integrate custom components.

Pipelines can be made of a linear sequence of components, but pipelines can also branch out by using decision-making components like Routers. Pipelines can also be designed to loop until a condition has been met.

This example uses the `ingestion_pipeline` to ingest a text document about a fictional planet called Novusmundus23 into the simplest type of Haystack document store. The [`InMemoryDocumentStore`](https://docs.haystack.deepset.ai/docs/inmemorydocumentstore) has no setup requirements. In production RAG systems, this needs to be changed to a [permanent data store](https://docs.haystack.deepset.ai/docs/document-store) like Pinecone, Chroma, Qdrant etc.

This example then uses the `rag_or_websearch` pipeline to answer questions. This pipeline first tries to answer questions by using RAG with the information from the document store. If the information in the document store does not provide an answer to the question, then the RAG will answer with `n/a`. A "Router" component then decides how to proceed. If the RAG answer was satisfactory (no `n/a` answer), then it will decide to take the path `go_to_answer`, which will simply output the RAG answer and terminate the `rag_or_websearch` pipline. If the RAG answer was `n/a`, then it will take the path `go_to_websearch` and use the `SerperDevWebSearch` component. This component will search the web for the required information. It will then use the information that it finds on the web to make another LLM call. It will then output this new answer and terminate the `rag_or_websearch` pipeline.

Both the RAG and the websearch outputs will mention their sources in their answers.

The `images` folder contains visualisations of both the `ingestion_pipeline` and the `rag_or_websearch` pipelines.

You need an OpenAI API key for this example. [Get your OpenAI API key here](https://platform.openai.com/login). You can insert your OpenAI API key in the `main.py` script, or you can supply your OpenAI API key either via the `.env` file, or through an environment variable called `OPENAI_API_KEY`. If you don't want to use an OpenAI model, then you can also use other models, including local models.

You also need a free SerperDev API key for this example for the `SerperDevWebSearch` component. [Get your free SerperDev API key here](https://serper.dev/signup). You can insert your SerperDev API key in the `main.py` script, or you can supply your SerperDev API key either via the `.env` file, or through an environment variable called `SERPERDEV_API_KEY`.

## The results

| Questions                                               | Answers (might vary)                                                                                                                                                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `What Alien Life Forms exisit on planet Novusmundus23?` | Aquafins, Lumipods, Treetenders, and Sandstriders are the Alien Life Forms that exist on planet Novusmundus23. (file path: data/novusmundus23.txt, page number: 1)                                                             |
| `What is the current USA effective federal funds rate?` | The current effective federal funds rate in the United States is 5.33%. This rate has remained unchanged as of August 23, according to historical data. (Source: https://www.tradingeconomics.com/united-states/interest-rate) |
