FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install --upgrade pip && pip install fastapi uvicorn scikit-learn numpy
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
