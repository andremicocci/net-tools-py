from tests.connectivity_tests import (
    test_socket_connection,
    test_netcat_connection,
    test_curl_connection,
    test_ssl_connection,
    test_socket_connection
)

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List
import csv
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import setup_logger

logger = setup_logger()

app = FastAPI(title="Connectivity Tester API")

@app.get("/socket")
def socket_test(host: str, port: int, timeout: int = 5):
    return {"success": test_socket_connection(host, port, timeout)}

@app.get("/netcat")
def netcat_test(host: str, port: int, timeout: int = 5):
    return {"success": test_netcat_connection(host, port, timeout)}

@app.get("/curl")
def curl_test(
    url: str,
    method: str = "GET",
    timeout: int = 5,
    proxy_host: str = None,
    proxy_port: int = None
):
    return {"success": test_curl_connection(url, method, timeout, proxy_host, proxy_port)}

@app.get("/ssl")
def ssl_test(host: str, port: int, timeout: int = 5):
    return {"success": test_ssl_connection(host, port, timeout)}

@app.post("/socket/batch")
async def socket_batch_upload(file: UploadFile = File(...), timeout: int = 5, workers: int = 10):
    """
    📄 Testa múltiplos hosts e portas via socket em paralelo a partir de um arquivo .txt ou .csv.
    """
    logger.info(f"📥 Recebido arquivo: {file.filename}")

    if not (file.filename.endswith(".txt") or file.filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .txt ou .csv")

    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        reader = csv.reader(io.StringIO(decoded), delimiter=',' if ',' in decoded else ':')
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo: {e}")
        raise HTTPException(status_code=400, detail="Erro ao processar o arquivo")

    targets = []
    for row in reader:
        if len(row) != 2:
            logger.warning(f"Linha ignorada (inválida): {row}")
            continue
        host, port = row
        try:
            targets.append((host.strip(), int(port.strip())))
        except ValueError:
            logger.warning(f"Porta inválida: {port}")

    if not targets:
        raise HTTPException(status_code=400, detail="Nenhum destino válido encontrado no arquivo")

    results = []

    logger.info(f"🚀 Iniciando {len(targets)} testes com {workers} threads")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(test_socket_connection, host, port, timeout): (host, port)
            for host, port in targets
        }

        for future in as_completed(future_map):
            host, port = future_map[future]
            try:
                status = "success" if future.result() else "failure"
            except Exception as e:
                logger.error(f"Erro ao testar {host}:{port} - {e}")
                status = "error"
            results.append({"host": host, "port": port, "status": status})

    logger.info("✅ Testes concluídos")
    return JSONResponse(content={"results": results, "summary": _generate_summary(results)})

def _generate_summary(results: List[dict]) -> dict:
    total = len(results)
    success = len([r for r in results if r["status"] == "success"])
    failure = len([r for r in results if r["status"] == "failure"])
    error = len([r for r in results if r["status"] == "error"])
    return {
        "total": total,
        "success": success,
        "failure": failure,
        "error": error
    }