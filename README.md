Transfer Redis data across Redis pods in Kubernetes
======
There are some some possibilities to migrate redis data from one redis instance
to another, but for some reason I found that for me only the righteousness way
(key by key copying) is accepted.

### The goal

We want to change the way we deploy Redis db from pod-yml to deployment-yml.
We dont want to lose our redis data.

### The predicament
- can not migrate via `dump.rdb`, coz I can not reload Redis instance because
  it has not PV, and I will merely lose data.

- cat not migrate via `appendonly.aof` redis file, coz it seems to be
  bugged on dump and load on different instances located in K&s.

- we dont want data to be changed due to copying.
Thus, we ought to remove K&s service from the source redis instance.

### The way

Briefly: we use tmp redis pod.

Deeply: we need `python-tmp` pod. Thus we can copy with help of python and can reach each redis in cluster.

Example of steps below are for redis `redis-gate` pod with `db0` and `redis-gate` as a service in terms of K&s service definition.
I prepare backup of the service file in `gate-redis-service-old.yml` in order to apply after copying.    

### Steps

1. Create tmp pods (with python and `redis-migrate.py` file inside, and `redis-tmp` pod with `redis-gate-tmp` service):

```
kubectl apply -f tmp-pods-svcs.yml
kubectl cp redis-migrate.py python-tmp:redis-migrate.py
```

2. You ought to stop redis to be usable by micro-services inside cluster by removing old service:

```
kubectl delete service redis-gate
```

3. Connect to `python-tmp` pod and proceed migrating a data to `redis-tmp`:

```
kubectl exec -ti python-tmp -- bash
pip install redis && python redis-migrate.py redis-gate-tmp:6379/0 redis-tmp:6379/0
```

4. Launch new redis-pod and delete old one

```
kubectl delete <REDIS_OLD_POD>
kubectl create -f ... (deployment in my case)
```

5. Copy data from `redis-tmp` to the new created from `python-tmp` pod:

```
python redis-migrate.py redis-tmp:6379/0 redis-gate-tmp:6379/0
```

6. Checkout to old redis service to make redis reachable:

```
kubectl apply -f gate-redis-service-old.yml
```

7. Del tmps:

```
kubectl delete -f tmp-pods-svcs.yml
```
