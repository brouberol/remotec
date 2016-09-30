"""
CDS-like deployment script.
"""

import os
import sys
import json
import requests
import pprint


def deploy(data):
    url = '%s/v2/apps' % (os.environ['MARATHON_URL'].rstrip('/'))
    app_url = '%s/%s?force=true' % (url, data['id'])
    auth = (os.environ['MARATHON_USER'], os.environ['MARATHON_PASSWORD'])
    r = requests.get(app_url, auth=auth)
    if r.status_code == 200:
        r2 = requests.put(app_url, auth=auth, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        print(r2.status_code)
        pprint.pprint(r2.json())
    elif r.status_code == 404:
        r2 = requests.post(url, auth=auth, data=json.dumps(data), headers={'Content-Type': 'application/json'})
        print(r2.status_code)
        pprint.pprint(r2.json())
    else:
        r.raise_for_status()


def deploy_workers():
    data = {
        'id': '/summit/workers',
        'instances': 3,
        'constraints': [["hostname", "GROUP_BY"]],
        'container': {
            'type': 'DOCKER',
            'volumes': [],
            'docker': {
                'forcePullImage': True,
                'image': 'bewiwi/remotec',
                'network': 'BRIDGE',
                'portMappings': [],
                'priviledged': False
            }
        },
        'cpus': 0.1,
        'mem': 128,
        'disk': 0,
        'env': {
            'CELERY_BROKER_URL': os.environ['CELERY_BROKER_URL'],
            'CELERY_RESULT_BACKEND': os.environ['CELERY_RESULT_BACKEND'],
            'LOAD_BALANCER': os.environ['LOAD_BALANCER'],
            'MARATHON_URL': os.environ['MARATHON_URL'],
            'MARATHON_USER': os.environ['MARATHON_USER'],
            'MARATHON_PASSWORD': os.environ['MARATHON_PASSWORD'],
            'API_URL': os.environ['API_URL'],
            'LOGS_TOKEN': os.environ['LOGS_TOKEN'],
            'ENTRYPOINT_CMD': 'celery_worker',
        },
        'healthChecks': [],
        'labels': {
            'USER_LOGS_TOKEN': os.environ['LOGS_TOKEN'],
        },
        'maxLaunchDelaySeconds': 600
    }
    deploy(data)


def deploy_beat():
    data = {
        'id': '/summit/beat',
        'instances': 1,
        'constraints': [["hostname", "GROUP_BY"]],
        'container': {
            'type': 'DOCKER',
            'volumes': [],
            'docker': {
                'forcePullImage': True,
                'image': 'bewiwi/remotec',
                'network': 'BRIDGE',
                'portMappings': [],
                'priviledged': False
            }
        },
        'cpus': 0.1,
        'mem': 128,
        'disk': 0,
        'env': {
            'CELERY_BROKER_URL': os.environ['CELERY_BROKER_URL'],
            'CELERY_RESULT_BACKEND': os.environ['CELERY_RESULT_BACKEND'],
            'LOAD_BALANCER': os.environ['LOAD_BALANCER'],
            'MARATHON_URL': os.environ['MARATHON_URL'],
            'MARATHON_USER': os.environ['MARATHON_USER'],
            'MARATHON_PASSWORD': os.environ['MARATHON_PASSWORD'],
            'API_URL': os.environ['API_URL'],
            'LOGS_TOKEN': os.environ['LOGS_TOKEN'],
            'ENTRYPOINT_CMD': 'celery_beat',
        },
        'healthChecks': [],
        'labels': {
            'USER_LOGS_TOKEN': os.environ['LOGS_TOKEN'],
        },
        'maxLaunchDelaySeconds': 600
    }
    deploy(data)


def deploy_api():
    data = {
        'id': '/summit/api',
        'instances': 3,
        'constraints': [["hostname", "GROUP_BY"]],
        'container': {
            'type': 'DOCKER',
            'volumes': [],
            'docker': {
                'forcePullImage': True,
                'image': 'bewiwi/remotec',
                'network': 'BRIDGE',
                'portMappings': [
                    {
                        'containerPort': os.environ.get('API_PORT', 5000),
                        'servicePort': 0,
                        'protocol': 'tcp',
                    }
                ],
                'priviledged': False
            }
        },
        'cpus': 0.1,
        'mem': 128,
        'disk': 0,
        'env': {
            'CELERY_BROKER_URL': os.environ['CELERY_BROKER_URL'],
            'CELERY_RESULT_BACKEND': os.environ['CELERY_RESULT_BACKEND'],
            'LOAD_BALANCER': os.environ['LOAD_BALANCER'],
            'MARATHON_URL': os.environ['MARATHON_URL'],
            'MARATHON_USER': os.environ['MARATHON_USER'],
            'MARATHON_PASSWORD': os.environ['MARATHON_PASSWORD'],
            'ENTRYPOINT_CMD': 'api',
        },
        'healthChecks': [
            {
                'gracePeriodSeconds': 300,
                'ignoreHttp1xx': False,
                'intervalSeconds': 10,
                'maxConsecutiveFailures': 3,
                'path': '/ping',
                'portIndex': 0,
                'protocol': 'HTTP',
                'timeoutSeconds': 20,
            },
        ],
        'labels': {
            'HAPROXY_0_MODE': 'http',
            'HAPROXY_0_VHOST': os.environ['API_URL'],
            'USER_LOGS_TOKEN': os.environ['LOGS_TOKEN'],
        },
        'maxLaunchDelaySeconds': 600,
    }
    deploy(data)


def deploy_consumer():
    data = {
        'id': '/summit/twitter-consumer',
        'instances': 1,
        'constraints': [],
        'container': {
            'type': 'DOCKER',
            'volumes': [],
            'docker': {
                'forcePullImage': True,
                'image': 'bewiwi/remotec',
                'network': 'BRIDGE',
                'portMappings': [],
                'priviledged': False
            }
        },
        'cpus': 0.1,
        'mem': 128,
        'disk': 0,
        'env': {
            'CELERY_BROKER_URL': os.environ['CELERY_BROKER_URL'],
            'CELERY_RESULT_BACKEND': os.environ['CELERY_RESULT_BACKEND'],
            'LOAD_BALANCER': os.environ['LOAD_BALANCER'],
            'MARATHON_URL': os.environ['MARATHON_URL'],
            'MARATHON_USER': os.environ['MARATHON_USER'],
            'MARATHON_PASSWORD': os.environ['MARATHON_PASSWORD'],
            'TWITTER_CONSUMER_KEY': os.environ['TWITTER_CONSUMER_KEY'],
            'TWITTER_SECRET_KEY': os.environ['TWITTER_SECRET_KEY'],
            'TWITTER_KEY': os.environ['TWITTER_KEY'],
            'TWITTER_SECRET': os.environ['TWITTER_SECRET'],
            'STREAM_HASHTAG': os.environ['STREAM_HASHTAG'],
            'ENTRYPOINT_CMD': 'consumer',
        },
        'healthChecks': [],
        'labels': {
            'USER_LOGS_TOKEN': os.environ['LOGS_TOKEN'],
        },
        'maxLaunchDelaySeconds': 600
    }
    deploy(data)


def deploy_broker():
    data = {
        'id': '/summit/broker',
        'instances': 1,
        'constraints': [],
        'cmd': 'redis-server --appendonly yes --requirepass %s' % (os.environ['REDIS_PASSWORD']),
        'container': {
            'type': 'DOCKER',
            'volumes': [
                {
                    'containerPath': '/data',
                    'hostPath': '/summit/redis/data',
                    'mode': 'RW'
                }
            ],
            'docker': {
                'forcePullImage': True,
                'image': 'redis',
                'network': 'BRIDGE',
                'portMappings': [
                    {
                        'containerPort': 6379,
                        'protocol': 'tcp',
                    }
                ],
                'priviledged': False
            }
        },
        'cpus': 0.1,
        'mem': 128,
        'disk': 0,
        'env': {
        },
        'healthChecks': [
            {
                'ignoreHttp1xx': False,
                'gracePeriodSeconds': 300,
                'intervalSeconds': 10,
                'maxConsecutiveFailures': 3,
                'portIndex': 0,
                'protocol': 'TCP',
                'timeoutSeconds': 20,
            },
        ],
        'labels': {
            'HAPROXY_0_MODE': 'tcp',
            # 'HAPROXY_0_BACKEND_NETWORK_ALLOWED_ACL': os.environ['REDIS_ACL'],
            'USER_LOGS_TOKEN': os.environ['LOGS_TOKEN'],
        },
        'maxLaunchDelaySeconds': 600,
    }
    deploy(data)


def main():
    app = sys.argv[1]
    if app == 'worker':
        deploy_workers()
    elif app == 'consumer':
        deploy_consumer()
    elif app == 'api':
        deploy_api()
    elif app == 'broker':
        deploy_broker()
    elif app == 'beat':
        deploy_beat()
    elif app == 'all':
        deploy_api()
        deploy_consumer()
        deploy_workers()
        deploy_beat()
        deploy_broker()
    else:
        print("Unhandled app")


if __name__ == '__main__':
    main()
