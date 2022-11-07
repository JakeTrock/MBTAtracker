import json
import requests
import typing

class Route(object):
    def __init__(self, record: dict):
        attributes = record.get("attributes", {})
        self.route_id = record.get("id")
        self.long_name = attributes.get("long_name")

class Stop(object):
    def __init__(self, record: dict):
        attributes = record.get("attributes", {})
        self.stop_id = record.get("id")
        self.name = attributes.get("name")


class MbtaApi(object):
    def __init__(self, api_key: str):
        self._api_key = api_key

    def routes(self, route_type=None) -> typing.List[Route]:
        return self._request(
            path="routes",
            query_params={
                "fields[route]": "long_name",#shave down requests
                "filter[type]": "0,1"
            },
            model=Route,
        )

    def stops(self, route_id: str) -> typing.List[Stop]:
        return self._request(
            path="stops",
            query_params={
                "fields[stop]": "name",#shave down requests
                "filter[route]": route_id,
            },
            model=Stop,
        )

    def _request(self, path, query_params: dict, model: typing.Type) -> typing.List:
        res = requests.get(
            f"https://api-v3.mbta.com/{path}",
            params={**{
                "api_key": self._api_key,
                "page[limit]": 1000000,#there probably won't ever be this many
            }, **(query_params if query_params else {})},
            headers={
                "Accept-Encoding": "gzip"#I have a need... a need for speed...
            }
        )
        if res.status_code == 200:
            return [model(record) for record in res.json().get("data", [])]