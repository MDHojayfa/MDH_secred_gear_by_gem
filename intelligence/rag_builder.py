import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings # A powerful, free, local embedding model
import requests
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()
VECTOR_DB_DIR = "data/learn_db"
KNOWLEDGE_SOURCE = "data/knowledge_base.txt"

def scrape_public_reports_simulated():
    """
    Simulates scraping and aggregation of public bug reports.
    In a real-world scenario, this would iterate through
    HackerOne/Bugcrowd public API or scrape pages.
    """
    console.print("[RECON:CYAN]Starting simulated scrape of public bug reports (HackerOne/Bugcrowd).[/RECON:CYAN]")
    
    # Example simulated public vulnerability data
    example_reports = [
        "VULN: Reflected XSS on /search?q=PAYLOAD. Root Cause: Lack of output encoding on search parameter. Remediation: Use context-aware output encoding.",
        "VULN: Time-based Blind SQLi on /api/user/ID. Attacker manipulated ID=1' AND (SELECT 1 FROM (SELECT(SLEEP(5)))a) AND '1'='1. Remediation: Use parameterized queries.",
        "VULN: IDOR on /profile?id=123. Attacker changed ID from 123 to 456 to view another user's profile. Remediation: Implement row-level access control checks.",
        "VULN: SSRF via PDF generator. The URL parameter was not validated, allowing access to AWS metadata service via http://169.254.169.254/latest/meta-data/. Remediation: Whitelist external domains.",
        "VULN: Authentication bypass using JWT token manipulation. Set 'role':'admin' in the token payload and re-signed with a known public key from a misconfiguration. Remediation: Verify JWT signature using the correct secret key.",
        # Add more real-world patterns here
    ]
    
    with open(KNOWLEDGE_SOURCE, "w") as f:
        f.write("\n---\n".join(example_reports))

    console.print(f"[RECON:CYAN]Simulated {len(example_reports)} reports aggregated to {KNOWLEDGE_SOURCE}.[/RECON:CYAN]")


def build_vector_store():
    """Loads, chunks, embeds, and stores the knowledge base into ChromaDB."""
    
    if not os.path.exists(KNOWLEDGE_SOURCE):
        scrape_public_reports_simulated()

    # 1. Load the document
    loader = TextLoader(KNOWLEDGE_SOURCE)
    documents = loader.load()

    # 2. Split the document into chunks for better retrieval
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(documents)
    console.print(f"[SYSTEM:ELECTRIC BLUE]Text split into {len(texts)} chunks for deep learning.[/SYSTEM:ELECTRIC BLUE]")

    # 3. Create a free, powerful, local embedding model
    # 'all-MiniLM-L6-v2' is a good balance of performance and size for local use
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # 4. Store the vectors in ChromaDB (our local, free Vector Store)
    console.print(f"[SYSTEM:ELECTRIC BLUE]Building Knowledge Graph in ChromaDB at {VECTOR_DB_DIR}...[/SYSTEM:ELECTRIC BLUE]")
    vector_store = Chroma.from_documents(
        documents=texts,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )
    vector_store.persist()
    console.print("[SUCCESS:NEON GREEN]Continuous Learning Engine is now fully armed with 🧠 past bug data![/SUCCESS:NEON GREEN]")

def load_vector_store_retriever():
    """Loads the persistent ChromaDB and returns a retriever."""
    if not os.path.exists(VECTOR_DB_DIR):
        console.print("[WARNING:YELLOW]Knowledge base not found. Running build process...[/WARNING:YELLOW]")
        build_vector_store()
        
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
    
    # The retriever is the component the AI uses to search its own memory
    return vector_store.as_retriever(search_kwargs={"k": 3})

# --- Run this one time to build the initial knowledge base ---
if __name__ == "__main__":
    build_vector_store()
