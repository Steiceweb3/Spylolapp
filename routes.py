import json
import uuid
import logging
import random
from datetime import datetime
from flask import render_template, request, jsonify, session, redirect, url_for
from app import app, db
from models import Enigma, UserProgress, AirdropConfig, AppConfig


def get_motivational_message(completed_count, total_enigmas):
    """Get motivational message based on progress"""
    
    # Motivational messages for every 2 questions
    progress_messages = [
        "Excellent work, agent. Your intelligence is above average.",
        "You're proving to be one of the best. HQ is keeping an eye on you.",
        "Sharp answers, just as we expect from a true secret agent.",
        "Keep it up. Few have come this far.",
        "Outstanding performance. The conspiracy deepens with each answer.",
        "Your analytical skills are impressive. Agent 404 would be proud.",
        "Exceptional deduction abilities detected. Continue the investigation.",
        "Top-tier intelligence confirmed. You're getting closer to the truth."
    ]
    
    # Final recruitment messages
    final_messages = [
        "Mission accomplished. You've been selected to join our Secret HQ. Welcome to the elite.",
        "Congratulations, agent. You are now recruited into our Secret HQ. Prepare for upcoming missions.",
        "Outstanding! You have proven worthy of the highest clearance. Welcome to Agent 404's inner circle.",
        "Recruitment complete. Your skills have earned you a place among the conspiracy's greatest minds."
    ]
    
    # Show motivational message every 2 correct answers
    if completed_count > 0 and completed_count % 2 == 0 and completed_count < total_enigmas:
        return {
            'type': 'progress',
            'message': random.choice(progress_messages),
            'title': 'INTELLIGENCE ASSESSMENT'
        }
    
    # Show final recruitment message when all questions are completed
    elif completed_count >= total_enigmas and total_enigmas > 0:
        return {
            'type': 'final',
            'message': random.choice(final_messages),
            'title': 'MISSION COMPLETE - RECRUITMENT CONFIRMED'
        }
    
    return None


def check_app_access():
    """Check if app is currently accessible"""
    app_config = AppConfig.query.first()
    if not app_config:
        # Create default config if none exists
        app_config = AppConfig()
        db.session.add(app_config)
        db.session.commit()
    
    return app_config.is_accessible(), app_config.maintenance_message


@app.route('/')
def index():
    """Home page"""
    accessible, message = check_app_access()
    if not accessible:
        return render_template('maintenance.html', message=message), 503
    
    return render_template('index.html', now=datetime.utcnow())


@app.route('/game')
def game():
    """Game page displaying enigmas"""
    accessible, message = check_app_access()
    if not accessible:
        return render_template('maintenance.html', message=message), 503
    # Ensure the user has a session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        
    # Get user progress or create new
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    
    if user_progress is None:
        # New user, create randomized enigma order
        import random
        all_enigmas = Enigma.query.all()
        
        if not all_enigmas:
            return render_template('game.html', error="No enigmas found in the database.", now=datetime.utcnow())
        
        # Randomize the order of enigmas for this user
        enigma_ids = [enigma.id for enigma in all_enigmas]
        random.shuffle(enigma_ids)
        
        # Create new user progress
        user_progress = UserProgress()
        user_progress.session_id = session['session_id']
        user_progress.current_enigma_id = enigma_ids[0]  # Start with first in randomized order
        user_progress.completed_enigmas = '[]'
        user_progress.enigma_order = json.dumps(enigma_ids)  # Store randomized order
        user_progress.total_points = 0
        user_progress.last_active = datetime.utcnow()
        user_progress.token_eligibility = False
        
        db.session.add(user_progress)
        db.session.commit()
    
    # Get the current enigma
    current_enigma = Enigma.query.get(user_progress.current_enigma_id)
    
    if not current_enigma:
        return render_template('game.html', error="Error loading enigma.", now=datetime.utcnow())
    
    # Parse completed enigmas and enigma order
    completed_enigmas = json.loads(user_progress.completed_enigmas)
    enigma_order = json.loads(user_progress.enigma_order)
    
    # Get current position in randomized order
    current_position = enigma_order.index(int(user_progress.current_enigma_id)) + 1
    total_enigmas = len(enigma_order)
    
    return render_template(
        'game.html',
        enigma=current_enigma,
        user_progress=user_progress,
        completed_count=len(completed_enigmas),
        total_enigmas=total_enigmas,
        current_position=current_position,
        progress_percentage=int((len(completed_enigmas) / total_enigmas) * 100) if total_enigmas > 0 else 0,
        now=datetime.utcnow()
    )


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Handle answer submission"""
    accessible, message = check_app_access()
    if not accessible:
        return jsonify({'success': False, 'message': 'App is currently unavailable'}), 503
        
    if 'session_id' not in session:
        return jsonify({'success': False, 'message': 'Session expired, please refresh'})
    
    data = request.json
    user_answer = data.get('answer', '').strip().lower() if data else ''
    enigma_id = data.get('enigma_id') if data else None
    
    if not user_answer or not enigma_id:
        return jsonify({'success': False, 'message': 'Invalid submission'})
    
    # Get current enigma
    enigma = Enigma.query.get(enigma_id)
    if not enigma:
        return jsonify({'success': False, 'message': 'Enigma not found'})
    
    # Get user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        return jsonify({'success': False, 'message': 'User progress not found'})
    
    # Normalize both answers for comparison
    def normalize_answer(text):
        import re
        # Remove extra spaces and convert to uppercase
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        return text.strip().upper()
    
    # Check if the answer is correct - support multiple correct answers
    normalized_user = normalize_answer(user_answer)
    
    # Parse possible answers (can be JSON array or single string)
    import json
    try:
        possible_answers = json.loads(enigma.answer)
        if not isinstance(possible_answers, list):
            possible_answers = [possible_answers]
    except (json.JSONDecodeError, TypeError):
        # If not JSON, treat as single answer
        possible_answers = [enigma.answer]
    
    # Check if user answer matches any of the possible answers
    is_correct = any(normalize_answer(correct_answer) == normalized_user for correct_answer in possible_answers)
    
    response = {
        'success': True,
        'is_correct': is_correct,
        'feedback': enigma.correct_feedback if is_correct else enigma.incorrect_feedback
    }
    
    # If correct, update user progress
    if is_correct:
        # Parse completed enigmas
        completed_enigmas = json.loads(user_progress.completed_enigmas)
        
        # Only add points if this enigma hasn't been completed before
        if enigma_id not in completed_enigmas:
            completed_enigmas.append(enigma_id)
            user_progress.completed_enigmas = json.dumps(completed_enigmas)
            user_progress.total_points += enigma.points
            
            # Check if user has completed all enigmas
            total_enigmas = Enigma.query.count()
            if len(completed_enigmas) >= total_enigmas:
                user_progress.token_eligibility = True
                response['completed_all'] = True
            
            # Find next enigma using randomized order
            enigma_order = json.loads(user_progress.enigma_order)
            current_index = enigma_order.index(int(enigma_id))
            
            # If there's a next enigma in the randomized order
            if current_index + 1 < len(enigma_order):
                next_enigma_id = enigma_order[current_index + 1]
                user_progress.current_enigma_id = next_enigma_id
                response['next_enigma'] = True
        
        user_progress.last_active = datetime.utcnow()
        db.session.commit()
        
        # Update progress stats for the response
        total_enigmas = Enigma.query.count()
        completed_count = len(completed_enigmas)
        response['progress'] = {
            'completed_count': completed_count,
            'total_enigmas': total_enigmas,
            'progress_percentage': int((completed_count / total_enigmas) * 100) if total_enigmas > 0 else 0,
            'total_points': user_progress.total_points
        }
        
        # Check for motivational messages
        motivational_message = get_motivational_message(completed_count, total_enigmas)
        if motivational_message:
            response['motivational_message'] = motivational_message
    
    return jsonify(response)


def is_valid_solana_address(address):
    """Validate if address is a real Solana public key"""
    if not address or len(address) < 32 or len(address) > 44:
        return False
    
    # Check if it's obviously a demo address
    if any(keyword in address.upper() for keyword in ['DEMO', 'TEST', 'SPY', 'LOL']):
        return False
    
    try:
        import base58
        decoded = base58.b58decode(address)
        return len(decoded) == 32  # Solana public keys are 32 bytes
    except:
        return False


@app.route('/connect_wallet_real', methods=['POST'])
def connect_wallet_real():
    """Handle real Solana wallet connection - AIRDROP ELIGIBLE"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    data = request.json
    wallet_address = data.get('wallet_address') if data else None
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'No wallet address provided'})
    
    # Validate real Solana address
    if not is_valid_solana_address(wallet_address):
        return jsonify({'success': False, 'message': 'Invalid Solana wallet address'})
    
    # Get or create user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        first_enigma = Enigma.query.order_by(Enigma.order_position).first()
        if first_enigma:
            user_progress = UserProgress(
                session_id=session['session_id'],
                current_enigma_id=first_enigma.id
            )
            db.session.add(user_progress)
            db.session.commit()
    
    # Save REAL wallet - ELIGIBLE for airdrop
    user_progress.wallet_address = wallet_address
    user_progress.last_active = datetime.utcnow()
    user_progress.token_eligibility = True  # ✅ AIRDROP ELIGIBLE
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'wallet_address': wallet_address, 
        'airdrop_eligible': True
    })


@app.route('/export_airdrop_wallets')
def export_airdrop_wallets():
    """Export eligible wallets for REAL airdrop distribution"""
    # Get users with REAL wallets eligible for airdrop
    eligible_users = UserProgress.query.filter(
        UserProgress.wallet_address.isnot(None),
        UserProgress.token_eligibility == True,
        UserProgress.total_points >= 50  # Minimum points threshold
    ).all()
    
    airdrop_list = []
    for user in eligible_users:
        # Double-check: skip any demo addresses that might have slipped through
        if not user.wallet_address or any(keyword in user.wallet_address.upper() 
                                        for keyword in ['DEMO', 'TEST', 'SPY', 'LOL']):
            continue
            
        airdrop_list.append({
            'wallet_address': user.wallet_address,
            'total_points': user.total_points,
            'token_amount': user.total_points * 1000000,  # 1M tokens per point
            'completed_enigmas': len(json.loads(user.completed_enigmas)),
            'last_active': user.last_active.isoformat() if user.last_active else None
        })
    
    return jsonify({
        'eligible_wallets': len(airdrop_list),
        'total_tokens_to_distribute': sum(item['token_amount'] for item in airdrop_list),
        'airdrop_data': airdrop_list,
        'export_date': datetime.utcnow().isoformat()
    })


@app.route('/profile')
def profile():
    """User profile and progress page"""
    accessible, message = check_app_access()
    if not accessible:
        return render_template('maintenance.html', message=message), 503
    if 'session_id' not in session:
        return redirect(url_for('game'))
    
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    
    if not user_progress:
        return redirect(url_for('game'))
    
    # Parse completed enigmas
    completed_enigmas = json.loads(user_progress.completed_enigmas)
    completed_enigma_objects = Enigma.query.filter(Enigma.id.in_(completed_enigmas)).all()
    
    # Get total enigma count for progress calculation
    total_enigmas = Enigma.query.count()
    progress_percentage = int((len(completed_enigmas) / total_enigmas) * 100) if total_enigmas > 0 else 0
    
    return render_template(
        'profile.html',
        user_progress=user_progress,
        completed_enigmas=completed_enigma_objects,
        completed_count=len(completed_enigmas),
        total_enigmas=total_enigmas,
        progress_percentage=progress_percentage,
        now=datetime.utcnow()
    )


@app.route('/wallet')
def wallet():
    """Wallet connection and token claiming page"""
    accessible, message = check_app_access()
    if not accessible:
        return render_template('maintenance.html', message=message), 503
    if 'session_id' not in session:
        return redirect(url_for('game'))
    
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    
    if not user_progress:
        return redirect(url_for('game'))
    
    # Parse completed enigmas
    completed_enigmas = json.loads(user_progress.completed_enigmas)
    
    # Get total enigma count for progress calculation
    total_enigmas = Enigma.query.count()
    progress_percentage = int((len(completed_enigmas) / total_enigmas) * 100) if total_enigmas > 0 else 0
    
    return render_template(
        'wallet.html',
        user_progress=user_progress,
        completed_count=len(completed_enigmas),
        total_enigmas=total_enigmas,
        progress_percentage=progress_percentage,
        now=datetime.utcnow()
    )


@app.route('/connect_wallet_simple')
def connect_wallet_simple():
    """Simple wallet connection via GET request"""
    # Ensure user has a session
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Get or create user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        # Create new user progress starting from first enigma
        first_enigma = Enigma.query.order_by(Enigma.order_position).first()
        if first_enigma:
            user_progress = UserProgress(
                session_id=session['session_id'],
                current_enigma_id=first_enigma.id
            )
            db.session.add(user_progress)
            db.session.commit()
    
    # Generate a wallet address for demo
    import time
    wallet_address = 'SPY' + str(int(time.time()))[-6:] + 'LOL'
    
    # Update wallet address
    user_progress.wallet_address = wallet_address
    user_progress.last_active = datetime.utcnow()
    db.session.commit()
    
    return redirect(url_for('wallet'))


@app.route('/connect_wallet_simple', methods=['POST'])
def connect_wallet_simple_post():
    """Handle AJAX wallet connection"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    data = request.json
    wallet_address = data.get('wallet_address') if data else None
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'No wallet address provided'})
    
    # Get or create user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        first_enigma = Enigma.query.order_by(Enigma.order_position).first()
        if first_enigma:
            user_progress = UserProgress(
                session_id=session['session_id'],
                current_enigma_id=first_enigma.id
            )
            db.session.add(user_progress)
            db.session.commit()
    
    if user_progress:
        user_progress.wallet_address = wallet_address
        user_progress.last_active = datetime.utcnow()
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Wallet connected successfully'})

@app.route('/connect_wallet_form', methods=['POST'])
def connect_wallet_form():
    """Handle wallet connection via form submission"""
    if 'session_id' not in session:
        return redirect(url_for('wallet'))
    
    # Get user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        return redirect(url_for('game'))
    
    # Generate a wallet address for demo
    import time
    wallet_address = 'SPY' + str(int(time.time()))[-6:] + 'LOL'
    
    # Update wallet address
    user_progress.wallet_address = wallet_address
    user_progress.last_active = datetime.utcnow()
    db.session.commit()
    
    return redirect(url_for('wallet'))

@app.route('/connect_wallet', methods=['POST'])
def connect_wallet():
    """Handle wallet connection"""
    if 'session_id' not in session:
        return jsonify({'success': False, 'message': 'Session expired, please refresh'})
    
    data = request.json
    wallet_address = data.get('wallet_address') if data else None
    wallet_type = data.get('wallet_type', 'unknown')
    
    if not wallet_address:
        return jsonify({'success': False, 'message': 'No wallet address provided'})
    
    # Validate Solana wallet address format (basic check)
    if not wallet_address.replace('...', '').replace('-', '').replace('_', '').isalnum():
        return jsonify({'success': False, 'message': 'Invalid wallet address format'})
    
    # Get or create user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        # Create new user progress starting from first enigma
        first_enigma = Enigma.query.order_by(Enigma.order_position).first()
        if first_enigma:
            user_progress = UserProgress(
                session_id=session['session_id'],
                current_enigma_id=first_enigma.id
            )
            db.session.add(user_progress)
            db.session.commit()
    
    # Update wallet address
    user_progress.wallet_address = wallet_address
    user_progress.last_active = datetime.utcnow()
    
    # Calculate airdrop amount based on current points
    user_progress.airdrop_amount = user_progress.total_points * 1000000  # 1 token per point
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Wallet connected successfully',
        'wallet_address': wallet_address
    })


@app.route('/disconnect_wallet', methods=['GET', 'POST'])
def disconnect_wallet():
    """Handle wallet disconnection"""
    if 'session_id' not in session:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'No session found'})
        else:
            return redirect(url_for('wallet'))
    
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        if request.method == 'POST':
            return jsonify({'success': False, 'message': 'User progress not found'})
        else:
            return redirect(url_for('wallet'))
    
    # Remove wallet address and reset airdrop status
    user_progress.wallet_address = None
    user_progress.airdrop_status = 'pending'
    user_progress.airdrop_tx_hash = None
    user_progress.airdrop_sent_at = None
    user_progress.last_active = datetime.utcnow()
    
    db.session.commit()
    
    if request.method == 'POST':
        return jsonify({'success': True, 'message': 'Wallet disconnected successfully'})
    else:
        return redirect(url_for('wallet'))


@app.route('/claim_tokens', methods=['POST'])
def claim_tokens():
    """Handle token claiming"""
    if 'session_id' not in session:
        return jsonify({'success': False, 'message': 'Session expired, please refresh'})
    
    # Get user progress
    user_progress = UserProgress.query.filter_by(session_id=session['session_id']).first()
    if not user_progress:
        return jsonify({'success': False, 'message': 'User progress not found'})
    
    if not user_progress.wallet_address:
        return jsonify({'success': False, 'message': 'No wallet connected'})
    
    if not user_progress.token_eligibility:
        return jsonify({'success': False, 'message': 'Not eligible for tokens yet. Complete more enigmas!'})
    
    # This is a mock implementation - in a real app, this would interact with a blockchain
    return jsonify({
        'success': True,
        'message': 'Congratulations! $SPYLOL tokens have been sent to your wallet!',
        'tokens_sent': True
    })


@app.route('/get_hint', methods=['POST'])
def get_hint():
    """Get a hint for the current enigma"""
    if 'session_id' not in session:
        return jsonify({'success': False, 'message': 'Session expired, please refresh'})
    
    data = request.json
    enigma_id = data.get('enigma_id') if data else None
    
    if not enigma_id:
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    # Get current enigma
    enigma = Enigma.query.get(enigma_id)
    if not enigma or not enigma.hint:
        return jsonify({'success': False, 'message': 'No hint available'})
    
    return jsonify({
        'success': True,
        'hint': enigma.hint
    })


# Administrative routes for access control
@app.route('/admin/access-control')
def admin_access_control():
    """Admin interface for controlling app access"""
    app_config = AppConfig.query.first()
    if not app_config:
        app_config = AppConfig()
        db.session.add(app_config)
        db.session.commit()
    
    return render_template('admin/access_control.html', config=app_config, now=datetime.utcnow())


@app.route('/admin/update-access', methods=['POST'])
def admin_update_access():
    """Update app access configuration"""
    data = request.get_json()
    
    app_config = AppConfig.query.first()
    if not app_config:
        app_config = AppConfig()
        db.session.add(app_config)
    
    app_config.app_active = data.get('app_active', True)
    app_config.maintenance_message = data.get('maintenance_message', 'App is temporarily unavailable')
    
    # Handle datetime strings
    if data.get('access_start_time'):
        try:
            app_config.access_start_time = datetime.fromisoformat(data['access_start_time'].replace('Z', '+00:00'))
        except:
            app_config.access_start_time = None
    else:
        app_config.access_start_time = None
    
    if data.get('access_end_time'):
        try:
            app_config.access_end_time = datetime.fromisoformat(data['access_end_time'].replace('Z', '+00:00'))
        except:
            app_config.access_end_time = None
    else:
        app_config.access_end_time = None
    
    app_config.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Access configuration updated successfully',
        'is_accessible': app_config.is_accessible()
    })


@app.route('/admin/toggle-access', methods=['POST'])
def admin_toggle_access():
    """Quick toggle for app access"""
    app_config = AppConfig.query.first()
    if not app_config:
        app_config = AppConfig()
        db.session.add(app_config)
    
    app_config.app_active = not app_config.app_active
    app_config.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'app_active': app_config.app_active,
        'is_accessible': app_config.is_accessible()
    })
