from app import db
from datetime import datetime


class Enigma(db.Model):
    """Model for storing game enigmas"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    answer = db.Column(db.Text, nullable=False)  # Now stores JSON array of possible answers
    difficulty = db.Column(db.Integer, default=1)  # 1-5 scale
    points = db.Column(db.Integer, default=10)
    hint = db.Column(db.Text, nullable=True)
    correct_feedback = db.Column(db.Text, nullable=False)
    incorrect_feedback = db.Column(db.Text, nullable=False)
    order_position = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<Enigma {self.title}>'


class UserProgress(db.Model):
    """Model for tracking user progress"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    wallet_address = db.Column(db.String(100), nullable=True, index=True)
    current_enigma_id = db.Column(db.Integer, db.ForeignKey('enigma.id'), nullable=False)
    completed_enigmas = db.Column(db.Text, default='[]')  # JSON string of completed enigma IDs
    enigma_order = db.Column(db.Text, default='[]')  # JSON string of randomized enigma IDs order
    total_points = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    token_eligibility = db.Column(db.Boolean, default=False)
    
    # Airdrop tracking fields
    airdrop_status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    airdrop_amount = db.Column(db.Integer, default=0)  # Amount of tokens to send
    airdrop_tx_hash = db.Column(db.String(100), nullable=True)  # Transaction hash
    airdrop_sent_at = db.Column(db.DateTime, nullable=True)  # When airdrop was sent
    
    def __repr__(self):
        return f'<UserProgress {self.session_id}>'


class AirdropConfig(db.Model):
    """Configuration for airdrop parameters"""
    id = db.Column(db.Integer, primary_key=True)
    token_mint = db.Column(db.String(100), nullable=False)  # SPL token mint address
    admin_wallet = db.Column(db.String(100), nullable=False)  # Admin wallet public key
    tokens_per_point = db.Column(db.Integer, default=1000000)  # Tokens per point (with decimals)
    minimum_points = db.Column(db.Integer, default=50)  # Minimum points for eligibility
    airdrop_active = db.Column(db.Boolean, default=False)  # Whether airdrop is active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AirdropConfig {self.token_mint}>'


class AppConfig(db.Model):
    """Configuration for app availability and time-based access control"""
    id = db.Column(db.Integer, primary_key=True)
    app_active = db.Column(db.Boolean, default=True)  # Whether app is accessible
    access_start_time = db.Column(db.DateTime, nullable=True)  # When access period starts
    access_end_time = db.Column(db.DateTime, nullable=True)  # When access period ends
    maintenance_message = db.Column(db.Text, default="App is temporarily unavailable for maintenance")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AppConfig active={self.app_active}>'
    
    def is_accessible(self):
        """Check if app is currently accessible based on time restrictions"""
        if not self.app_active:
            return False
        
        now = datetime.utcnow()
        
        # If no time restrictions set, app is accessible when active
        if not self.access_start_time and not self.access_end_time:
            return True
        
        # Check if within access time window
        if self.access_start_time and now < self.access_start_time:
            return False
        
        if self.access_end_time and now > self.access_end_time:
            return False
        
        return True
