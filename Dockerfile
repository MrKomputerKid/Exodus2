FROM python:3.11-bookworm
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]
ENV DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
ENV OPENWEATHERMAP_API_KEY=${OPENWEATHERMAP_API_KEY}
ENV OPENCAGE_API_KEY=${OPENCAGE_API_KEY}
ENV OWNER_ID=${OWNER_ID}
ENV DB_HOST=${DB_HOST}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_USER=${DB_USER}
ENV DB_DATABASE=${DB_DATABASE}