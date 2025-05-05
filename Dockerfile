FROM python:3.13-slim

# Diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY . .

# Instala dependências
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Exponha a porta usada pelo Streamlit
EXPOSE 8501

# Comando padrão (modo Streamlit)
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.enableCORS=false"]
