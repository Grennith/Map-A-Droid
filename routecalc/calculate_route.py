#coding:utf-8
import numpy as np
import json
import math
from util import *
from args import *
import collections
import logging

log = logging.getLogger(__name__)

ShortestDistance = collections.namedtuple('ShortestDistance', ['index', 'distance'])

def __midPoint(lat1, lon1, lat2, lon2):

    dLon = math.radians(lon2 - lon1)

    #convert to radians
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    lon1 = math.radians(lon1)

    x = math.cos(lat2) * math.cos(dLon)
    y = math.cos(lat2) * math.sin(dLon);
    lat3 = math.atan2(math.sin(lat1) + math.sin(lat2), math.sqrt((math.cos(lat1) + x) * (math.cos(lat1) + x) + y * y));
    lon3 = lon1 + math.atan2(y, math.cos(lat1) + x);


    coord = [math.degrees(lat3), math.degrees(lon3)]
    return coord

def getDistanceOfTwoPointsInMeters(startLat, startLng, destLat, destLng):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = math.radians(startLat)
    lon1 = math.radians(startLng)
    lat2 = math.radians(destLat)
    lon2 = math.radians(destLng)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    distanceInMeters = distance * 1000
    return distanceInMeters

def __lessCoordsMiddle(coordinates):
    less = []
    #TODO: consider sorting by distances before cutting out points?
    while coordinates.size > 0:
        for coord in coordinates:
            coordIndex = np.nonzero(coordinates == coord)[0][0]
            shortestDistance = __getShortestDistanceOfPointLessMax(coord, coordinates, 500)
            if shortestDistance.index == -1:
                #no other gym in 500m radius
                less.append(coord)
                coordinates = np.delete(coordinates, coordIndex, 0)
                #coordinates.remove(coord)
                break

            #we got at least one gym nearby, summarize!
            nearbyPoint = coordinates[shortestDistance.index]
            middle = __midPoint(coord[0], coord[1], nearbyPoint[0], nearbyPoint[1])
            less.append(middle)

            #numpy does not delete in-place :(
            coordinates = np.delete(coordinates, [shortestDistance.index, coordIndex], 0) #the 0 indicates that we keep our 2D structure
            break
    return np.array(less)

def __lessCoords(coordinates, gymDistance, maxAmountOfGymsToSumUpWithGym):
    less = []
    #log.debug("Summing up gyms...")
    while coordinates.size > 0:
        coord = coordinates[0]
        #log.debug("Summing up up to 5 gyms around %s" % str(coord))
        less.append(coord)

        coordinates = np.delete(coordinates, 0, 0)
        for x in range(maxAmountOfGymsToSumUpWithGym - 1):
            if (coordinates.size == 0):
                #we already cut down all the gyms...
                return np.array(less)
            shortestDistance = __getShortestDistanceOfPointLessMax(coord, coordinates, gymDistance)

            if (shortestDistance.index == -1):
                #no (more) gym found in range
                break;
            #log.debug("%s is %sm close to gym %s" % (str(coordinates[shortestDistance.index]), str(shortestDistance), str(coord)))
            coordinates = np.delete(coordinates, shortestDistance.index, 0)
    return np.array(less)

def __getShortestDistanceOfPointLessMax(point, coordinates, maxDistance):
    index = -1
    shortestDistance = maxDistance #we only summarize gyms that are less then n meters apart
    for coord in coordinates:
        if (point[0] == coord[0] and point[1] == coord[1]):
            continue
        distanceToCoord = getDistanceOfTwoPointsInMeters(point[0], point[1], coord[0], coord[1])

        if distanceToCoord < shortestDistance:
            #index = np.where(coordinates == coord)
            index = np.nonzero(coordinates == coord)[0][0]

            shortestDistance = distanceToCoord

    return ShortestDistance(index, shortestDistance)

def getJsonRoute(filePath, gymDistance, maxAmountOfGymsToSumUpWithGym):
    csvCoordinates = np.loadtxt(filePath, delimiter=',')
    log.debug("Read %s coordinates from file" % str(len(csvCoordinates)))
    #log.debug("Read from file: %s" % str(csvCoordinates))

    if (csvCoordinates.size > 1 and gymDistance and maxAmountOfGymsToSumUpWithGym):
        #TODO: consider randomizing coords and trying a couple times to get "best" result
        log.info("Found %s coordinates" % (csvCoordinates.size / 2))
        log.info("Calculating...")
        lessCoordinates = __lessCoords(csvCoordinates, gymDistance, maxAmountOfGymsToSumUpWithGym)
        log.debug("Coords summed up: %s, that's just %s coords" % (str(lessCoordinates), str(len(lessCoordinates))))
        #TODO: use smallest enclosing ball instead of this shit or just make __lessCoords better

    log.info("Got %s coordinates" % (lessCoordinates.size / 2.0))
    if (not len(lessCoordinates) > 2):
        log.info("less than 3 coordinates... not gonna take a shortest route on that")
        export_data = []
        for i in range(len(lessCoordinates)):
            export_data.append(lessCoordinates[i])
        return export_data

    log.info("Calculating a short route through all those coords. Might take a while")
    # Constant Definitions
    NUM_NEW_SOLUTION_METHODS = 3
    SWAP, REVERSE, TRANSPOSE = 0, 1, 2

    coordinates = lessCoordinates.copy()
    # Params Initial
    num_location = coordinates.shape[0]
    markov_step = 10 * num_location
    T_0, T, T_MIN = 100, 100, 1
    T_NUM_CYCLE = 1

    # Build distance matrix to accelerate cost computing
    distmat = get_distmat(coordinates)

    # States: New, Current and Best
    sol_new, sol_current, sol_best = (np.arange(num_location), ) * 3
    cost_new, cost_current, cost_best = (float('inf'), ) * 3

    # Record costs during the process
    costs = []

    # previous cost_best
    prev_cost_best = cost_best

    # counter for detecting how stable the cost_best currently is
    cost_best_counter = 0

    # Simulated Annealing
    while T > T_MIN and cost_best_counter < 150:
        for i in np.arange(markov_step):
            # Use three different methods to generate new solution
            # Swap, Reverse, and Transpose
            choice = np.random.randint(NUM_NEW_SOLUTION_METHODS)
            if choice == SWAP:
                sol_new = swap(sol_new)
            elif choice == REVERSE:
                sol_new = reverse(sol_new)
            elif choice == TRANSPOSE:
                sol_new = transpose(sol_new)
            else:
                print("ERROR: new solution method %d is not defined" % choice)
                exit(2);
            # Get the total distance of new route
            cost_new = sum_distmat(sol_new, distmat)

            if accept(cost_new, cost_current, T):
                # Update sol_current
                sol_current = sol_new.copy()
                cost_current = cost_new

                if cost_new < cost_best:
                    sol_best = sol_new.copy()
                    cost_best = cost_new
            else:
                sol_new = sol_current.copy()

        # Lower the temperature
        alpha = 1 + math.log(1 + T_NUM_CYCLE)
        T = T_0 / alpha
        costs.append(cost_best)

        # Increment T_NUM_CYCLE
        T_NUM_CYCLE += 1

        # Detect stability of cost_best
        if isclose(cost_best, prev_cost_best, abs_tol=1e-12):
          cost_best_counter += 1
        else:
          # Not stable yet, reset
          cost_best_counter = 0

        # Update prev_cost_best
        prev_cost_best = cost_best

        # Monitor the temperature & cost
        #print("Temperature:", "%.2f°C" % round(T, 2),
        #      " Distance:", "%.2fm" % round(cost_best, 2),
        #      " Optimization Threshold:", "%d" % cost_best_counter)

    export_data = []
    for i in range(len(sol_best)):
        export_data.append({'lat' : lessCoordinates[int(sol_best[i])][0].item(),
            'lng' : lessCoordinates[int(sol_best[i])][1].item()})

    #return json.dumps(export_data)
    return export_data
