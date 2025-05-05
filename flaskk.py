from flask import Flask, render_template, request, Response
from werkzeug.security import check_password_hash, generate_password_hash
import socket
import subprocess
import platform
import locale

app = Flask(__name__)

# Configurações de autenticação (substitua com usuários reais)
users = {
    'admin': generate_password_hash('senha123')
}

def check_auth(username, password):
    """Verifica se o nome de usuário e senha são válidos."""
    if username in users and check_password_hash(users.get(username), password):
        return True
    return False

def authenticate():
    """Envia uma resposta 401 para solicitar autenticação."""
    return Response(
        'Autenticação Necessária', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    """Decorador para exigir autenticação."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def ping(host):
    """Executa o comando ping e retorna o resultado com a decodificação apropriada."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(timeout=5)

    if platform.system().lower() == 'windows':
        try:
            return stdout.decode('cp850')
        except UnicodeDecodeError:
            return "Erro ao decodificar a saída do ping (cp850)."
    else:  # Assumindo Linux ou outro sistema com UTF-8
        try:
            return stdout.decode('utf-8')
        except UnicodeDecodeError:
            return "Erro ao decodificar a saída do ping (utf-8)."

def check_port(host, port):
    """Tenta conectar a um host e porta específicos."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return f"Conexão bem-sucedida com {host}:{port}"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return f"Falha ao conectar com {host}:{port}: {e}"
# def ping(host):
#     """Tenta conectar à porta 80 do host para verificar a conectividade."""
#     port = 80  # Porta HTTP (uma porta comumente aberta)
#     timeout = 2  # Timeout em segundos

#     try:
#         socket.create_connection((host, port), timeout=timeout)
#         return f"Host {host} está acessível (conexão TCP na porta {port} bem-sucedida)."
#     except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
#         return f"Falha ao conectar ao host {host} (porta {port}): {e}"

# def check_port(host, port):
#     """Tenta conectar a um host e porta específicos."""
#     timeout = 2  # Timeout em segundos
#     try:
#         socket.create_connection((host, port), timeout=timeout)
#         return f"Conexão bem-sucedida com {host}:{port}"
#     except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
#         return f"Falha ao conectar com {host}:{port}: {e}"
    
@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    results = {}
    target_host_value = ''
    test_type_value = ''
    target_port_value = ''  # Inicializa a variável para o valor da porta

    if request.method == 'POST':
        target_host = request.form.get('target_host')
        test_type = request.form.get('test_type')
        target_port = request.form.get('target_port')
        target_host_value = target_host
        test_type_value = test_type
        target_port_value = target_port  # Armazena o valor da porta

        if target_host:
            if test_type == 'ping':
                results['ping'] = ping(target_host)
            elif test_type == 'port':
                if target_port and target_port.isdigit():
                    results['port'] = check_port(target_host, int(target_port))
                else:
                    results['error'] = "Por favor, insira uma porta válida."
            else:
                results['error'] = "Selecione um tipo de teste."
        else:
            results['error'] = "Por favor, insira um host de destino."

    return render_template('index.html', results=results, target_host_value=target_host_value, test_type_value=test_type_value, target_port_value=target_port_value)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)