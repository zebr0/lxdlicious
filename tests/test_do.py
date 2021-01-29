from pathlib import Path

import pytest
import zebr0

import zebr0_lxd
from zebr0_lxd import Command


@pytest.fixture(scope="module")
def server():
    with zebr0.TestServer() as server:
        yield server


@pytest.fixture
def mock_client(monkeypatch):
    log = []

    def mock_create(_, collection, resource):
        log.append((Command.CREATE, collection, resource))

    def mock_start(_, instance_name):
        log.append((Command.START, instance_name))

    def mock_stop(_, instance_name):
        log.append((Command.STOP, instance_name))

    def mock_delete(_, collection, resource_name):
        log.append((Command.DELETE, collection, resource_name))

    monkeypatch.setattr(zebr0_lxd.Client, Command.CREATE, mock_create)
    monkeypatch.setattr(zebr0_lxd.Client, Command.START, mock_start)
    monkeypatch.setattr(zebr0_lxd.Client, Command.STOP, mock_stop)
    monkeypatch.setattr(zebr0_lxd.Client, Command.DELETE, mock_delete)

    return log


def test_ko_key_not_found(server, capsys):
    server.data = {}

    with pytest.raises(SystemExit) as e:
        zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.CREATE)
    assert e.value.code == 1
    assert capsys.readouterr().out == "key 'lxd-stack' not found on server http://localhost:8000\n"


def test_ko_not_a_stack(server, capsys):
    server.data = {"lxd-stack": "not a stack"}

    with pytest.raises(SystemExit) as e:
        zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.CREATE)
    assert e.value.code == 1
    assert capsys.readouterr().out == "key 'lxd-stack' on server http://localhost:8000 is not a proper yaml or json dictionary\n"


LXD_STACK = """
---
storage-pools:
- name: test-storage-pool
  driver: dir

networks:
- name: test-network

profiles:
- name: test-profile

instances:
- name: test-instance
  source:
    type: none
""".lstrip()


def test_create_stack(server, mock_client):
    server.data = {"lxd-stack": LXD_STACK}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.CREATE)
    assert mock_client == [(Command.CREATE, "storage-pools", {"name": "test-storage-pool", "driver": "dir"}),
                           (Command.CREATE, "networks", {"name": "test-network"}),
                           (Command.CREATE, "profiles", {"name": "test-profile"}),
                           (Command.CREATE, "instances", {"name": "test-instance", "source": {"type": "none"}})]


def test_start_stack(server, mock_client):
    server.data = {"lxd-stack": LXD_STACK}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.START)
    assert mock_client == [(Command.START, "test-instance")]


def test_stop_stack(server, mock_client):
    server.data = {"lxd-stack": LXD_STACK}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.STOP)
    assert mock_client == [(Command.STOP, "test-instance")]


def test_delete_stack(server, mock_client):
    server.data = {"lxd-stack": LXD_STACK}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.DELETE)
    assert mock_client == [(Command.DELETE, "instances", "test-instance"),
                           (Command.DELETE, "profiles", "test-profile"),
                           (Command.DELETE, "networks", "test-network"),
                           (Command.DELETE, "storage-pools", "test-storage-pool")]


CONTAINERS_ONLY = """
---
instances:
- name: test-instance-1
  source:
    type: none
- name: test-instance-2
  source:
    type: none
""".lstrip()


def test_create_containers_only(server, mock_client):
    server.data = {"lxd-stack": CONTAINERS_ONLY}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.CREATE)
    assert mock_client == [(Command.CREATE, "instances", {"name": "test-instance-1", "source": {"type": "none"}}),
                           (Command.CREATE, "instances", {"name": "test-instance-2", "source": {"type": "none"}})]


def test_start_containers_only(server, mock_client):
    server.data = {"lxd-stack": CONTAINERS_ONLY}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.START)
    assert mock_client == [(Command.START, "test-instance-1"),
                           (Command.START, "test-instance-2")]


def test_stop_containers_only(server, mock_client):
    server.data = {"lxd-stack": CONTAINERS_ONLY}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.STOP)
    assert mock_client == [(Command.STOP, "test-instance-1"),
                           (Command.STOP, "test-instance-2")]


def test_delete_containers_only(server, mock_client):
    server.data = {"lxd-stack": CONTAINERS_ONLY}

    zebr0_lxd.do("http://localhost:8000", [], 1, Path(""), Command.DELETE)
    assert mock_client == [(Command.DELETE, "instances", "test-instance-1"),
                           (Command.DELETE, "instances", "test-instance-2")]
