import streamlit as st
import tempfile
from tests.connectivity_tests import (
    test_socket_connection,
    test_netcat_connection,
    test_curl_connection,
    test_ssl_connection
)


st.set_page_config(page_title="Conectividade - Ferramentas", layout="centered")
st.title("🔧 Ferramentas de Troubleshooting de Conectividade")

st.sidebar.title("📋 Selecione o teste")
test_type = st.sidebar.selectbox("Tipo de teste", [
    "Teste via socket",
    "Teste via socket (lote)",
    "Teste via netcat",
    "Teste via curl",
    "Teste de SSL"
])

st.markdown("---")

col1, col2 = st.columns(2, border=True)


if test_type == "Teste via socket":
    host = st.text_input("Host", value="google.com")
    port = st.number_input("Porta", min_value=1, max_value=65535, value=80)
    timeout = st.slider("Timeout (segundos)", 1, 30, 5)
    with col1:
        if st.button("Executar teste"):
            with st.spinner("Testando conexão..."):
                success = test_socket_connection(host, port, timeout)
                #st.success("✅ Conexão bem-sucedida") if success else st.error("❌ Falha na conexão")
                if success:
                    st.success("✅ Conexão bem-sucedida")
                else:
                    st.error("❌ Falha na conexão")
    with col2:
        if st.button("🧹 Limpar Tela"):
            for key in st.session_state.keys():
                del st.session_state[key]

elif test_type == "Teste via socket (lote)":
    uploaded_file = st.file_uploader("Arquivo .txt ou .csv", type=["txt", "csv"])
    timeout = st.slider("Timeout (segundos)", 1, 30, 5)
    workers = st.slider("Threads paralelas", 1, 30, 10)

    if uploaded_file and st.button("Executar teste em lote"):
        import csv, io
        from concurrent.futures import ThreadPoolExecutor, as_completed

        content = uploaded_file.read().decode("utf-8")
        reader = csv.reader(io.StringIO(content), delimiter=',' if ',' in content else ':')

        targets = []
        for row in reader:
            if len(row) == 2:
                try:
                    targets.append((row[0].strip(), int(row[1].strip())))
                except:
                    pass

        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {
                executor.submit(test_socket_connection, host, port, timeout): (host, port)
                for host, port in targets
            }
            for future in as_completed(future_map):
                host, port = future_map[future]
                try:
                    success = future.result()
                    results.append({"host": host, "port": port, "status": "success" if success else "failure"})
                except Exception as e:
                    results.append({"host": host, "port": port, "status": f"error: {str(e)}"})

        st.write("📊 Resultados:")
        for r in results:
            st.write(f"{r['host']}:{r['port']} → {r['status']}")

elif test_type == "Teste via netcat":
    host = st.text_input("Host", value="google.com")
    port = st.number_input("Porta", min_value=1, max_value=65535, value=80)
    timeout = st.slider("Timeout (segundos)", 1, 30, 5)
    if st.button("Executar netcat"):
        with st.spinner("Executando netcat..."):
            success = test_netcat_connection(host, port, timeout)
            st.success("✅ Netcat conectou") if success else st.error("❌ Netcat falhou")

elif test_type == "Teste via curl":
    url = st.text_input("URL", value="https://www.google.com")
    method = st.selectbox("Método HTTP", ["GET", "POST", "PUT", "DELETE"])
    use_proxy = st.checkbox("Usar proxy?")
    proxy_host = st.text_input("Proxy Host") if use_proxy else None
    proxy_port = st.number_input("Proxy Porta", min_value=1, max_value=65535, value=8080) if use_proxy else None
    timeout = st.slider("Timeout (segundos)", 1, 30, 5)

    if st.button("Executar curl"):
        with st.spinner("Executando curl..."):
            success = test_curl_connection(url, method, timeout, proxy_host, proxy_port) if use_proxy else test_curl_connection(url, method, timeout)
            st.success("✅ Conectado com sucesso via curl") if success else st.error("❌ Falha na conexão via curl")

elif test_type == "Teste de SSL":
    host = st.text_input("Host", value="google.com")
    port = st.number_input("Porta", min_value=1, max_value=65535, value=443)
    timeout = st.slider("Timeout (segundos)", 1, 30, 5)

    if st.button("Executar teste SSL"):
        with st.spinner("Testando SSL..."):
            success = test_ssl_connection(host, port, timeout)
            st.success("✅ SSL válido") if success else st.error("❌ Falha no teste SSL")
