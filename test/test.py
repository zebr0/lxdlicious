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


# opens a unix socket session to call the lxd api
session = requests_unixsocket.Session()
api_url = "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"

# ensures the test resources don't exist before continuing
run("../zebr0-lxd delete -u http://localhost:8000 -l project stage")

# test creating and running a container (twice, for idempotence)
run("../zebr0-lxd create -u http://localhost:8000 -l project stage")
run("../zebr0-lxd create -u http://localhost:8000 -l project stage")
assert session.get(api_url + "/1.0/storage-pools/nominal-storage-pool").json() == {'error': '',
                                                                                   'error_code': 0,
                                                                                   'metadata': {'config': {'source': '/var/snap/lxd/common/lxd/storage-pools/nominal-storage-pool'},
                                                                                                'description': '',
                                                                                                'driver': 'dir',
                                                                                                'locations': ['none'],
                                                                                                'name': 'nominal-storage-pool',
                                                                                                'status': 'Created',
                                                                                                'used_by': ['/1.0/instances/dummy-container', '/1.0/profiles/nominal-profile']},
                                                                                   'operation': '',
                                                                                   'status': 'Success',
                                                                                   'status_code': 200,
                                                                                   'type': 'sync'}
assert session.get(api_url + "/1.0/networks/nominalnetwork0").json() == {'error': '',
                                                                         'error_code': 0,
                                                                         'metadata': {'config': {'dns.domain': 'test',
                                                                                                 'dns.mode': 'dynamic',
                                                                                                 'ipv4.address': '10.42.254.1/24',
                                                                                                 'ipv4.nat': 'true',
                                                                                                 'ipv6.address': 'none'},
                                                                                      'description': '',
                                                                                      'locations': ['none'],
                                                                                      'managed': True,
                                                                                      'name': 'nominalnetwork0',
                                                                                      'status': 'Created',
                                                                                      'type': 'bridge',
                                                                                      'used_by': ['/1.0/instances/dummy-container', '/1.0/profiles/nominal-profile']},
                                                                         'operation': '',
                                                                         'status': 'Success',
                                                                         'status_code': 200,
                                                                         'type': 'sync'}
assert session.get(api_url + "/1.0/profiles/nominal-profile").json() == {'error': '',
                                                                         'error_code': 0,
                                                                         'metadata': {'config': {},
                                                                                      'description': '',
                                                                                      'devices': {'eth0': {'nictype': 'bridged',
                                                                                                           'parent': 'nominalnetwork0',
                                                                                                           'type': 'nic'},
                                                                                                  'root': {'path': '/',
                                                                                                           'pool': 'nominal-storage-pool',
                                                                                                           'type': 'disk'}},
                                                                                      'name': 'nominal-profile',
                                                                                      'used_by': ['/1.0/instances/dummy-container']},
                                                                         'operation': '',
                                                                         'status': 'Success',
                                                                         'status_code': 200,
                                                                         'type': 'sync'}
# cleans the api output of "random" information before testing
container_json = session.get(api_url + "/1.0/containers/dummy-container").json()
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
                                                           'image.type': 'squashfs',
                                                           'image.version': '18.04',
                                                           'volatile.apply_template': 'create',
                                                           'volatile.eth0.name': 'eth0',
                                                           'volatile.idmap.base': '0'},
                                       'expanded_devices': {'eth0': {'nictype': 'bridged',
                                                                     'parent': 'nominalnetwork0',
                                                                     'type': 'nic'},
                                                            'root': {'path': '/',
                                                                     'pool': 'nominal-storage-pool',
                                                                     'type': 'disk'}},
                                       'location': 'none',
                                       'name': 'dummy-container',
                                       'profiles': ['nominal-profile'],
                                       'stateful': False,
                                       'status': 'Stopped',
                                       'status_code': 102,
                                       'type': 'container'},
                          'operation': '',
                          'status': 'Success',
                          'status_code': 200,
                          'type': 'sync'}

# test starting a stack (twice, for idempotence)
run("../zebr0-lxd start -u http://localhost:8000 -l project stage")
run("../zebr0-lxd start -u http://localhost:8000 -l project stage")
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("metadata").get("status") == "Running"

# test stopping a stack (twice, for idempotence)
run("../zebr0-lxd stop -u http://localhost:8000 -l project stage")
run("../zebr0-lxd stop -u http://localhost:8000 -l project stage")
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("metadata").get("status") == "Stopped"

# test deleting a container (twice, for idempotence)
run("../zebr0-lxd delete -u http://localhost:8000 -l project stage")
run("../zebr0-lxd delete -u http://localhost:8000 -l project stage")
assert session.get(api_url + "/1.0/storage-pools/nominal-storage-pool").json().get("error_code") == 404
assert session.get(api_url + "/1.0/networks/nominalnetwork0").json().get("error_code") == 404
assert session.get(api_url + "/1.0/profiles/nominal-profile").json().get("error_code") == 404
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("error_code") == 404

session.close()

server.shutdown()
