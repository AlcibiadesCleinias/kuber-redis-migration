# Python3 script for migrating data from redis db to redis db.
# We use strict redis connect and we expect you to pass 2 arguments
# for source redis and destination redis accordingly:
# <host>:<port>/<db>
#
# Creds:
# https://gist.github.com/josegonzalez/6049a72cb163337a18102743061dfcac
import redis
import argparse

def connect_redis(conn_dict):
    conn = redis.StrictRedis(host=conn_dict['host'],
                             port=conn_dict['port'],
                             db=conn_dict['db'])
    return conn

def conn_string_type(string):
    format = '<host>:<port>/<db>'
    try:
        host, portdb = string.split(':')
        port, db = portdb.split('/')
        db = int(db)
    except ValueError:
        raise argparse.ArgumentTypeError('incorrect format, should be: %s' % format)
    return {'host': host,
            'port': port,
            'db': db}

def migrate_redis(source, destination):
    src = connect_redis(source)
    dst = connect_redis(destination)
    for key in src.keys('*'):
        ttl = src.ttl(key)
        # we handle TTL command returning -1 (no expire) or -2 (no key)
        if ttl < 0:
            ttl = 0
        print ("Dumping key: %s" % key)
        value = src.dump(key)
        print ("Restoring key: %s" % key)
        try:
            dst.restore(key, ttl * 1000, value, replace=True)
        except redis.exceptions.ResponseError:
            print ("Failed to restore key: %s" % key)
            pass
    return

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=conn_string_type)
    parser.add_argument('destination', type=conn_string_type)
    options = parser.parse_args()
    migrate_redis(options.source, options.destination)

if __name__ == '__main__':
    run()
