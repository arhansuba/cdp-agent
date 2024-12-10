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
        except Exception as e:
            print(f'Error initializing CLI: {e}')
            sys.exit(1)

    def show_help(self):
        help_text = """
        Available commands:
        help - Show this help message
        wallet - Get wallet information
        balance - Check balance of assets
        deploy - Deploy ERC20 tokens
        transfer - Transfer assets between addresses
        stats - Show performance metrics
        history - Show transaction history
        """
        print(help_text)

    async def get_wallet_info(self):
        wallet_id = "example_wallet_id"  # Replace with actual wallet ID
        details = self.agent.get_wallet_details()
        print(details)

    async def check_balance(self):
        # Implement the logic for checking balance
        print("Checking balance...")

    async def handle_deployment(self):
        # Implement the logic for handling deployment
        print("Handling deployment...")

    async def handle_transfer(self, args):
        # Implement the logic for handling transfer
        print(f"Handling transfer with args: {args}")

    async def show_stats(self):
        # Implement the logic for showing stats
        print("Showing stats...")

    async def show_history(self):
        # Implement the logic for showing history
        print("Showing history...")

    async def handle_command(self, command: str):
        if command in self.commands:
            await self.commands[command]()
        else:
            response = await self.agent.execute(command)
            print(f"Agent: {response}")

if __name__ == '__main__':
    cli = AgentCLI()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            user_input = input("\nUser: ").strip()
            if user_input.lower() == 'exit':
                break
            loop.run_until_complete(cli.handle_command(user_input))
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error processing command: {e}")
    print("\nGoodbye!")