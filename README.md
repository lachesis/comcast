Comcast
-------
Comcast has recently implemented a data cap in my area. I wanted to track their
view of my usage so I could compare it with my vnstat logs. This Python script
(`comcast.py`) will dump a JSON blob with usage information. The included bash
script (`comcast.sh`) uses that data to write to a local statsd/graphite
installation.

The only requirement for the Python script is the requests library.

Usage
-----
```bash
COMCAST_USERNAME=bob COMCAST_PASSWORD=hope python3 comcast.py
```
