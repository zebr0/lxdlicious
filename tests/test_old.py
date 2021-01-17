import subprocess
import time

import pytest
import zebr0

import zebr0_lxd
from zebr0_lxd import Collection

LXD_STACK = """
---
storage_pools:
- name: nominal-storage-pool
  driver: dir

networks:
- name: nominalnetwork0
  config:
    ipv4.address: 10.42.254.1/24
    ipv4.nat: true
    ipv6.address: none
    dns.mode: dynamic
    dns.domain: test

profiles:
- name: nominal-profile
  devices:
    root:
      path: /
      pool: nominal-storage-pool
      type: disk
    eth0:
      type: nic
      nictype: bridged
      parent: nominalnetwork0

containers:
- name: dummy-container
  profiles:
  - nominal-profile
  source:
    type: image
    mode: pull
    server: https://cloud-images.ubuntu.com/daily
    protocol: simplestreams
    alias: bionic
""".lstrip()

LXD_USER_DATA = """
#cloud-config
""".lstrip()


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


def test_exists():
    client = zebr0_lxd.Client()
    assert not client.exists(Collection.STORAGE_POOLS, "nominal-storage-pool")
    subprocess.Popen("lxc storage create nominal-storage-pool dir", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    assert client.exists(Collection.STORAGE_POOLS, "nominal-storage-pool")
    subprocess.Popen("lxc storage delete nominal-storage-pool", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()


def test_create():
    client = zebr0_lxd.Client()
    assert not client.exists(Collection.STORAGE_POOLS, "nominal-storage-pool")
    client.create(Collection.STORAGE_POOLS, {"name": "nominal-storage-pool", "driver": "dir"})
    assert client.exists(Collection.STORAGE_POOLS, "nominal-storage-pool")
    subprocess.Popen("lxc storage delete nominal-storage-pool", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()


def test_delete():
    client = zebr0_lxd.Client()
    subprocess.Popen("lxc storage create nominal-storage-pool dir", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    assert client.exists(Collection.STORAGE_POOLS, "nominal-storage-pool")
    client.delete(Collection.STORAGE_POOLS, "nominal-storage-pool")
    assert not client.exists(Collection.STORAGE_POOLS, "nominal-storage-pool")


def test_is_running():
    client = zebr0_lxd.Client()
    subprocess.Popen("lxc launch ubuntu:focal test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert client.is_running("test")
    subprocess.Popen("lxc stop test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert not client.is_running("test")
    client.delete(Collection.CONTAINERS, "test")


def test_start():
    client = zebr0_lxd.Client()
    client.create(Collection.CONTAINERS, {"name": "test", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/daily", "protocol": "simplestreams", "alias": "bionic"}})
    assert not client.is_running("test")
    client.start("test")
    time.sleep(1)
    assert client.is_running("test")
    subprocess.Popen("lxc stop test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert not client.is_running("test")
    client.delete(Collection.CONTAINERS, "test")


def test_stop():
    client = zebr0_lxd.Client()
    subprocess.Popen("lxc launch ubuntu:focal test", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).wait()
    time.sleep(1)
    assert client.is_running("test")
    client.stop("test")
    assert not client.is_running("test")
    client.delete(Collection.CONTAINERS, "test")


def test_ok(server):
    client = zebr0_lxd.Client()
    server.data = {
        "lxd-stack": LXD_STACK,
        "lxd-user-data": LXD_USER_DATA
    }

    # ensures the test resources don't exist before continuing
    zebr0_lxd.main("delete -u http://localhost:8000 -l project stage".split())

    # test creating and running a container (twice, for idempotence)
    zebr0_lxd.main("create -u http://localhost:8000 -l project stage".split())
    zebr0_lxd.main("create -u http://localhost:8000 -l project stage".split())
    assert client.session.get(client.url + "/1.0/storage-pools/nominal-storage-pool").json() == {'error': '',
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
    assert client.session.get(client.url + "/1.0/networks/nominalnetwork0").json() == {'error': '',
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
    assert client.session.get(client.url + "/1.0/profiles/nominal-profile").json() == {'error': '',
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
    container_json = client.session.get(client.url + "/1.0/containers/dummy-container").json()
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
    zebr0_lxd.main("start -u http://localhost:8000 -l project stage".split())
    zebr0_lxd.main("start -u http://localhost:8000 -l project stage".split())
    assert client.session.get(client.url + "/1.0/containers/dummy-container").json().get("metadata").get("status") == "Running"

    # test stopping a stack (twice, for idempotence)
    zebr0_lxd.main("stop -u http://localhost:8000 -l project stage".split())
    zebr0_lxd.main("stop -u http://localhost:8000 -l project stage".split())
    assert client.session.get(client.url + "/1.0/containers/dummy-container").json().get("metadata").get("status") == "Stopped"

    # test deleting a container (twice, for idempotence)
    zebr0_lxd.main("delete -u http://localhost:8000 -l project stage".split())
    zebr0_lxd.main("delete -u http://localhost:8000 -l project stage".split())
