import os
import json
from typing import Any, Dict, Optional
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from config import *

# Import new components
from database import Database

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
        self.network = NETWORK_ID
        self.initialize_agent()

    def initialize_agent(self):
        """Initialize agent with enhanced tracking and metrics."""
        try:
            # Load or create wallet
            wallet_data = self._load_wallet_data()
            
            # Initialize CDP wrapper
            self.cdp = CdpAgentkitWrapper(
                cdp_wallet_data=wallet_data if wallet_data else None
            )
            
            # Export and save wallet data
            exported_wallet = self.cdp.export_wallet()
            if exported_wallet:
                self._save_wallet_data(exported_wallet)
                try:
                    # Parse wallet data
                    wallet_json = json.loads(exported_wallet)
                    self.wallet_address = wallet_json.get('default_address_id')
                    
                    # Save to database
                    db = Database()
                    db.save_wallet_data({
                        'address': self.wallet_address,
                        'network': self.network,
                        'metadata': wallet_json
                    })
                except json.JSONDecodeError as e:
                    print(f"Error parsing wallet data: {e}")

            # Initialize toolkit and tools
            cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(self.cdp)
            tools = cdp_toolkit.get_tools()

            # Set up memory and configuration
            memory = MemorySaver()
            self.config = {'configurable': {'thread_id': 'CDP_Groq_Agent'}}
            
            # Create agent
            self.agent_executor = create_react_agent(
                self.llm,
                tools=tools,
                checkpointer=memory,
                state_modifier=AGENT_PROMPT
            )

        except Exception as e:
            print(f"Error initializing agent: {e}")
            raise

    def _load_wallet_data(self) -> Optional[str]:
        """Load wallet data from file."""
        try:
            if os.path.exists(WALLET_FILE):
                with open(WALLET_FILE) as f:
                    data = f.read()
                    print(f"Loaded wallet data: {data}")
                    return data
            return None
        except Exception as e:
            print(f"Error loading wallet data: {e}")
            return None

    def _save_wallet_data(self, wallet_data: str) -> None:
        """Save wallet data to file and database."""
        try:
            # Save to file
            with open(WALLET_FILE, 'w') as f:
                f.write(wallet_data)

            # Parse and save to database
            try:
                wallet_json = json.loads(wallet_data)
                db = Database()
                db.save_wallet_data({
                    'address': wallet_json.get('default_address_id'),
                    'network': self.network,
                    'metadata': wallet_json
                })
            except json.JSONDecodeError:
                print("Error parsing wallet data for database")

        except Exception as e:
            print(f"Error saving wallet data: {e}")

    def get_wallet_details(self) -> Dict[str, Any]:
        """Get detailed wallet information."""
        try:
            return {
                "address": self.wallet_address,
                "network": self.network,
                "balance": self._get_wallet_balance()
            }
        except Exception as e:
            raise Exception(f"Error getting wallet details: {str(e)}")

    def _get_wallet_balance(self) -> str:
        """Get current wallet ETH balance."""
        try:
            # Use execute method to get balance from CDP toolkit
            response = self.execute("What is my ETH balance?")
            # Extract balance from response
            return response.split()[0] if response else "0"
        except Exception:
            return "0"

    def execute(self, prompt: str) -> str:
        """Execute agent commands with proper error handling."""
        try:
            # Special commands handling
            if prompt.lower() == "what is my eth balance?":
                return self._handle_balance_check()
            elif prompt.lower() == "wallet":
                return self._handle_wallet_info()
            elif prompt.lower() == "faucet":
                return self._handle_faucet_request()
            
            # Regular command processing through agent executor
            response = ""
            for chunk in self.agent_executor.stream(
                {'messages': [HumanMessage(content=prompt)]},
                self.config
            ):
                if 'agent' in chunk:
                    response += chunk['agent']['messages'][0].content + "\n"
                elif 'tools' in chunk:
                    response += chunk['tools']['messages'][0].content + "\n"
            return response.strip()
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def _handle_balance_check(self) -> str:
        """Handle balance check command."""
        try:
            balance_response = self.execute_cdp("get_balance", {"asset_id": "eth"})
            return f"Current ETH balance: {balance_response}"
        except Exception as e:
            return f"Error checking balance: {str(e)}"

    def _handle_wallet_info(self) -> str:
        """Handle wallet info command."""
        try:
            wallet_details = self.get_wallet_details()
            return f"""
Wallet Information:
Address: {wallet_details['address']}
Network: {wallet_details['network']}
Balance: {wallet_details['balance']} ETH
"""
        except Exception as e:
            return f"Error getting wallet info: {str(e)}"

    def _handle_faucet_request(self) -> str:
        """Handle faucet request command."""
        try:
            faucet_response = self.execute_cdp("request_faucet_funds", {"asset_id": "eth"})
            return f"Faucet request result: {faucet_response}"
        except Exception as e:
            return f"Error requesting faucet funds: {str(e)}"

    def execute_cdp(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute CDP toolkit commands directly."""
        try:
            for tool in self.tools:
                if tool.name == tool_name:
                    result = tool.func(**params)
                    return str(result)
            return "Tool not found"
        except Exception as e:
            return f"Error executing CDP command: {str(e)}"

    def _get_wallet_info(self) -> str:
        """Get current wallet info."""
        try:
            response = f"""
Wallet Information:
Address: {self.wallet_address}
Network: {self.network}
"""
            return response
        except Exception as e:
            return f"Error getting wallet info: {str(e)}"

    def _check_balance(self) -> str:
        """Check wallet balance."""
        try:
            response = self.agent_executor.stream(
                {"messages": [HumanMessage(content="What is my ETH balance?")]},
                self.config
            )
            return next(response)['agent']['messages'][0].content
        except Exception as e:
            return f"Error checking balance: {str(e)}"

    def _request_faucet(self) -> str:
        """Request funds from faucet."""
        try:
            response = self.agent_executor.stream(
                {"messages": [HumanMessage(content="Request funds from the faucet")]},
                self.config
            )
            return next(response)['agent']['messages'][0].content
        except Exception as e:
            return f"Error requesting faucet funds: {str(e)}"

    def _handle_wow_buy(self) -> str:
        """Handle WOW token purchase."""
        try:
            contract_address = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
            amount = "100000000000000"  # 0.0001 ETH in wei
            
            response = self.agent_executor.stream(
                {"messages": [HumanMessage(content=f"Buy WOW token at {contract_address} for {amount} wei")]},
                self.config
            )
            return next(response)['agent']['messages'][0].content
        except Exception as e:
            return f"Error buying WOW token: {str(e)}"

    def get_capabilities(self) -> str:
        return """Available Commands:
1. Check wallet balance
2. Deploy tokens (ERC20, NFT)
3. Transfer assets
4. Request testnet funds
5. View transaction history

For example:
- "What is my wallet balance?"
- "Deploy a new ERC20 token"
- "Transfer 0.1 ETH to <address>"
- "Request testnet funds"
"""
