# web_app.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uvicorn

from agent import CDPAgent
from metrics import PerformanceMetrics
from database import Database

# Initialize FastAPI app
app = FastAPI(title="CDP Agent Dashboard")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize core components
agent = CDPAgent()
metrics = PerformanceMetrics()
db = Database()

# API Models
class TransactionRequest(BaseModel):
   operation_type: str
   amount: Optional[float]
   recipient: Optional[str]
   token_address: Optional[str]
   details: Optional[Dict[str, Any]]

class DeployTokenRequest(BaseModel):
   name: str
   symbol: str
   total_supply: int
   
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
   """Render main dashboard."""
   wallet_details = agent.get_wallet_details()
   performance_stats = metrics.get_operation_stats()
   recent_transactions = db.get_transaction_history(limit=5)
   
   return templates.TemplateResponse(
       "index.html",
       {
           "request": request,
           "wallet": wallet_details,
           "stats": performance_stats,
           "transactions": recent_transactions
       }
   )

@app.get("/api/wallet")
async def get_wallet_info():
   """Get current wallet information."""
   try:
       wallet_info = agent.get_wallet_details()
       return {
           "status": "success",
           "data": wallet_info
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transaction")
async def execute_transaction(request: TransactionRequest):
   """Execute a blockchain transaction."""
   try:
       result = await agent.execute_transaction(
           operation_type=request.operation_type,
           params={
               "amount": request.amount,
               "recipient": request.recipient,
               "token_address": request.token_address,
               "details": request.details
           }
       )
       return {
           "status": "success",
           "transaction": result
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deploy/token")
async def deploy_token(request: DeployTokenRequest):
   """Deploy a new ERC20 token."""
   try:
       result = await agent.execute_transaction(
           operation_type="deploy_token",
           params={
               "name": request.name,
               "symbol": request.symbol,
               "total_supply": request.total_supply
           }
       )
       return {
           "status": "success",
           "contract": result
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions")
async def get_transactions(limit: int = 10, wallet_address: Optional[str] = None):
   """Get transaction history."""
   try:
       transactions = db.get_transaction_history(
           wallet_address=wallet_address,
           limit=limit
       )
       return {
           "status": "success",
           "transactions": transactions
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics(operation_type: Optional[str] = None):
   """Get performance metrics."""
   try:
       if operation_type:
           stats = metrics.get_operation_stats(operation_type=operation_type)
       else:
           stats = metrics.generate_performance_report()
       return {
           "status": "success",
           "metrics": stats
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gas-trends")
async def get_gas_trends(days: int = 7):
   """Get gas usage trends."""
   try:
       trends = metrics.get_gas_usage_trends(days=days)
       return {
           "status": "success",
           "trends": trends
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
   return {
       "status": "error",
       "code": exc.status_code,
       "message": exc.detail
   }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
   return {
       "status": "error",
       "code": 500,
       "message": str(exc)
   }

# WebSocket for real-time updates
from fastapi import WebSocket
from typing import List

class ConnectionManager:
   def __init__(self):
       self.active_connections: List[WebSocket] = []

   async def connect(self, websocket: WebSocket):
       await websocket.accept()
       self.active_connections.append(websocket)

   def disconnect(self, websocket: WebSocket):
       self.active_connections.remove(websocket)

   async def broadcast(self, message: Dict[str, Any]):
       for connection in self.active_connections:
           await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
   await manager.connect(websocket)
   try:
       while True:
           data = await websocket.receive_text()
           # Handle incoming WebSocket messages if needed
   except Exception as e:
       manager.disconnect(websocket)

def run_app():
   """Run the FastAPI application."""
   uvicorn.run(
       "web_app:app",
       host="0.0.0.0",
       port=8000,
       reload=True
   )

if __name__ == "__main__":
   run_app()