from config import config
import psycopg2
import psycopg2.extras


class Persistent(object):
    @staticmethod
    def exists(conn, table, **kwargs):
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT * FROM {} WHERE {};".format(
            table,
            ' AND '.join([table + "." + key + "=%s" for (key, _) in kwargs.items()])
        ), list(kwargs.values()))

        ret = cur.fetchone() is not None

        conn.commit()
        cur.close()

        return ret

    def __init__(self, db_connection, table, pkey=(), update=False, return_cols=(), **vars):
        self.__cur = db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

        self.__select(table, pkey=pkey, **vars)

        if self.__cur.fetchone() is None:
            self.__cur.execute("INSERT INTO {} ({}) VALUES ({});".format(
                table,
                ",".join(['"' + v + '"' for v in list(vars)]),
                ",".join(["%s"]*len(vars))
            ), list(vars.values()))
        elif update:
            # TODO
            pass

        self.__select(table, pkey=pkey, return_cols=return_cols, **vars)
        self.result = self.__cur.fetchone()

        db_connection.commit()
        self.__cur.close()

    def __select(self, table, pkey=(), return_cols=(), **vars):
        if len(return_cols) == 0:
            cols = "*"
        else:
            cols = ",".join([table + "." + col for col in return_cols])

        if len(pkey) > 0:
            pkey_vars = {key: val for key, val in vars.items() if key in pkey}
            self.__cur.execute("SELECT {} FROM {} WHERE {};".format(
                cols,
                table,
                ' AND '.join([table + "." + key + "=%s" for (key, _) in pkey_vars.items()])
            ), list(pkey_vars.values()))
        else:
            self.__cur.execute("SELECT {} FROM {} WHERE {};".format(
                cols,
                table,
                ' AND '.join([table + "." + key + "=%s" for (key, _) in vars.items()])
            ), list(vars.values()))


def test_connection():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        params = config()

        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        cur = conn.cursor()

        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        db_version = cur.fetchone()
        print(db_version)

        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
