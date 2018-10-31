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


Relation = collections.namedtuple('Relation', ['otherCoord', 'distance'])


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

# returns a map of coords and all their closest neighbours based on a given radius * 2 (hence circles...)
def __getRelationsInRange(coordinates, rangeRadiusMeter):
    # print "Got " + str(len(coordinates)) + " coordinates and will build relations with radius " + str(rangeRadiusMeter)
    relations = {}
    for coord in coordinates:
        for otherCoord in coordinates:
            if coord.lat == otherCoord.lat and coord.lng == otherCoord.lng:
                if coord not in relations:
                    relations[coord] = []
            distance = getDistanceOfTwoPointsInMeters(coord.lat, coord.lng, otherCoord.lat, otherCoord.lng)
            if 0 <= distance <= rangeRadiusMeter * 2:
                if coord not in relations:
                    relations[coord] = []
                # we need to avoid duplicates...
                alreadyPresent = False
                for relation in relations[coord]:
                    if relation.otherCoord.lat == otherCoord.lat and relation.otherCoord.lng == otherCoord.lng:
                        alreadyPresent = True
                if not alreadyPresent:
                    relations[coord].append(Relation(otherCoord, distance))
    # print "Got " + str(len(relations)) + " relations"
    # print relations
    return relations

def __countOfGymsInCircle(middle, radius, relations):
    count = 1 # the origin of our relations is assumed to be in the circle anyway...
    for relation in relations:
        distance = getDistanceOfTwoPointsInMeters(middle.lat, middle.lng, relation.otherCoord.lat, relation.otherCoord.lng)
        if distance <= radius:
            count += 1
    return count

# adapted from https://stackoverflow.com/questions/6671183/calculate-the-center-point-of-multiple-latitude-longitude-coordinate-pairs
def __getMiddleOfCoordList(listOfCoords):
    if len(listOfCoords) == 1:
        return listOfCoords[0]

    x = 0
    y = 0
    z = 0

    for coord in listOfCoords:
        # transform to radians...
        latRad = math.radians(coord.lat)
        lngRad = math.radians(coord.lng)

        x += math.cos(latRad) * math.cos(lngRad)
        y += math.cos(latRad) * math.sin(lngRad)
        z += math.sin(latRad)

    amountOfCoords = len(listOfCoords)
    x = x / amountOfCoords
    y = y / amountOfCoords
    z = z / amountOfCoords
    centralLng = math.atan2(y, x)
    centralSquareRoot = math.sqrt(x * x + y * y)
    centralLat = math.atan2(z, centralSquareRoot)

    return Location(math.degrees(centralLat), math.degrees(centralLng))

def __getCircle(coord, toBeInspected, relations, maxCount, maxDistance):
    # print "Next Circle with coord " + str(coord)
    # print "Relations: \n" + str(relations)
    #includedInCircle = [coord]
    includedInCircle = []
    #toBeInspected = relations[coord]
    if len(toBeInspected) == 0:
        # coord is alone at its position...
        return coord, []
    elif len(toBeInspected) == 1:
        # print "Just one coord, returning it as the middle: " + str(coord)
        return coord, [coord]
    # elif len(toBeInspected) == 2:
    #     for relation in toBeInspected:
    #         includedInCircle.append(relation.otherCoord)
    #     print "just two coords, returning the middle of " + str(coord) + " and " + str(relation.otherCoord)
    #     middle = __getMiddleOfCoordList(includedInCircle)
    #     print "Returning middle: " + str(middle) + " included in the circle: " + str(includedInCircle)
    #     return middle, includedInCircle

    # check if middle of the two farthest away already holds everything needed
    farthestAway, distanceToFarthest = __getFarthestInRelation(toBeInspected)
    allCoordsWithinRange = [coord, farthestAway]
    # for locationInUnion in unionOfFarthest:
    #     allCoordsWithinRange.append(locationInUnion)
    middle = __getMiddleOfCoordList(allCoordsWithinRange)
    countInside, coordsInCircle = __getCountAndCoordsInCircle(middle, relations, maxDistance)
    # print "Coords in circle basic middle: " + str(coordsInCircle) + " middle at: " + str(middle)
    # print "Relation inspected: " + str(toBeInspected)
    # print (len(coordsInCircle) == len(toBeInspected))
    # print "Count inside circle: " + str(countInside) + " maxCount: " + str(maxCount)
    if countInside <= maxCount and len(coordsInCircle) == len(toBeInspected):
        # print "Returning middle " + str(middle) + " and telling to remove " + str(coordsInCircle)
        return middle, coordsInCircle
    elif countInside > maxCount:
        toBeInspected = [toKeep for toKeep in toBeInspected if
                         not (toKeep.otherCoord.lat == farthestAway.lat
                              and toKeep.otherCoord.lng == farthestAway.lng)]
        return __getCircle(coord, toBeInspected, relations, maxCount, distanceToFarthest)
    else:
        return middle, coordsInCircle
        # TODO: calculate the entire stuff distributed by degrees north/south to coord

def __getMostSouthern(coord, relation):
    mostSouthern = coord
    for coordInRel in relation:
        if coordInRel.otherCoord.lat < mostSouthern.lat:
            mostSouthern = coordInRel.otherCoord
    return mostSouthern

def __listOfCoordsContainsCoord(listOfCoords, coord):
    # print "List to be searched: " + str(listOfCoords)
    # print "Coord to be searched for: " + str(coord)
    for coordOfList in listOfCoords:
        if coord.lat == coordOfList.lat and coord.lng == coordOfList.lng:
            return True
    return False

def __getMostNorthernInRelation(coord, relation):
    mostNorthern = coord
    for coordInRel in relation:
        if coordInRel.otherCoord.lat >= mostNorthern.lat:
            mostNorthern = coordInRel.otherCoord
    return mostNorthern

def __getMostWestAmongstRelations(relations):
    selected = relations.keys()[0]
    # print selected
    for relation in relations:
        if relation.lng < selected.lng:
            selected = relation
            # print selected
        elif relation.lng == selected.lng and relation.lat > selected.lat:
            selected = relation
            # print selected
    return selected

def __getFarthestInRelation(relation):
    distance = -1
    farthest = None
    for location in relation:
        if location.distance > distance:
            distance = location.distance
            farthest = location.otherCoord
    return farthest, distance

# only returns the union, not the points of origins of the two relations!
def __getUnionOfRelations(relationsOne, relationsTwo):
    listToReturn = []
    for relation in relationsOne:
        for otherRelation in relationsTwo:
            if (otherRelation.otherCoord.lat == relation.otherCoord.lat
                and otherRelation.otherCoord.lng == relation.otherCoord.lng):
                listToReturn.append(otherRelation.otherCoord)
    return listToReturn

def __getCountAndCoordsInCircle(middle, relations, maxRadius):
    # print "looking for gyms from " + str(middle) + " with a range of " + str(maxRadius) +  " in " + str(len(relations)) + " relations"
    insideCircle = []
    for locationSource in relations:
        distance = getDistanceOfTwoPointsInMeters(middle.lat, middle.lng, locationSource.lat, locationSource.lng)
        if 0 <= distance <= maxRadius:
            insideCircle.append(locationSource)
    return len(insideCircle), insideCircle

def __sumUpRelations(relations, maxCountPerCircle, maxDistance):
    finalSet = []

    while len(relations) > 0:
        # get the most western north point in relations
        next = __getMostWestAmongstRelations(relations)
        # get a circle with "next" in it...
        middle, coordsToBeRemoved = __getCircle(next, relations[next], relations, maxCountPerCircle, maxDistance)
        # print "Removing: " + str(coordsToBeRemoved) + " Center of circle: " + str(middle)
        # remove the coords covered by the circle...
        finalSet.append(middle)
        relations = __removeCoordsFromRelations(relations, coordsToBeRemoved)
    return finalSet

def __removeCoordsFromRelations(relations, listOfCoords):
    for sourceLocation, distanceRelations in relations.items():
        # iterate relations, remove anything matching listOfCoords
        for coord in listOfCoords:
            #print "Coord: " + str(coord) + " sourceLocation: " + str(sourceLocation)
            if coord.lat == sourceLocation.lat and coord.lng == sourceLocation.lng:
                # entire relation matches the coord, remove it
                relations.pop(sourceLocation)
                break
            # iterate through the entire distance relations...
            for distRel in distanceRelations:
                if distRel.otherCoord.lat == coord.lat and distRel.otherCoord.lng == coord.lng:
                    relations[sourceLocation].remove(distRel)
    return relations

def getLessCoords(npCoordinates, maxRadius, maxCountPerCircle):
    coordinates = []
    for coord in npCoordinates:
        coordinates.append(Location(coord[0].item(), coord[1].item()))

    relations = __getRelationsInRange(coordinates, maxRadius)
    summedUp = __sumUpRelations(relations, maxCountPerCircle, maxRadius)
    # print "Done summing up: " + str(summedUp) + " that's just " + str(len(summedUp))
    return summedUp


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
        # relations = __getDistanceRelationsInRange(csvCoordinates, gymDistance * 2)
        # newCoords = __getLessWithRelations(relations, maxAmountOfGymsToSumUpWithGym)
        newCoords = getLessCoords(csvCoordinates, gymDistance, maxAmountOfGymsToSumUpWithGym)
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
                # print("ERROR: new solution method %d is not defined" % choice)
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
