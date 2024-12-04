from redis import Redis
from redis.exceptions import ConnectionError # type: ignore
from os import getenv


def str_to_bool(value: str) -> bool:
    """
        Transforms an string type to boolean
    """
    return value.lower() in {'true', '1', 'yes'}

try:
    redis_client = Redis(
        host=getenv('REDIS_HOST'),
        port=getenv('REDIS_PORT'),
        #password=getenv("REDIS_PASSWORD") or None, we are using None because no password is required for this example
        ssl=str_to_bool(getenv("REDIS_SSL", "False")),
        socket_timeout=5
    )
    print("Connected to Redis!")
except Exception as e:
    print(f"Exception error: {e}")