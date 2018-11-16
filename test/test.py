#!/usr/bin/python3 -u

import http.server
import socketserver
import subprocess
import sys
import threading

import requests_unixsocket


class ThreadingHttpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass


server = ThreadingHttpServer(("0.0.0.0", 8000), http.server.SimpleHTTPRequestHandler)
thread = threading.Thread(target=server.serve_forever)
thread.start()


def run(command):
    subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr).wait()


# ensures the test resources don't exist before continuing
run("../src/zebr0-lxd delete -u http://localhost:8000 -p project -s stage")

# test creating a container (twice, for idempotence)
run("../src/zebr0-lxd create -u http://localhost:8000 -p project -s stage")
run("../src/zebr0-lxd create -u http://localhost:8000 -p project -s stage")

# opens a unix socket session to call the lxd api
session = requests_unixsocket.Session()
api_url = "http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket"

# cleans the api output of volatile information before testing
container_json = session.get(api_url + "/1.0/containers/project-stage").json()
container_json.get("metadata").pop("created_at")
container_json.get("metadata").pop("last_used_at")
container_json.get("metadata").pop("config")
container_json.get("metadata").get("expanded_config").pop("volatile.base_image")
container_json.get("metadata").get("expanded_config").pop("volatile.idmap.next")
container_json.get("metadata").get("expanded_config").pop("volatile.last_state.idmap")
container_json.get("metadata").get("expanded_config").pop("volatile.eth0.hwaddr")
container_json.get("metadata").get("expanded_config").pop("image.description")
container_json.get("metadata").get("expanded_config").pop("image.serial")
assert container_json == {'error': '',
                          'error_code': 0,
                          'metadata': {'architecture': 'x86_64',
                                       'description': '',
                                       'devices': {},
                                       'ephemeral': False,
                                       'expanded_config': {'image.architecture': 'amd64',
                                                           'image.label': 'daily',
                                                           'image.os': 'ubuntu',
                                                           'image.release': 'bionic',
                                                           'image.version': '18.04',
                                                           'user.user-data': '#cloud-config',
                                                           'volatile.eth0.name': 'eth0',
                                                           'volatile.idmap.base': '0',
                                                           'volatile.last_state.power': 'RUNNING'},
                                       'expanded_devices': {'eth0': {'nictype': 'bridged',
                                                                     'parent': 'lxd0',
                                                                     'type': 'nic'},
                                                            'root': {'path': '/',
                                                                     'pool': 'default',
                                                                     'type': 'disk'}},
                                       'location': '',
                                       'name': 'project-stage',
                                       'profiles': ['default'],
                                       'stateful': False,
                                       'status': 'Running',
                                       'status_code': 103},
                          'operation': '',
                          'status': 'Success',
                          'status_code': 200,
                          'type': 'sync'}

# test deleting a container (twice, for idempotence)
run("../src/zebr0-lxd delete -u http://localhost:8000 -p project -s stage")
run("../src/zebr0-lxd delete -u http://localhost:8000 -p project -s stage")
assert session.get(api_url + "/1.0/containers/project-stage").json().get("error_code") == 404

session.close()

server.shutdown()
