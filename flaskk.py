from flask import Flask, render_template, request, Response, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import socket
import subprocess
import platform
import locale
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
def ping_executor(host):
    """Tenta conectar à porta 80 do host para verificar a conectividade e retorna o resultado."""
    port = 80  # Porta HTTP (uma porta comumente aberta)
    timeout = 2  # Timeout em segundos
    try:
        socket.create_connection((host, port), timeout=timeout)
        return f"Host {host} está acessível (conexão TCP na porta {port} bem-sucedida)."
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
        return f"Falha ao conectar ao host {host} (porta {port}): {e}"

def check_port_executor(host, port):
    """Tenta conectar a um host e porta específicos e retorna o resultado."""
    timeout = 2  # Timeout em segundos
    try:
        socket.create_connection((host, port), timeout=timeout)
        return f"Conexão bem-sucedida com {host}:{port}"
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
        return f"Falha ao conectar com {host}:{port}: {e}"

@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    results = {}
    target_host_value = ''
    test_type_value = ''
    target_port_value = ''

    if request.method == 'POST':
        target_host = request.form.get('target_host')
        test_type = request.form.get('test_type')
        target_port = request.form.get('target_port')
        target_host_value = target_host
        test_type_value = test_type
        target_port_value = target_port

        if target_host:
            if test_type == 'ping':
                results['ping'] = ping_executor(target_host)
            elif test_type == 'port':
                if target_port and target_port.isdigit():
                    results['port'] = check_port_executor(target_host, int(target_port))
                else:
                    results['error'] = "Por favor, insira uma porta válida."
            else:
                results['error'] = "Selecione um tipo de teste."
        else:
            results['error'] = "Por favor, insira um host de destino."

    return render_template('index.html', results=results, target_host_value=target_host_value, test_type_value=test_type_value, target_port_value=target_port_value, bulk_results=None, bulk_summary=None)

@app.route('/bulk_test', methods=['POST'])
@requires_auth
def bulk_test():
    if 'file' not in request.files:
        return render_template('index.html', error="Nenhum arquivo selecionado.", bulk_results=None, bulk_summary=None)

    file = request.files['file']

    if file.filename == '':
        return render_template('index.html', error="Nenhum arquivo selecionado.", bulk_results=None, bulk_summary=None)

    if file:
        all_results = []
        success_count = 0
        error_count = 0
        futures = []
        max_workers = 10  # Defina um número máximo razoável de threads
        try:
            lines = file.read().decode('utf-8').splitlines()
            if len(lines) > 100:
                return render_template('index.html', error="O arquivo deve conter no máximo 100 linhas.", bulk_results=None, bulk_summary=None)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for line in lines:
                    line = line.strip()
                    if line:
                        if ':' in line:
                            host, port_str = line.split(':', 1)
                            if port_str.isdigit():
                                future = executor.submit(check_port_executor, host.strip(), int(port_str))
                            else:
                                all_results.append(f"Formato inválido: {line} (porta deve ser um número).")
                                error_count += 1
                                continue
                        else:
                            future = executor.submit(ping_executor, line.strip())

                        if 'future' in locals():
                            futures.append(future)
                            del future # Limpa a variável para a próxima iteração

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                        if "bem-sucedida" in result or "acessível" in result:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        error_count += 1
                        all_results.append(f"Erro ao executar teste: {e}")

        except UnicodeDecodeError:
            return render_template('index.html', error="Erro ao decodificar o arquivo. Certifique-se de que ele esteja em UTF-8.", bulk_results=None, bulk_summary=None)
        except Exception as e:
            return render_template('index.html', error=f"Ocorreu um erro ao processar o arquivo: {e}", bulk_results=None, bulk_summary=None)

        bulk_summary = f"Resumo: {success_count} conexões bem-sucedidas, {error_count} falhas."
        return render_template('index.html', bulk_results=all_results, bulk_summary=bulk_summary)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)