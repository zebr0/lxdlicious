import enum
import json
from pathlib import Path
from typing import Optional, List

import requests_unixsocket
import yaml
import zebr0

KEY_DEFAULT = "lxd-stack"
URL_DEFAULT = "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"


class Collection(str, enum.Enum):
    STORAGE_POOLS = "/1.0/storage-pools",
    NETWORKS = "/1.0/networks",
    PROFILES = "/1.0/profiles",
    INSTANCES = "/1.0/instances"


class Client:
    def __init__(self, url: str = URL_DEFAULT):
        self.url = url

        # this "hook" will be executed after each request
        # see http://docs.python-requests.org/en/master/user/advanced/#event-hooks
        def hook(response, **_):
            if not response.ok:
                raise Exception(response.text)

            # this will wait for lxd asynchronous operations to be finished
            # see https://github.com/lxc/lxd/blob/master/doc/rest-api.md#background-operation
            if response.json().get("type") == "async":
                self.session.get(self.url + response.json().get("operation") + "/wait")

        self.session = requests_unixsocket.Session()
        self.session.hooks["response"].append(hook)

    def exists(self, collection, resource_name):
        print(f"checking {collection}/{resource_name}")
        return any(filter(
            lambda a: a == collection + "/" + resource_name,
            self.session.get(self.url + collection).json().get("metadata")
        ))

    def create(self, collection, resource):
        if not self.exists(collection, resource.get("name")):
            print(f"creating {collection}/{json.dumps(resource)}")
            self.session.post(self.url + collection, json=resource)

    def delete(self, collection, resource_name):
        if self.exists(collection, resource_name):
            print(f"deleting {collection}/{resource_name}")
            self.session.delete(self.url + collection + "/" + resource_name)

    def is_running(self, instance_name):
        print(f"checking status {Collection.INSTANCES}/{instance_name}")
        return self.session.get(self.url + Collection.INSTANCES + "/" + instance_name).json().get("metadata").get("status") == "Running"

    def start(self, instance_name):
        if not self.is_running(instance_name):
            print(f"starting {Collection.INSTANCES}/{instance_name}")
            self.session.put(self.url + Collection.INSTANCES + "/" + instance_name + "/state", json={"action": "start"})

    def stop(self, instance_name):
        if self.is_running(instance_name):
            print(f"stopping {Collection.INSTANCES}/{instance_name}")
            self.session.put(self.url + Collection.INSTANCES + "/" + instance_name + "/state", json={"action": "stop"})


def create(url: str, levels: Optional[List[str]], cache: int, configuration_file: Path, key: str = KEY_DEFAULT, lxd_url: str = URL_DEFAULT):
    stack = yaml.load(zebr0.Client(url, levels, cache, configuration_file).get(key), Loader=yaml.BaseLoader)
    client = Client(lxd_url)

    for resource in stack.get("storage_pools") or []:
        client.create(Collection.STORAGE_POOLS, resource)
    for resource in stack.get("networks") or []:
        client.create(Collection.NETWORKS, resource)
    for resource in stack.get("profiles") or []:
        client.create(Collection.PROFILES, resource)
    for resource in stack.get("instances") or []:
        client.create(Collection.INSTANCES, resource)


def start(url: str, levels: Optional[List[str]], cache: int, configuration_file: Path, key: str = KEY_DEFAULT, lxd_url: str = URL_DEFAULT):
    stack = yaml.load(zebr0.Client(url, levels, cache, configuration_file).get(key), Loader=yaml.BaseLoader)
    client = Client(lxd_url)

    for resource in stack.get("instances") or []:
        client.start(resource.get("name"))


def stop(url: str, levels: Optional[List[str]], cache: int, configuration_file: Path, key: str = KEY_DEFAULT, lxd_url: str = URL_DEFAULT):
    stack = yaml.load(zebr0.Client(url, levels, cache, configuration_file).get(key), Loader=yaml.BaseLoader)
    client = Client(lxd_url)

    for resource in stack.get("instances") or []:
        client.stop(resource.get("name"))


def delete(url: str, levels: Optional[List[str]], cache: int, configuration_file: Path, key: str = KEY_DEFAULT, lxd_url: str = URL_DEFAULT):
    stack = yaml.load(zebr0.Client(url, levels, cache, configuration_file).get(key), Loader=yaml.BaseLoader)
    client = Client(lxd_url)

    for resource in stack.get("instances") or []:
        client.delete(Collection.INSTANCES, resource.get("name"))
    for resource in stack.get("profiles") or []:
        client.delete(Collection.PROFILES, resource.get("name"))
    for resource in stack.get("networks") or []:
        client.delete(Collection.NETWORKS, resource.get("name"))
    for resource in stack.get("storage_pools") or []:
        client.delete(Collection.STORAGE_POOLS, resource.get("name"))


def main(args: Optional[List[str]] = None) -> None:
    argparser = zebr0.build_argument_parser(description="zebr0 client to deploy an application to a local LXD environment")
    argparser.add_argument("command", choices=["create", "start", "stop", "delete"])
    argparser.add_argument("key", nargs="?", default="lxd-stack", help="the stack's key, defaults to 'lxd-stack'")
    argparser.add_argument("--lxd-url", default=URL_DEFAULT, help="")
    args = argparser.parse_args(args)

    globals()[args.command](args.url, args.levels, args.cache, args.configuration_file, args.key, args.lxd_url)
