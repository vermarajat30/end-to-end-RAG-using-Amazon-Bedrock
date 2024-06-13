import boto3
import streamlit as st
from langchain.llms.bedrock import Bedrock
# for embedding model we are using amazon embedding from bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import retrieval_qa


def get_documents():
    loader = PyPDFDirectoryLoader("data")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 500)
    docs = text_splitter.split_documents(documents)
    return docs
#bedrock client
bedrock = boto3.client(service_name = "bedrock-runtime", region_name = "us-east-1")

# get embedding model from Bedrock
bedrock_embedding = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1", client= bedrock)

def get_vector_store(docs):
    vectorstore_faiss = FAISS.from_documents(
        docs,
        bedrock_embedding
    )
    vectorstore_faiss.save_local("faiss_local")# storing the embedded vector in local machine

def get_llm():
    llm = Bedrock(model_id = "mistral.mistral-7b-instruct-v0:2", client = bedrock)
    return llm

prompt_template = """
Human: Use the following pieces of context to provide a 
concise answer to the question at the end but use atlease summarize with 250 words
with detailed explanations. If you don't know the answer, just say that you don't know
don't try to make up an answer.
<context>
{context}
</context>
 
 Question:{question}
 Assistant:""" 

PromptTemplate(
    template = prompt_template, input_variables=["context", "question"]
)

def get_llm_response(llm, vectorstore_faiss, query):
    qa = retrieval_qa.from_chain_type(
        llm = llm,
        chain_type = "stuff",
        retriever = vectorstore_faiss.as_retriever(search_type = "similarity", search_kwargs={"k": 3}),
        return_source_documents = True,
        chain_type_kwargs={"prompt":PROMPT},
        )
    response = qa({"query": query})
    return response['results']


def main():