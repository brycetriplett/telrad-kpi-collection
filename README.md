# telrad-kpi-collection
process for pulling KPIs via SNMP for a(n) entire network(s) of Telrad CPEs.

To be used for building graphs. Intended as an @reboot cron job.

requires an existing Influxdb database, and the following python libraries:
```
configparser
influxdb
netaddr
easysnmp
```
  
configuration lives in config.ini
