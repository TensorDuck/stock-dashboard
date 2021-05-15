FROM python:3.8-slim
EXPOSE 8080
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
COPY stock_dashboard stock_dashboard
ENV PYTHONPATH=/app/stock_dashboard:$PYTHONPATH
ENTRYPOINT ["streamlit", "run", "stock_dashboard/app.py", "--server.port=8080"]
