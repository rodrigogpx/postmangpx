"""
PostmanGPX - Sistema de Envio de E-mails
Flask Application
"""
import os
import hashlib
import secrets
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data/postmangpx.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================
# Models
# ============================================

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    key_hash = db.Column(db.String(256), nullable=False, unique=True)
    key_prefix = db.Column(db.String(20), nullable=False)  # Para exibição
    is_active = db.Column(db.Boolean, default=True)
    rate_limit = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('api_keys', lazy=True))


class SmtpProvider(db.Model):
    __tablename__ = 'smtp_providers'
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.String(50), nullable=False)  # gmail, smtp, sendgrid, etc
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    username = db.Column(db.String(255))
    password = db.Column(db.String(255))
    use_tls = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('smtp_providers', lazy=True))


class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(db.String(36), primary_key=True)
    api_key_id = db.Column(db.String(36), db.ForeignKey('api_keys.id'))
    provider_id = db.Column(db.String(36), db.ForeignKey('smtp_providers.id'))
    to_address = db.Column(db.String(320), nullable=False)
    cc = db.Column(db.Text)
    bcc = db.Column(db.Text)
    subject = db.Column(db.String(500), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, sent, delivered, failed, bounced
    attempts = db.Column(db.Integer, default=0)
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)  # Quando foi entregue ao provedor
    delivery_status = db.Column(db.String(50))  # delivered, bounced, delayed, etc
    delivery_response = db.Column(db.Text)  # Resposta do servidor SMTP
    failure_reason = db.Column(db.Text)
    external_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    api_key = db.relationship('ApiKey', backref=db.backref('emails', lazy=True))
    provider = db.relationship('SmtpProvider', backref=db.backref('emails', lazy=True))


# ============================================
# Auth Decorator
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API Key required'}), 401
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key = ApiKey.query.filter_by(key_hash=key_hash, is_active=True).first()
        
        if not key:
            return jsonify({'error': 'Invalid API Key'}), 401
        
        key.last_used_at = datetime.utcnow()
        db.session.commit()
        
        request.api_key = key
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# Web Routes
# ============================================

@app.route('/')
@login_required
def dashboard():
    # Estatísticas
    total_emails = Email.query.count()
    sent_emails = Email.query.filter_by(status='sent').count()
    failed_emails = Email.query.filter_by(status='failed').count()
    pending_emails = Email.query.filter_by(status='pending').count()
    
    # Últimos e-mails
    recent_emails = Email.query.order_by(Email.created_at.desc()).limit(10).all()
    
    # API Keys
    api_keys_count = ApiKey.query.filter_by(is_active=True).count()
    
    # Providers
    providers_count = SmtpProvider.query.filter_by(is_active=True).count()
    
    return render_template('dashboard.html',
        total_emails=total_emails,
        sent_emails=sent_emails,
        failed_emails=failed_emails,
        pending_emails=pending_emails,
        recent_emails=recent_emails,
        api_keys_count=api_keys_count,
        providers_count=providers_count
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('login'))


@app.route('/api-keys')
@login_required
def api_keys():
    keys = ApiKey.query.filter_by(user_id=session['user_id']).all()
    return render_template('api_keys.html', api_keys=keys)


@app.route('/api-keys/create', methods=['POST'])
@login_required
def create_api_key():
    name = request.form.get('name', 'Nova API Key')
    
    # Gerar chave
    raw_key = f"pmgpx_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:20] + "..."
    
    api_key = ApiKey(
        id=secrets.token_hex(18),
        user_id=session['user_id'],
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix
    )
    
    db.session.add(api_key)
    db.session.commit()
    
    flash(f'API Key criada: {raw_key}', 'success')
    return redirect(url_for('api_keys'))


@app.route('/api-keys/<key_id>/delete', methods=['POST'])
@login_required
def delete_api_key(key_id):
    key = ApiKey.query.filter_by(id=key_id, user_id=session['user_id']).first()
    if key:
        db.session.delete(key)
        db.session.commit()
        flash('API Key removida.', 'success')
    return redirect(url_for('api_keys'))


@app.route('/providers')
@login_required
def providers():
    providers_list = SmtpProvider.query.filter_by(user_id=session['user_id']).all()
    return render_template('providers.html', providers=providers_list)


@app.route('/providers/create', methods=['GET', 'POST'])
@login_required
def create_provider():
    if request.method == 'POST':
        provider = SmtpProvider(
            id=secrets.token_hex(18),
            user_id=session['user_id'],
            name=request.form.get('name'),
            provider_type=request.form.get('provider_type'),
            host=request.form.get('host'),
            port=int(request.form.get('port', 587)),
            username=request.form.get('username'),
            password=request.form.get('password'),
            use_tls=request.form.get('use_tls') == 'on'
        )
        db.session.add(provider)
        db.session.commit()
        flash('Provedor SMTP criado com sucesso!', 'success')
        return redirect(url_for('providers'))
    
    return render_template('provider_form.html')


@app.route('/providers/<provider_id>/delete', methods=['POST'])
@login_required
def delete_provider(provider_id):
    provider = SmtpProvider.query.filter_by(id=provider_id, user_id=session['user_id']).first()
    if provider:
        db.session.delete(provider)
        db.session.commit()
        flash('Provedor removido.', 'success')
    return redirect(url_for('providers'))


@app.route('/emails')
@login_required
def emails():
    page = request.args.get('page', 1, type=int)
    emails_list = Email.query.order_by(Email.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('emails.html', emails=emails_list)


@app.route('/emails/<email_id>')
@login_required
def email_details(email_id):
    email = Email.query.filter_by(id=email_id).first_or_404()
    return render_template('email_details.html', email=email)


# ============================================
# API Routes
# ============================================

@app.route('/api/v1/send', methods=['POST'])
@api_key_required
def api_send_email():
    data = request.get_json(force=True)
    print(f'[DEBUG] Received data: {data}')
    print(f'[DEBUG] Data type: {type(data)}')
    
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    
    required = ['to', 'subject']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Field "{field}" is required'}), 400
    
    email = Email(
        id=secrets.token_hex(18),
        api_key_id=request.api_key.id,
        to_address=data['to'],
        cc=','.join(data.get('cc', [])) if isinstance(data.get('cc'), list) else data.get('cc'),
        bcc=','.join(data.get('bcc', [])) if isinstance(data.get('bcc'), list) else data.get('bcc'),
        subject=data['subject'],
        html_content=data.get('html'),
        text_content=data.get('text'),
        external_id=data.get('external_id'),
        status='pending'
    )
    
    db.session.add(email)
    db.session.commit()
    
    # TODO: Enviar para fila de processamento
    # Por enquanto, simular envio
    email.status = 'sent'
    email.sent_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'id': email.id,
        'status': email.status
    })


@app.route('/api/v1/status/<email_id>', methods=['GET'])
@api_key_required
def api_email_status(email_id):
    email = Email.query.filter_by(id=email_id).first()
    
    if not email:
        return jsonify({'error': 'Email not found'}), 404
    
    return jsonify({
        'id': email.id,
        'to': email.to_address,
        'subject': email.subject,
        'status': email.status,
        'delivery_status': email.delivery_status,
        'created_at': email.created_at.isoformat(),
        'sent_at': email.sent_at.isoformat() if email.sent_at else None,
        'delivered_at': email.delivered_at.isoformat() if email.delivered_at else None,
        'failure_reason': email.failure_reason,
        'delivery_response': email.delivery_response
    })


@app.route('/api/v1/delivery/<email_id>', methods=['POST'])
@api_key_required
def api_check_delivery(email_id):
    """Verifica o status de delivery de um email (simulação)"""
    email = Email.query.filter_by(id=email_id).first()
    
    if not email:
        return jsonify({'error': 'Email not found'}), 404
    
    if email.status != 'sent':
        return jsonify({'error': 'Email not sent yet'}), 400
    
    # Simulação de verificação de delivery
    # Em produção, isso verificaria com o servidor SMTP ou serviço de email
    import random
    delivery_statuses = ['delivered', 'bounced', 'delayed']
    weights = [0.85, 0.10, 0.05]  # 85% delivered, 10% bounced, 5% delayed
    
    delivery_status = random.choices(delivery_statuses, weights=weights)[0]
    
    if delivery_status == 'delivered':
        email.delivery_status = 'delivered'
        email.delivered_at = datetime.utcnow()
        email.delivery_response = '250 2.0.0 OK Message accepted for delivery'
        email.status = 'delivered'
    elif delivery_status == 'bounced':
        email.delivery_status = 'bounced'
        email.delivery_response = '550 5.1.1 User unknown'
        email.status = 'bounced'
        email.failure_reason = 'Email bounced - recipient not found'
    else:  # delayed
        email.delivery_status = 'delayed'
        email.delivery_response = '451 4.4.1 Temporary server error'
    
    db.session.commit()
    
    return jsonify({
        'id': email.id,
        'status': email.status,
        'delivery_status': email.delivery_status,
        'delivered_at': email.delivered_at.isoformat() if email.delivered_at else None,
        'delivery_response': email.delivery_response
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


# ============================================
# Inicialização
# ============================================

def init_db():
    """Inicializa o banco de dados e cria usuário admin padrão"""
    # Criar diretório de dados se não existir
    os.makedirs('data', exist_ok=True)
    
    with app.app_context():
        db.create_all()
        
        # Verificar se usuário admin existe
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                role='admin'
            )
            admin.set_password('Carbex100')
            db.session.add(admin)
            db.session.commit()
            print('[Init] Usuário admin criado (senha: Carbex100)')
        else:
            print('[Init] Usuário admin já existe')


# Inicializar banco de dados ao importar o módulo (necessário para Gunicorn)
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
