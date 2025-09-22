import requests
import json
import sys
from datetime import datetime

def send_test_alert(webhook_url, alert_type="test"):
    """
    Send a test Grafana alert to the webhook
    """
    # Current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Different test alert types
    alerts = {
        "test": {
            "status": "firing",
            "message": "Test Alert - Please Ignore",
            "ruleId": "test_alert",
            "evalMatches": [
                {
                    "value": 42,
                    "metric": "test_metric",
                    "tags": {"environment": "test"}
                }
            ]
        },
        "cpu": {
            "status": "firing",
            "message": "High CPU Usage Detected",
            "ruleId": "cpu_alert",
            "evalMatches": [
                {
                    "value": 95.5,
                    "metric": "cpu_usage_percent",
                    "tags": {"host": "test-server", "service": "web"}
                }
            ]
        },
        "memory": {
            "status": "firing",
            "message": "Low Memory Warning",
            "ruleId": "memory_alert",
            "evalMatches": [
                {
                    "value": 92.3,
                    "metric": "memory_usage_percent",
                    "tags": {"host": "test-server", "service": "database"}
                }
            ]
        }
    }
    
    # Get the alert data
    alert_data = alerts.get(alert_type, alerts["test"])
    
    # Add timestamp to the message
    alert_data["message"] = f"{alert_data['message']} (Test at {timestamp})"
    
    try:
        # Send the alert
        response = requests.post(
            webhook_url,
            json=alert_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Print the result
        if response.status_code == 200:
            print(f"✅ Alert sent successfully!")
            print(f"Alert type: {alert_type}")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Failed to send alert!")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending alert: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Get webhook URL from command line argument or use default
    if len(sys.argv) < 2:
        print("Usage: python test.py <webhook_url> [alert_type]")
        print("Alert types: test, cpu, memory")
        print("Example: python test.py http://localhost:5000/webhook cpu")
        sys.exit(1)
        
    webhook_url = sys.argv[1]
    # Get optional alert type
    alert_type = sys.argv[2] if len(sys.argv) > 2 else "test"
    
    # Send the test alert
    send_test_alert(webhook_url, alert_type)
