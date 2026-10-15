"""Seed reference data for deployments using Prisma Client Python. Demo API state is self-contained."""
import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()
    circuit = await db.circuit.upsert(where={"name":"Circuit de Monaco"}, data={"create":{"name":"Circuit de Monaco","country":"Monaco","city":"Monte Carlo","lengthKm":3.337,"characteristics":{"overtaking":"very difficult","pitLossGreen":22,"pitLossSafetyCar":12.5}},"update":{}})
    teams = [("Ferrari","#E80020"),("McLaren","#FF8000"),("Mercedes","#27F4D2"),("Red Bull Racing","#3671C6"),("Aston Martin","#229971")]
    team_objs = {}
    for name,color in teams: team_objs[name] = await db.team.upsert(where={"name":name},data={"create":{"name":name,"color":color},"update":{"color":color}})
    drivers = [("LEC","Charles Leclerc","Ferrari"),("SAI","Carlos Sainz","Ferrari"),("NOR","Lando Norris","McLaren"),("PIA","Oscar Piastri","McLaren"),("HAM","Lewis Hamilton","Mercedes"),("RUS","George Russell","Mercedes"),("VER","Max Verstappen","Red Bull Racing"),("PER","Sergio Perez","Red Bull Racing"),("ALO","Fernando Alonso","Aston Martin"),("STR","Lance Stroll","Aston Martin")]
    for code,name,team in drivers: await db.driver.upsert(where={"code":code},data={"create":{"code":code,"name":name,"teamId":team_objs[team].id},"update":{"name":name,"teamId":team_objs[team].id}})
    for compound,pace,wear,wet in [("SOFT",-.35,1.55,1.7),("MEDIUM",0,1,1.4),("HARD",.28,.68,1.25),("INTERMEDIATE",1.3,.9,.35),("WET",3.8,.85,.15)]:
        await db.tirecompound.upsert(where={"name":compound},data={"create":{"name":compound,"paceDelta":pace,"wearFactor":wear,"wetPerformance":wet},"update":{"paceDelta":pace,"wearFactor":wear,"wetPerformance":wet}})
    race = await db.race.upsert(where={"slug":"monaco-2024"},data={"create":{"slug":"monaco-2024","name":"Monaco Grand Prix","year":2024,"totalLaps":53,"circuitId":circuit.id,"status":"RUNNING"},"update":{"totalLaps":53}})
    await db.racestate.create(data={"raceId":race.id,"lap":31,"trackStatus":"SAFETY_CAR","safetyCarActive":True,"positions":{"LEC":1,"PIA":2,"NOR":3},"gaps":{"ahead":2.1,"behind":4.7},"weather":{"rainProbability":.78,"rainEtaLaps":3,"trackTempC":31.5},"driverId":(await db.driver.find_unique(where={"code":"NOR"})).id})
    await db.weatherforecast.create(data={"raceId":race.id,"targetLap":34,"rainProbability":.78,"rainfallExpected":True,"expectedRainfallMm":.3,"source":"demo"})
    await db.racecontrolevent.create(data={"raceId":race.id,"lap":31,"type":"SAFETY_CAR","message":"Safety Car deployed","active":True})
    for key,name,action,compound in [("stay-out","Stay out","stay","MEDIUM"),("pit-now","Pit now","pit","MEDIUM"),("inter","Pit for Intermediates","pit","INTERMEDIATE"),("undercut","Undercut attempt","undercut","MEDIUM"),("overcut","Overcut attempt","overcut","MEDIUM")]:
        await db.strategyoption.upsert(where={"raceId_key":{"raceId":race.id,"key":key}},data={"create":{"raceId":race.id,"key":key,"name":name,"action":action,"compound":compound},"update":{"name":name,"action":action,"compound":compound}})
    await db.disconnect()

if __name__ == "__main__": asyncio.run(main())
