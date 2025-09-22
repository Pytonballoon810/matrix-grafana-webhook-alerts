import os
import asyncio
import threading
from flask import Flask, request, jsonify
from nio import AsyncClient
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configuration from environment variables
MATRIX_HOMESERVER = os.environ.get("MATRIX_HOMESERVER")
MATRIX_USER = os.environ.get("MATRIX_USER")
MATRIX_PASSWORD = os.environ.get("MATRIX_PASSWORD")
MATRIX_ROOM_ID = os.environ.get("MATRIX_ROOM_ID")

# Global variables for Matrix client and message queue
matrix_client = None
message_queue = Queue()
executor = ThreadPoolExecutor(max_workers=1)
loop = None


async def process_message_queue():
    """Background task to process messages from the queue"""
    global matrix_client
    while True:
        try:
            if not matrix_client:
                matrix_client = AsyncClient(MATRIX_HOMESERVER, MATRIX_USER)
                response = await matrix_client.login(MATRIX_PASSWORD)
                if not hasattr(response, 'access_token'):
                    raise Exception(f"Failed to login to Matrix: {response}")
                print("✅ Successfully connected to Matrix")

            # Get message from queue (if any)
            try:
                message = message_queue.get_nowait()
                await matrix_client.room_send(
                    room_id=MATRIX_ROOM_ID,
                    message_type="m.room.message",
                    content={"msgtype": "m.text", "body": message},
                )
                print(f"✅ Sent message to Matrix room")
            except Queue.empty:
                await asyncio.sleep(1)  # Wait a bit before checking queue again
                
        except Exception as e:
            print(f"❌ Error in message processing: {str(e)}")
            matrix_client = None  # Reset client on error
            await asyncio.sleep(5)  # Wait before retrying

def run_async_loop():
    """Run the async event loop in a separate thread"""
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(process_message_queue())


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


def run_async(coro):
    """Helper function to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        alert_data = request.get_json()
        if not alert_data:
            return jsonify({"error": "No data received"}), 400

        message = format_alert_message(alert_data)
        
        # Add message to queue for processing
        message_queue.put(message)
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
    
    # Start the async processing thread
    thread = threading.Thread(target=run_async_loop, daemon=True)
    thread.start()
    
    print("✅ Started Matrix message processing thread")

    # Run Flask app
    app.run(host="0.0.0.0", port=5000)
