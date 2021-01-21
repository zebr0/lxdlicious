import subprocess
import time

import pytest

import zebr0_lxd
from zebr0_lxd import Collection


@pytest.fixture(scope="module")
def client():
    return zebr0_lxd.Client()


@pytest.fixture(autouse=True)
def clean_before_after():
    def clean():
        subprocess.Popen("lxc storage delete test-storage-pool", shell=True).wait()
        subprocess.Popen("lxc network delete test-network", shell=True).wait()
        subprocess.Popen("lxc profile delete test-profile", shell=True).wait()
        subprocess.Popen("lxc stop test-instance", shell=True).wait()
        subprocess.Popen("lxc delete test-instance", shell=True).wait()

    clean()
    yield  # see https://stackoverflow.com/questions/22627659/run-code-before-and-after-each-test-in-py-test
    clean()


def test_exists_storage_pool(client):
    assert not client.exists(Collection.STORAGE_POOLS, "test-storage-pool")
    subprocess.Popen("lxc storage create test-storage-pool dir", shell=True).wait()
    assert client.exists(Collection.STORAGE_POOLS, "test-storage-pool")


def test_exists_network(client):
    assert not client.exists(Collection.NETWORKS, "test-network")
    subprocess.Popen("lxc network create test-network", shell=True).wait()
    assert client.exists(Collection.NETWORKS, "test-network")


def test_exists_profile(client):
    assert not client.exists(Collection.PROFILES, "test-profile")
    subprocess.Popen("lxc profile create test-profile", shell=True).wait()
    assert client.exists(Collection.PROFILES, "test-profile")


def test_exists_instance(client):
    assert not client.exists(Collection.INSTANCES, "test-instance")
    subprocess.Popen("lxc launch test-instance --empty", shell=True).wait()
    assert client.exists(Collection.INSTANCES, "test-instance")


def test_create_error(client):
    with pytest.raises(Exception) as exception:
        client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool"})
    assert '{"error":"No driver provided","error_code":400,"type":"error"}' in str(exception.value)


def test_create_storage_pool(client):
    client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    assert client.exists(Collection.STORAGE_POOLS, "test-storage-pool")


def test_create_network(client):
    client.create(Collection.NETWORKS, {"name": "test-network"})
    assert client.exists(Collection.NETWORKS, "test-network")


def test_create_profile(client):
    client.create(Collection.PROFILES, {"name": "test-profile"})
    assert client.exists(Collection.PROFILES, "test-profile")


def test_create_instance(client):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})
    assert client.exists(Collection.INSTANCES, "test-instance")


def test_delete_storage_pool(client):
    client.create(Collection.STORAGE_POOLS, {"name": "test-storage-pool", "driver": "dir"})
    client.delete(Collection.STORAGE_POOLS, "test-storage-pool")
    assert not client.exists(Collection.STORAGE_POOLS, "test-storage-pool")


def test_delete_network(client):
    client.create(Collection.NETWORKS, {"name": "test-network"})
    client.delete(Collection.NETWORKS, "test-network")
    assert not client.exists(Collection.NETWORKS, "test-network")


def test_delete_profile(client):
    client.create(Collection.PROFILES, {"name": "test-profile"})
    client.delete(Collection.PROFILES, "test-profile")
    assert not client.exists(Collection.PROFILES, "test-profile")


def test_delete_instance(client):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "none"}})
    client.delete(Collection.INSTANCES, "test-instance")
    assert not client.exists(Collection.INSTANCES, "test-instance")


def test_is_running(client):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    assert not client.is_running("test-instance")
    subprocess.Popen("lxc start test-instance", shell=True).wait()
    assert client.is_running("test-instance")


def test_start(client):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    client.start("test-instance")
    assert client.is_running("test-instance")


def test_stop(client):
    client.create(Collection.INSTANCES, {"name": "test-instance", "source": {"type": "image", "mode": "pull", "server": "https://cloud-images.ubuntu.com/releases", "protocol": "simplestreams", "alias": "focal"}})
    client.start("test-instance")
    time.sleep(0.1)
    client.stop("test-instance")
    assert not client.is_running("test-instance")
