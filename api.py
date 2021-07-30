
from fastapi import FastAPI, BackgroundTasks
import time
from eventManager import Event
from resquest_test import Webhook
from db import RecorderDB,Recorder
from __GraphQL import *
from eventRun import NGlive
from log import logger
import subprocess

NGlive = NGlive()

def eventGo():
    logger.info("正在启动录播姬")
    from initial import RecorderPath,works_path,api_port
    cmd = f'{RecorderPath} run {works_path}  --bind http://127.0.0.1:{api_port}'
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,shell=True,encoding="gbk")
    logger.info("录播姬启动完毕")
    
    logger.info("正在初始化")
    NGlive.ListenerImport()
    NGlive.functionBlock()
    NGlive.tasksGo()
    logger.info("初始化成功")

app = FastAPI(on_startup=[eventGo])

def timetr(timestr):
    return time.mktime(time.strptime(timestr,'%Y-%m-%dT%H:%M:%S'))

def Event_Sender(Data: object):
    event = Event(type_=Data.EventType)
    event.dict["artical"] = Data
    NGlive.eventManager.SendEvent(event)
    EventData = Data.EventData

    with RecorderDB(Recorder) as f:
        f.add(
            EventId = Data.EventId, 
            SessionId = EventData.SessionId, 
            EventType = Data.EventType, 
            RoomId = EventData.RoomId, 
            ShortId = EventData.ShortId, 
            Name = EventData.Name, 
            Title = EventData.Title,
            RelativePath = EventData.RelativePath, 
            FileOpenTime = EventData.FileOpenTime, 
            FileCloseTime = EventData.FileCloseTime, 
            FileSize = EventData.FileSize, 
            Duration = EventData.Duration
        )


@app.post("/webhook/")
async def create_item(item: Webhook, background_tasks: BackgroundTasks):
    background_tasks.add_task(Event_Sender, item)
    return "ok"

@app.get("/addroom")
async def add_room(roomid:int):
    # 使用直播间号码 支持短号
    if roomid <= 0:
        return {"code":"4031","msg":"不正确的房间号"}
    allroominfo = getRooms()
    for room in allroominfo["data"]["rooms"]:
        objectId = room["objectId"]
        roomId = room["roomConfig"]["roomId"]
        shortId = room["shortId"]
        if roomId == roomid or shortId == roomid:
            return {"code":4032,"msg":"房间已经存在"}
    
    res = addRoom(roomid)
    res = refreshRoom(res["data"]["addRoom"]["roomConfig"]["roomId"],res["data"]["addRoom"]["objectId"])
    return {"code":0,"data":res["data"]["refreshRoomInfo"]}

@app.get("/removeroom")
async def remove_Room(roomid:int):
    # 查看这个房间号有没有在这里
    if roomid <= 0:
        return {"code":"4031","msg":"不正确的房间号"}
    allroominfo = getRooms()
    for room in allroominfo["data"]["rooms"]:
        recording = room["recording"]
        objectId = room["objectId"]
        roomId = room["roomConfig"]["roomId"]
        shortId = room["shortId"]
        if roomId == roomid or shortId == roomid:
            if recording:
                # 这个人人还在播，先给他掐了
                stopRecording(roomid,objectId)
            # 然后再移出录播列表
            res = removeRoom(roomid,objectId)
            return {"code":0,"data":res["data"]["removeRoom"]}
    return {"code":4042,"msg":"没有这个房间哦"}

@app.get("/allroom")
async def all_Room():
    res = getRooms()
    res["code"] = 0
    return res

@app.get("/getroom")
async def get_Room(roomid:int):
    # 查看这个房间号有没有在这里
    if roomid <= 0:
        return {"code":"4031","msg":"不正确的房间号"}
    allroominfo = getRooms()
    for room in allroominfo["data"]["rooms"]:
        roomId = room["roomConfig"]["roomId"]
        shortId = room["shortId"]
        if roomId == roomid or shortId == roomid:
            return {"code":0,"data":room}
    return {"code":4042,"msg":"没有这个房间哦"}



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app='api:app', host="127.0.0.1",
                port=8100, reload=True, debug=True)