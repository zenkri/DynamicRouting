#--------------------Constants---------------------------------------

cyclist_weight = 80.0

bike_weight = 20.0

earth_acceleration = 9.81

battery_capacity = 400

total_weight = cyclist_weight + bike_weight

material_dict = dict([(0, 'Unknown'), (1, 'Paved'), (2, 'Unpaved'), (3, 'Asphalt'), (4, 'Concrete'),
                      (5, 'Cobblestone'), (6, 'Metal'), (7, 'Wood'), (8, 'Compacted Gravel'), (9, 'Fine Gravel'),
                      (10, 'Gravel'), (11, 'Dirt'), (12, 'Ground'), (13, 'Ice'), (14, 'Paving Stones'), (15, 'Sand'),
                      (16, 'Woodchips'), (17, 'Grass'), (18, 'Grass Paver')])

roll_coefficients = dict([('Asphalt', 0.004), ('Concrete', 0.002), ('Wood', 0.001), ('Woodchips', 0.001), ('Paved', 0.008),
                          ('Grass', 0.007), ('Gravel', 0.006), ('Sand', 0.03), ('Unknown', 0.008)])

# define some coefficient for the air drag
c_w = 0.5
A = 0.45
rho = 1.2041
average_speed = 20 / 3.6

#--------------------Get elevation data------------------------------

def get_mu_roll(dictionary):

    materials = dictionary['features'][0]['properties']['extras']['surface']['summary']

    mu_roll = 0.0

    for element in materials:
        if material_dict[element['value']] in roll_coefficients:
            mu_roll = mu_roll + element['amount'] * roll_coefficients[material_dict[element['value']]]
        else:
            mu_roll = mu_roll + element['amount'] * roll_coefficients['Unknown']

    return mu_roll / 100.0



def call2elevation(res):

    # this function extracts the altitude values from the OpenRoute API response
    start_idx = res.find('"geometry":[')
    end_idx = res.find(']]', start_idx, len(res))

    geometry = res[start_idx + 12:end_idx + 1]

    altitudes = []
    while True:
        first_idx = geometry.find(']')
        if first_idx == -1:
            break
        second_comma = geometry.find(',', first_idx - 10, first_idx)
        altitudes.append(float(geometry[second_comma + 1:first_idx]))
        geometry = geometry[first_idx + 2:len(geometry)]

    return altitudes


def makeRequest(locations):
    import requests

    body = {"coordinates": locations, "elevation": "true", "extra_info": ["surface"]}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': '5b3ce3597851110001cf624826dff6fca2c74f82af5b82773385f154'
    }

    try:
        call = requests.post('https://api.openrouteservice.org/v2/directions/cycling-electric/geojson', json=body,
                             headers=headers)
    except:
        print('Altitude request failed!')
        return -1


    return call.json()

def makeRequestWithouElev(locations):
    import requests

    body = {"coordinates": locations, "elevation": "false", "extra_info": [
        "surface"]}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': '5b3ce3597851110001cf624826dff6fca2c74f82af5b82773385f154'
    }

    try:
        call = requests.post('https://api.openrouteservice.org/v2/directions/cycling-electric/geojson', json=body,
                             headers=headers)
    except:
        print('Altitude request failed!')
        return -1


    return call.json()



def getDescendancePortion(path):
    import numpy as np

    altitudePoints = getAltitudePoints(path)

    # calculate the slope
    slope = np.array(differentiate(altitudePoints))

    descendancePortion = np.sum(slope < 0) / len(slope)

    return descendancePortion


def getElevation(dix):


    #pointList = dix['features'][0]['geometry']['coordinates']

    # for point in pointList:
    #     print(point[2])

    return dix['features'][0]['properties']['ascent']


def differentiate(vec):

    diffVec = []

    diffVec.append(vec[1] - vec[0])

    for idx in range(1, len(vec)):
        diffVec.append(vec[idx] - vec[idx - 1])

    return diffVec


def getAltitudePoints(pointsList):
    import requests

    body = {"format_in": "polyline", "format_out": "polyline",
            "geometry": pointsList}

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': '5b3ce3597851110001cf624826dff6fca2c74f82af5b82773385f154'
    }
    call = requests.post('https://api.openrouteservice.org/elevation/line', json=body, headers=headers).json()

    geometryList = call['geometry']

    altitudeList = []

    for geometryElement in geometryList:
        altitudeList.append(geometryElement[2])

    return altitudeList


def getDistance(p1, p2):

    import math

    return math.sqrt(math.pow(p1[0] - p2[0], 2) + math.pow(p1[1] - p2[1], 2))


def getStartSearchIdx(pointsList, remaining_power, mu):

    import numpy as np
    import utm


    # transform geo. locations to the Cartesian coordinate system
    xy = []

    for geoLoc in pointsList:
        xy.append(utm.from_latlon(geoLoc[1], geoLoc[0])[0:2])

    # get altitude loss occurance profile
    altitudeProfile = getAltitudePoints(pointsList)

    # calculate the slope
    slope = differentiate(altitudeProfile)

    # create a profile
    ## create an array from altitudeProfile
    lossOccuranceProfile = np.array(slope)

    ## binarize the lossOccuranceProfile
    lossOccuranceProfile[np.where(lossOccuranceProfile < 0)] = 0
    lossOccuranceProfile[np.where(lossOccuranceProfile > 0)] = 1

    # transform xy to traveled distances
    distanceList = []
    distanceList.append(0)

    for index in range(1, len(xy)):
        distanceList.append(distanceList[index - 1] + lossOccuranceProfile[index] * getDistance(xy[index], xy[index - 1]))

    # transform distanceList to an array
    distanceProfile = np.array(distanceList)

    # transform slope list to array
    slope_array = np.array(slope)

    # delete negative slopes
    slope_array[np.where(slope_array < 0)] = 0

    # create a slope array profile
    for idx in range(1, len(slope)):
        slope_array[idx] = slope_array[idx] + slope_array[idx - 1]

    # calculate potential energy profile
    E_potProfile = total_weight * earth_acceleration * slope_array

    #calculate the friction profile
    rollFrictionProfile = mu * total_weight * earth_acceleration * distanceProfile

    # calculate the air drag profile
    airDragProfile = 0.5 * c_w * A * rho * average_speed**2 * distanceProfile

    # calculate total loss profile
    lossProfile = joule2Wh(E_potProfile + rollFrictionProfile + airDragProfile)

    availablePower = max(0.001, (remaining_power - 0.05) * battery_capacity)

    return np.where((availablePower - lossProfile) < 0)[0][0] - 1


def joule2Wh(joule_energy):

    return joule_energy / 3600.0


def estimateNeededPower(track, battery_level):

    # define return dictionary
    return_dict = dict([('isSufficient', False), ('pointList', [[]]), ('startSearchingIdx', -1)])

    resp = makeRequest(track)

    # get all the path points
    path_points = resp['features'][0]['geometry']['coordinates']

    # get total ascendant elevation
    ascendant_elevation = getElevation(resp)

    # calculate the needed potential energy
    potential_energy = joule2Wh(total_weight * earth_acceleration * ascendant_elevation)

    # determine rolling friction coefficient
    mu_roll = get_mu_roll(resp)

    # determine the total distance
    distance = resp['features'][0]['properties']['summary']['distance']

    # get portion of descendant track
    descentionPortion = getDescendancePortion(path_points)

    #calculate rolling friction loss
    friction_loss = joule2Wh(mu_roll * total_weight * earth_acceleration * distance * (1.0 - descentionPortion))

    # calculate the air drag
    drag_loss = joule2Wh(0.5 * c_w * A * rho * average_speed**2 * distance * (1.0 - descentionPortion))

    # total loss calculation
    total_loss = potential_energy + friction_loss + drag_loss

    print(total_loss)

    respNoElev = makeRequestWithouElev(track)

    # get all the path points
    path_points_without_elev = respNoElev['features'][0]['geometry']['coordinates']

    if total_loss < max(0.001, battery_level - 0.05) * battery_capacity:
        return_dict['isSufficient'] = True
        return_dict['pointList'] = path_points_without_elev

    else:
        return_dict['isSufficient'] = False
        return_dict['pointList'] = path_points_without_elev
        return_dict['startSearchingIdx'] = getStartSearchIdx(path_points, battery_level, mu_roll)


    return return_dict


import json
import io


# print(estimateNeededPower([[8.683319, 49.429287], [8.601608, 49.370302]],
#                           0.12))

