import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import HuggingFaceHub
from rich.console import Console

# Load configuration
load_dotenv(dotenv_path='config/.env')
console = Console()

class AI_Manager:
    def __init__(self, console_logger):
        self.console = console_logger
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        # HuggingFace token is often needed for community/DeepSeek models, 
        # but we'll try to keep it local/free-tier where possible.
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") 
        
        # Define the priority AI list (Name, Model Function/Reference, Rate Limit Delay in seconds)
        self.ai_priorities = []
        self._initialize_models()
        self.active_model_name = self.ai_priorities[0][0]
        self.active_model = self.ai_priorities[0][1]
        self.last_call_time = 0

    def _initialize_models(self):
        """Initializes all models based on available keys and free alternatives."""
        
        # 1. Primary: Gemini 2.5 Pro (Highest performance, but optional key)
        if self.gemini_key:
            self.ai_priorities.append((
                "Gemini 2.5 Pro (Primary)",
                ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=self.gemini_key, temperature=0.1),
                5 # 5 RPM rate limit
            ))
            self.console.print("[AI:PURPLE]✔ Primary Model Activated: Gemini 2.5 Pro (Paid/Key)[/AI:PURPLE]")
        
        # 2. Secondary: DeepSeek R1 (The "Free Unlimited" reasoning powerhouse - via HuggingFace)
        # DeepSeek R1 is often accessible via HuggingFace's Inference API or local deployment.
        # We simulate the most powerful free access here.
        self.ai_priorities.append((
            "DeepSeek R1 (Secondary/FREE)",
            HuggingFaceHub(repo_id="deepseek-ai/DeepSeek-Coder-V2-Lite-Base", 
                           task="text-generation", 
                           huggingfacehub_api_token=self.hf_token if self.hf_token else "NO_TOKEN_USED"),
            0.5 # Fast, but requires local setup or minimal HF usage
        ))
        self.console.print("[AI:PURPLE]✔ Secondary Model Activated: DeepSeek R1 (FREE/Local)[/AI:PURPLE]")

        # 3. Tertiary: Gemini 2.5 Flash (The fast, free-tier fallback)
        if self.gemini_key: # Use Flash as a fast, low-quota key alternative
            self.ai_priorities.append((
                "Gemini 2.5 Flash (Tertiary)",
                ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=self.gemini_key, temperature=0.05),
                0.2 # Very fast
            ))
            self.console.print("[AI:PURPLE]✔ Tertiary Model Activated: Gemini 2.5 Flash (Fast/Key)[/AI:PURPLE]")
        else: # If no key, DeepSeek is the only option, but we can add a local open-source model too.
             self.console.print("[AI:PURPLE]⚠ Only FREE models available. Consider adding GEMINI_API_KEY for Pro features.[/AI:PURPLE]")

        if not self.ai_priorities:
             raise ValueError("No AI models could be initialized. Please check configuration.")


    def _switch_model(self):
        """Auto-fallback mechanism."""
        current_index = [i for i, (name, _, _) in enumerate(self.ai_priorities) if name == self.active_model_name][0]
        
        # Move to the next model in the priority list
        next_index = (current_index + 1) % len(self.ai_priorities)
        self.active_model_name = self.ai_priorities[next_index][0]
        self.active_model = self.ai_priorities[next_index][1]

        self.console.print(f"[AI:PURPLE]AUTO-FALLBACK[/AI:PURPLE]: Switching to [WARNING]{self.active_model_name}[/WARNING] due to rate limit/error.", style="yellow")
        self.last_call_time = 0 # Reset timer

    def generate_response(self, prompt: str, system_prompt: str) -> str:
        """Generates a response using the active model with rate-limiting and fallback."""
        
        # Enforce rate limit delay
        min_delay = self.ai_priorities[0][2] # Get delay for current model
        elapsed = time.time() - self.last_call_time
        if elapsed < min_delay:
            wait_time = min_delay - elapsed
            self.console.print(f"[AI:PURPLE]Waiting {wait_time:.2f}s to respect rate limit for {self.active_model_name}...[/AI:PURPLE]", style="dim")
            time.sleep(wait_time)
        
        template = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        
        chain = template | self.active_model
        
        attempts = 0
        max_attempts = len(self.ai_priorities)
        
        while attempts < max_attempts:
            try:
                self.console.print(f"[AI:PURPLE]Querying {self.active_model_name}...[/AI:PURPLE]", style="cyan")
                response = chain.invoke({"input": prompt})
                self.last_call_time = time.time()
                return response.content

            except Exception as e:
                self.console.print(f"[ERROR:RED]AI Call Error with {self.active_model_name}: {e}[/ERROR:RED]", style="red")
                self._switch_model()
                attempts += 1
                time.sleep(2) # Brief wait before next attempt

        self.console.print("[CRITICAL:RED]All AI models failed after exhausting fallbacks. Cannot proceed.[/CRITICAL:RED]", style="bold red")
        return "ERROR: All AI services failed."

