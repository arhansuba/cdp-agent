import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
CDP_API_KEY_NAME = os.getenv('CDP_API_KEY_NAME')
CDP_API_KEY_PRIVATE_KEY = os.getenv('CDP_API_KEY_PRIVATE_KEY')
NETWORK_ID = os.getenv('NETWORK_ID', 'base-sepolia')

# Model Config
DEFAULT_MODEL = 'mixtral-8x7b-32768'
TEMPERATURE = 0.7

# Agent Config
AGENT_PROMPT = '''You are a helpful agent that can interact with the Base blockchain using CDP AgentKit.
You can create wallets, deploy tokens, and perform transactions. If you need funds on testnet,
request them from the faucet. Be concise and efficient in your responses.'''

# Wallet Config
WALLET_FILE = 'wallet_data.txt'
