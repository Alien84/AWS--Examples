**Test the application locally:**

```
cd fastapi-app
uvicorn app.main:app --reload
```


**Build the Docker image**

```
docker build -t fastapi-chatbot .
```


**Run the container locally to test**

```
docker run -p 8000:8000 fastapi-chatbot
```
