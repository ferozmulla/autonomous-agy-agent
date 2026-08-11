"""HTTP server wrapper for the Conversational Analytics ADK agent.

Provides Flask routes that map to the ADK agent's conversation methods.
Handles CORS (frontend is on a different Cloud Run URL) and implements
the /health endpoint for status monitoring.
"""

from __future__ import annotations

import os
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

from agent import agent, PROJECT_ID, DATASET_NAME
from bigquery_tool import get_dataset_schema

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the frontend


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint.

    Returns the agent's status and dataset information. Used by the
    frontend to update the status indicator (gray → yellow → green).

    Returns:
        JSON with status, dataset name, and table list.
    """
    try:
        # Verify BigQuery connectivity and dataset existence
        from google.cloud import bigquery
        client = bigquery.Client(project=PROJECT_ID)
        tables = list(client.list_tables(f"{PROJECT_ID}.{DATASET_NAME}"))
        table_names = [t.table_id for t in tables]

        if table_names:
            return jsonify({
                "status": "healthy",
                "dataset": f"{PROJECT_ID}.{DATASET_NAME}",
                "tables": table_names,
            })
        else:
            return jsonify({
                "status": "initializing",
                "dataset": f"{PROJECT_ID}.{DATASET_NAME}",
                "tables": [],
                "message": "Dataset exists but no tables found.",
            })
    except Exception as exc:
        return jsonify({
            "status": "unhealthy",
            "error": str(exc)[:200],
        }), 503


@app.route("/chat", methods=["POST"])
def chat():
    """Chat endpoint — accepts a natural-language question and returns an answer.

    Expects JSON body: {"message": "your question here"}
    Returns JSON: {"response": "answer text", "sql": "generated SQL or null"}
    """
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({
            "error": "Request body must contain a 'message' field.",
        }), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({
            "error": "Message cannot be empty.",
        }), 400

    try:
        # Run the ADK agent with the user's message
        from google.adk.runners import InMemoryRunner
        from google.genai import types
        import uuid

        runner = InMemoryRunner(agent=agent, app_name="ca-agent")
        runner.auto_create_session = True  # Auto-create sessions for new requests
        user_id = "web_user"
        session_id = str(uuid.uuid4())

        new_message = types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )

        response = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message,
        )

        # Extract the agent's response
        response_text = ""
        sql_used = None

        for event in response:
            if hasattr(event, "content") and event.content:
                for part in event.content.parts or []:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text
            # Try to extract SQL from function calls
            if hasattr(event, "function_calls") and event.function_calls:
                for fc in event.function_calls:
                    if fc.name == "query_bigquery" and fc.args:
                        sql_used = fc.args.get("sql")

        if not response_text:
            response_text = "I wasn't able to generate a response. Please try rephrasing your question."

        return jsonify({
            "response": response_text,
            "sql": sql_used,
        })

    except Exception as exc:
        traceback.print_exc()
        return jsonify({
            "response": f"An error occurred while processing your question: {str(exc)[:200]}",
            "sql": None,
        }), 500


@app.route("/schema", methods=["GET"])
def schema():
    """Schema endpoint — returns the dataset schema for debugging.

    Returns:
        JSON with the formatted schema string.
    """
    try:
        schema_info = get_dataset_schema(PROJECT_ID, DATASET_NAME)
        return jsonify({"schema": schema_info})
    except Exception as exc:
        return jsonify({"error": str(exc)[:200]}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
