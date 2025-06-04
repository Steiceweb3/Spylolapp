"""
SPYLOLenigma Airdrop Manager
Handles token distribution to eligible users
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solders.keypair import Keypair as SoldersKeypair
from solders.pubkey import Pubkey as SoldersPubkey
import base58

from app import app, db
from models import UserProgress, AirdropConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AirdropManager:
    """Manages SPL token airdrops for SPYLOLenigma players"""
    
    def __init__(self, network: str = "devnet"):
        self.network = network
        if network == "mainnet":
            self.rpc_url = "https://api.mainnet-beta.solana.com"
        else:
            self.rpc_url = "https://api.devnet.solana.com"
        
        self.client = Client(self.rpc_url, commitment=Commitment("confirmed"))
        self.admin_keypair = None
    
    def setup_admin_wallet(self, private_key_base58: str) -> bool:
        """Setup admin wallet from private key"""
        try:
            private_key_bytes = base58.b58decode(private_key_base58)
            self.admin_keypair = Keypair.from_secret_key(private_key_bytes)
            logger.info(f"Admin wallet setup: {self.admin_keypair.public_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup admin wallet: {e}")
            return False
    
    def get_airdrop_config(self) -> Optional[AirdropConfig]:
        """Get current airdrop configuration"""
        return AirdropConfig.query.first()
    
    def create_airdrop_config(self, token_mint: str, admin_wallet: str, 
                            tokens_per_point: int = 1000000, 
                            minimum_points: int = 50) -> AirdropConfig:
        """Create new airdrop configuration"""
        config = AirdropConfig(
            token_mint=token_mint,
            admin_wallet=admin_wallet,
            tokens_per_point=tokens_per_point,
            minimum_points=minimum_points,
            airdrop_active=True
        )
        db.session.add(config)
        db.session.commit()
        return config
    
    def get_eligible_users(self) -> List[UserProgress]:
        """Get users eligible for airdrop"""
        config = self.get_airdrop_config()
        if not config:
            return []
        
        return UserProgress.query.filter(
            UserProgress.wallet_address.isnot(None),
            UserProgress.total_points >= config.minimum_points,
            UserProgress.airdrop_status == 'pending'
        ).all()
    
    def calculate_airdrop_amount(self, user: UserProgress) -> int:
        """Calculate airdrop amount for user based on points"""
        config = self.get_airdrop_config()
        if not config:
            return 0
        
        return user.total_points * config.tokens_per_point
    
    def export_airdrop_data(self) -> List[Dict]:
        """Export airdrop data for external processing"""
        eligible_users = self.get_eligible_users()
        airdrop_data = []
        
        for user in eligible_users:
            amount = self.calculate_airdrop_amount(user)
            airdrop_data.append({
                "wallet_address": user.wallet_address,
                "total_points": user.total_points,
                "airdrop_amount": amount,
                "session_id": user.session_id,
                "last_active": user.last_active.isoformat() if user.last_active else None
            })
        
        return airdrop_data
    
    def save_airdrop_data_to_file(self, filename: str = "airdrop_data.json") -> str:
        """Save airdrop data to JSON file"""
        data = self.export_airdrop_data()
        filepath = os.path.join("data", filename)
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "total_recipients": len(data),
                "network": self.network,
                "recipients": data
            }, f, indent=2)
        
        logger.info(f"Airdrop data saved to {filepath}")
        return filepath
    
    def simulate_airdrop(self) -> Dict:
        """Simulate airdrop without sending transactions"""
        eligible_users = self.get_eligible_users()
        config = self.get_airdrop_config()
        
        if not config:
            return {"error": "No airdrop configuration found"}
        
        total_tokens = 0
        recipients = []
        
        for user in eligible_users:
            amount = self.calculate_airdrop_amount(user)
            total_tokens += amount
            recipients.append({
                "wallet": user.wallet_address,
                "points": user.total_points,
                "tokens": amount / (10 ** 6)  # Convert to human readable
            })
        
        return {
            "config": {
                "token_mint": config.token_mint,
                "tokens_per_point": config.tokens_per_point / (10 ** 6),
                "minimum_points": config.minimum_points
            },
            "summary": {
                "total_recipients": len(recipients),
                "total_tokens": total_tokens / (10 ** 6),
                "network": self.network
            },
            "recipients": recipients
        }
    
    def update_airdrop_status(self, user_id: int, status: str, 
                            tx_hash: str = None, amount: int = None):
        """Update airdrop status for a user"""
        user = UserProgress.query.get(user_id)
        if user:
            user.airdrop_status = status
            if tx_hash:
                user.airdrop_tx_hash = tx_hash
            if amount:
                user.airdrop_amount = amount
            if status == 'sent':
                user.airdrop_sent_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Updated airdrop status for user {user_id}: {status}")


def main():
    """Command line interface for airdrop management"""
    with app.app_context():
        manager = AirdropManager("devnet")  # Use devnet for testing
        
        print("=== SPYLOLenigma Airdrop Manager ===")
        print("1. View eligible users")
        print("2. Export airdrop data") 
        print("3. Simulate airdrop")
        print("4. Setup airdrop config")
        
        choice = input("Choose an option (1-4): ")
        
        if choice == "1":
            users = manager.get_eligible_users()
            print(f"\nFound {len(users)} eligible users:")
            for user in users:
                amount = manager.calculate_airdrop_amount(user)
                print(f"Wallet: {user.wallet_address}, Points: {user.total_points}, Tokens: {amount / (10**6)}")
        
        elif choice == "2":
            filepath = manager.save_airdrop_data_to_file()
            print(f"Airdrop data exported to: {filepath}")
        
        elif choice == "3":
            result = manager.simulate_airdrop()
            print("\n=== Airdrop Simulation ===")
            print(json.dumps(result, indent=2))
        
        elif choice == "4":
            token_mint = input("Enter token mint address: ")
            admin_wallet = input("Enter admin wallet address: ")
            tokens_per_point = int(input("Enter tokens per point (with decimals, e.g., 1000000 for 1 token): "))
            min_points = int(input("Enter minimum points for eligibility: "))
            
            config = manager.create_airdrop_config(token_mint, admin_wallet, tokens_per_point, min_points)
            print(f"Airdrop config created: {config}")


if __name__ == "__main__":
    main()