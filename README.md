# telrad-kpi-collection
process for pulling KPIs via SNMP for an entire network of Telrad CPEs and inserting the data into InfluxDB.

To be used for building graphs.

requires an existing Influxdb database, and the following python libraries:
```
configparser
influxdb
netaddr
easysnmp
```
  
configuration lives in config.ini
