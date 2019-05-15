#--------------------Constants---------------------------------------

cyclist_weight = 80.0

bike_weight = 20.0

earth_acceleration = 9.81

total_weight = cyclist_weight + bike_weight

material_dict = dict([(0, 'Unknown'), (1, 'Paved'), (2, 'Unpaved'), (3, 'Asphalt'), (4, 'Concrete'),
                      (5, 'Cobblestone'), (6, 'Metal'), (7, 'Wood'), (8, 'Compacted Gravel'), (9, 'Fine Gravel'),
                      (10, 'Gravel'), (11, 'Dirt'), (12, 'Ground'), (13, 'Ice'), (14, 'Paving Stones'), (15, 'Sand'),
                      (16, 'Woodchips'), (17, 'Grass'), (18, 'Grass Paver')])

roll_coefficients = dict([('Asphalt', 0.004), ('Concrete', 0.002), ('Wood', 0.001), ('Woodchips', 0.001), ('Paved', 0.008),
                          ('Grass', 0.007), ('Gravel', 0.006), ('Sand', 0.03), ('Unknown', 0.008)])

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

    return call.json()


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


def joule2Wh(joule_energy):

    return joule_energy / 3600.0

# as input we expect a list of tuples, which includes equidistant geo coordinates of the path


def estimateNeededPower(track):

    resp = makeRequest(track)

    ascendent_elevation = getElevation(resp)

    # calculate the needed potential energy
    potential_energy = joule2Wh(total_weight * earth_acceleration * ascendent_elevation)

    # determine rolling friction coefficient
    mu_roll = get_mu_roll(resp)

    # determine the total distance
    distance = resp['features'][0]['properties']['summary']['distance']

    #calculate rolling friction loss
    friction_loss = joule2Wh(mu_roll * total_weight * earth_acceleration * distance)

    # define some coefficient for the air drag
    c_w = 0.5
    A = 0.45
    rho = 1.2041
    average_speed = 20 / 3.6

    # calculate the air drag
    drag_loss = joule2Wh(0.5 * c_w * A * rho * average_speed**2 * distance)

    return potential_energy + friction_loss + drag_loss


import json
import io


print(estimateNeededPower([[8.683319, 49.429287],[8.601608, 49.370302]]))

