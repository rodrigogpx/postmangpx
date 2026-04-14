"""
PostmanGPX - Sistema de Envio de E-mails
Flask Application
"""
import os
import hashlib
import secrets
import smtplib
import ssl
import base64
from email.message import EmailMessage
from email.utils import parseaddr
from io import StringIO
from contextlib import redirect_stdout
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
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
    provider_id = db.Column(db.String(36), db.ForeignKey('smtp_providers.id'))
    name = db.Column(db.String(255), nullable=False)
    key_hash = db.Column(db.String(256), nullable=False, unique=True)
    key_prefix = db.Column(db.String(20), nullable=False)  # Para exibição
    is_active = db.Column(db.Boolean, default=True)
    rate_limit = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('api_keys', lazy=True))
    provider = db.relationship('SmtpProvider', backref=db.backref('api_keys', lazy=True))


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

    # Tracking columns
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    open_count = db.Column(db.Integer, default=0)
    click_count = db.Column(db.Integer, default=0)
    tracking_enabled = db.Column(db.Boolean, default=True)
    tracking_token = db.Column(db.String(64), unique=True)  # Token único para tracking

    api_key = db.relationship('ApiKey', backref=db.backref('emails', lazy=True))
    provider = db.relationship('SmtpProvider', backref=db.backref('emails', lazy=True))


class EmailEvent(db.Model):
    __tablename__ = 'email_events'
    id = db.Column(db.String(36), primary_key=True)
    email_id = db.Column(db.String(36), db.ForeignKey('emails.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # delivered, bounced, opened, clicked, complained, etc
    provider = db.Column(db.String(50))  # SES, SendGrid, Mailgun, etc
    ip_address = db.Column(db.String(45))  # IP do usuário (para opened/clicked)
    user_agent = db.Column(db.Text)  # User agent (para opened/clicked)
    link_url = db.Column(db.Text)  # URL clicada (para clicked)
    event_metadata = db.Column(db.Text)  # JSON com dados extras do evento (renomeado de metadata)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    email = db.relationship('Email', backref=db.backref('events', lazy=True, order_by='EmailEvent.created_at.desc()'))


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


@app.route('/update-system', methods=['POST'])
@login_required
def update_system():
    if session.get('role') != 'admin':
        flash('Apenas administradores podem atualizar o sistema.', 'error')
        return redirect(url_for('dashboard'))
        
    try:
        import subprocess
        # Executa o script de atualização em background para não bloquear a requisição atual
        # que seria derrubada quando o container reiniciar
        subprocess.Popen(['bash', 'update.sh'], start_new_session=True)
        flash('Atualização do sistema iniciada! O sistema será reiniciado em breve.', 'success')
    except Exception as e:
        flash(f'Erro ao iniciar atualização: {str(e)}', 'error')
        
    return redirect(url_for('settings'))


@app.route('/settings')
@login_required
def settings():
    if session.get('role') != 'admin':
        flash('Acesso negado. Apenas administradores podem acessar as configurações.', 'error')
        return redirect(url_for('dashboard'))
        
    users = User.query.all()
    
    # Obter versão do git (short hash)
    git_version = "Desconhecida"
    try:
        import subprocess
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                               capture_output=True, text=True, check=True)
        git_version = result.stdout.strip()
    except Exception:
        pass
        
    return render_template('settings.html', users=users, git_version=git_version)


@app.route('/settings/users/create', methods=['POST'])
@login_required
def create_user():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
        
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if User.query.filter_by(username=username).first():
        flash('Nome de usuário já existe.', 'error')
        return redirect(url_for('settings'))
        
    user = User(username=username, role=role)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'Usuário {username} criado com sucesso!', 'success')
    return redirect(url_for('settings'))


@app.route('/settings/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
        
    if user_id == session.get('user_id'):
        flash('Você não pode excluir seu próprio usuário.', 'error')
        return redirect(url_for('settings'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash('Usuário removido com sucesso.', 'success')
    return redirect(url_for('settings'))


@app.route('/api-keys')
@login_required
def api_keys():
    keys = ApiKey.query.filter_by(user_id=session['user_id']).all()
    providers_list = SmtpProvider.query.filter_by(user_id=session['user_id']).all()
    return render_template('api_keys.html', api_keys=keys, providers=providers_list)


@app.route('/api-keys/create', methods=['POST'])
@login_required
def create_api_key():
    name = request.form.get('name', 'Nova API Key')
    provider_id = request.form.get('provider_id')
    
    # Gerar chave
    raw_key = f"pmgpx_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:20] + "..."
    
    api_key = ApiKey(
        id=secrets.token_hex(18),
        user_id=session['user_id'],
        provider_id=provider_id if provider_id else None,
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


@app.route('/api-keys/<key_id>/provider', methods=['POST'])
@login_required
def set_api_key_provider(key_id):
    key = ApiKey.query.filter_by(id=key_id, user_id=session['user_id']).first_or_404()
    provider_id = request.form.get('provider_id')

    if provider_id:
        provider = SmtpProvider.query.filter_by(id=provider_id, user_id=session['user_id'], is_active=True).first()
        if not provider:
            flash('Provedor inválido ou inativo.', 'error')
            return redirect(url_for('api_keys'))
        key.provider_id = provider.id
    else:
        key.provider_id = None

    db.session.commit()
    flash('Provedor de envio atualizado para a API Key.', 'success')
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
    
    return render_template('provider_edit.html', provider=None, edit_mode=False)


@app.route('/providers/<provider_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_provider(provider_id):
    provider = SmtpProvider.query.filter_by(id=provider_id, user_id=session['user_id']).first_or_404()

    if request.method == 'POST':
        provider.name = request.form.get('name')
        provider.provider_type = request.form.get('provider_type')
        provider.host = request.form.get('host')
        provider.port = int(request.form.get('port', 587))
        provider.username = request.form.get('username')
        # So atualiza senha se foi fornecida
        if request.form.get('password'):
            provider.password = request.form.get('password')
        provider.use_tls = request.form.get('use_tls') == 'on'
        provider.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash('Provedor SMTP atualizado com sucesso!', 'success')
        return redirect(url_for('providers'))

    return render_template('provider_edit.html', provider=provider, edit_mode=True)


@app.route('/providers/<provider_id>/delete', methods=['POST'])
@login_required
def delete_provider(provider_id):
    provider = SmtpProvider.query.filter_by(id=provider_id, user_id=session['user_id']).first()
    if provider:
        db.session.delete(provider)
        db.session.commit()
        flash('Provedor removido.', 'success')
    return redirect(url_for('providers'))


@app.route('/providers/<provider_id>/test', methods=['POST'])
@login_required
def test_provider(provider_id):
    provider = SmtpProvider.query.filter_by(id=provider_id, user_id=session['user_id']).first_or_404()
    test_to = request.form.get('test_to')
    if not test_to:
        flash('Informe o email do destinatário para teste.', 'error')
        return redirect(url_for('providers'))

    from_address = provider.username or test_to

    try:
        refused, log = _smtp_send(
            provider=provider,
            from_address=from_address,
            to_address=test_to,
            subject='Teste SMTP - PostmanGPX',
            html='<p>Teste de envio SMTP via PostmanGPX</p>',
            text_content='Teste de envio SMTP via PostmanGPX'
        )

        log_preview = (log or '')[-2000:]

        if refused:
            flash(f'Falha ao enviar teste. Recusados: {refused}. Log: {log_preview}', 'error')
            return redirect(url_for('providers'))

        flash(f'Teste enviado com sucesso. Log SMTP: {log_preview}', 'success')
        return redirect(url_for('providers'))
    except Exception as e:
        flash(f'Falha ao enviar teste: {str(e)}', 'error')
        return redirect(url_for('providers'))


def _get_active_provider(user_id: int):
    return (
        SmtpProvider.query
        .filter_by(user_id=user_id, is_active=True)
        .order_by(SmtpProvider.priority.desc(), SmtpProvider.created_at.desc())
        .first()
    )


def _extract_email(value: str | None):
    if not value:
        return None
    _, addr = parseaddr(value)
    addr = (addr or '').strip()
    return addr or None


def _inject_tracking(html_content: str, token: str) -> str:
    """Injeta pixel de tracking e substitui links no HTML"""
    import re
    from urllib.parse import quote

    if not html_content:
        return html_content

    # URL base para tracking (deve ser configurável via env)
    tracking_base = os.environ.get('TRACKING_BASE_URL', 'http://localhost:3000')

    # 1. Injetar pixel de abertura (1x1 transparente GIF)
    pixel_url = f"{tracking_base}/track/open/{token}"
    pixel_img = f'<img src="{pixel_url}" width="1" height="1" alt="" style="display:block;width:1px;height:1px;" />'

    # Tentar injetar antes do </body> ou </html>, ou no final
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{pixel_img}</body>')
    elif '</html>' in html_content:
        html_content = html_content.replace('</html>', f'{pixel_img}</html>')
    else:
        html_content = html_content + pixel_img

    # 2. Substituir links por proxy de tracking
    # Padrão: href="URL" ou href='URL'
    def replace_link(match):
        full_match = match.group(0)
        url = match.group(1) or match.group(2)  # Captura de aspas duplas ou simples

        # Não substituir links internos (tel:, mailto:, #, javascript:)
        if url.startswith(('tel:', 'mailto:', '#', 'javascript:', 'data:')):
            return full_match

        # Criar URL de tracking
        tracking_url = f"{tracking_base}/track/click/{token}?url={quote(url, safe='')}"  # noqa: E501
        return full_match.replace(url, tracking_url)

    # Regex para capturar href="URL" ou href='URL'
    html_content = re.sub(
        r'href=["\']([^"\']+)["\']',
        replace_link,
        html_content
    )

    return html_content


def _smtp_send(
    provider: SmtpProvider,
    from_address: str,
    to_address: str,
    subject: str,
    html: str | None,
    text_content: str | None,
    reply_to: str | None = None,
    cc: str | None = None,
    bcc: str | None = None,
    attachments: list[dict] | None = None,
):
    if not provider.host or not provider.port:
        raise ValueError('SMTP provider host/port not configured')
 
    msg = EmailMessage()
    msg['From'] = from_address
    msg['To'] = to_address
    if cc:
        msg['Cc'] = cc
    if bcc:
        # NOTE: EmailMessage/send_message pode usar este header para determinar destinatários.
        # Alguns clientes exibem Bcc se não for removido, então removemos antes de enviar.
        msg['Bcc'] = bcc
    msg['Subject'] = subject
    if reply_to:
        msg['Reply-To'] = reply_to
    msg.set_content(text_content or '', subtype='plain')
    if html:
        msg.add_alternative(html, subtype='html')

    if attachments:
        for att in attachments:
            filename = att.get('filename')
            content_type = att.get('contentType') or att.get('content_type') or 'application/octet-stream'
            content_base64 = att.get('contentBase64') or att.get('content_base64')
            cid = att.get('cid')
            disposition = att.get('disposition') or ('inline' if cid else 'attachment')

            if not filename or not content_base64:
                raise ValueError('Attachment requires filename and contentBase64')

            try:
                raw = base64.b64decode(content_base64)
            except Exception:
                raise ValueError('Invalid attachment contentBase64')

            maintype, subtype = (content_type.split('/', 1) + ['octet-stream'])[:2]

            if cid and html:
                html_part = msg.get_payload()[-1]
                html_part.add_related(
                    raw,
                    maintype=maintype,
                    subtype=subtype,
                    cid=f"<{cid}>",
                    filename=filename,
                    disposition=disposition,
                )
            else:
                msg.add_attachment(
                    raw,
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename,
                    disposition=disposition,
                )

    buffer = StringIO()
    with redirect_stdout(buffer):
        ctx = ssl.create_default_context()
        if provider.port == 465 and provider.use_tls:
            with smtplib.SMTP_SSL(provider.host, provider.port, timeout=30, context=ctx) as smtp:
                smtp.set_debuglevel(1)
                if provider.username and provider.password:
                    smtp.login(provider.username, provider.password)
                if 'Bcc' in msg:
                    del msg['Bcc']
                refused = smtp.send_message(msg)
        else:
            with smtplib.SMTP(provider.host, provider.port, timeout=30) as smtp:
                smtp.set_debuglevel(1)
                if provider.use_tls:
                    smtp.starttls(context=ctx)
                if provider.username and provider.password:
                    smtp.login(provider.username, provider.password)
                if 'Bcc' in msg:
                    del msg['Bcc']
                refused = smtp.send_message(msg)

    return refused, buffer.getvalue()


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

    provider = None
    provider_source = None

    if getattr(request.api_key, 'provider_id', None):
        # API Key TEM provider designado -> OBRIGATORIO usar esse provider
        provider = SmtpProvider.query.filter_by(
            id=request.api_key.provider_id,
            user_id=request.api_key.user_id,
            is_active=True,
        ).first()

        if not provider:
            email.status = 'failed'
            email.failure_reason = f'Provider {request.api_key.provider_id} not found or inactive for this API key'
            db.session.commit()
            return jsonify({
                'error': 'Configured provider not available',
                'provider_id': request.api_key.provider_id,
                'message': 'This API key is tied to a specific provider that is currently unavailable. '
                           'Please check provider status or use an API key without provider restriction.'
            }), 400

        provider_source = 'api_key_configured'
    else:
        # API Key NAO TEM provider designado -> usar qualquer provider ativo do usuario
        provider = _get_active_provider(request.api_key.user_id)
        if not provider:
            email.status = 'failed'
            email.failure_reason = 'No active SMTP provider configured'
            db.session.commit()
            return jsonify({'error': 'No active SMTP provider configured'}), 400
        provider_source = 'user_default'

    email.provider_id = provider.id

    # Gerar token de tracking
    email.tracking_token = secrets.token_hex(32)
    db.session.commit()

    try:
        requested_from = data.get('from')
        requested_reply_to = data.get('replyTo') or data.get('reply_to')

        attachments = data.get('attachments')
        if attachments is not None and not isinstance(attachments, list):
            raise ValueError('Field "attachments" must be a list')

        provider_email = _extract_email(provider.username)
        requested_from_email = _extract_email(requested_from)

        # Política simples anti-spoofing:
        # - Se o provider tem username/email e o "from" solicitado não bate com ele,
        #   manter From como provider.username e usar Reply-To como solicitado.
        # - Se não existe provider.username, aceitar o From solicitado.
        if provider_email and requested_from_email and requested_from_email.lower() != provider_email.lower():
            from_address = provider.username
            reply_to = requested_from_email
        else:
            from_address = requested_from or provider.username or email.to_address
            reply_to = _extract_email(requested_reply_to)

        # Processar HTML para tracking (se habilitado)
        html_content = email.html_content
        if html_content and email.tracking_enabled:
            html_content = _inject_tracking(html_content, email.tracking_token)

        refused, log = _smtp_send(
            provider=provider,
            from_address=from_address,
            to_address=email.to_address,
            subject=email.subject,
            html=html_content,
            text_content=email.text_content,
            reply_to=reply_to,
            cc=email.cc,
            bcc=email.bcc,
            attachments=attachments,
        )

        if refused:
            email.status = 'failed'
            email.failure_reason = f'Recipient refused: {refused}'
            email.delivery_response = log
            db.session.commit()
            return jsonify({'success': False, 'id': email.id, 'status': email.status, 'error': email.failure_reason}), 500

        email.status = 'sent'
        email.sent_at = datetime.utcnow()
        email.delivery_status = 'smtp_accepted'
        email.delivered_at = datetime.utcnow()
        email.delivery_response = log
        db.session.commit()
    except Exception as e:
        email.status = 'failed'
        email.failure_reason = str(e)
        try:
            email.delivery_response = (email.delivery_response or '')
        except Exception:
            pass
        db.session.commit()
        return jsonify({'success': False, 'id': email.id, 'status': email.status, 'error': email.failure_reason}), 500
     
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
# Tracking Routes (Pixel + Click)
# ============================================

@app.route('/track/open/<token>')
def track_open(token):
    """Tracking pixel - registra abertura de email"""
    email = Email.query.filter_by(tracking_token=token).first()

    if email and email.tracking_enabled:
        # Atualizar estatísticas
        email.open_count += 1
        if not email.opened_at:
            email.opened_at = datetime.utcnow()

        # Registrar evento
        event = EmailEvent(
            id=secrets.token_hex(18),
            email_id=email.id,
            event_type='opened',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        db.session.add(event)
        db.session.commit()

    # Retornar pixel 1x1 transparente GIF
    pixel = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
    return pixel, 200, {'Content-Type': 'image/gif', 'Cache-Control': 'no-cache, no-store, must-revalidate'}


@app.route('/track/click/<token>')
def track_click(token):
    """Redireciona e registra clique em link"""
    url = request.args.get('url')

    email = Email.query.filter_by(tracking_token=token).first()

    if email and email.tracking_enabled:
        # Atualizar estatísticas
        email.click_count += 1
        if not email.clicked_at:
            email.clicked_at = datetime.utcnow()

        # Registrar evento
        event = EmailEvent(
            id=secrets.token_hex(18),
            email_id=email.id,
            event_type='clicked',
            link_url=url,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        db.session.add(event)
        db.session.commit()

    # Redirecionar para URL original ou página de erro
    if url:
        return redirect(url)
    return 'Link não encontrado', 404


# ============================================
# Webhook Routes (Provider callbacks)
# ============================================

@app.route('/webhooks/ses', methods=['POST'])
def webhook_ses():
    """Recebe callbacks do Amazon SES"""
    data = request.get_json(force=True, silent=True) or {}

    # SES envia notificações SNS que precisam ser processadas
    # ou diretamente via HTTP POST em configurações de eventos
    if 'Message' in data:  # Formato SNS
        import json
        try:
            message = json.loads(data['Message'])
            event_type = message.get('eventType') or message.get('notificationType')
            message_id = message.get('mail', {}).get('messageId')
        except:
            return jsonify({'error': 'Invalid SNS message'}), 400
    else:  # Formato direto
        event_type = data.get('eventType')
        message_id = data.get('mail', {}).get('messageId')

    if not message_id:
        return jsonify({'error': 'MessageId required'}), 400

    # Buscar email pelo external_id (MessageId do SES)
    email = Email.query.filter_by(external_id=message_id).first()
    if not email:
        return jsonify({'error': 'Email not found'}), 404

    # Mapear evento SES para nosso formato
    event_mapping = {
        'send': 'sent',
        'delivery': 'delivered',
        'bounce': 'bounced',
        'complaint': 'complained',
        'reject': 'rejected'
    }

    mapped_event = event_mapping.get(event_type, event_type)

    # Atualizar email
    if mapped_event == 'delivered':
        email.status = 'delivered'
        email.delivery_status = 'delivered'
        email.delivered_at = datetime.utcnow()
    elif mapped_event == 'bounced':
        email.status = 'bounced'
        email.delivery_status = 'bounced'
        email.failure_reason = data.get('bounce', {}).get('bounceType', 'Bounce')
    elif mapped_event == 'complained':
        email.delivery_status = 'complained'

    # Registrar evento
    event = EmailEvent(
        id=secrets.token_hex(18),
        email_id=email.id,
        event_type=mapped_event,
        provider='ses',
        event_metadata=str(data)
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({'success': True}), 200


@app.route('/webhooks/sendgrid', methods=['POST'])
def webhook_sendgrid():
    """Recebe callbacks do SendGrid"""
    data = request.get_json(force=True, silent=True) or []

    # SendGrid envia array de eventos
    if not isinstance(data, list):
        data = [data]

    processed = 0
    for event_data in data:
        event_type = event_data.get('event')
        message_id = event_data.get('smtp-id') or event_data.get('sg_message_id')

        if not message_id:
            continue

        # Buscar email (SendGrid sg_message_id precisa ser extraído)
        email = Email.query.filter(
            db.or_(
                Email.external_id == message_id,
                Email.delivery_response.contains(message_id)
            )
        ).first()

        if not email:
            continue

        # Mapear evento SendGrid
        event_mapping = {
            'delivered': 'delivered',
            'bounce': 'bounced',
            'dropped': 'rejected',
            'deferred': 'delayed',
            'processed': 'sent',
            'open': 'opened',
            'click': 'clicked',
            'spamreport': 'complained',
            'unsubscribe': 'unsubscribed'
        }

        mapped_event = event_mapping.get(event_type, event_type)

        # Atualizar email
        if mapped_event == 'delivered':
            email.status = 'delivered'
            email.delivery_status = 'delivered'
            email.delivered_at = datetime.utcnow()
        elif mapped_event == 'bounced':
            email.status = 'bounced'
            email.delivery_status = 'bounced'
            email.failure_reason = event_data.get('reason', 'Bounce')
        elif mapped_event == 'opened' and not email.opened_at:
            email.opened_at = datetime.utcnow()
            email.open_count += 1
        elif mapped_event == 'clicked' and not email.clicked_at:
            email.clicked_at = datetime.utcnow()
            email.click_count += 1

        # Registrar evento
        event = EmailEvent(
            id=secrets.token_hex(18),
            email_id=email.id,
            event_type=mapped_event,
            provider='sendgrid',
            event_metadata=str(event_data)
        )
        db.session.add(event)
        processed += 1

    db.session.commit()
    return jsonify({'success': True, 'processed': processed}), 200


@app.route('/api/v1/api-keys/<key_id>/provider', methods=['PUT'])
@login_required
def api_set_api_key_provider(key_id):
    data = request.get_json(force=True, silent=True) or {}
    provider_id = data.get('providerId') or data.get('provider_id')

    key = ApiKey.query.filter_by(id=key_id, user_id=session['user_id']).first()
    if not key:
        return jsonify({'error': 'API Key not found'}), 404

    if provider_id:
        provider = SmtpProvider.query.filter_by(id=provider_id, user_id=session['user_id'], is_active=True).first()
        if not provider:
            return jsonify({'error': 'Provider not found or inactive'}), 400
        key.provider_id = provider.id
    else:
        key.provider_id = None

    db.session.commit()
    return jsonify({'success': True, 'apiKeyId': key.id, 'providerId': key.provider_id})


# ============================================
# Inicialização
# ============================================

def init_db():
    """Inicializa o banco de dados e cria usuário admin padrão"""
    # Criar diretório de dados se não existir
    os.makedirs('data', exist_ok=True)
    
    with app.app_context():
        db.create_all()

        try:
            if str(db.engine.url).startswith('sqlite'):
                columns = set()
                with db.engine.connect() as conn:
                    result = conn.execute(text('PRAGMA table_info(emails)'))
                    for row in result:
                        columns.add(row[1])

                    if 'delivered_at' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN delivered_at DATETIME'))
                    if 'delivery_status' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN delivery_status VARCHAR(50)'))
                    if 'delivery_response' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN delivery_response TEXT'))
                    # Tracking columns
                    if 'opened_at' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN opened_at DATETIME'))
                    if 'clicked_at' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN clicked_at DATETIME'))
                    if 'open_count' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN open_count INTEGER DEFAULT 0'))
                    if 'click_count' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN click_count INTEGER DEFAULT 0'))
                    if 'tracking_enabled' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN tracking_enabled BOOLEAN DEFAULT 1'))
                    if 'tracking_token' not in columns:
                        conn.execute(text('ALTER TABLE emails ADD COLUMN tracking_token VARCHAR(64)'))
                    conn.commit()
        except Exception:
            pass

        try:
            if str(db.engine.url).startswith('sqlite'):
                columns = set()
                with db.engine.connect() as conn:
                    result = conn.execute(text('PRAGMA table_info(api_keys)'))
                    for row in result:
                        columns.add(row[1])

                    if 'provider_id' not in columns:
                        conn.execute(text('ALTER TABLE api_keys ADD COLUMN provider_id VARCHAR(36)'))
                    conn.commit()
        except Exception:
            pass
        
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
