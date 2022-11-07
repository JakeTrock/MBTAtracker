import math
import mbta_requests
import typing
import sys

api_key = ''
mbta_api = mbta_requests.MbtaApi(api_key)


def routeBuilder(route_res: typing.List[mbta_requests.Route]) -> dict:
    stops = {}
    total_stops = set()

    if len(route_res) == 0:
        raise Exception("failure to get routes!")

    for route_item in route_res:
        stops_data = mbta_api.stops(route_item.route_id)

        # compare number of stops for rq2
        num_stops = len(stops_data)

        if num_stops == 0:
            raise Exception("a train must have at least one stop!")

        stops_as_set = set(map(lambda stop: stop.stop_id, stops_data))
        stops[route_item.long_name] = stops_as_set
        total_stops = total_stops.union(stops_as_set)

    return stops


def stop_stats(stops_data: dict) -> dict:  # get least/most stops
    least_stops_name = ""
    most_stops_name = ""
    least_stops = math.inf
    most_stops = 0
    for route_name in stops_data.keys():

        # compare number of stops for rq2
        num_stops = len(stops_data[route_name])

        if num_stops == 0:
            raise Exception("a train must have at least one stop!")

        if num_stops > most_stops:
            most_stops = num_stops
            most_stops_name = route_name
        if num_stops < least_stops:
            least_stops = num_stops
            least_stops_name = route_name
    return {
        "least_stops_name": least_stops_name,
        "most_stops_name": most_stops_name,
        "least_stops": least_stops,
        "most_stops": most_stops
    }


def calculate_connectors(stops_data: dict) -> dict:
    connectors = {}  # "name":set("loc1","loc2")

    for line_name in stops_data.keys():  # build list of list of potential intersects
        for stop in stops_data[line_name]:
            if stop in connectors:
                connectors[stop] = connectors[stop].union(set([line_name]))
            else:
                connectors[stop] = set([line_name])

    final_connectors = {}

    for key in connectors.keys():
        if len(connectors[key]) > 1:
            final_connectors[key] = connectors[key]

    return final_connectors


def print_data():
    # complete req 1 and 2
    # I will let the server do the sorting because otherwise it'd defeat the design principle of an effective api,
    # which is one that communicates the minimum useful information
    all_routes = mbta_api.routes()

    route_data = routeBuilder(all_routes)  # organized route data

    route_metadata = stop_stats(route_data)  # route metadata

    route_intersections = calculate_connectors(
        route_data)  # route intersections

    print("=====[STOP DATA {rq1}]=====")
    for route_item in route_data.keys():
        num_stops = len(route_data[route_item])
        print(f"name:{route_item} len:{num_stops}")

    print("=====[METADATA {rq2}]=====")
    print(f"Most Stops: {route_metadata['most_stops_name']}")
    print(f"Least Stops: {route_metadata['least_stops_name']}")

    print("=====[CONNECTING STOPS {rq2}]=====")
    for key in route_intersections.keys():
        print(
            f"A stop named: -[ {key} ]- connects trains: {route_intersections[key]}")


def shortest_path(graph, node_a, node_b) -> typing.List[str]:
    possible_paths = [[node_a]]
    num_paths = 0
    nodes_prev_visited = {node_a}

    if node_a == node_b:  # node a is node b, return.
        return possible_paths[0]

    while num_paths < len(possible_paths):
        curr_path = possible_paths[num_paths]
        last_node = curr_path[-1]
        next_nodes = graph[last_node]
        # Search goal node
        if node_b in next_nodes:
            curr_path.append(node_b)
            return curr_path
        # Add new paths
        for node in next_nodes:
            if not node in nodes_prev_visited:
                new_path = curr_path[:]
                new_path.append(node)
                possible_paths.append(new_path)
                nodes_prev_visited.add(node)
        num_paths += 1  # follow next path

    return []  # fallback: found nothing


def atob(start: str, stop: str) -> typing.List[str]:
    all_routes = mbta_api.routes()
    route_data = routeBuilder(all_routes)
    route_intersections = calculate_connectors(route_data)

    # get nodes(routes) for a and b
    # if the key is in the place's keylist("greenline":{"loc1","loc2"}), set the node to greenline for example
    start_line = ""
    stop_line = ""
    for key in route_data.keys():
        if start_line == "" and start in route_data[key]:
            start_line = key
        if stop_line == "" and stop in route_data[key]:
            stop_line = key
    if start_line == "":
        raise Exception("invalid source name!")
    if stop_line == "":
        raise Exception("invalid destinaiton name!")


    # convert route data/intersects to graph
    graph = {}
    for key in route_intersections.keys():
        for line in route_intersections[key]:
            if not line in graph:
                graph[line]=route_intersections[key]
            else:
                intersects_select = route_intersections[key].copy()
                intersects_select.remove(line)
                graph[line]=graph[line].union(intersects_select)


    # get the shortest path from the data above
    return shortest_path(graph, start_line, stop_line)

def data_prompt():
    if "--route" in sys.argv:
        if len(sys.argv) == 2:
            raise Exception("you must provide a source and destination!")
        else:
            lines_taken = atob(sys.argv[2], sys.argv[3])
            print(lines_taken)
    elif "--route-data" in sys.argv:
        all_routes = mbta_api.routes()
        route_data = routeBuilder(all_routes)
        print(route_data)
    elif "--data" in sys.argv:
        print_data()
    else:
        print("=====[Welcome to MACHmbta]=====")
        print("- use flag '--data' to get all data for req 1/2")
        print("- use flag '--route \"a\" \"b\"' to get an AtoB route prompt for req3")
        print("- use flag '--route-data was added for my sake, prints all of the stop names to the console so you can use them for --route")
        print("- otherwise, the program will display this text")


data_prompt()
