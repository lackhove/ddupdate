# ddupdate - a tiny IPv6 dyndns updater

ddupdate updates a dyndns IPv6 addresses.
 
## Config file 
example `config.ini`:

```ini
[strato]
net_dev = wlp2s0
domain = foobar.com
username = foobar.com
password = topsecret
url=https://dyndns.strato.comm/nic/update
```   


## Docker usage

run
```bash
docker run -it --rm --net=host -v $(pwd)/config.ini:/ddupdate/config.ini:ro  crabmanx2/ddupdate
```

`--net=host` is essential for obtaining the public ipv6 address.