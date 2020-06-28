from configparser import ConfigParser
import os


def config(filename='database.ini', section='postgresql'):
    # if we detect a heroku environment, override the local db settings
    if "DATABASE_URL" in os.environ:
        return {
            "dsn": os.environ["DATABASE_URL"],
            "sslmode": "require"
        }
    else :
        # create a parser
        parser = ConfigParser()
        # read config file
        parser.read(filename)

        # get section, default to postgresql
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))

        return db