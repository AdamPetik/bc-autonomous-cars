from src.common.Location import Location
from src.placeable.stationary.MacroCell import MacroCell
import requests
import json
import os

import os.path


class MacrocellLoader:

    def getMacrocells(self, ip, latmin, latmax, lonmin, lonmax, locationsTable, map, nets=None):
        stations = []
        print("getMacrocells called with atributes: ip:", ip, " latmin:",latmin, " latmax:",latmax, " lonmin:",lonmin, " lonmax:",lonmax)
        json = self.getCellJson(ip, latmin, latmax, lonmin, lonmax)
        cells = json['cells']
        num_items = len(cells)

        for j in range(0, num_items):
            bts = MacroCell(locationsTable, map)
            location = Location(float(cells[j]['lat']), float(cells[j]['lon']), 0)
            x, y = map.mapGrid.getGridCoordinates(location)
            location.setGridCoordinates(x, y)
            bts.tableRow = locationsTable.insertNewActor(bts)
            bts.setLocation(location)

            bts.openCellId = cells[j]['id']
            bts.created_at = cells[j]['created_at']
            bts.updated_at = cells[j]['updated_at']
            bts.radio = cells[j]['radio']
            bts.mcc = cells[j]['mcc']
            bts.net = cells[j]['net']
            bts.area = cells[j]['area']
            bts.cell = cells[j]['cell']
            bts.unit = cells[j]['unit']
            bts.range = cells[j]['range']
            bts.samples = cells[j]['samples']
            bts.changeable = cells[j]['changeable']
            bts.created = cells[j]['created']
            bts.updated = cells[j]['updated']
            bts.averageSignal = cells[j]['averageSignal']

            if (bts.radio == 'LTE'):
                if (nets is None):
                    stations.append(bts)
                else:
                    if bts.net in nets:
                        stations.append(bts)

        added = len(stations)
        print("MacrocellLoader:", added, "were added to the list")
        if (added == 0):
            raise ValueError('No Macrocells were added to the list')
        return stations

    def getCellJson(self, ip, latmin, latmax, lonmin, lonmax):
        receivedData = {}
        receivedData['cells'] = []

        filename = "cellCache/" + (str(latmin) + "_" + str(latmax) + "_" + str(lonmin) + "_" + str(lonmax)).replace(".", "-") + ".json"

        if os.path.exists(filename):
            print("MacrocellLoader - returning cached data from file", filename)
            with open(filename) as cachedData:
                cached = json.load(cachedData)
            return cached

        else:
            url = "http://" + ip + "/cellsBackend/public/api/cells"
            print("MacrocellLoader - no cached data found, executing post request to: " + url)

            payload = {
                "latmin": latmin,
                "latmax": latmax,
                "lonmin": lonmin,
                "lonmax": lonmax,
                "perpage": 50
            }

            while (url is not None):
                response = requests.post(url, data=payload)

                # print(response.text) #TEXT/HTML
                # print(response.status_code, response.reason) #HTTP
                if (response.status_code != 200):
                    raise ValueError('Unable to retreive data from server')

                resp_json = json.loads(response.text)

                data = resp_json['cells']['data']
                print("Current page: ", resp_json['cells']['current_page'])
                num_items = len(data)
                print("Page contains", num_items, "items")

                for j in range(0, num_items):
                    # print("Reading item",j)
                    receivedData['cells'].append(data[j])

                url = resp_json['cells']['next_page_url']

            json_data = json.dumps(receivedData)

            if not os.path.exists('cellCache/'):
                os.makedirs('cellCache/')

            with open(filename, 'w+') as outfile:
                json.dump(receivedData, outfile)

            with open(filename) as cachedData:
                cached = json.load(cachedData)
            return cached
