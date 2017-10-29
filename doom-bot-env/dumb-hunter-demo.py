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
    print('Calling {} with payload {}'.format(url, payload))
    try:
        requests.post(url, json=payload)
        return True
    except:
        logging.error('POST API call failed')
        return False

def turnPlayer(degree):
    global RESTFUL_HOST
    global RESTFUL_PORT

    url = 'http://{}:{}/api/player/turn'.format(RESTFUL_HOST, RESTFUL_PORT)
    print('Calling {} with payload'.format(url))
    try:
        requests.post(url, json={"type" : "right", "target_angle" : degree})
        return True
    except:
        logging.error('POST API call failed')
        return False


def getAction(objectName):
    global RESTFUL_HOST
    global RESTFUL_PORT

    url = 'http://{}:{}/api/{}'.format(RESTFUL_HOST, RESTFUL_PORT, objectName)
    print('Calling {}'.format(url))
    try:
        req = requests.get(url)
        data = json.loads(req.text)
        return data
    except:
        logging.error('GET API call failed')
        return None


def spinPlayer(amount):
    print ("Spinning to the angle {}" .format(amount))
    turnPlayer(amount)

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


def simpleTrig(player_x,player_y,enemy_x,enemy_y):
    #print('simpleTrig({}, {})'.format(a, b))
    return math.degrees(
        math.atan2((enemy_y - player_y), (enemy_x - player_x))
    )



def moveToPoint(enemy, attempts=1, pause=2, accuracy=25):
    """Try to move in a straight line from where we are to a destination
    point in a finite amount of steps. Z axis is disregarded
    """
    currentData = getAction('player')

    destX = enemy["position"]["x"]
    destY = enemy["position"]["y"]

    distance = distanceBetweenPoints(
        currentData["position"]["x"],
        currentData["position"]["y"],
        enemy["position"]["x"],
        enemy["position"]["y"]
    )

    angle = int(simpleTrig(
        currentData["position"]["x"],
        currentData["position"]["y"],
        enemy["position"]["x"],
        enemy["position"]["y"]
    ))

    print angle

    if angle < 0:
        angle = 360 - abs(angle)

    spinPlayer(angle)

    movePlayer(10) #change to walk to enemy only if needed

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
        if worldObject['type'] == "Player" and worldObject['id'] != myId():
            enemies.append(worldObject)

    print('Found {} enemies'.format(len(enemies)))

    nearestEnemy = None
    nearestEnemyDistance = 999999.0

    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        distance = distanceBetweenPoints(
            playerData["position"]["x"],
            playerData["position"]["y"],
            enemy["position"]["x"],
            enemy["position"]["y"]
        )

        if distance < nearestEnemyDistance:
            print('Found a new nearest enemy - {}, {} @ {} x {} angle {}'.format(
                enemy['id'],
                enemy['type'],
                enemy["position"]["x"],
                enemy["position"]["y"],
                enemy["angle"]
            ))
            print('Found a me- {}, {} @ {} x {} angle {}'.format(
                playerData['id'],
                playerData['type'],
                playerData["position"]["x"],
                playerData["position"]["y"],
                playerData["angle"]
            ))
            print json.dumps(enemy, indent=4)
            nearestEnemy = enemy
            nearestEnemyDistance = distance
    return nearestEnemy



def unStuck():
    canMove = getAction('world/movetest')
    br = 0
    if (canMove(myId(), getX(), getY())):
        br += 1
        if (br >= 2):
            randomAngle = random.randInt(90, 270)
            reorientPlayer(randomAngle)


def getX():
    return player()['position']['x']


def getY():
    return player()['position']['y']


def myId():
    players = getAction('players')
    for dict in players:
        if (dict['isConsolePlayer'] == True):
            return dict['id']


def player():
    return getAction('player')


objects = getAction('world/objects')


def objectsCanSee(obj):
    idCanSee = []
    for dict in obj:
        if getAction('world/los/{id1}/{id2}'.format(id1=myId(), id2=dict['id'])):
            idCanSee.append(dict['id'])
    return idCanSee


def distanceFromObjectsIWant(objectsIWant=[]):
    distanceFromObjects = {}
    ids = {}
    br = 0
    for dict in objects:
        if (dict["type"] in objectsIWant):
            distanceFromObjects[br] = dict['distance']
            ids[br] = dict['id']
            br += 1
    return [distanceFromObjects, ids]


def nearestObject(distanceFromObjectsAndId):
    temp = 999999999
    id = -1
    br = 0
    for dist in distanceFromObjectsAndId[0]:
        if (dist[br] < temp):
            temp = dict[br]
            id = br
        br += 1
    return distanceFromObjectsAndId[1][id]


def nearestObjectIWant(objectsIWant=[]):
    return nearestObject(distanceFromObjectsIWant(objectsIWant))


def checkHealth():
    if playerStatus()['health'] < 30:
        idNearestHealthPlus = nearestObjectIWant(
            ["Health Potion +1% health", "Stimpack", "Medikit", "Supercharge", "Med Patch", "Medical Kit",
             "Surgery Kit"])
        return idNearestHealthPlus


def checkAmmo():
    if playerStatus()['ammo']['Bullets'] < 15:
        idNearestAmmoPlus = nearestObjectIWant(
            ["Ammo clip", "Box of ammo", "Box of rockets", "Box of shells", "Cell charge", "Cell charge pack", "Rocket",
             "Shotgun shells"])
        return idNearestAmmoPlus


def tryShoot(enemy):
    if (enemy['id'] in objectsCanSee(getAction('players')) and enemy['distance'] < 300):
        shoot()




def enemyAttack():
    enemy = findNearestEnemy()
    #print json.dumps(enemy, indent=4)
    moveToPoint(enemy)
    tryShoot(enemy)


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s')
# enemy = findNearestEnemy()
# print json.dumps(enemy, indent=4)
# moveToPoint(enemy["position"]["x"], enemy["position"]["y"])
# shoot()



while 1 == 1:
    # unStuck()

    enemyAttack()
    # checkVitals(playerStatus())