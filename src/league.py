import json
import requests
import vars
from interactions import Embed, AllowedMentions
from requests.auth import HTTPBasicAuth
import datetime
from cairosvg import svg2png
import os

def get_json():
    json_file = {}
    with open(os.path.dirname(os.path.realpath(__file__))+'/league.json') as json_file:
        json_file = json.load(json_file)
        return json_file

async def start_league(ctx, league_name, challonge_link, maps):
    json_file = get_json()
    if (json_file["current_league"]["name"] != ""):
        await ctx.send("A league is already running. End it with /end_league", ephemeral=True)
        return
    
    id = challonge_link.split()[0].split("/")[-1]
    response = requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/participants.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'})
    if response.status_code != 200:
        await ctx.send("Error with Challonge API. Please try again later", ephemeral=True)
        return
    
    delay_token_dict = {}
    for team in response.json():
        delay_token_dict[team["participant"]["name"]] = 1

    json_file["current_league"] = {"name": league_name, "challonge_link": challonge_link, "map_pool": maps, "delay_tokens": delay_token_dict, "owner_guildid": ctx.guild.id}
    with open(os.path.dirname(os.path.realpath(__file__))+'/league.json', 'w',) as outfile:
        json.dump(json_file, outfile, indent=4)
        await ctx.send(league_name + " has been started!", ephemeral=True)

async def end_league(ctx, confirm):
    json_file = get_json()
    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return

    if confirm != "YES I AM SURE":
        await ctx.send("Please write `YES I AM SURE` as an argument to confirm", ephemeral=True)
        return
    
    previous_league = json_file["current_league"]["name"]
    
    json_file["previous_leagues"].append({"name": json_file["current_league"]["name"], "challonge_link": json_file["current_league"]["challonge_link"]})
    json_file["current_league"] = {"name": "", "challonge_link": "", "map_pool": [], "delay_tokens": {}, "owner_guildid": 0}
    with open(os.path.dirname(os.path.realpath(__file__))+'/league.json', 'w') as outfile:
        json.dump(json_file, outfile, indent=4)
        await ctx.send(previous_league + " has been ended!", ephemeral=True)

async def show_delay_tokens(ctx, ephemeral):
    json_file = get_json()

    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return

    tokens_text = ""
    for team_name in json_file["current_league"]["delay_tokens"].keys():
        if (json_file["current_league"]["delay_tokens"][team_name] == 0):
            tokens_text += ":x: " + team_name + "\n"
        else:
            tokens_text += ":coin: " + team_name + "\n"
            
    emb = Embed(title=json_file["current_league"]["name"] + " - Delay Tokens", description=tokens_text, color=0x3498db)
    await ctx.send(embed=emb,  ephemeral=ephemeral)

async def update_delay_tokens(ctx, team_name, action):
    json_file = get_json()
    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return

    if (action.lower() == "add"):
        json_file["current_league"]["delay_tokens"][team_name] = 1
    elif (action.lower() == "remove"):
        json_file["current_league"]["delay_tokens"][team_name] = 0
    
    with open(os.path.dirname(os.path.realpath(__file__))+'/league.json', 'w') as outfile:
        json.dump(json_file, outfile, indent=4)
    
    await show_delay_tokens(ctx, True)
    
async def get_challonge_link(ctx, league_name):
    json_file = get_json()
    url = ""
    if (league_name.lower() == json_file["current_league"]["name"].lower()):
        url = json_file["current_league"]["challonge_link"]
    else:
        for league in json_file["previous_leagues"]:
            if (league["name"].lower() == league_name.lower()):
                url = league["challonge_link"]
                break

    return url

async def get_challonge_image(ctx, league_name):
    url = await get_challonge_link(ctx, league_name)

    if (url == ""):
        await ctx.send(league_name + " has no challonge link", ephemeral=True)
        return
    
    await ctx.defer()
    url += ".svg"
    svg = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}).content
    svg2png(bytestring=svg,write_to='output.png', background_color="white", output_width=1920)
    await ctx.send(file='output.png')

async def get_post_when2meet(ctx, matches, startDate, endDate):
    json_file = get_json()
    roles = ctx.guild.roles
    text_to_send = ""
    for match in matches:
        role1 = match[0]
        role2 = match[1]
        for role in roles:
            if role.name == match[0]:
                role1 = role.mention
            if role.name == match[1]:
                role2 = role.mention

        post = {
            "MatchName": json_file["current_league"]["name"] + " - " + match[0] + " vs " + match[1], 
            "Team1Name": match[0], 
            "Team1RoleId": role1, 
            "Team2Name": match[1], 
            "Team2RoleId": role2, 
            "StartDate": startDate, 
            "EndDate": endDate,
            "DateTimeZone": "America/Los_Angeles"
        }
        header = {"Authorization" : "Basic " + vars.bloon_auth}
        response = requests.post('https://bloon.sparkedservers.us/api/v1/createMatch', json=post, headers=header)
        json_response = response.json()
        print (json_response)
        
        text_to_send += "\n"+role1+" vs "+role2+" \n" + json_response['matchUrl'] +"\n"
    return text_to_send

async def create_when2meet(ctx, matches_with_names, makeup_matches_with_names):
    json_file = get_json()

    today = datetime.date.today()
    friday = today + datetime.timedelta( (4-today.weekday()) % 7 )
    monday = friday + datetime.timedelta( (3-today.weekday()) % 7 )

    friday_text = friday.strftime("%d.%m.%Y.00.00")
    monday_text = monday.strftime("%d.%m.%Y.00.00")

    text_to_send = "**" + json_file["current_league"]["name"] + "**\n\nWhen2Meets:\n"

    text_to_send += await get_post_when2meet(ctx, matches_with_names, friday_text, monday_text)
    
    if (len(makeup_matches_with_names) > 0):
        text_to_send += "\nMakeup Matches:\n"
        text_to_send += await get_post_when2meet(ctx, makeup_matches_with_names, friday_text, monday_text)
    
    await ctx.send(text_to_send, ephemeral=True)

def get_last_played_round(matches_json):
    last_played_round = 0
    for match in matches_json:
        if (match["match"]["state"] == "complete" and match["match"]["forfeited"] == None and match["match"]["round"] > last_played_round):
            last_played_round = match["match"]["round"]
    return last_played_round

async def get_challonge_api(ctx, request):
    if request.status_code == 404:
            await ctx.send("Tournament doesn't exist or the bot does not have access to it", ephemeral=True)
            return
    if request.status_code != 200:
        await ctx.send("Error with Challonge API. Please try again later", ephemeral=True)
        return
    return request.json()

def get_match_names_from_ids(match, participants_json):
    player1 = ""
    player2 = ""
    for participant in participants_json:
        if (participant["participant"]["group_player_ids"][0] == match[0] or participant["participant"]["id"] == match[0]):
            player1 = participant["participant"]["name"]
        if (participant["participant"]["group_player_ids"][0] == match[1] or participant["participant"]["id"] == match[1]):
            player2 = participant["participant"]["name"]
    return player1, player2

async def when2meet(ctx):
    json_file = get_json()

    await ctx.defer(ephemeral=True)

    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return
    
    matches_with_ids = []
    makeup_matches_with_ids = []

    id = json_file["current_league"]["challonge_link"].split()[0].split("/")[-1]

    matches_json = await get_challonge_api(ctx, requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/matches.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}))
    if matches_json == None:
        return False

    last_played_round = get_last_played_round(matches_json)

    for match in matches_json:
        if (match["match"]["state"] == "open" and (match["match"]["round"] == last_played_round+1 or match["match"]["group_id"] == None)):
            matches_with_ids.append([match["match"]["player1_id"], match["match"]["player2_id"]])
        elif (match["match"]["state"] == "open" and match["match"]["round"] < last_played_round+1):
            makeup_matches_with_ids.append([match["match"]["player1_id"], match["match"]["player2_id"]])

    participants_json = await get_challonge_api(ctx, requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/participants.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}))

    matches_with_names = []
    makeup_matches_with_names = []

    for match in matches_with_ids:
        player1, player2 = get_match_names_from_ids(match, participants_json)
        if (player1 != "" and player2 != ""):
            matches_with_names.append([player1, player2])

    for match in makeup_matches_with_ids:
        player1, player2 = get_match_names_from_ids(match, participants_json)
        if (player1 != "" and player2 != ""):
            makeup_matches_with_names.append([player1, player2])

    await create_when2meet(ctx, matches_with_names, makeup_matches_with_names)

def get_participant_id(participant, is_group_stage):
    if (is_group_stage):
        return participant["participant"]["group_player_ids"][0]
    else:
        return participant["participant"]["id"]
    


async def report_scoreboard(ctx, stage, guards, intruders, map, scoreboard):
    await ctx.defer(ephemeral=True)

    json_file = get_json()

    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return

    if (not scoreboard.content_type.startswith("image")):
        await ctx.send("File is not an image\nIt is " + scoreboard.content_type, ephemeral=True)
        return False

    if (ctx.guild.id != json_file["current_league"]["owner_guildid"]):
        await ctx.send("No League is running", ephemeral=True)
        return 0

    id = json_file["current_league"]["challonge_link"].split()[0].split("/")[-1]

    if stage == "Lower Bracket":
        id += "_Lower"

    

    matches_json = await get_challonge_api(ctx, requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/matches.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}))
    if matches_json == None:
        return False

    participants_json = await get_challonge_api(ctx, requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/participants.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}))

    guards_id = 0
    intruders_id = 0
    for participant in participants_json:
        if (participant["participant"]["name"].lower() == guards.lower()):
            guards_id = get_participant_id(participant, (stage == "Group Stage"))
        
        if (participant["participant"]["name"].lower() == intruders.lower()):
            intruders_id = get_participant_id(participant, (stage == "Group Stage"))

    if (guards_id == 0 or intruders_id == 0):
        await ctx.send("The selected team names do not exist in this tournament", ephemeral=True)
        return False

    match_id = None
    for match in matches_json:
        if (match["match"]["state"] != "open"):
            continue
        if ((match["match"]["player1_id"] == guards_id and match["match"]["player2_id"] == intruders_id) or (match["match"]["player1_id"] == intruders_id and match["match"]["player2_id"] == guards_id)):
            match_id = match["match"]["id"]

    if match_id == None:
        await ctx.send("No available matches between those teams were found.\nMaybe you chose the wrong Stage or maybe the scoreboard of this match has already been reported\n\nIf you think the bot is wrong, report the match scoreboard without using the bot", ephemeral=True)
        return False

    post_response = requests.post('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/matches/'+str(match_id)+'/attachments.json', json={'url':scoreboard.proxy_url, 'description': 'Water:'+guards.upper()+" | Fire:"+intruders.upper() + " | Map: " + map}, headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'})
    if post_response.status_code != 200:
        await ctx.send("Attachment creation failed. Challonge error", ephemeral=True)
        return False

    await ctx.send("Scoreboard submitted and referenced in <#" + str(vars.guilds[ctx.guild.id]['results_channel']) + ">")
    return True











async def submit_video(ctx, stage, guards, intruders, link):
    await ctx.defer(ephemeral=True)

    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return

    json_file = get_json()

    if (ctx.guild.id != json_file["current_league"]["owner_guildid"]):
        await ctx.send("No League is running", ephemeral=True)
        return False

    id = json_file["current_league"]["challonge_link"].split()[0].split("/")[-1]

    if stage == "Lower Bracket":
        id += "_Lower"

    matches_json = await get_challonge_api(ctx, requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/matches.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}))
    if matches_json == None:
        return False

    participants_json = await get_challonge_api(ctx, requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/participants.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}))

    guards_id = 0
    intruders_id = 0
    for participant in participants_json:
        if (participant["participant"]["name"].lower() == guards.lower()):
            guards_id = get_participant_id(participant, (stage == "Group Stage"))
        
        if (participant["participant"]["name"].lower() == intruders.lower()):
            intruders_id = get_participant_id(participant, (stage == "Group Stage"))

    if ((guards_id == 0 or intruders_id == 0)):
        await ctx.send("The selected team names do not exist in this tournament", ephemeral=True)
        return False

    post_response = None
    for match in reversed(matches_json):
        if ((match["match"]["state"] != "open") and (match["match"]["state"] != "complete")):
            continue
        if ((match["match"]["player1_id"] == guards_id and match["match"]["player2_id"] == intruders_id) or (match["match"]["player1_id"] == intruders_id and match["match"]["player2_id"] == guards_id)):
            post_response = requests.post('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/matches/'+str(match["match"]["id"])+'/attachments.json', json={'url':link, 'description': 'VIDEO'}, headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'})
            if post_response.status_code != 200:
                await ctx.send("Video submission failed. Challonge error", ephemeral=True)
                return False
            break

    if post_response == None:
        await ctx.send("No available matches between those teams were found.\nMaybe you chose the wrong Stage or maybe the match isnt available yet.", ephemeral=True)
        return False

    await ctx.send("Video submitted and referenced in <#" + str(vars.guilds[ctx.guild.id]['picsnvids_channel']) + ">")
    return True