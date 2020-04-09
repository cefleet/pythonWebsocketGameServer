from asyncio import get_event_loop, wait
from websockets import serve
from json import loads, dumps
from uuid import uuid1

connections = []
games = []
users = []#{'deviceId':deviceId,'name':name}

async def newConnection(websocket):
    id = str(uuid1())
    nc = {'socket':websocket, 'id':id}
    connections.append(nc)
    await websocket.send(dumps({'action':"newConnectionAccepted", 'payload':nc['id']}))

async def sendAllInGame(gameId):
    #await wait([con['socket'].send(dumps(data)) for con in connections])
    return

async def sendAll(message):
    await wait([con['socket'].send(dumps({'action':"allMessage", 'payload':message})) for con in connections])

async def setupConnection(websocket,data):
    u = data['payload']
    cU = list(filter(lambda user:user['deviceId'] == u['deviceId'], users)) #current user   
    if len(cU) < 1:
        users.append(u)
    else:
        u = cU[0]
    if 'userName' not in u:
        await websocket.send(dumps({'action':'needUserName'}))#if no commander name need a name    
    else:
        await sendReadyToStart(websocket)
        await sendGameList(websocket)

async def applyUserName(websocket,data):    
    deviceId = data['deviceId']
    cU = list(filter(lambda user:user['deviceId'] == deviceId, users))
    cU[0]['userName'] = data['payload']['userName']
    await sendReadyToStart(websocket)
    await sendGameList(websocket)

async def sendReadyToStart(websocket):
    await websocket.send((dumps({'action':'readyToStart'})))

async def sendGameList(websocket):
    await websocket.send((dumps({'action':'sentGamesList', 'payload':games})))#if we have a commander name give a list of games

async def addNewGame(websocket, data):
    game = {
        'host':data['deviceId'],
        'players': [data['deviceId']],
        'id':str(uuid1()), 
        'connections':[data['connection']],
        'status':'waitingOnPlayer',
        'name':data['payload']['name']
    }
    games.append(game)
    await websocket.send((dumps({'action':'gameJoined', 'payload':game})))

#thisi s the main handler
async def handler(websocket, path):
    await newConnection(websocket)
    while True:
        data = await websocket.recv()
        data = loads(data)
        action = data['action']
        
        if action == 'sendDeviceId':
            await setupConnection(websocket,data)

        elif action == 'sendUserName':
            await applyUserName(websocket,data)
        
        elif action == 'createNewGame':
            await addNewGame(websocket, data)

start_server = serve(handler, '0.0.0.0', 5678)
get_event_loop().run_until_complete(start_server)
get_event_loop().run_forever()