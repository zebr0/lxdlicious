#!/usr/bin/python3 -u

import subprocess
import sys

import requests_unixsocket


def run(command):
    subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr).wait()


# cleans the api output of volatile information before testing
def clean_container_json(json):
    json.get("metadata").pop("created_at")
    json.get("metadata").pop("config")
    json.get("metadata").pop("last_used_at")
    json.get("metadata").get("expanded_config").pop("volatile.base_image")
    json.get("metadata").get("expanded_config").pop("volatile.idmap.next")
    json.get("metadata").get("expanded_config").pop("volatile.last_state.idmap")
    json.get("metadata").get("expanded_config").pop("volatile.eth0.hwaddr")
    json.get("metadata").get("expanded_config").pop("image.description")
    json.get("metadata").get("expanded_config").pop("image.serial")

    return json


# opens a unix socket session to call the lxd api
session = requests_unixsocket.Session()
api_url = "http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket"

# ensures the test resources don't exist before continuing
run("cat nominal.yml | ../src/lxd-compose delete")

# test creating a stack (twice, for idempotence)
run("cat nominal.yml | ../src/lxd-compose create")
run("cat nominal.yml | ../src/lxd-compose create")
assert session.get(api_url + "/1.0/storage-pools/nominal-storage-pool").json() == {'error': '',
                                                                                   'error_code': 0,
                                                                                   'metadata': {'config': {'source': '/var/lib/lxd/storage-pools/nominal-storage-pool'},
                                                                                                'description': '',
                                                                                                'driver': 'dir',
                                                                                                'locations': ['none'],
                                                                                                'name': 'nominal-storage-pool',
                                                                                                'status': 'Created',
                                                                                                'used_by': ['/1.0/containers/dummy-container', '/1.0/containers/parent-container',
                                                                                                            '/1.0/profiles/nominal-profile']},
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
                                                                                      'used_by': ['/1.0/containers/dummy-container', '/1.0/containers/parent-container']},
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
                                                                                      'used_by': ['/1.0/containers/dummy-container', '/1.0/containers/parent-container']},
                                                                         'operation': '',
                                                                         'status': 'Success',
                                                                         'status_code': 200,
                                                                         'type': 'sync'}
assert clean_container_json(session.get(api_url + "/1.0/containers/parent-container").json()) == {'error': '',
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
                                                                                                                                   'user.user-data': '#cloud-config\n'
                                                                                                                                                     'runcmd:\n'
                                                                                                                                                     '  - echo "parent configuration"\n'
                                                                                                                                                     'power_state:\n'
                                                                                                                                                     '  mode: poweroff\n',
                                                                                                                                   'volatile.eth0.name': 'eth0',
                                                                                                                                   'volatile.idmap.base': '0',
                                                                                                                                   'volatile.last_state.power': 'STOPPED'},
                                                                                                               'expanded_devices': {'eth0': {'nictype': 'bridged',
                                                                                                                                             'parent': 'nominalnetwork0',
                                                                                                                                             'type': 'nic'},
                                                                                                                                    'root': {'path': '/',
                                                                                                                                             'pool': 'nominal-storage-pool',
                                                                                                                                             'type': 'disk'}},
                                                                                                               'location': '',
                                                                                                               'name': 'parent-container',
                                                                                                               'profiles': ['nominal-profile'],
                                                                                                               'stateful': False,
                                                                                                               'status': 'Stopped',
                                                                                                               'status_code': 102},
                                                                                                  'operation': '',
                                                                                                  'status': 'Success',
                                                                                                  'status_code': 200,
                                                                                                  'type': 'sync'}
assert clean_container_json(session.get(api_url + "/1.0/containers/dummy-container").json()) == {'error': '',
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
                                                                                                                                  'user.user-data': '#cloud-config\n'
                                                                                                                                                    'runcmd:\n'
                                                                                                                                                    '  - echo "child configuration"\n',
                                                                                                                                  'volatile.apply_template': 'copy',
                                                                                                                                  'volatile.eth0.name': 'eth0',
                                                                                                                                  'volatile.idmap.base': '0'},
                                                                                                              'expanded_devices': {'eth0': {'nictype': 'bridged',
                                                                                                                                            'parent': 'nominalnetwork0',
                                                                                                                                            'type': 'nic'},
                                                                                                                                   'root': {'path': '/',
                                                                                                                                            'pool': 'nominal-storage-pool',
                                                                                                                                            'type': 'disk'}},
                                                                                                              'location': '',
                                                                                                              'name': 'dummy-container',
                                                                                                              'profiles': ['nominal-profile'],
                                                                                                              'stateful': False,
                                                                                                              'status': 'Stopped',
                                                                                                              'status_code': 102},
                                                                                                 'operation': '',
                                                                                                 'status': 'Success',
                                                                                                 'status_code': 200,
                                                                                                 'type': 'sync'}

# test starting a stack (twice, for idempotence)
run("cat nominal.yml | ../src/lxd-compose start")
run("cat nominal.yml | ../src/lxd-compose start")
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("metadata").get("status") == "Running"

# test stopping a stack (twice, for idempotence)
run("cat nominal.yml | ../src/lxd-compose stop")
run("cat nominal.yml | ../src/lxd-compose stop")
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("metadata").get("status") == "Stopped"

# test deleting a stack (twice, for idempotence)
assert session.get(api_url + "/1.0/storage-pools/nominal-storage-pool").json().get("error_code") == 0
assert session.get(api_url + "/1.0/networks/nominalnetwork0").json().get("error_code") == 0
assert session.get(api_url + "/1.0/profiles/nominal-profile").json().get("error_code") == 0
assert session.get(api_url + "/1.0/containers/parent-container").json().get("error_code") == 0
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("error_code") == 0
run("cat nominal.yml | ../src/lxd-compose delete")
run("cat nominal.yml | ../src/lxd-compose delete")
assert session.get(api_url + "/1.0/storage-pools/nominal-storage-pool").json().get("error_code") == 404
assert session.get(api_url + "/1.0/networks/nominalnetwork0").json().get("error_code") == 404
assert session.get(api_url + "/1.0/profiles/nominal-profile").json().get("error_code") == 404
assert session.get(api_url + "/1.0/containers/parent-container").json().get("error_code") == 404
assert session.get(api_url + "/1.0/containers/dummy-container").json().get("error_code") == 404

# tests if an empty configuration is handled without error, even if it does nothing
run("echo | ../src/lxd-compose create")
run("echo | ../src/lxd-compose start")
run("echo | ../src/lxd-compose stop")
run("echo | ../src/lxd-compose delete")

session.close()
