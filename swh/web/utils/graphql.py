from typing import Dict

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from swh.web.utils.exc import NotFoundExc

transport = AIOHTTPTransport(url="http://127.0.0.1:8000/")
client = Client(transport=transport, fetch_schema_from_transport=True)


def get_one(
    query: str, variables, query_root, enrich=None, error_msg="", request=None
) -> Dict:
    # FIXME add a cache with query normalization
    try:
        result = client.execute(gql(query), variable_values=variables)[query_root]
    except Exception as e:
        # not found error
        raise NotFoundExc(error_msg, e)
    except Exception as e:
        # unknown error
        raise NotFoundExc(error_msg, e)
    if enrich is not None:
        result = enrich(result, request)
    return result


def get_many(query: str):
    pass
