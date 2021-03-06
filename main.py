from configparser import ConfigParser
from influxdb import InfluxDBClient
from datetime import datetime
from netaddr import IPNetwork
from easysnmp import Session
from threading import Thread
import traceback
import time



config = ConfigParser()
config.read('config.ini')

hostname = config['influxdb']['hostname']
port = config['influxdb']['port']
username = config['influxdb']['username']
password = config['influxdb']['password']
database = config['influxdb']['database']

#CIDR notated network names seperated by spaces from config
networks = [IPNetwork(x) for x in config['snmp']['networks'].split()]
community = config['snmp']['community']


#adding a proper OID to this dictionary will add to the result.
#repeat values to adjust for different OIDs between CPE9000 and CPE12000SG
oids = {
    "iso.3.6.1.4.1.17713.20.2.1.2.2.0": "connectiontime",
    "iso.3.6.1.4.1.17713.20.2.1.2.14.0": "download",
    "iso.3.6.1.4.1.17713.20.2.1.2.11.0": "upload",
    "iso.3.6.1.4.1.17713.20.2.1.2.6.0": "RSRP0",
    "iso.3.6.1.4.1.17713.20.2.1.2.6.1.0": "RSRP0",
    "iso.3.6.1.4.1.17713.20.2.1.2.7.0": "RSRP1",
    "iso.3.6.1.4.1.17713.20.2.1.2.6.2.0": "RSRP1",
    "iso.3.6.1.4.1.17713.20.2.1.2.9.0": "CINR0",
    "iso.3.6.1.4.1.17713.20.2.1.2.32.1.0": "CINR0",
    "iso.3.6.1.4.1.17713.20.2.1.2.10.0": "CINR1",
    "iso.3.6.1.4.1.17713.20.2.1.2.32.2.0": "CINR1",
    "iso.3.6.1.4.1.17713.20.2.1.5.18.0": "niceuptime",
    "iso.3.6.1.4.1.17713.20.2.1.4.6.0": "firmware",
    "iso.3.6.1.4.1.17713.20.2.1.4.2.0": "model",
    "iso.3.6.1.4.1.17713.20.2.1.2.18.0": "pci"
}


def main():
    while True:
        data = poll()

        if data:
            result = update_influx(data)
            print(f'{str(result[0])} successes and {str(result[1])} failures')


def timer(func):
    def inner(*args, **kwargs):
        start = time.time()

        try: 
            result = func(*args, **kwargs)
            return result

        except Exception: 
            print(''.join(traceback.format_exc()))
            return False
        
        finally: print((
            f"{func.__name__} took " 
            f"{str(int(time.time()-start))} second(s)"
        ))
    
    return inner


def poll():
    """poll the entire network for active CPE. Creates a thread for each IP to speed up the process"""

    def get_session(ip):
        """handles the snmp client getting overwhelmed by all the threads"""

        try:
            return Session(hostname=str(ip), community=community, version=2)

        except Exception:
            time.sleep(0.01)
            return get_session(ip)


    def walk(ip):
        """mib walk function. expects resultdict to be defined before running"""

        session = get_session(ip)

        try:
            result = session.walk('.1.3.6.1.4.1.17713.20.2.1')
            timestamp = datetime.utcnow()
            resultdict[str(ip)] = dict(time=timestamp.isoformat())
            for x in result:
                if x.oid in oids:
                    resultdict[str(ip)][oids[x.oid]] = str(x.value).strip(' kbps')

        #insert None for all params if device is offline
        except Exception:
            timestamp = datetime.utcnow()
            resultdict[str(ip)] = dict(time=timestamp.isoformat())
            for x in oids.values():
                resultdict[str(ip)][x] = None


    resultdict = dict()
    threadlist = list()
    for network in networks:
        for ip in network:
            single = Thread(target=walk, args=(ip,))
            single.start()
            threadlist.append(single)

    #wait until each thread is finished before returning
    for x in threadlist: x.join()
    return resultdict


def update_influx(data):
    """inserts the result from the snmp process into the influx database"""
    fail_tally = 0
    success_tally = 0

    client = InfluxDBClient(hostname, port, username, password, database)

    for device in data:
        json_body = [
            {
                "measurement": "snmp",
                "tags": {'host': f"{device}"},
                "time": str(data[device]['time']),

                "fields": {
                    oid: str(data[device][oid]) 
                    for oid in data[device]
                    if oid != 'time'
                }
            }
        ]
        try:
            client.write_points(json_body, protocol='json')
            success_tally += 1
        
        except Exception:
            fail_tally += 1

    
    return [success_tally, fail_tally]


if __name__ == "__main__":
    main()
   
