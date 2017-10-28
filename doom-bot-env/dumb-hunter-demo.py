#!/usr/bin/python

import requests
import logging
import random
import time
import json
import math



RESTFUL_HOST = "localhost"
RESTFUL_PORT = int(raw_input("Which restful port: "))


def sendAction(objectName, payload):
    global RESTFUL_HOST
    global RESTFUL_PORT

    url = 'http://{}:{}/api/{}/actions'.format(RESTFUL_HOST, RESTFUL_PORT, objectName)
    logging.debug('Calling {} with payload {}'.format(url, payload))
    try:
        requests.post(url, json=payload)
        return True
    except:
        logging.error('POST API call failed')
        return False


def getAction(objectName):
    global RESTFUL_HOST
    global RESTFUL_PORT

    url = 'http://{}:{}/api/{}'.format(RESTFUL_HOST, RESTFUL_PORT, objectName)
    logging.debug('Calling {}'.format(url))
    try:
        req = requests.get(url)
        data = json.loads(req.text)
        return data
    except:
        logging.error('GET API call failed')
        return None


def spinPlayer(amount):
    if amount < 0:
        actionType = "turn-left"
        amount = abs(amount)
    else:
        actionType = "turn-right"

    sendAction('player', {'type': actionType, 'amount': amount})


def movePlayer(amount):
    if amount < 0:
        actionType = "backward"
        amount = abs(amount)
    else:
        actionType = "forward"

    sendAction('player', {'type': actionType, 'amount': amount})


def shoot():
    sendAction('player', {'type': 'shoot'})


def distanceBetweenPoints(x1, y1, x2, y2):
    dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return dist


def simpleTrig(a, b):
    logging.debug('simpleTrig({}, {})'.format(a, b))
    return math.degrees(
        math.acos(float(a) / float(b))
    )


def turnToFacePoint(destX, destY):
    currentData = getAction('player')

    distance = distanceBetweenPoints(
        currentData["position"]["x"],
        currentData["position"]["y"],
        destX,
        destY
    )

    angle = int(simpleTrig(
        abs(currentData["position"]["x"] - destX),
        abs(distance)
    ))

    logging.debug('Uncorrected angle is {}'.format(angle))

    if currentData["position"]["x"] < destX and currentData["position"]["y"] < destY:
        angle = 90 - angle
    elif currentData["position"]["x"] < destX and currentData["position"]["y"] >= destY:
        angle += 90
    elif currentData["position"]["x"] >= destX and currentData["position"]["y"] >= destY:
        angle = 270 - angle
    elif currentData["position"]["x"] >= destX and currentData["position"]["y"] < destY:
        angle += 270

    logging.debug('Corrected angle is {}'.format(angle))

    reorientPlayer(angle)


def moveToPoint(destX, destY, attempts=20, pause=1, accuracy=25):
    """Try to move in a straight line from where we are to a destination
    point in a finite amount of steps. Z axis is disregarded
    """

    for i in range(attempts):
        currentData = getAction('player')
        logging.debug('moveToPoint iteration {} - I am at {} x {} @ {} deg, I need to get to {} x {}'.format(
            i,
            currentData["position"]["x"],
            currentData["position"]["y"],
            currentData["angle"],
            destX,
            destY
        ))

        distance = distanceBetweenPoints(
            currentData["position"]["x"],
            currentData["position"]["y"],
            destX,
            destY
        )

        if abs(distance) < 300:
            shoot()

        if abs(distance) < accuracy:
            logging.debug('moveToPoint is close enough - {} x {} vs {} x {}'.format(
                currentData["position"]["x"],
                currentData["position"]["y"],
                destX,
                destY
            ))
            return True

        turnToFacePoint(destX, destY)

        movePlayer(100)

        time.sleep(pause)

    return False


def findNearestEnemy():
    """Gets all the world objects, finds the enemies, then
    figures out which one is closest to the player's current
    position. Dumb calculation, does not take map into account.
    """

    playerData = getAction('player')
    worldObjectData = getAction('world/objects')

    enemies = []

    for worldObject in worldObjectData:
        if worldObject['type'] == "Player" and worldObject['id']!= myId():
            enemies.append(worldObject)

    logging.debug('Found {} enemies'.format(len(enemies)))

    nearestEnemy = None
    nearestEnemyDistance = 999999.0

    for enemy in enemies:
        if enemy["health"] < 0:
            pass

        distance = distanceBetweenPoints(
            playerData["position"]["x"],
            playerData["position"]["y"],
            enemy["position"]["x"],
            enemy["position"]["y"]
        )

        if distance < nearestEnemyDistance:
            logging.debug('Found a new nearest enemy - {}, {} @ {} x {}'.format(
                enemy['id'],
                enemy['type'],
                enemy["position"]["x"],
                enemy["position"]["y"]
            ))
            nearestEnemy = enemy
            nearestEnemyDistance = distance

    return nearestEnemy


def reorientPlayer(angle, attempts=10, pause=1, accuracy=10):
    """Try and make the player point in a specific direction
    """

    for i in range(attempts):
        currentData = getAction('player')

        diff = currentData["angle"] - angle

        """If we would spin >180 degrees, go the other way"""
        if diff > 180:
            diff -= 360

        logging.debug(
            'We are facing {} and want to be facing {}, difference of {}'.format(currentData["angle"], angle, diff))

        if abs(diff) < accuracy:
            logging.debug('Close enough - angle is {} vs {}'.format(currentData["angle"], angle))
            return True

        """Game units are roughly 105 in a circle"""
        spinAmount = int(float(diff) * float(105.0 / 360.0))

        spinPlayer(spinAmount)

        time.sleep(pause)

    logging.debug('Gave up - angle is {} vs {}'.format(currentData["angle"], angle))

    return False



def unStuck():
    canMove = getAction('world/movetest')
    br=0
    if(canMove(myId(), getX(), getY())):
        br+=1
        if(br>=2):
            randomAngle = random.randInt(90, 270)
            reorientPlayer(randomAngle)

def getX():
    return player()['position']['x']

def getY():
    return player()['position']['y']

def myId():
    players = getAction('players')
    for dict in players:
        if(dict['isConsolePlayer']==True):
            return dict['id']

def player():
    return getAction('player')


objects = getAction('world/objects')

def objectsCanSee():
    idCanSee = []
    for dict in objects:
        if getAction('world/los/{id1}/{id2}'.format(id1=myId(), id2=dict['id'])):
            idCanSee.append(dict['id'])
    return idCanSee

def distanceFromObjectsIWant(objectsIWant = []):
    distanceFromObjects = {}
    ids = {}
    br=0
    for dict in objects:
        if(dict["type"] in objectsIWant):
            distanceFromObjects[br] = dict['distance']
            ids[br] = dict['id']
            br+=1
    return [distanceFromObjects, ids]


def nearestObject(distanceFromObjectsAndId):
    temp = 999999999
    id=-1
    br=0
    for dist in distanceFromObjectsAndId[0]:
        if(dist[br]<temp):
            temp=dict[br]
            id=br
        br+=1
    return distanceFromObjectsAndId[1][id]


def nearestObjectIWant(objectsIWant = []):
    return nearestObject(distanceFromObjectsIWant(objectsIWant))

def checkHealth():
    if playerStatus()['health']<30:
        idNearestHealthPlus = nearestObjectIWant(["Health Potion +1% health", "Stimpack", "Medikit", "Supercharge", "Med Patch", "Medical Kit", "Surgery Kit"])
        return idNearestHealthPlus

def checkAmmo():
    if playerStatus()['ammo']['Bullets']<15:
        idNearestAmmoPlus = nearestObjectIWant(["Ammo clip", "Box of ammo", "Box of rockets", "Box of shells", "Cell charge", "Cell charge pack", "Rocket", "Shotgun shells"])
        return idNearestAmmoPlus


def enemyAttack():
    enemy = findNearestEnemy()
    print json.dumps(enemy, indent=4)
    moveToPoint(enemy["position"]["x"], enemy["position"]["y"])
    shoot()



logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)





#enemy = findNearestEnemy()
#print json.dumps(enemy, indent=4)
#moveToPoint(enemy["position"]["x"], enemy["position"]["y"])
#shoot()



while 1 == 1:
    #unStuck()
    spinAmount = int((random.random() * 200.0) - 100)
    spinPlayer(spinAmount)

    enemyAttack()
    #checkVitals(playerStatus())