import os
from typing import Dict, Any, Optional
from datetime import datetime
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from config import *

# Import new components
from logger import TransactionLogger
from database import Database
from metrics import PerformanceMetrics

class CDPAgent:
    def __init__(self):
        # Initialize core LLM
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name=DEFAULT_MODEL,
            temperature=TEMPERATURE
        )
        self.agent_executor = None
        self.config = None
        self.wallet_address = None
        self.cdp = None
        self.initialize_agent()

    def initialize_agent(self):
        """Initialize agent with enhanced tracking and metrics."""
        try:
            # Initialize CDP wrapper
            self.cdp = CdpAgentkitWrapper()

            # Create toolkit from wrapper
            toolkit = CdpToolkit.from_cdp_agentkit_wrapper(self.cdp)

            # Get tools and create agent executor
            tools = toolkit.get_tools()
            self.agent_executor = create_react_agent(self.llm, tools)

            # Export wallet data and update address
            wallet_data = self.cdp.export_wallet()
            print(f"Wallet data: {wallet_data}")  # Debug print
            self._save_wallet_data(wallet_data)
            wallet_details = self.cdp.get_wallet_details()
            print(f"Wallet details: {wallet_details}")  # Debug print
            self.wallet_address = wallet_details["address"]

            # Initialize toolkit and tools
            cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(self.cdp)
            tools = cdp_toolkit.get_tools()

            # Set up memory and configuration
            memory = MemorySaver()
            # Additional initialization code here
        except Exception as e:
            print(f"Error initializing agent: {e}")

    def get_wallet_details(self) -> Optional[Dict[str, Any]]:
        """Retrieves detailed wallet information."""
        db = Database()
        wallet_details = db.get_wallet_details(self.wallet_address)
        print(f"Retrieved wallet details: {wallet_details}")  # Debug print
        return wallet_details

    def _save_wallet_data(self, wallet_data: Dict[str, Any]) -> None:
        """Saves wallet data to a persistent storage."""
        db = Database()
        db.save_wallet_data(wallet_data)

    async def execute(self, user_input: str) -> str:
        if user_input.lower() == 'what can you do':
            return self.get_capabilities()
        # Add more command handling here
        return "Command not recognized."

    def get_capabilities(self) -> str:
        return (
            "As a helpful agent that can interact with the Base blockchain using CDP AgentKit, I can perform various tasks for you. Here are some examples:\n\n"
            "1. Create new wallets.\n"
            "2. Deploy ERC20 tokens.\n"
            "3. Check the balance of assets in a wallet.\n"
            "4. Transfer assets between addresses.\n"
            "5. Perform transactions with Zora Wow ERC20 memecoins (buy, sell, or create).\n\n"
            "Please note that the available actions depend on the provided tools and the balance of the wallet. If the faucet does not send tokens, some actions may not be possible.\n\n"
            "If you need funds on the testnet, you can request them using the `request_faucet_funds` tool.\n\n"
            "I will be concise and efficient in my responses, following the TOOL_INSTRUCTIONS or TEXT_INSTRUCTIONS based on the conversation."
        )