"""
Definition of the celery tasks
"""
import json
import os
import requests

from slugify import slugify
from marathon.models import MarathonApp, MarathonHealthCheck
from marathon.models.container import (
    MarathonContainer,
    MarathonDockerContainer,
    MarathonContainerPortMapping)
from celery.utils.log import get_task_logger
from .app import cel


LOG = get_task_logger(__name__)


def find_app_id(username):
    url = 'http://%s/apps' % (os.environ['API_URL'].rstrip('/'))
    apps = requests.get(url).json()['apps']
    for app in apps:
        if app['username'] == username:
            return app['id']
    LOG.warning('App with username %s not found', username)


def make_app_id(username):
    return "/summit/users/%s" % (slugify(username))


def make_app(username, instances):
    if instances > 5:
        instances = 5
    app = MarathonApp(
        id=make_app_id(username),
        instances=instances,
        mem=32,
        cpus=0.01,
        labels={
            'HAPROXY_0_MODE': 'http',
            'HAPROXY_0_VHOST': '{username}.summit.{lb}'.format(
                username=slugify(username),
                lb=os.environ['LOAD_BALANCER']),
            'TWITTER_HANDLE': username,
        },
        container=MarathonContainer(
            type='DOCKER',
            docker=MarathonDockerContainer(
                image='nginx',
                network='HOST',
                port_mappings=[
                    MarathonContainerPortMapping(container_port=80, service_port=0),
                    MarathonContainerPortMapping(container_port=443, service_port=0),
                ],
                priviledged=False,
                force_pull_image=False)
        ),
        health_checks=[MarathonHealthCheck(
            grace_period_seconds=10,
            interval_seconds=10,
            max_consecutive_failures=3,
            path='/',
            port_index=0,
            protocol='HTTP',
            timeout_seconds=3)],
    )
    return app


@cel.task(bind=True)
def start_app(self, username, instances):
    app = make_app(username, instances)
    resp = cel.marathon.create_app(app_id=app.id, app=app)
    if resp:
        return json.loads(resp.to_json())
    return resp


@cel.task(bind=True)
def scale_app(self, username, instances):
    app_id = find_app_id(username)
    if app_id:
        resp = cel.marathon.scale_app(app_id, instances=instances)
        return resp


@cel.task(bind=True)
def restart_app(self, username, **kwargs):
    app_id = find_app_id(username)
    if app_id:
        resp = cel.marathon.restart_app(app_id, force=True)
        return resp


@cel.task(bind=True)
def delete_app(self, username, **kwargs):
    app_id = find_app_id(username)
    if app_id:
        resp = cel.marathon.delete_app(app_id, force=True)
        return resp


@cel.task(bind=True)
def stop_app(self, username):
    app_id = find_app_id(username)
    if app_id:
        resp = cel.marathon.scale_app(app_id, instances=0)
        return resp
