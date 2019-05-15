import cherrypy
from pprint import pprint
from geojson import LineString
from geojson import Point
import requests
import random
import sys
import json
import NeededEnergyEstimator

"""CONSTANTS-------------------------------------"""
# access keys for HERE API - routing
here_app_id = "G9R3VhY5VRjtzpLUOUb8"
here_app_code = "3N-P2kC4aILShL93eATfnA"
# access keys for Open route service API - To find fuel stations
open_route_service_auth_code = \
    '5b3ce3597851110001cf6248620fe1f9983d4e8ea401c1ffa5b3580a'


# START OF CUSTOM FUNCTIONS________________________________________________
# Dummy function to find the point at which station search needs to happen
# based on battery level or for user choosing closest station
def fetch_dummy_idx(min_val, max_val):
    return random.randrange(min_val, max_val)


# Dummy function to find the the radius of the circle within which to search
# for stations and the shifting of way-point to account for topographical
# elevation- move towards lower elevation to save energy if required.
def fetch_dummy_radius_and_way_point_shift(min_val=0, max_val=500):
    dummy_radius = random.randrange(min_val, max_val)
    dummy_way_point_shift = random.randrange(-1, +1)
    return dummy_radius, dummy_way_point_shift


# Function to return a list of fuel stations in geoJSON format around a
# specific point within a given radius which is given by the buffer_value in
# metres.
def get_stations_around_point(geojson_value,
                              buffer_value=2000):
    """
    :param geojson_value: The point or line in GeoJSON from which the
    distance to the station is calculated
    :param buffer_value: The radius of the circle around the way-point
    within which a fuel station is searched for
    :return: a list of stations in GeoJSON format
    """

    body = {"request" : "pois",
            "geometry": {"geojson": geojson_value, "buffer": buffer_value},
            "filters" : {"category_ids": [596]}, "sortby": "distance"}

    # print("body:",body)

    headers = {
        'Accept'       : 'application/json, application/geo+json, '
                         'application/gpx+xml, img/png; charset=utf-8',
        'Authorization': open_route_service_auth_code
        }
    call = requests.post('https://api.openrouteservice.org/pois', json=body,
                         headers=headers)

    print(call.status_code, call.reason)
    # print(call.json())
    response_dump = json.dumps(call.json())
    response = json.loads(response_dump)
    # print(response)
    station_details = "NO_DATA"
    if (call.status_code != 200):
        station_details = "NO_DATA"
    elif response['features']:
        station_details = json.dumps(response)
    return (station_details)


# Function to return
def get_route_distance_time_elevation(way_points_list,
                                      elevation_flag="false",
                                      alternative_routes_value=1,
                                      return_type="point"):
    """
    :param way_points_list: List of points starting with origin and ending
    with destination with waypoints in between for which the route is to be
    calculated
    :param elevation_flag: Flag to return elevation values for points-
    default is false
    :param alternative_routes_value: How many alternative routes need to be
    generated - default is 1
    :param return_type: The format of returning value changes between list
    of GeoJSON Linestrings and list of list of GeoJSON points
    :return: one or a list of routes for the given set of waypoints- each
    route will be in GeoJSON format(Linestring or list of GeoJSON points)
    """
    base_url_calculate_route = "https://route.api.here.com/routing/7.2" \
                               "/calculateroute.json?app_id="

    # Mode- balanced between fastest and least distance
    # mode of transport - bicycle
    mode = "balanced;bicycle"

    # How many alternative routes to find
    alternative_routes = "&alternatives=" + str(alternative_routes_value)
    waypoint_string = ""
    counter = 0
    # Build the waypoint string to pass to the API
    for waypoint in way_points_list:
        waypoint_string += "&waypoint" + str(counter) + "=" + waypoint
        counter += 1

    # Build the URL to fetch the route using the HERE API
    url = base_url_calculate_route + here_app_id + "&app_code=" + \
          here_app_code + \
          waypoint_string + "&mode=" + mode \
          + "&routeattributes=sh,labels" + "&returnElevation=" + \
          elevation_flag + alternative_routes

    # print the URL for reference
    pprint(url)
    # Response from the API in JSON format
    resp = requests.get(url)
    way_points_linestring_list = []
    geojson_way_point_list_for_routes = []
    if resp.status_code != 200:
        # This means something went wrong.
        raise ('GET /tasks/ {}'.format(resp.status_code))
    else:

        response_json = resp.json()
        # pprint(response_json)
        # Iterate through each available route individually to build
        # GeoJSON Linestrings for the route and GeoJSON Points for the
        # indiviual way points
        for alt_route_idx in range(len(response_json['response']['route'])):
            print(
                "#########ROUTE" + str(alt_route_idx + 1) + "###############")
            shape_value_of_route = response_json['response']['route'][
                alt_route_idx][
                'shape']
            elevation_Array = []
            elevation_gain_array = []
            elevation_loss_array = []
            point_counter = 0
            prev_elevation = 0
            way_point_list_for_geo = []
            geojson_way_point_list_for_route = []

            # Break up each rout to create the GeoJSON points and also to
            # calculate elevation gain and loss if required
            for i in shape_value_of_route:
                point_split_string = [x.strip() for x in i.split(',')]
                # GeoJSON needs Latitude and Longitude inverted
                way_point_list_for_geo.append((float(point_split_string[1]),
                                               float(point_split_string[0])))
                # Convert and Add each new GeoJSON point to the list of points
                geojson_way_point_list_for_route.append(
                    Point((float(point_split_string[1]),
                           float(point_split_string[0]))))

                if (len(point_split_string) > 2):
                    elevation = float(point_split_string[2])
                    elevation_Array.append(elevation)
                    # the following code is only when elevation is enabled
                    if (point_counter > 0):
                        elevation_gain = int(elevation) - int(prev_elevation)
                        if (elevation_gain > 0):
                            elevation_gain_array.append(elevation_gain)
                        if (elevation_gain < 0):
                            elevation_loss_array.append(elevation_gain)

                    prev_elevation = elevation
                    point_counter += 1
            overall_elevation_gain = sum(elevation_gain_array)
            overall_elevation_loss = sum(elevation_loss_array)
            # Convert Linestring to GeoJSON point
            way_points_linestring = LineString(way_point_list_for_geo)

        way_points_linestring_list.append(way_points_linestring)
        geojson_way_point_list_for_routes.append(
                geojson_way_point_list_for_route)
    if return_type == "point":

        return (geojson_way_point_list_for_routes)
    elif return_type == "linestring":
        return (way_points_linestring_list)


# Function to build the locations in the format required by HERE routing API
def geo_point_formatter_for_HERE_API(lat, lon):
    return ("geo!" + str(lat) + "," + str(lon))


# Constant values being passed temporarily to calculate routes-Needs to be
# dynamic
origin_lat = "52.500396"
origin_lon = "13.407807"
dest_lat = "52.541439"
dest_lon = "13.421164"
origin_uphill_lat = "47.16757543377595"
origin_uphill_lon = "7.262282020247881"
dest_uphill_lat = "47.17349788688307"
dest_uphill_lon = "7.268998271621172"
origin_uphill_ls = "[47.16757543377595,7.262282020247881]"
dest_uphill_ls = "[47.17349788688307,7.268998271621172]"


def routing_protocol(origin_lat="52.500396", origin_lon="13.407807",
                     dest_lat="52.541439", dest_lon="13.421164",
                     battery_percent=40):
    way_point_list = [geo_point_formatter_for_HERE_API(origin_lat, origin_lon),
                      geo_point_formatter_for_HERE_API(dest_lat, dest_lon)]

    # Function call to get a route for given origin and dest
    # No of routes can potentially be increased using alternative routes param
    # Result is given as a list of list of GeoJSON points as returntype is
    # "point"
    way_point_lists_list_of_points = \
        get_route_distance_time_elevation(
                way_point_list, elevation_flag="false",
                alternative_routes_value=1,
                return_type="point")

    # To fetch the first route in the list
    way_point_list_first_route = way_point_lists_list_of_points[0]

    way_point_list_length = len(way_point_list_first_route)

    ########################################################################
    # REMOVE DUMMY FUNCTIONS AND USE ACTUAL FUNCTIONS
    # fetching dummy waypoint index at which stations have to be searched and
    # the radius to be used
    # Actual function would need, route with origin,dest and waypoints and
    # battery level to be passed
    power_route_dict = NeededEnergyEstimator.estimateNeededPower([[float(
            origin_lon), float(origin_lat)],[float(dest_lon),
                                             float(dest_lat)]],
                                             float(battery_percent))

    search_radius, way_point_shift = fetch_dummy_radius_and_way_point_shift(
            1800,
            2000)
    ########################################################################
    way_point_list_first_route = power_route_dict['pointList']
    new_idx = power_route_dict['startSearchingIdx']

    closest_stations = "NO_DATA"
    if (power_route_dict['isSufficient'] == True):
        closest_stations = "NOT NEEDED"
    while (closest_stations == "NO_DATA"):
        # Search for fuel stations around the selected waypoint
        print("checking near:",Point((float(way_point_list_first_route[
                                                new_idx][0]),
               float(way_point_list_first_route[new_idx][1]))))
        print("search_radius:",search_radius)

        closest_stations = get_stations_around_point(
                geojson_value= Point((float(way_point_list_first_route[
                                                new_idx][0]),
               float(way_point_list_first_route[new_idx][1]))),
                buffer_value=search_radius)
        # If NO_DATA stations available for current way point need to go to
        # next point
        if (closest_stations == "NO_DATA"):
            print("NEED to move to next waypoint")
            if (new_idx > 0):
                new_idx = new_idx - 1
            else:
                print("UNABLE TO FIND STATION en ROUTE AND TRIP NOT POSSIBLE "
                      "WITHOUT CHARGING")
                break

            if (search_radius <= 1000):
                search_radius = search_radius * 2

    if (closest_stations != "NOT NEEDED"):
        # Simulation of user choosing a station

        closest_stations = json.loads(closest_stations)
        ########################################################################
        # REMOVE DUMMY AND REPLACE WITH ACTUAL FUNCTION
        # Function for user to choose fuel/recharge station
        chosen_closest_station_idx = fetch_dummy_idx(0, len(closest_stations[
                                                                'features']))
        closest_station = closest_stations['features'][
            chosen_closest_station_idx]
        ########################################################################
        # print("closest_station:",closest_station)

        closest_station_HERE_format = geo_point_formatter_for_HERE_API(
                closest_station['geometry']['coordinates'][1],
                closest_station['geometry']['coordinates'][0])
        # New routes calculated by using the chosen station as a waypoint
        way_point_list_new = [way_point_list[0], closest_station_HERE_format,
                              way_point_list[-1]]

        # Result is given as a list of  GeoJSON Linestrings as returntype is
        # "LineString"
        way_point_lists_linestrings = get_route_distance_time_elevation(
                way_point_list_new,
                elevation_flag="false",
                alternative_routes_value=3, return_type="linestring")


    else:
        closest_station = "NOT USED AS CHARGE WAS SUFFICIENT or UNABLE TO FIND STATION en ROUTE AND TRIP NOT POSSIBLE WITHOUT CHARGING"
        way_point_lists_linestrings = get_route_distance_time_elevation(
                way_point_list,
                elevation_flag="false",
                alternative_routes_value=3, return_type="linestring")

    routes_feature_coll = {"type"           : "FeatureCollection",
                           "closest_station": closest_station,
                           "features"       : way_point_lists_linestrings}

    routes_feature_coll = json.dumps(routes_feature_coll)
    print(routes_feature_coll)
    return (routes_feature_coll)


class webService(object):
    exposed = True

    def GET(self, origin_latitude="52.500396", origin_longitude="13.407807",
            dest_latitude="52.541439", dest_longitude="13.421164",
            battery_percentage=40):
        return routing_protocol(origin_lat=origin_latitude,
                                origin_lon=origin_longitude,
                                dest_lat=dest_latitude,
                                dest_lon=dest_longitude,
                                battery_percent=battery_percentage)

    def POST(self, *uri):
        pass

    def PUT(self):
        pass

    def DELETE(self):
        pass


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch' : cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
            }
        }
    cherrypy.config.update({
        'server.socket_host': 'localhost',
        'server.socket_port': 8080,
        })
    cherrypy.tree.mount(webService(), '/route', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
