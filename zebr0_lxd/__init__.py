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
    STORAGE_POOLS = "storage-pools",
    NETWORKS = "networks",
    PROFILES = "profiles",
    INSTANCES = "instances"

    def path(self):
        return "/1.0/" + self


class Command(str, enum.Enum):
    CREATE = "create",
    START = "start",
    STOP = "stop",
    DELETE = "delete"


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
            lambda a: a == collection.path() + "/" + resource_name,
            self.session.get(self.url + collection.path()).json().get("metadata")
        ))

    def create(self, collection, resource):
        if not self.exists(collection, resource.get("name")):
            print(f"creating {collection}/{json.dumps(resource)}")
            self.session.post(self.url + collection.path(), json=resource)

    def delete(self, collection, resource_name):
        if self.exists(collection, resource_name):
            print(f"deleting {collection}/{resource_name}")
            self.session.delete(self.url + collection.path() + "/" + resource_name)

    def is_running(self, instance_name):
        print(f"checking {Collection.INSTANCES}/{instance_name}")
        return self.session.get(self.url + Collection.INSTANCES.path() + "/" + instance_name).json().get("metadata").get("status") == "Running"

    def start(self, instance_name):
        if not self.is_running(instance_name):
            print(f"starting {Collection.INSTANCES}/{instance_name}")
            self.session.put(self.url + Collection.INSTANCES.path() + "/" + instance_name + "/state", json={"action": "start"})

    def stop(self, instance_name):
        if self.is_running(instance_name):
            print(f"stopping {Collection.INSTANCES}/{instance_name}")
            self.session.put(self.url + Collection.INSTANCES.path() + "/" + instance_name + "/state", json={"action": "stop"})


def do(url: str, levels: Optional[List[str]], cache: int, configuration_file: Path, command: Command, key: str = KEY_DEFAULT, lxd_url: str = URL_DEFAULT):
    value = zebr0.Client(url, levels, cache, configuration_file).get(key)
    if not value:
        print(f"key '{key}' not found on server {url}")
        exit(1)

    stack = yaml.load(value, Loader=yaml.BaseLoader)
    if not isinstance(stack, dict):
        print(f"key '{key}' on server {url} is not a proper yaml or json dictionary")
        exit(1)

    client = Client(lxd_url)

    if command == Command.CREATE:
        for collection in list(Collection):
            for resource in stack.get(collection) or []:
                client.create(collection, resource)
    elif command == Command.START:
        for resource in stack.get(Collection.INSTANCES) or []:
            client.start(resource.get("name"))
    elif command == Command.STOP:
        for resource in stack.get(Collection.INSTANCES) or []:
            client.stop(resource.get("name"))
    elif command == Command.DELETE:
        for collection in reversed(Collection):
            for resource in stack.get(collection) or []:
                client.delete(collection, resource.get("name"))


def main(args: Optional[List[str]] = None) -> None:
    argparser = zebr0.build_argument_parser(description="zebr0 client to deploy an application to a local LXD environment")
    argparser.add_argument("command", choices=list(Command))
    argparser.add_argument("key", nargs="?", default="lxd-stack", help="the stack's key, defaults to 'lxd-stack'")
    argparser.add_argument("--lxd-url", default=URL_DEFAULT, help="")
    args = argparser.parse_args(args)

    do(args.url, args.levels, args.cache, args.configuration_file, args.command, args.key, args.lxd_url)
