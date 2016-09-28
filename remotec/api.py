"""
Definition of an HTTP/WS API streaming the apps modifications
"""
import json
import os

from flask import Flask, make_response, jsonify
from marathon.client import MarathonClient

WHITELIST = ['id', 'instances']

app = Flask(__name__)
app.marathon = MarathonClient(
    servers=[os.environ['MARATHON_URL']],
    username=os.environ['MARATHON_USER'],
    password=os.environ['MARATHON_PASSWORD'])


def get_status(app):
    if app['instances'] == 0:
        return 'suspended'
    elif app['tasksRunning'] == app['instances']:
        return 'running'
    elif app['tasksStaged'] <= app['instances']:
        return 'deploying'
    else:
        return 'unknown'


@app.route('/apps', methods=['GET'])
def list_apps():
    apps = []
    for marathon_app in app.marathon.list_apps():
        if marathon_app.id.startswith('/summit'):
            marathon_app = json.loads(marathon_app.to_json())
            app_doc = {field: marathon_app[field] for field in WHITELIST}
            app_doc['status'] = get_status(marathon_app)
            app_doc['url'] = 'http://%s' % (marathon_app['labels']['HAPROXY_0_VHOST'])
            apps.append(app_doc)
    return make_response(jsonify({'apps': apps}), 200)


@app.route('/ping', methods=['GET'])
def healthcheck():
    return "pong\n"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=6666, debug=True)
