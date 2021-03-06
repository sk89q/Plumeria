import aiomysql
from pymysql import OperationalError

from plumeria import config
from plumeria.core.storage.migration import MigrationManager
from plumeria.plugin import PluginSetupError

host = config.create("storage", "host", fallback="localhost", comment="The database server host")
port = config.create("storage", "port", type=int, fallback=3306, comment="The database server port")
user = config.create("storage", "user", fallback="plumeria", comment="The database server username")
password = config.create("storage", "password", fallback="", comment="The database server password")
db = config.create("storage", "db", fallback="plumeria", comment="The database name")


class Pool:
    def __init__(self):
        self.pool = None

    def acquire(self):
        return self.pool.acquire()


pool = Pool()
migrations = MigrationManager(pool)


async def setup():
    config.add(host)
    config.add(port)
    config.add(user)
    config.add(password)
    config.add(db)

    try:
        pool.pool = await aiomysql.create_pool(host=host(), port=port(), user=user(), password=password(), db=db(),
                                               autocommit=True, charset='utf8mb4')
    except OperationalError as e:
        raise PluginSetupError('Failed to connect to database: {}'.format(str(e)))

    await migrations.setup()
