# telrad-kpi-collection
process for pulling KPIs via SNMP for a(n) entire network(s) of Telrad CPEs. 

intended as an @reboot cron job

requires an existing Influxdb database, and the following python libraries:
```
configparser
influxdb
netaddr
easysnmp
```
  
Be sure to fill out the config.ini!
