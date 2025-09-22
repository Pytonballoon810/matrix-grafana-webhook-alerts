import os
import asyncio
from flask import Flask, request, jsonify
from nio import AsyncClient

app = Flask(__name__)

# Configuration from environment variables
MATRIX_HOMESERVER = os.environ.get("MATRIX_HOMESERVER")
MATRIX_USER = os.environ.get("MATRIX_USER")
MATRIX_PASSWORD = os.environ.get("MATRIX_PASSWORD")
MATRIX_ROOM_ID = os.environ.get("MATRIX_ROOM_ID")

# Initialize Matrix client
matrix_client = None


async def init_matrix_client():
    global matrix_client
    matrix_client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER)
    response = await matrix_client.login(MATRIX_PASSWORD)
    
    # Check if login was successful
    if hasattr(response, 'access_token'):
        return True
    else:
        raise Exception(f"Failed to login to Matrix: {response}")


async def send_matrix_message(message):
    if not matrix_client:
        await init_matrix_client()
    await matrix_client.room_send(
        room_id=MATRIX_ROOM_ID,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": message},
    )


def format_alert_message(alert_data):
    """Format Grafana alert data into a readable message"""
    try:
        status = alert_data.get("status", "unknown")
        message = alert_data.get("message", "No message provided")
        rule_id = alert_data.get("ruleId", "unknown")

        formatted_message = f"""🚨 Grafana Alert
Status: {status}
Rule ID: {rule_id}
Message: {message}"""

        # Add alert details if available
        if "evalMatches" in alert_data:
            formatted_message += "\n\nEvaluation Results:"
            for match in alert_data["evalMatches"]:
                value = match.get("value", "N/A")
                metric = match.get("metric", "N/A")
                formatted_message += f"\n- {metric}: {value}"

        return formatted_message
    except Exception as e:
        return f"Error formatting alert: {str(e)}\nRaw data: {str(alert_data)}"


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        alert_data = request.get_json()
        if not alert_data:
            return jsonify({"error": "No data received"}), 400

        message = format_alert_message(alert_data)

        try:
            # Send message to Matrix room asynchronously
            asyncio.run(send_matrix_message(message))
        except Exception as matrix_error:
            return jsonify({"error": f"Matrix error: {str(matrix_error)}"}), 500

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": f"Webhook error: {str(e)}"}), 500


if __name__ == "__main__":
    # Verify required environment variables
    required_vars = [
        "MATRIX_HOMESERVER",
        "MATRIX_USER",
        "MATRIX_PASSWORD",
        "MATRIX_ROOM_ID",
    ]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        exit(1)

    # Run Flask app
    app.run(host="0.0.0.0", port=5000)
