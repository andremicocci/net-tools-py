import typer
from tests.connectivity_tests import (
    test_socket_connection,
    test_netcat_connection,
    test_curl_connection,
    test_ssl_connection
)
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import setup_logger

logger = setup_logger()

app = typer.Typer(help="🛠️ Ferramenta de Troubleshooting de Conectividade entre Servidores")

@app.command()
def socket(
    host: str = typer.Option(..., "--host", help="Hostname ou IP para testar"),
    port: int = typer.Option(..., "--port", help="Porta de destino"),
    timeout: int = typer.Option(5, "--timeout", help="Timeout em segundos (padrão: 5)")
):
    """🔌 Testa conexão via socket TCP"""
    test_socket_connection(host, port, timeout)

@app.command()
def netcat(
    host: str = typer.Option(..., "--host", help="Hostname ou IP para testar"),
    port: int = typer.Option(..., "--port", help="Porta de destino"),
    timeout: int = typer.Option(5, "--timeout", help="Timeout em segundos (padrão: 5)")
):
    """🔗 Testa conexão via netcat"""
    test_netcat_connection(host, port, timeout)

@app.command()
def curl(
    url: str = typer.Option(..., "--url", help="URL de destino (ex: https://example.com)"),
    method: str = typer.Option("GET", "--method", help="Método HTTP (GET, POST, etc.)"),
    timeout: int = typer.Option(5, "--timeout", help="Timeout em segundos"),
    proxy_host: str = typer.Option(None, "--proxy-host", help="Proxy hostname (opcional)"),
    proxy_port: int = typer.Option(None, "--proxy-port", help="Proxy porta (opcional)")
):
    """🌐 Testa conexão HTTP via cURL"""
    test_curl_connection(url, method, timeout, proxy_host, proxy_port)

@app.command()
def ssl(
    host: str = typer.Option(..., "--host", help="Hostname ou IP para teste SSL"),
    port: int = typer.Option(..., "--port", help="Porta SSL (geralmente 443)"),
    timeout: int = typer.Option(5, "--timeout", help="Timeout em segundos")
):
    """🔒 Testa conexão SSL, validade do certificado e suporte a TLS/cifras"""
    test_ssl_connection(host, port, timeout)

@app.command("socket-batch")
def socket_batch(
    file: str = typer.Option(..., "--file", help="Arquivo .txt ou .csv com lista de host:porta ou host,porta"),
    timeout: int = typer.Option(5, "--timeout", help="Timeout em segundos (padrão: 5)"),
    workers: int = typer.Option(10, "--workers", help="Número de threads paralelas (padrão: 10)"),
    json_output: bool = typer.Option(False, "--json", help="Exibir resultado em JSON")
):
    """
    📄 Testa múltiplos hosts e portas via socket em paralelo, a partir de um arquivo .txt ou .csv.
    """
    import os
    import csv
    import json
    from tests.connectivity_tests import test_socket_connection

    if not os.path.isfile(file):
        logger.error(f"❌ Arquivo não encontrado: {file}")
        raise typer.Exit(code=1)

    # Detecta delimitador e lê pares host/porta
    targets = []
    with open(file, "r") as f:
        sample = f.readline()
        delimiter = ',' if ',' in sample else ':'
        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if len(row) != 2:
                logger.warning(f"⚠️ Linha inválida: {row}")
                continue
            host, port = row
            try:
                targets.append((host.strip(), int(port.strip())))
            except ValueError:
                logger.warning(f"⚠️ Porta inválida: {port}")

    results = []

    logger.info(f"🚀 Iniciando testes em paralelo ({len(targets)} alvos)...")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_target = {
            executor.submit(test_socket_connection, host, port, timeout): (host, port)
            for host, port in targets
        }

        for future in as_completed(future_to_target):
            host, port = future_to_target[future]
            try:
                success = future.result()
                results.append({"host": host, "port": port, "status": "success" if success else "failure"})
            except Exception as e:
                logger.error(f"❌ Erro ao testar {host}:{port} - {e}")
                results.append({"host": host, "port": port, "status": "error"})

    # Exibe resumo
    total = len(results)
    success = len([r for r in results if r["status"] == "success"])
    failure = total - success
    logger.info(f"\n📊 Resultado final: {success} sucesso(s), {failure} falha(s), {total} total")

    if json_output:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    app()
