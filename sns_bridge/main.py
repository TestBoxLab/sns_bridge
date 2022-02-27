import json
import threading
import time

import click
from bottle import route, run, request
from pyngrok import ngrok

from sns_bridge.chalice import trigger_chalice_method
from sns_bridge.sns import subscribe_to_sns, unsubscribe_from_sns, confirm_sns
from sns_bridge.wsgi import ThreadedWSGIServer

subscription_arn = None
sns_topic_name = None


@route('/', method='POST')
def index():
    global subscription_arn
    body = json.loads(request.body.read())
    if body:
        if body.get('Type') == 'SubscriptionConfirmation':
            subscription_arn = confirm_sns(body.get('SubscribeURL'))
            print("Ready to receive SNS messages!")
            return "OK"
        if body.get('Type') == 'Notification':
            # Call the method!
            trigger_chalice_method(sns_topic_name, subscription_arn, body)
            return "OK"

    return "Hello"


@click.command()
@click.option('--role-arn', help='ARN of the role to assume')
@click.option('--port', help='Port number to run', default=65500)
@click.option('--topic-name', help='SNS topic name', required=True)
def main(topic_name, role_arn, port):
    global subscription_arn, sns_topic_name
    sns_topic_name = topic_name

    # Start web server to receive SNS messages
    threaded_wsgi = ThreadedWSGIServer(port=port)
    http_server = threading.Thread(target=run, kwargs={'server': threaded_wsgi})
    http_server.start()

    # Start local tunnel to connect to SNS
    http_tunnel = ngrok.connect(addr=port)

    # Subscribe to SNS via the tunnel
    url = http_tunnel.public_url.replace('http:', 'https:')
    subscribe_to_sns(url, topic_name, role_arn)

    # Wait
    try:
        while http_server.is_alive():
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Stop received! Stopping web server...")
        threaded_wsgi.stop()

    # After we're done, unsubscribe our subscription
    print("Unsubscribing from SNS topic...")
    unsubscribe_from_sns(subscription_arn)


# Start our web server on a background thread, then proceed.
if __name__ == "__main__":
    main()
