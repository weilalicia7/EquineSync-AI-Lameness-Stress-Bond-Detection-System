"""
EquineSync Slack Notifier
Sends health alerts to Slack channels via webhook
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class SlackNotifier:
    """Sends formatted health alerts to Slack"""

    def __init__(self):
        """Initialize Slack notifier"""
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.channel = os.getenv('SLACK_CHANNEL', '#equinesync-alerts')
        self.enabled = bool(self.webhook_url)

        # Load alert message templates
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'alert_thresholds.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.alert_messages = config['alert_messages']

        if self.enabled:
            print(f"✅ Slack notifications enabled: {self.channel}")
        else:
            print("⚠️  Slack webhook URL not configured - notifications disabled")

    def format_alert_message(self, alert_data: Dict) -> Dict:
        """
        Format alert data into Slack message blocks

        Args:
            alert_data: Alert information
                {
                    'alert_type': str,
                    'severity': str,
                    'horse_id': str,
                    'affected_leg': str (optional),
                    'metric_value': float,
                    'threshold': float,
                    'timestamp': int
                }

        Returns:
            Slack message payload
        """
        alert_type = alert_data['alert_type']
        severity = alert_data['severity']
        horse_id = alert_data.get('horse_id', 'Unknown')

        # Get message template
        template = self.alert_messages.get(alert_type, {
            'title': f'⚠️ {alert_type} Alert',
            'message_template': 'Alert detected',
            'recommendation': 'Please investigate'
        })

        # Format message with actual values
        message = template['message_template'].format(
            affected_leg=alert_data.get('affected_leg', 'N/A'),
            metric_value=alert_data.get('metric_value', 0),
            threshold=alert_data.get('threshold', 0)
        )

        # Severity color
        colors = {
            'CRITICAL': '#FF0000',  # Red
            'WARNING': '#FFA500',   # Orange
            'INFO': '#0000FF'       # Blue
        }
        color = colors.get(severity, '#808080')

        # Severity emoji
        emojis = {
            'CRITICAL': '🔴',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }
        emoji = emojis.get(severity, '•')

        # Timestamp
        timestamp = alert_data.get('timestamp', int(datetime.now().timestamp() * 1000))
        dt = datetime.fromtimestamp(timestamp / 1000)
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')

        # Build Slack message
        return {
            'channel': self.channel,
            'username': 'EquineSync Alert System',
            'icon_emoji': ':horse:',
            'attachments': [
                {
                    'color': color,
                    'blocks': [
                        {
                            'type': 'header',
                            'text': {
                                'type': 'plain_text',
                                'text': f"{emoji} {template['title']}",
                                'emoji': True
                            }
                        },
                        {
                            'type': 'section',
                            'fields': [
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Horse:*\n{horse_id}"
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Severity:*\n{severity}"
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Time:*\n{time_str}"
                                },
                                {
                                    'type': 'mrkdwn',
                                    'text': f"*Alert Type:*\n{alert_type}"
                                }
                            ]
                        },
                        {
                            'type': 'section',
                            'text': {
                                'type': 'mrkdwn',
                                'text': f"*Details:*\n{message}"
                            }
                        },
                        {
                            'type': 'section',
                            'text': {
                                'type': 'mrkdwn',
                                'text': f"*Recommendation:*\n{template['recommendation']}"
                            }
                        },
                        {
                            'type': 'divider'
                        },
                        {
                            'type': 'context',
                            'elements': [
                                {
                                    'type': 'mrkdwn',
                                    'text': f"Alert ID: `{alert_data.get('alert_id', 'N/A')}` | Generated by EquineSync Real-Time Analytics"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

    def send_alert(self, alert_data: Dict) -> bool:
        """
        Send alert to Slack

        Args:
            alert_data: Alert information dict

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"ℹ️  Slack disabled - Alert would have been sent: {alert_data.get('alert_type')}")
            return False

        try:
            # Format message
            payload = self.format_alert_message(alert_data)

            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )

            if response.status_code == 200:
                print(f"✅ Slack alert sent: {alert_data.get('alert_type')} for {alert_data.get('horse_id')}")
                return True
            else:
                print(f"❌ Slack webhook error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")
            return False

    def send_summary(self, horse_id: str, metrics: Dict) -> bool:
        """
        Send daily health summary to Slack

        Args:
            horse_id: Horse identifier
            metrics: Summary metrics
                {
                    'symmetry_avg': float,
                    'hrv_status': str,
                    'alerts_today': int,
                    'exercise_duration_min': int
                }

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        try:
            message = {
                'channel': self.channel,
                'username': 'EquineSync Daily Summary',
                'icon_emoji': ':chart_with_upwards_trend:',
                'blocks': [
                    {
                        'type': 'header',
                        'text': {
                            'type': 'plain_text',
                            'text': f"📊 Daily Health Summary - {horse_id}",
                            'emoji': True
                        }
                    },
                    {
                        'type': 'section',
                        'fields': [
                            {
                                'type': 'mrkdwn',
                                'text': f"*Avg Symmetry:*\n{metrics.get('symmetry_avg', 0):.1f}/100"
                            },
                            {
                                'type': 'mrkdwn',
                                'text': f"*HRV Status:*\n{metrics.get('hrv_status', 'Unknown')}"
                            },
                            {
                                'type': 'mrkdwn',
                                'text': f"*Alerts Today:*\n{metrics.get('alerts_today', 0)}"
                            },
                            {
                                'type': 'mrkdwn',
                                'text': f"*Exercise Time:*\n{metrics.get('exercise_duration_min', 0)} min"
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Failed to send Slack summary: {e}")
            return False

    def test_notification(self) -> bool:
        """Send test notification to verify Slack integration"""
        test_alert = {
            'alert_id': 'test-001',
            'alert_type': 'ASYMMETRY',
            'severity': 'WARNING',
            'horse_id': 'test-horse',
            'affected_leg': 'FL',
            'metric_value': 58.5,
            'threshold': 60.0,
            'timestamp': int(datetime.now().timestamp() * 1000)
        }

        print("📤 Sending test notification to Slack...")
        return self.send_alert(test_alert)


# Example usage
if __name__ == "__main__":
    notifier = SlackNotifier()

    # Test notification
    if notifier.enabled:
        notifier.test_notification()
    else:
        print("\n💡 To enable Slack notifications:")
        print("   1. Create a Slack webhook: https://api.slack.com/messaging/webhooks")
        print("   2. Set SLACK_WEBHOOK_URL in your .env file")
        print("   3. Optionally set SLACK_CHANNEL (default: #equinesync-alerts)")

    # Example: Send different alert types
    examples = [
        {
            'alert_id': 'alert-001',
            'alert_type': 'ASYMMETRY',
            'severity': 'WARNING',
            'horse_id': 'Thunder',
            'affected_leg': 'FL',
            'metric_value': 55.2,
            'threshold': 60.0
        },
        {
            'alert_id': 'alert-002',
            'alert_type': 'HRV_CRITICAL',
            'severity': 'CRITICAL',
            'horse_id': 'Thunder',
            'metric_value': 25.3,
            'threshold': 30.0
        },
        {
            'alert_id': 'alert-003',
            'alert_type': 'EMOTIONAL_DISTRESS',
            'severity': 'WARNING',
            'horse_id': 'Thunder',
            'metric_value': 45,
            'threshold': 60
        }
    ]

    print("\n📋 Example alert formats:\n")
    for example in examples:
        payload = notifier.format_alert_message(example)
        print(f"Alert Type: {example['alert_type']}")
        print(json.dumps(payload, indent=2))
        print("-" * 60)
