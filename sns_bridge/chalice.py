import ast
import subprocess
from typing import Any


class Visitor(ast.NodeVisitor):
    def __init__(self, sns_topic_name):
        self._sns_topic_name = sns_topic_name
        self.method_name = None
        self.node = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        """
        Find function definitions, look for the decorators,
        and find our sns topic name in the arguments list
        :param node:
        :return:
        """
        for l in node.decorator_list:
            for a in l.args:
                if a.value == self._sns_topic_name:
                    print(node.name)
                    self.method_name = node.name
                    self.node = node


def trigger_chalice_method(topic_name, subscription_arn, body):
    """
    Trigger the Chalice method.

    :param topic_name: SNS topic name
    :param subscription_arn: Real-life subscription ARN
    :param body: The body of the SNS message
    :return:
    """

    # First, determine the method name to call by using AST
    # to visit the method decorators and find the SNS topic name
    f = open('app.py', 'r')
    v = Visitor(topic_name)
    node = ast.parse(f.read())
    v.visit(node)
    f.close()

    # unrelated, we need to fake the SNS message
    event = {
        'Records': [
            {
                'EventSource': 'aws:sns',
                "EventVersion": "1.0",
                "EventSubscriptionArn": subscription_arn,
                "Sns": body,
            }
        ]
    }

    code = f"""
from app import {v.method_name}
event = {event}
{v.method_name}(event, None)"""

    # Now, run the method in a new Python interpreter each time
    # to lazily replicate hot reloading
    with subprocess.Popen(["python", "-"],
                          stdout=subprocess.PIPE,
                          stdin=subprocess.PIPE,
                          universal_newlines=True,
                          bufsize=1) as p:
        p.stdin.write(code)
        p.stdin.close()
        for line in p.stdout:
            print(line, end='')
