import socket
import ssl
import subprocess
import pycurl
import io
from datetime import datetime, timezone
from typing import Optional
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from utils.logger import setup_logger

logger = setup_logger()

def test_socket_connection(host: str, port: int, timeout: int = 5) -> bool:
    #logger.info(f"🔌 Testando socket {host}:{port}")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            logger.info(f"🔌 Testando socket {host}:{port} ==> ✅ Socket OK")
            #logger.info("✅ Socket OK")
            return True
    except Exception as e:
        logger.error(f"🔌 Testando socket {host}:{port} ==> ❌ Socket Falhou: {e}")
        #logger.error(f"❌ Socket Falhou: {e}")
        return False

def test_netcat_connection(host: str, port: int, timeout: int = 5) -> bool:
    logger.info(f"🔗 Testando netcat {host}:{port}")
    try:
        result = subprocess.run(
            ["nc", "-zv", "-w", str(timeout), host, str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        logger.info(result.stdout.strip())
        return result.returncode == 0
    except Exception as e:
        logger.error(f"❌ Netcat Falhou: {e}")
        return False

def test_curl_connection(url: str, method: str = "GET", timeout: int = 5,
                         proxy_host: Optional[str] = None, proxy_port: Optional[int] = None) -> bool:
    logger.info(f"🌐 Testando cURL {url} ({method})")
    buffer = io.BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.CUSTOMREQUEST, method.upper())
    c.setopt(c.TIMEOUT, timeout)
    c.setopt(c.WRITEDATA, buffer)

    if proxy_host and proxy_port:
        c.setopt(c.PROXY, proxy_host)
        c.setopt(c.PROXYPORT, proxy_port)
        logger.info(f"🔀 Proxy: {proxy_host}:{proxy_port}")

    try:
        c.perform()
        response_code = c.getinfo(c.RESPONSE_CODE)
        logger.info(f"✅ Código HTTP: {response_code}")
        return 200 <= response_code < 400
    except pycurl.error as e:
        logger.error(f"❌ cURL Falhou: {e}")
        return False
    finally:
        c.close()

def test_ssl_connection(host: str, port: int, timeout: int = 5) -> bool:
    logger.info(f"🔒 Testando SSL {host}:{port}")
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert_bin = ssock.getpeercert(binary_form=True)
                x509_cert = x509.load_der_x509_certificate(cert_bin, default_backend())

                not_before = x509_cert.not_valid_before_utc
                not_after = x509_cert.not_valid_after_utc
                now = datetime.utcnow().replace(tzinfo=timezone.utc)

                logger.info(f"📅 Validade: {not_before} até {not_after}")
                logger.info(f"🔐 Protocolo: {ssock.version()} - Cifra: {ssock.cipher()}")

                if not_before <= now <= not_after:
                    logger.info("✅ Certificado válido no momento")
                    return True
                else:
                    logger.warning("⚠️ Certificado fora do período de validade")
                    return False
    except Exception as e:
        logger.error(f"❌ SSL Falhou: {e}")
        return False
