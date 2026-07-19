# One-command runnable demo for the Epistack instrument.
#
# Build:
#   docker build -t epistack .
#
# See the shape with NO API key (placeholders, not results):
#   docker run --rm epistack --dry-run
#
# Real run (needs a key; the real large base is covid_large):
#   docker run --rm -e ANTHROPIC_API_KEY=sk-... epistack --case covid_large --model claude-opus-4-8
#
# Run on a base the author never touched (mount it in):
#   docker run --rm -e ANTHROPIC_API_KEY=sk-... -v "$PWD/your_base.json:/app/your_base.json" \
#       epistack --kb-file your_base.json --model claude-opus-4-8
#
# Fresh machine to running process in ~5 min (mostly the base image pull).

FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir anthropic
COPY epistack_eval.py external_base_template.json ./
ENTRYPOINT ["python3", "epistack_eval.py"]
CMD ["--dry-run"]
