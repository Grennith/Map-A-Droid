#coding:utf-8
import numpy as np
import json
import math
from util import *
from args import *
import collections
import logging
import glob, os

log = logging.getLogger(__name__)

Location = collections.namedtuple('Location', ['lat', 'lng'])
ShortestDistance = collections.namedtuple('ShortestDistance', ['index', 'distance'])
GymInfoDistance =  collections.namedtuple('GymInfoDistance', ['distance', 'location'])

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

    return Location(math.degrees(lat3), math.degrees(lon3))

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

def __getDistanceRelationsInRange(coordinates, gymDistance):
    #each field holds a tuple of (Location, Array of GymInfoDistance)
    #GymInfoDistance is a namedtuple of distance, location of gym
    relations = []
    for coord in coordinates:
        #array of GymInfoDistance
        closest = []
        coordsToBeInspected = coordinates.copy()
        #copied the coordinates, remove one by one and get the closest gyms and remove those within gymDistance
        while coordsToBeInspected.size > 0:
            if (coordsToBeInspected.size == 0):
                #we already cut down all the gyms...
                #TODO: add the gym to the returning set somewhere
                break
            shortestDistance = __getShortestDistanceOfPointLessMax(coord, coordsToBeInspected, gymDistance)

            if (shortestDistance.index == -1):
                #no (more) gym found in range
                #TODO: add the gym and it's closest neighbours to set
                break;
            closest.append(GymInfoDistance(shortestDistance.distance,
                Location(coordsToBeInspected[shortestDistance.index][0].item(),
                    coordsToBeInspected[shortestDistance.index][1].item())))
            coordsToBeInspected = np.delete(coordsToBeInspected, shortestDistance.index, 0)
        relations.append( (Location(coord[0].item(), coord[1].item()), closest) )
    #log.error("__getDistanceRelations: got %s" % str(relations))
    return relations

#return a list of locations to be scanned based on relations
def __getLessWithRelations(relations, maxAmountOfGymsToSumUpWithGym):
    #select point farthest in northeast of relations and get a set with at most maxGyms (smallest circle so to speak)
    #get the most west point
    if relations is None or len(relations) == 0:
        log.error("__getMaxSetInGivenSet: relations none or empty")
        return [] #TODO: return useful data...

    #log.debug("__getLessWithRelations: Relations: %s" % str(relations))
    coordsToReturn = []
    while len(relations) > 0:
        relationToBeInspected = None
        mostWest = relations[0]
        #log.error("Most west init: %s" % str(mostWest))
        mostWestRelations = []
        for relation in relations:
            if relation[0].lat < mostWest[0].lat:
                mostWest = relation
                mostWestRelations = []
            elif relation[0].lat == mostWest[0].lat:
                mostWestRelations.append(relation)
        #we found the most west relation...
        if len(mostWestRelations) > 0:
            relationToBeInspected = mostWestRelations[0]
            while len(mostWestRelations) > 0:
                #well, got more than one relation farthest west select the farthest north
                if mostWestRelations[0][0].lng > relationToBeInspected[0].lng:
                    relationToBeInspected = mostWestRelations[0]
                mostWestRelations.remove(mostWestRelations[0])
        else:
            relationToBeInspected = mostWest
        if relationToBeInspected is None:
            #we cannot find any more relations apparently, wtf
            #log.error("relationToBeInspected is None")
            return coordsToReturn

        #log.error("Relation to be inspected: %s" % str(relationToBeInspected))
        #get the coords relevant for the relation :)
        circleOfRelation = __getCirclePositionInRelation(relationToBeInspected,
            maxAmountOfGymsToSumUpWithGym)
        coordsToReturn.append(circleOfRelation[0])
        #we added the middle of the circle, let's remove all related coords
        #from the relations themselves as well as all distance relations
        #let's first retrieve all the relations to be removed
        coordsToDelete = circleOfRelation[1]
        for coord in coordsToDelete:
            for relation in relations:
                if coord.lat == relation[0].lat and coord.lng == relation[0].lng:
                    #found relation, remove it...
                    #log.error("Found %s in relations reflection coord. %s" % (str(relation), str(relations)))
                    relations.remove(relation)
                    #log.error("New relations: %s" % str(relations))
                    break
            #now also remove all occurences in subsets...
            for relation in relations:
                nearbyLocations = relation[1]
                for loc in nearbyLocations:
                    if (coord.lat == loc.location.lat and
                        coord.lng == loc.location.lng):
                        #found an occurence..
                        relation[1].remove(loc)
                        break;

        #okay, we now updated relations as required...

    return coordsToReturn


#return tuple of (coord, coords). First coord being the middle of the circle
#coords being the coords inside it (array)
def __getCirclePositionInRelation(relation, maxAmountOfGymsToSumUpWithGym):
    #relation consists of (Location, [ GymInfoDistance ] )
    #log.error("Relation given:  %s " % str(relation))
    locationToSpanFrom = relation[0]
    coordsInCircle = []
    coordsInCircle.append(locationToSpanFrom)
    distanceLocations = relation[1]
    #log.error(relation)
    if len(distanceLocations) == 0:
        #no point in range, stop right there and return
        return (locationToSpanFrom, coordsInCircle)
    while len(distanceLocations) > 0:
        #log.error("Distance locations: %s" % str(distanceLocations))
        selected = distanceLocations[0] #get the first element
        #get the farthest point
        for loc in distanceLocations:
            if loc.distance > selected.distance:
                selected = loc

        #remove the selected coord from the set
        distanceLocations.remove(selected)

        tempCircle = [] # Location[]
        #we got the point farthest from our locationToSpanFrom, get the middle
        #and check the amount of gyms that are in that circle with the given range
        middle = __midPoint(selected.location.lat, selected.location.lng,
            locationToSpanFrom.lat, locationToSpanFrom.lng)
        tempCircle.append(selected.location)
        tempCircle.append(locationToSpanFrom)
        #we now have the middle, take selected.distance / 2 as radius and check the amount of raids
        #we only need to inspect the coords in our distanceLocations set
        for distLoc in distanceLocations:
            dist = getDistanceOfTwoPointsInMeters(distLoc.location.lat,
                distLoc.location.lng, middle.lat, middle.lng)
            if dist <= selected.distance / 2:
                #we found a gym in our circle...
                #add it to our tempCircle
                tempCircle.append(distLoc.location)
        if len(tempCircle) - 1 <= maxAmountOfGymsToSumUpWithGym:
            #well, we found a matching circle
            #return tuple of (midpointCircle, coordsInCircle)
            return ( middle, tempCircle )
    #seems we haven't found a circle properly, just return the point itself...
    return ( locationToSpanFrom, [] )



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

def getJsonRoute(filePath, gymDistance, maxAmountOfGymsToSumUpWithGym, routefile):
    export_data = []
    if os.path.isfile(routefile + '.calc'):
        log.info('Found existing Routefile')
        route = open(routefile + '.calc', 'r') 
        for line in route: 
            lineSplit = line.split(',')
            export_data.append({'lat' : float(lineSplit[0].replace('\n','')),
                'lng' : float(lineSplit[1].replace('\n',''))})
        return export_data
            
    csvCoordinates = np.loadtxt(filePath, delimiter=',')
    log.debug("Read %s coordinates from file" % str(len(csvCoordinates)))
    #log.debug("Read from file: %s" % str(csvCoordinates))
    lessCoordinates = csvCoordinates
    if (csvCoordinates.size > 1 and gymDistance and maxAmountOfGymsToSumUpWithGym):
        #TODO: consider randomizing coords and trying a couple times to get "best" result
        log.info("Calculating...")
        relations = __getDistanceRelationsInRange(csvCoordinates, gymDistance * 2)
        newCoords = __getLessWithRelations(relations, maxAmountOfGymsToSumUpWithGym)
        lessCoordinates = np.zeros(shape=(len(newCoords) , 2))
        for i in range(len(lessCoordinates)):
            lessCoordinates[i][0] = newCoords[i][0]
            lessCoordinates[i][1] = newCoords[i][1]
        #log.error("Summed up down to %s" % str(newCoords))
        #lessCoordinates = __lessCoords(csvCoordinates, gymDistance, maxAmountOfGymsToSumUpWithGym)
        log.debug("Coords summed up: %s, that's just %s coords" % (str(lessCoordinates), str(len(lessCoordinates))))
        #TODO: use smallest enclosing ball instead of this shit or just make __lessCoords better

    log.info("Got %s coordinates" % (lessCoordinates.size / 2.0))
    if (not len(lessCoordinates) > 2):
        log.info("less than 3 coordinates... not gonna take a shortest route on that")
        export_data = []
        for i in range(len(lessCoordinates)):
            export_data.append({'lat' : lessCoordinates[i][0].item(),
                'lng' : lessCoordinates[i][1].item()})
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

    
    for i in range(len(sol_best)):
        with open(routefile + '.calc', 'a') as f:
            f.write(str(lessCoordinates[int(sol_best[i])][0].item()) + ', ' + str(lessCoordinates[int(sol_best[i])][1].item()) + '\n')
        export_data.append({'lat' : lessCoordinates[int(sol_best[i])][0].item(),
            'lng' : lessCoordinates[int(sol_best[i])][1].item()})

    #return json.dumps(export_data)
    return export_data
