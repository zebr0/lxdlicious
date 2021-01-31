import pytest

import zebr0_lxd


@pytest.fixture(scope="module")
def client():
    return zebr0_lxd.Client()


@pytest.fixture
def mock_client(monkeypatch):
    log = []

    def mock_create(_, resource, config):
        log.append(("create", resource, config))

    def mock_start(_, name):
        log.append(("start", name))

    def mock_stop(_, name):
        log.append(("stop", name))

    def mock_delete(_, resource, name):
        log.append(("delete", resource, name))

    monkeypatch.setattr(zebr0_lxd.Client, "create", mock_create)
    monkeypatch.setattr(zebr0_lxd.Client, "start", mock_start)
    monkeypatch.setattr(zebr0_lxd.Client, "stop", mock_stop)
    monkeypatch.setattr(zebr0_lxd.Client, "delete", mock_delete)

    return log


LXD_STACK = {
    "storage-pools": [{"name": "test-storage-pool", "driver": "dir"}],
    "networks": [{"name": "test-network"}],
    "profiles": [{"name": "test-profile"}],
    "instances": [{"name": "test-instance", "source": {"type": "none"}}]
}


def test_create_stack(client, mock_client):
    client.create_stack(LXD_STACK)
    assert mock_client == [("create", "storage-pools", {"name": "test-storage-pool", "driver": "dir"}),
                           ("create", "networks", {"name": "test-network"}),
                           ("create", "profiles", {"name": "test-profile"}),
                           ("create", "instances", {"name": "test-instance", "source": {"type": "none"}})]


def test_start_stack(client, mock_client):
    client.start_stack(LXD_STACK)
    assert mock_client == [("start", "test-instance")]


def test_stop_stack(client, mock_client):
    client.stop_stack(LXD_STACK)
    assert mock_client == [("stop", "test-instance")]


def test_delete_stack(client, mock_client):
    client.delete_stack(LXD_STACK)
    assert mock_client == [("delete", "instances", "test-instance"),
                           ("delete", "profiles", "test-profile"),
                           ("delete", "networks", "test-network"),
                           ("delete", "storage-pools", "test-storage-pool")]


CONTAINERS_ONLY = {"instances": [
    {"name": "test-instance-1", "source": {"type": "none"}},
    {"name": "test-instance-2", "source": {"type": "none"}}
]}


def test_create_containers_only(client, mock_client):
    client.create_stack(CONTAINERS_ONLY)
    assert mock_client == [("create", "instances", {"name": "test-instance-1", "source": {"type": "none"}}),
                           ("create", "instances", {"name": "test-instance-2", "source": {"type": "none"}})]


def test_start_containers_only(client, mock_client):
    client.start_stack(CONTAINERS_ONLY)
    assert mock_client == [("start", "test-instance-1"),
                           ("start", "test-instance-2")]


def test_stop_containers_only(client, mock_client):
    client.stop_stack(CONTAINERS_ONLY)
    assert mock_client == [("stop", "test-instance-1"),
                           ("stop", "test-instance-2")]


def test_delete_containers_only(client, mock_client):
    client.delete_stack(CONTAINERS_ONLY)
    assert mock_client == [("delete", "instances", "test-instance-1"),
                           ("delete", "instances", "test-instance-2")]
