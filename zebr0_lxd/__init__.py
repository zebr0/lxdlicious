import enum
import json
from typing import Optional, List

import requests_unixsocket
import yaml
import zebr0

KEY_DEFAULT = "lxd-stack"
URL_DEFAULT = "http+unix://%2Fvar%2Fsnap%2Flxd%2Fcommon%2Flxd%2Funix.socket"


class Resource(str, enum.Enum):
    STORAGE_POOLS = "storage-pools",
    NETWORKS = "networks",
    PROFILES = "profiles",
    INSTANCES = "instances"

    def path(self):
        return "/1.0/" + self


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

    def exists(self, resource, name):
        print(f"checking {resource}/{name}")
        return any(filter(
            lambda a: a == resource.path() + "/" + name,
            self.session.get(self.url + resource.path()).json().get("metadata")
        ))

    def create(self, resource, config):
        if not self.exists(resource, config.get("name")):
            print(f"creating {resource}/{json.dumps(config)}")
            self.session.post(self.url + resource.path(), json=config)

    def delete(self, resource, name):
        if self.exists(resource, name):
            print(f"deleting {resource}/{name}")
            self.session.delete(self.url + resource.path() + "/" + name)

    def is_running(self, name):
        print(f"checking {Resource.INSTANCES}/{name}")
        return self.session.get(self.url + Resource.INSTANCES.path() + "/" + name).json().get("metadata").get("status") == "Running"

    def start(self, name):
        if not self.is_running(name):
            print(f"starting {Resource.INSTANCES}/{name}")
            self.session.put(self.url + Resource.INSTANCES.path() + "/" + name + "/state", json={"action": "start"})

    def stop(self, name):
        if self.is_running(name):
            print(f"stopping {Resource.INSTANCES}/{name}")
            self.session.put(self.url + Resource.INSTANCES.path() + "/" + name + "/state", json={"action": "stop"})

    def create_stack(self, stack):
        for resource in list(Resource):
            for config in stack.get(resource) or []:
                self.create(resource, config)

    def delete_stack(self, stack):
        for resource in reversed(Resource):
            for config in stack.get(resource) or []:
                self.delete(resource, config.get("name"))

    def start_stack(self, stack):
        for config in stack.get(Resource.INSTANCES) or []:
            self.start(config.get("name"))

    def stop_stack(self, stack):
        for config in stack.get(Resource.INSTANCES) or []:
            self.stop(config.get("name"))


def main(args: Optional[List[str]] = None) -> None:
    argparser = zebr0.build_argument_parser(description="zebr0 client to deploy an application to a local LXD environment")
    argparser.add_argument("command", choices=["create", "delete", "start", "stop"])
    argparser.add_argument("key", nargs="?", default="lxd-stack", help="the stack's key, defaults to 'lxd-stack'")
    argparser.add_argument("--lxd-url", default=URL_DEFAULT, help="")
    args = argparser.parse_args(args)

    value = zebr0.Client(args.url, args.levels, args.cache, args.configuration_file).get(args.key)
    if not value:
        print(f"key '{args.key}' not found on server {args.url}")
        exit(1)

    stack = yaml.load(value, Loader=yaml.BaseLoader)
    if not isinstance(stack, dict):
        print(f"key '{args.key}' on server {args.url} is not a proper yaml or json dictionary")
        exit(1)

    getattr(Client(args.lxd_url), args.command + "_stack")(stack)
