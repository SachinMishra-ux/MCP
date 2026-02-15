FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for non-interactive execution
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=sse
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Command to run the MCP server in SSE mode by default
CMD ["python", "server.py"]
