from interactions import Task, IntervalTrigger
import requests
import json
import datetime
import worksheets

@Task.create(IntervalTrigger(days=1))
async def update_worksheets():
    worksheets.load_worksheets()
    print("Updated worksheets at " + str(datetime.datetime.now()))