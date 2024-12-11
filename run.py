from agent import CDPAgent
from logger import TransactionLogger
from metrics import PerformanceMetrics
from database import Database
from typing import Optional, Dict, Any
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentCLI:
    def __init__(self):
        try:
            self.agent = CDPAgent()
            self.logger = TransactionLogger()
            self.metrics = PerformanceMetrics()
            self.db = Database()
            
            self.commands = {
                'help': self.show_help,
                'wallet': self.get_wallet_info,
                'balance': self.check_balance,
                'deploy': self.handle_deployment,
                'transfer': self.handle_transfer,
                'stats': self.show_stats,
                'history': self.show_history
            }
            print("CDP Agent initialized successfully!")
        except Exception as e:
            print(f'Error initializing CLI: {e}')
            raise

    async def show_help(self, args=None):
        """Show available commands and their usage."""
        help_text = """
Available Commands:
- help              : Show this help message
- wallet           : Get wallet information
- balance          : Check your wallet balance
- deploy token     : Deploy an ERC20 token
- deploy nft       : Deploy an NFT collection
- transfer <amount> <to_address> : Transfer assets
- stats            : Show performance metrics
- history          : Show transaction history
- faucet           : Request testnet funds

You can also interact with natural language!
        """
        return help_text

    async def get_wallet_info(self, args=None):
        """Get wallet details."""
        try:
            details = self.agent.get_wallet_details()
            if details:
                return f"""
Wallet Details:
Address: {details.get('address', 'Not available')}
Network: {details.get('network', 'Not available')}
Balance: {details.get('balance', '0')} ETH
                """
            return "Could not retrieve wallet details."
        except Exception as e:
            return f"Error getting wallet info: {str(e)}"

    async def check_balance(self, args=None):
        """Check wallet balance."""
        try:
            response = self.agent.execute("What is my current balance?")
            return response
        except Exception as e:
            return f"Error checking balance: {str(e)}"

    async def handle_deployment(self, args=None):
        """Handle token deployment."""
        if not args:
            return "Please specify what to deploy (token/nft)"
        try:
            if args.lower() == "token":
                response = self.agent.execute(
                    "Deploy a new ERC20 token with name 'TestToken' and symbol 'TEST'"
                )
                return response
            elif args.lower() == "nft":
                response = self.agent.execute(
                    "Deploy a new NFT collection called 'TestNFT' with symbol 'TNFT'"
                )
                return response
            else:
                return "Invalid deployment type. Use 'token' or 'nft'"
        except Exception as e:
            return f"Error during deployment: {str(e)}"

    async def handle_transfer(self, args=None):
        """Handle asset transfer."""
        if not args:
            return "Please specify amount and recipient address"
        try:
            parts = args.split()
            if len(parts) < 2:
                return "Invalid transfer format. Use: transfer <amount> <address>"
            amount, recipient = parts[0], parts[1]
            response = self.agent.execute(f"Transfer {amount} ETH to {recipient}")
            return response
        except Exception as e:
            return f"Error during transfer: {str(e)}"

    async def show_stats(self, args=None):
        """Show performance statistics."""
        try:
            stats = self.metrics.get_operation_stats()
            return f"""
Performance Statistics:
Total Operations: {stats.get('total_operations', 0)}
Success Rate: {stats.get('success_rate', 0)}%
Average Duration: {stats.get('avg_duration_ms', 0)}ms
            """
        except Exception as e:
            return f"Error getting stats: {str(e)}"

    async def show_history(self, args=None):
        """Show transaction history."""
        try:
            transactions = self.db.get_transaction_history(limit=5)
            if not transactions:
                return "No transaction history found."
            
            history = "Recent Transactions:\n"
            for tx in transactions:
                history += f"- {tx['operation_type']}: {tx['tx_hash']} ({tx['status']})\n"
            return history
        except Exception as e:
            return f"Error getting history: {str(e)}"

    async def handle_command(self, user_input: str):
        """Process user commands."""
        try:
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None

            if command in self.commands:
                response = await self.commands[command](args)
            else:
                response = self.agent.execute(user_input)

            print("\nResponse:", response)

        except Exception as e:
            print(f"Error: {str(e)}")

async def main():
    """Main async CLI loop."""
    try:
        cli = AgentCLI()
        print('CDP Agent initialized with Groq LLM. Type \'help\' for commands or \'exit\' to quit.')
        
        while True:
            try:
                user_input = input('\nUser: ').strip()
                if not user_input:
                    continue
                    
                if user_input.lower() == 'exit':
                    break
                
                await cli.handle_command(user_input)
                
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print('\nGoodbye!')
        
    except Exception as e:
        print(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())