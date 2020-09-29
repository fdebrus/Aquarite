#!/usr/bin/python3

import time
import sys
import json
import requests
from requests import Session
import argparse

# Hayward PoolWatch Credentials
username='<email>'
password='<password>'

# Pool Param
poolId='<poolid>' # Get your poolID from developper console in Chrome watching network stream
hasPH='true' # PH Probe
hasRX='true' # RX Probe
hasCL='false' # ??
hasCD='false' # ??
hasHidro='true'
hasLight='true' # Has relay for light
hasRelays='true' # Has more relays
numRelays='1,2,3' # How many extra relay are present
hasFiltration='true' # Control the filtration
hasBackwash='false' # Control the backwash
hasIO='false' # ??
hasUV='false' # Has UV lights
needsTimeBesgoRemaining='false' # ??

# PoolWatch URL's
authURL = 'http://poolwatch.hayward.fr/fr/login/login'
queryURL = 'http://poolwatch.hayward.fr/fr/pool/getmainvalues?id='+poolId+'&hasPH='+hasPH+'&hasRX='+hasRX+'&hasCL='+                                                                                                                         hasCL+'&hasCD='+hasCD+'&hasHidro='+hasHidro+'&hasLight='+hasLight+'&hasRelays='+hasRelays+'&numRelays='+numRelays+'&                                                                                                                         hasFiltration='+hasFiltration+'&hasBackwash='+hasBackwash+'&hasIO='+hasIO+'&hasUV='+hasUV+'&needsTimeBesgoRemaining=                                                                                                                         '+needsTimeBesgoRemaining
lightURL = 'http://poolwatch.hayward.fr/fr/pool/setlightvalues?id='+poolId+'&type=0&status='
relayURL = 'http://poolwatch.hayward.fr/fr/pool/setauxvalues?id='+poolId
pumpURL = 'http://poolwatch.hayward.fr/fr/pool/setfiltrationvalues?id='+poolId

# OpenHAB
OpenHABIP = 'localhost:8080'

class HaywardConnectPool(object):

    def connectHayward(self):
        with Session() as s:
            try:
                print('Connecting to Hayward PoolWatch - ', end = '')
                login_data = {'user':username,'pass':password,'entrar':'Entrer'}
                response = s.post(authURL,login_data) # need to manage in case of error (code to be written) success                                                                                                                          login or not give 200
                print('Connected')
            except Exception as e:
                print('Error: %s' % e)
                exit(1)
        return s

    def ohPutValue(self, item, value):
        try:
            rc =requests.put('http://'+OpenHABIP+'/rest/items/'+item+'/state', str(value))
            if(rc.status_code != 202):
                print("Warning: couldn't save item "+item+" to openHAB")
                exit(1)
        except Exception as e:
            print('Error: %s' % e)
            exit(1)

    def setLight(self, session, status):
        try:
            print('Setting light to ' + status)
            response = session.post(lightURL + status)
        except Exception as e:
            print('Error: %s' % e)
            exit(1)

    def setPump(self, session, params):
        try:
            print('Pump mode' + params)
            print(pumpURL + params)
            response = session.post(pumpURL + params)
        except Exception as e:
            print('Error: %s' % e)
            exit(1)

    def setAux(self, session, aux, status):
        try:
            print('Setting AUX ' + aux + ' to ' + status)
            response = session.post(relayURL + '&rel=' + aux + '&data={"mode":0,"onoff":' + status + ',"name":""}')
        except Exception as e:
            print('Error: %s' % e)
            exit(1)

    def queryData(self, session, arg):
        if (arg == 'dashboard'):
           try:
              print('Dashboard for PoolID ' + poolId)
              json_string = session.get(queryURL+'&config=0')
           except Exception as e:
              print('Error: %s' % e)
              exit(1)
        elif (arg == 'config'):
           try:
              print('Config for PoolID ' + poolId)
              json_string = session.get(queryURL+'&config=1')
           except Exception as e:
              print('Error: %s' % e)
              exit(1)

        print(json_string.content)

        data = json.loads(json_string.content)
        if (data != 'not connected'): # Pool is not connected to PoolWatch
            print('Updating dashboard in OpenHAB - ', end = '')
            self.ohPutValue('Hayward_PoolTemp',data['temp'][:4])
            self.ohPutValue('Hayward_FiltrationStatus',data['filtration_stat'])
            self.ohPutValue('Hayward_FiltrationMode',data['filtration_mode'])
            self.ohPutValue('Hayward_FiltrationTimeRemaining',data['filtration_time_remaining'])
            self.ohPutValue('Hayward_FiltrationTime1',data['filtration']['inter-1'])
            self.ohPutValue('Hayward_FiltrationTime2',data['filtration']['inter-2'])
            self.ohPutValue('Hayward_FiltrationTime3',data['filtration']['inter-3'])
            self.ohPutValue('Hayward_PH',data['PH'])
            self.ohPutValue('Hayward_PHValue',data['PH_status']['hi_value'])
            self.ohPutValue('Hayward_PHAlarm',data['PH_status']['alarm'])
            self.ohPutValue('Hayward_PHStatus',data['PH_status']['status'])
            self.ohPutValue('Hayward_RX',data['RX'])
            self.ohPutValue('Hayward_RX1',data['RX1'])
            self.ohPutValue('Hayward_RXStatus',data['RX_status']['current'])
            print('Updated')

    def pumpDecode(self,x):
        return {
            'MANU': 0,
            'AUTO': 1,
            'HEAT': 2,
            'SMART': 3,
            'INTEL': 4,
        }[x]

def main():

    usage = '%prog [options] arg'

    parser = argparse.ArgumentParser(usage)

    parser.add_argument('-r', action='store', dest='refresh', choices=['dashboard', 'config'], help='request refresh                                                                                                                          of dashboard or config data')
    parser.add_argument('-l', action='store', dest='light', choices=['0','1'], help='set light status to 0:OFF or 1:                                                                                                                         ON')
    parser.add_argument('-a', action='append', nargs=2, dest='aux', choices=['0','1','2','3'], help='set aux relay s                                                                                                                         tatus to 0:OFF or 1:ON')
    parser.add_argument('-p', action='store', dest='pumpMode', choices=['MANU','AUTO','HEAT','SMART','INTEL'], help=                                                                                                                         'set filtration mode')
    parser.add_argument('-t', action='store', dest='pumpTemp', default='28', help='set target temperature')
    parser.add_argument('-c', action='store', dest='pumpClim', default='1', help='set climatisation 0:OFF or 1:ON')
    parser.add_argument('-f', action='store', dest='pumpFreeze', default='0', help='set freeze prevention 0:OFF or 1                                                                                                                         :ON')
    parser.add_argument('-d', action='store', dest='pumpDuration', default='1380', help='set intelligent mode minimu                                                                                                                         m filtration time') # 1380 = 24HRS, how ?
    parser.add_argument('-i', action='store', dest='pumpInterval', default='"inter1":"07:00-22:00","inter2":"00:00-0                                                                                                                         0:00","inter3":"00:00-00:00"', help='set interval for filtration')

    args = parser.parse_args()

    c = HaywardConnectPool()
    s = c.connectHayward()

    if args.refresh:
        print('Executing: REFRESH')
        returnVal = c.queryData(s,args.refresh)
    elif args.light:
        print('Executing: LIGHT')
        returnVal = c.setLight(s,args.light)
    elif args.aux:
        print('Executing: AUX')
        returnVal = c.setAux(s,args.aux[0][0],args.aux[0][1])
    elif args.pumpMode:
        print('Executing: PUMP')
        pumpType = str(c.pumpDecode(args.pumpMode))
        if (pumpType == '0'):
            params = '&data={"type":'+pumpType+',"mode":'+options.pumpMode[0][1]+',"vel":null}&int=&vel='
            print(params)
        if (pumpType == '1'):
            params = '&data={"type":'+pumpType+'}&int={'+options.pumpInterval+'}&vel='
            print(params)
        if (pumpType == '2'):
            params = '&data={"type":'+pumpType+',"temp":"'+options.pumpTemp+'","clima":'+options.pumpClim+'}&int={'+                                                                                                                         options.pumpInterval+'}&vel='
            print(params)
        if (pumpType == '3'):
            params = '&data={"type":'+pumpType+',"tempMin":20,"tempMax":'+options.pumpTemp+',"freeze":'+options.pump                                                                                                                         Freeze+'}&int={'+options.pumpInterval+'}&vel='
            print(params)
        if (pumpType == '4'):
            params = '&data={"type":'+pumpType+',"temp":"'+options.pumpTemp+'","time":'+options.pumpDuration+'}&int=                                                                                                                         &vel='
            print(params)
        returnVal = c.setPump(s,params)
    else :
        returnVal=2

    exit(returnVal)

if __name__ == '__main__':
    main()
