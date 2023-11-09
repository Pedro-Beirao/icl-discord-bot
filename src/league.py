import json
import requests
import vars
from interactions import Embed, AllowedMentions
import datetime
from cairosvg import svg2png

def get_json():
    json_file = {}
    with open('league.json') as json_file:
        json_file = json.load(json_file)
        return json_file

async def start_league(ctx, league_name, challonge_link, maps):
    json_file = get_json()
    if (json_file["current_league"]["name"] != ""):
        await ctx.send("A league is already running. End it with /end_league", hidden=True)
        return
    
    id = challonge_link.split()[0].split("/")[-1]
    response = requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/participants.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'})
    if response.status_code != 200:
        await ctx.send("Error with Challonge API. Please try again later", ephemeral=True)
        return
    
    delay_token_dict = {}
    for team in response.json():
        delay_token_dict[team["participant"]["name"]] = 1

    json_file["current_league"] = {"name": league_name, "challonge_link": challonge_link, "map_pool": maps, "delay_tokens": delay_token_dict}
    with open('league.json', 'w',) as outfile:
        json.dump(json_file, outfile, indent=4)
        await ctx.send(league_name + " had been started!")

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
    json_file["current_league"] = {"name": "", "challonge_link": "", "map_pool": [], "delay_tokens": {}}
    with open('league.json', 'w') as outfile:
        json.dump(json_file, outfile, indent=4)
        await ctx.send(previous_league + " has been ended!")

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
    
    with open('league.json', 'w') as outfile:
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
    await ctx.defer()

    url = await get_challonge_link(ctx, league_name)

    if (url == ""):
        await ctx.send(league_name + " has no challonge link", ephemeral=True)
        return
    url += ".svg"
    svg = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'}).content
    svg2png(bytestring=svg,write_to='output.png', background_color="white", output_width=1920)
    await ctx.send(file='output.png')

async def get_post_when2meet(ctx, matches, times):
    json_file = get_json()
    roles = ctx.guild.roles
    text_to_send = ""
    for match in matches:
        post = {
            "name": json_file["current_league"]["name"] + " - " + match[0] + " vs " + match[1],
            "times": times,
            "timezone": "US/Arizona"
        }
        response = requests.post('https://api.crab.fit/event', json=post)
        json_response = response.json()
        print ("https://crab.fit/" + json_response["id"])

        role1 = match[0]
        role2 = match[1]
        for role in roles:
            if role.name == match[0]:
                role1 = role.mention
            if role.name == match[1]:
                role2 = role.mention
        
        text_to_send += "\n"+role1+" vs "+role2+"\n<<https://crab.fit/" + json_response["id"] +">>\n"
    return text_to_send

async def create_when2meet(ctx, matches_with_names, makeup_matches_with_names):
    json_file = get_json()

    today = datetime.date.today()
    friday = f'{(today + datetime.timedelta( (4-today.weekday()) % 7 )):%d%m%Y}'
    saturday = str(int(friday)+1000000)
    sunday = str(int(friday)+2000000)
    monday = str(int(friday)+3000000)

    times = [
        "0700-"+friday,
        "0800-"+friday,
        "0900-"+friday,
        "1000-"+friday,
        "1100-"+friday,
        "1200-"+friday,
        "1300-"+friday,
        "1400-"+friday,
        "1500-"+friday,
        "1600-"+friday,
        "1700-"+friday,
        "1800-"+friday,
        "1900-"+friday,
        "2000-"+friday,
        "2100-"+friday,
        "2200-"+friday,
        "2300-"+friday,
        "0000-"+saturday,
        "0100-"+saturday,
        "0200-"+saturday,
        "0300-"+saturday,
        "0400-"+saturday,
        "0500-"+saturday,
        "0600-"+saturday,
        "0700-"+saturday,
        "0800-"+saturday,
        "0900-"+saturday,
        "1000-"+saturday,
        "1100-"+saturday,
        "1200-"+saturday,
        "1300-"+saturday,
        "1400-"+saturday,
        "1500-"+saturday,
        "1600-"+saturday,
        "1700-"+saturday,
        "1800-"+saturday,
        "1900-"+saturday,
        "2000-"+saturday,
        "2100-"+saturday,
        "2200-"+saturday,
        "2300-"+saturday,
        "0000-"+sunday,
        "0100-"+sunday,
        "0200-"+sunday,
        "0300-"+sunday,
        "0400-"+sunday,
        "0500-"+sunday,
        "0600-"+sunday,
        "0700-"+sunday,
        "0800-"+sunday,
        "0900-"+sunday,
        "1000-"+sunday,
        "1100-"+sunday,
        "1200-"+sunday,
        "1300-"+sunday,
        "1400-"+sunday,
        "1500-"+sunday,
        "1600-"+sunday,
        "1700-"+sunday,
        "1800-"+sunday,
        "1900-"+sunday,
        "2000-"+sunday,
        "2100-"+sunday,
        "2200-"+sunday,
        "2300-"+sunday,
        "0000-"+monday,
        "0100-"+monday,
        "0200-"+monday,
        "0300-"+monday,
        "0400-"+monday,
        "0500-"+monday,
        "0600-"+monday
    ]
    text_to_send = "**" + json_file["current_league"]["name"] + "**\n\nWhen2Meets:\n"

    text_to_send += await get_post_when2meet(ctx, matches_with_names, times)
    
    if (len(makeup_matches_with_names) > 0):
        text_to_send += "\nMakeup Matches:\n"
        text_to_send += await get_post_when2meet(ctx, makeup_matches_with_names, times)
    
    await ctx.send(text_to_send, allowed_mentions=AllowedMentions(roles=ctx.guild.roles), ephemeral=True)
        

async def when2meet(ctx):
    json_file = get_json()

    await ctx.defer(ephemeral=True)

    if (json_file["current_league"]["name"] == ""):
        await ctx.send("No league is currently running", ephemeral=True)
        return
    
    matches_with_ids = []
    makeup_matches_with_ids = []

    id = json_file["current_league"]["challonge_link"].split()[0].split("/")[-1]
    matches_response = requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/matches.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'})
    if matches_response.status_code != 200:
        await ctx.send("Error with Challonge API. Please try again laterb", ephemeral=True)
        return
    matches_json_response = matches_response.json()

    last_played_round = 0
    for match in matches_json_response:
        if (match["match"]["state"] == "complete" and match["match"]["round"] > last_played_round):
            last_played_round = match["match"]["round"]

    for match in matches_json_response:
        if (match["match"]["state"] == "open" and (match["match"]["round"] == last_played_round+1 or match["match"]["group_id"] == None)):
            matches_with_ids.append([match["match"]["player1_id"], match["match"]["player2_id"]])
        elif (match["match"]["state"] == "open" and match["match"]["round"] < last_played_round+1):
            makeup_matches_with_ids.append([match["match"]["player1_id"], match["match"]["player2_id"]])

    participants_response = requests.get('https://'+vars.challonge_username+':'+vars.challonge_api_key+'@api.challonge.com/v1/tournaments/'+id+'/participants.json', headers={'User-Agent': 'Mozilla/5.0 (Platform; Security; OS-or-CPU; Localization; rv:1.4) Gecko/20030624 Netscape/7.1 (ax)'})
    if participants_response.status_code != 200:
        await ctx.send("Error with Challonge API. Please try again later", ephemeral=True)
        return
    participants_json_response = participants_response.json()

    matches_with_names = []
    makeup_matches_with_names = []

    for match in matches_with_ids:
        player1 = ""
        player2 = ""
        for participant in participants_json_response:
            if (participant["participant"]["group_player_ids"][0] == match[0] or participant["participant"]["id"] == match[0]):
                player1 = participant["participant"]["name"]
            if (participant["participant"]["group_player_ids"][0] == match[1] or participant["participant"]["id"] == match[1]):
                player2 = participant["participant"]["name"]
        if (player1 != "" and player2 != ""):
            matches_with_names.append([player1, player2])

    for match in makeup_matches_with_ids:
        player1 = ""
        player2 = ""
        for participant in participants_json_response:
            if (participant["participant"]["group_player_ids"][0] == match[0] or participant["participant"]["id"] == match[0]):
                player1 = participant["participant"]["name"]
            if (participant["participant"]["group_player_ids"][0] == match[1] or participant["participant"]["id"] == match[1]):
                player2 = participant["participant"]["name"]
        if (player1 != "" and player2 != ""):
            makeup_matches_with_names.append([player1, player2])

    await create_when2meet(ctx, matches_with_names, makeup_matches_with_names)
