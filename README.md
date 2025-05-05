# Usage

## CLI
```
python main.py socket --host google.com --port 80
python main.py netcat --host google.com --port 443
python main.py curl --url https://www.google.com --method GET
python main.py ssl --host google.com --port 443
```

## REST
```
uvicorn web:app --reload

http://127.0.0.1:8000/docs
```

## STREAMLIT
```
streamlit run streamlit_app.py
```

## DOCKER
```
docker build -t your-docker-username/net-tools:latest .
docker push your-docker-username/net-tools:latest
```

## K8S
```
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```