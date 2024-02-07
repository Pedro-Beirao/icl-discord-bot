import interactions
from interactions import AutocompleteContext, Permissions, StringSelectMenu, Embed, slash_default_member_permission, slash_command, Intents, OptionType, slash_option, File, Button, ButtonStyle, listen, SlashCommandChoice
from interactions.api.events import Component, Error
import requests
import os
import io
import worksheets
import tasks
import league
import vars
import random
import re

intents=Intents.DEFAULT
bot = interactions.Client(intents=intents, send_command_tracebacks=False)

currentDir = os.path.dirname(os.path.realpath(__file__))
print(currentDir)

@listen()
async def on_startup(): 
    print("Bot is running")

@listen()
async def on_error(error: Error):
    if (vars.error_logs_channel == 0):
        return
    await bot.get_channel(vars.error_logs_channel).send(error.source)


async def check_admin(ctx):
    try:
        if ctx.author.id in vars.guilds[ctx.guild.id]['admins']:
            json_file = league.get_json()
            if (json_file["current_league"]["owner_guildid"] != 0) and (ctx.guild.id != json_file["current_league"]["owner_guildid"]):
                await ctx.send("A league is already running in " + bot.get_guild(json_file["current_league"]["owner_guildid"]).name + "\n\nAdmins actions are disabled until that league ends.", ephemeral=True)
                return False
            return True
    except: pass
    await ctx.send("You do not have permission to do that", ephemeral=True)
    return False

async def check_channel(ctx, channel_type):
    try:
        compare = []
        error_message = "You do not have permission to do that in this channel\n"

        if channel_type == "competitive":
            compare = vars.guilds[ctx.guild.id]['competitive_channel']
            error_message += "Use the command in <#"+str(compare)+">"
        elif channel_type == "commands":
            compare = vars.guilds[ctx.guild.id]['commands_channel']
            error_message += "Use the command in <#"+str(compare)+">"
        elif channel_type == "results":
            compare = vars.guilds[ctx.guild.id]['results_channel']
            error_message += "Use the command in <#"+str(compare)+">"
        elif channel_type == "picsnvids":
            compare = vars.guilds[ctx.guild.id]['picsnvids_channel']
            error_message += "Use the command in <#"+str(compare)+">"

        if (ctx.channel.id == compare):
            return True
        
        if ctx.author.id in vars.guilds[ctx.guild.id]['admins']:
            json_file = league.get_json()
            if (json_file["current_league"]["owner_guildid"] != 0) and (ctx.guild.id != json_file["current_league"]["owner_guildid"]):
                await ctx.send("A league is already running in " + bot.get_guild(json_file["current_league"]["owner_guildid"]).name + "\n\nAdmins actions are disabled until that league ends.", ephemeral=True)
            else:
                return True
    except: pass
    await ctx.send(error_message, ephemeral=True)
    return False

def interpolate(f_co, t_co, interval):
    det_co =[(t - f) / interval for f , t in zip(f_co, t_co)]
    for i in range(interval):
        yield [round(f + det * i) for f, det in zip(f_co, det_co)]

@slash_command(name="help", description="Documents every command", scopes=vars.guilds.keys())
async def help(ctx):
    emb = Embed(title="Help", description="**Everywhere**\n"
                                          "> /help - Shows this prompt\n"
                                          "> /rules - Links the ICL rulebook\n"
                                          "> /challonge_link - Displays the challonge link of the selected league\n"
                                          "> /report_scoreboard - Reports the scoreboard of a match to Challonge\n"
                                          "> /submit_video - Submits a video recording of a match to Challonge\n"
                                          , color=0x3498db)
    emb.add_field(name="\u200B\n<#"+str(vars.guilds[ctx.guild.id]["competitive_channel"])+">", value="> /map_banning - Handles the map banning process\n"
                                                        "** **\n"
                                                     , inline=False)
    emb.add_field(name="\u200B\n<#"+str(vars.guilds[ctx.guild.id]["commands_channel"])+">", value="> /challonge_image - Displays a live image of the selected league\n"
                                          "> /show_delay_tokens - Displays the delay tokens each team has on the current league\n"
                                          "> /match_score - Displays the scores of all matches between two teams\n"
                                          , inline=False)
    try: 
        if ctx.author.id in vars.guilds[ctx.guild.id]['admins']:
            emb.add_field(name="\u200B\nAdmin Only", value="> /start_league - Starts a league (needs a map pool to be provided + challonge link)\n"
                                                "> /end_league - Ends a league\n"
                                                "> /update_delay_tokens - Adds or removes a delay token from a team\n"
                                                "> /when2meet - Creates and shows https://crab.fit links\n"
                                                , inline=False)
    except: pass
    await ctx.send(embed = emb, ephemeral=True)

@slash_command(name="match_score", description="Get the scores of all matches between two teams", scopes=vars.guilds.keys())
@slash_option(name="league", description="ICL7, ICL8, Scrim, etc", opt_type=OptionType.STRING, required=True, autocomplete=True)
@slash_option(name="team1", description="Team 1", opt_type=OptionType.STRING, required=True)
@slash_option(name="team2", description="Team 2", opt_type=OptionType.STRING, required=True)
async def get_scores_teams(ctx, league, team1, team2):
        if await check_channel(ctx, "commands"):
            es = []
            fs = []

            curEmbed = 0

            if (league == "any"):
                for l in worksheets.leagues:
                    if l == "any": continue
                    e, f = worksheets.get_scores_teams_aux(l, team1, team2)
                    es += e
                    fs += f
            else:
                e, f = worksheets.get_scores_teams_aux(league, team1, team2)
                es += e
                fs += f

            if (len(es) > 1):
                buttons = [Button(style=ButtonStyle.BLUE, label="Previous", custom_id="prev", disabled=True), Button(style=ButtonStyle.BLUE, label="Next", custom_id="next")]

                async def check_get_scores_teams(component: Component) -> bool:
                    nonlocal curEmbed
                    if (component.ctx.custom_id == "next"):
                        curEmbed += 1
                        if (curEmbed == len(es)-1): buttons[1].disabled = True
                        buttons[0].disabled = False
                    elif (component.ctx.custom_id == "prev"):
                        curEmbed -= 1
                        if (curEmbed == 0): buttons[0].disabled = True
                        buttons[1].disabled = False
                    
                    buffer = io.BytesIO()
                    fs[curEmbed][1].save(buffer, format='PNG')
                    buffer.seek(0) 
                    f = File(buffer, fs[curEmbed][0])
                    await component.ctx.edit_origin(embed = es[curEmbed], file=f, components=buttons)
                    return True
                

                buffer = io.BytesIO()
                fs[curEmbed][1].save(buffer, format='PNG')
                buffer.seek(0) 
                f = File(buffer, fs[curEmbed][0])
                message = await ctx.send(embed = es[curEmbed], file=f, components=buttons)
                while (True):
                    try:
                        await bot.wait_for_component(components=buttons, check=check_get_scores_teams, timeout=60)
                    except:
                        await message.edit(components=[])
                        return
            elif (len(es) == 1):
                buffer = io.BytesIO()
                fs[0][1].save(buffer, format='PNG')
                buffer.seek(0) 
                f = File(buffer, fs[0][0])
                await ctx.send(embed = es[0], file=f)
            else:
                await ctx.send("No matches found", ephemeral=True)

@get_scores_teams.autocomplete("league")
async def autocomplete(ctx):
    await ctx.send(choices=worksheets.leagues)

@slash_command(name="start_league", description="Setups and starts a league", scopes=vars.guilds.keys())
@slash_default_member_permission(Permissions.MANAGE_ROLES)
@slash_option(name="league_name", description="Name of the league", opt_type=OptionType.STRING, required=True)
@slash_option(name="challonge_link", description="Link to the Challonge tournament", opt_type=OptionType.STRING, required=True)
@slash_option(name="map_pool", description="Map pool for the tournament. Separate maps with ,", opt_type=OptionType.STRING, required=True)
async def start_league(ctx, league_name, challonge_link, map_pool):
    if await check_admin(ctx):
        map_pool = map_pool.replace("\\", "\\\\")
        maps = map_pool.split(",")
        for m in range(len(maps)):
            maps[m] = maps[m].strip()
        await league.start_league(ctx, league_name, challonge_link, maps)

@slash_command(name="end_league", description="Ends a league", scopes=vars.guilds.keys())
@slash_default_member_permission(Permissions.MANAGE_ROLES)
@slash_option(name="confirm", description="ARE YOU SURE?", opt_type=OptionType.STRING, required=True)
async def end_league(ctx, confirm="NO"):
    if await check_admin(ctx):
        await league.end_league(ctx, confirm)

@slash_command(name="show_delay_tokens", description="Prints the delay tokens each team has", scopes=vars.guilds.keys())
async def show_delay_tokens(ctx):
    if await check_channel(ctx, "commands"):
        await league.show_delay_tokens(ctx, False)

@slash_command(name="update_delay_tokens", description="Removes or Adds a delay token to a team", scopes=vars.guilds.keys())
@slash_default_member_permission(Permissions.MANAGE_ROLES)
@slash_option(name="team_name", description="Name of the team", opt_type=OptionType.STRING, required=True)
@slash_option(name="action", description="Which action to perform", opt_type=OptionType.STRING, required=True, choices=[SlashCommandChoice(name="remove", value="remove"),SlashCommandChoice(name="add", value="add")])
async def update_delay_tokens(ctx, team_name, action):
    if await check_admin(ctx):
        await league.update_delay_tokens(ctx, team_name, action)

@slash_command(name="when2meet", description="Creates and shows https://crab.fit links", scopes=vars.guilds.keys())
@slash_default_member_permission(Permissions.MANAGE_ROLES)
@slash_option(name="confirm", description="This will ping multiple users and create w2m links", opt_type=OptionType.STRING, required=True)
async def when2meet(ctx, confirm):
    if await check_admin(ctx):
        if (confirm != "YES I AM SURE"):
            await ctx.send("Write `YES I AM SURE` as an argument to confirm\n\n(This is just a confirmation so that we don't create crab.fit links accidentaly)", ephemeral=True)
            return
        await league.when2meet(ctx)

def get_all_league_names():
    json_file = league.get_json()
    ls = []
    ls += worksheets.leagues
    if json_file["current_league"]["name"] != "":
        ls.insert(0, SlashCommandChoice(name=json_file["current_league"]["name"], value=json_file["current_league"]["name"]))
    return ls

def get_challonge_league_names():
    json_file = league.get_json()
    ls = []
    if json_file["current_league"]["name"] != "":
        ls = [{'name':json_file["current_league"]["name"], 'value':json_file["current_league"]["name"]}]
    
    for l in json_file["previous_leagues"]:
        if (l["challonge_link"] != ""):
            ls.insert(1, {'name':l["name"], 'value':l["name"]})
    return ls

@slash_command(name="challonge_link", description="Prints the link of the Challong tournament", scopes=vars.guilds.keys())
@slash_option(name="league_name", description="ICL7, ICL8, Scrim, etc", opt_type=OptionType.STRING, required=True, autocomplete=True)
async def challonge_link(ctx, league_name):
    url = await league.get_challonge_link(ctx, league_name)

    if (url == ""):
        await ctx.send(league_name + " has no challonge link", ephemeral=True)
    else:
        await ctx.send(url, ephemeral=True)

@slash_command(name="challonge_image", description="Display a Live image of a Challonge tournament", scopes=vars.guilds.keys())
@slash_option(name="league_name", description="ICL7, ICL8, Scrim, etc", opt_type=OptionType.STRING, required=True, autocomplete=True)
async def challonge_image(ctx, league_name):
    if await check_channel(ctx, "commands"):
        await league.get_challonge_image(ctx, league_name)
        
@challonge_link.autocomplete("league_name")
async def autocomplete(ctx):
    await ctx.send(choices=get_challonge_league_names())

@challonge_image.autocomplete("league_name")
async def autocomplete(ctx):
    await ctx.send(choices=get_challonge_league_names())

msg_map_banning = None

@slash_command(name="map_banning", description="Handles the map banning process", scopes=vars.guilds.keys())
@slash_option(name="captain_water", description="Who's the captain of team Water?", opt_type=OptionType.USER, required=True)
@slash_option(name="captain_fire", description="Who's the captain of team Fire?", opt_type=OptionType.USER, required=True)
async def map_banning(ctx, captain_water, captain_fire):
    global msg_map_banning
    if await check_channel(ctx, "competitive"):
        json_file = league.get_json()
        maps = json_file["current_league"]["map_pool"]
        maps_str = ""
        maps_available = len(maps)

        if maps_available == 0:
            await ctx.send("No league is currently running", ephemeral=True)
            return

        for i in range(len(maps)):
            maps_str += maps[i] + "\n"

        captain_to_pick = random.choice([True, False]) #True = water, False = fire

        emb = Embed(title="Map Ban", description=(captain_water.mention if captain_to_pick else captain_fire.mention) + "'s ban\n\n" + maps_str, color=0x3498db)

        buttons = [StringSelectMenu(
                    maps,
                    placeholder="What map to ban?",
                    min_values=1,
                    max_values=1,
                )]
        async def ban_map(component: Component) -> bool:
                nonlocal emb
                nonlocal maps
                nonlocal maps_str
                nonlocal maps_available
                nonlocal buttons
                nonlocal captain_to_pick

                if captain_to_pick and component.ctx.author.id != captain_water.id:
                    await component.ctx.send("You are not the captain of team Water", ephemeral=True)
                    return False
                if not captain_to_pick and component.ctx.author.id != captain_fire.id:
                    await component.ctx.send("You are not the captain of team Fire", ephemeral=True)
                    return False
                
                for m in range(len(maps)):
                    if (component.ctx.values[0] == maps[m]):
                        maps.pop(m)
                        maps_str = ""
                        for i in range(len(maps)):
                            maps_str += maps[i] + "\n"
                        captain_to_pick = not captain_to_pick
                        desc = (captain_water.mention if captain_to_pick else captain_fire.mention) + "'s ban\n\n" + maps_str
                        maps_available-=1
                        if maps_available == 1:
                            desc = maps_str
                        emb = Embed(title="Map Ban", description=desc, color=0x3498db)
                        break

                buttons = [StringSelectMenu(
                    maps,
                    placeholder="What map to ban?",
                    min_values=1,
                    max_values=1,
                )]
                
                if (maps_available == 1):
                    await component.ctx.edit_origin(embed=emb, components=[])
                    return False
                
                await component.ctx.edit_origin(embed=emb, components=buttons)
                return True
        
        msg_map_banning = await ctx.send(embed=emb, components=buttons)
        while (True):
                try:
                    await bot.wait_for_component(components=buttons, check=ban_map, timeout=300)
                except:
                    await msg_map_banning.edit(components=[])
                    return
            

@slash_command(name="report_scoreboard", description="Attaches the scoreboard on challonge", scopes=vars.guilds.keys())
@slash_option(name="guards", description="Team that started as guards", opt_type=OptionType.STRING, required=True)
@slash_option(name="intruders", description="Team that started as intruders", opt_type=OptionType.STRING, required=True)
@slash_option(name="map", description="Map where the match was played", opt_type=OptionType.STRING, required=True, autocomplete=True)
@slash_option(name="scoreboard", description="Screenshot with the scoreboard", opt_type=OptionType.ATTACHMENT, required=True)
async def report_scoreboard(ctx, guards, intruders, map, scoreboard):
    if await league.report_scoreboard(ctx, guards, intruders, map, scoreboard, False):
         await bot.get_channel(vars.guilds[ctx.guild.id]['results_channel']).send("Submitted by: <@" + str(ctx.author.id) + ">\n\nWater: " + guards.upper() + "\nFire: " + intruders.upper() + "\n\n" + scoreboard.proxy_url)

@report_scoreboard.autocomplete("map")
async def autocomplete(ctx):
    json_file = league.get_json()
    ls = []
    for l in json_file["current_league"]["map_pool"]:
        stripped = re.sub('[^A-Za-z0-9\']+', ' ', l).strip()
        ls.insert(1, {'name':l, 'value':stripped})

    await ctx.send(choices=ls)

@slash_command(name="submit_video", description="Attaches a video recording of a match on challonge", scopes=vars.guilds.keys())
@slash_option(name="guards", description="Team that started as guards", opt_type=OptionType.STRING, required=True)
@slash_option(name="intruders", description="Team that started as intruders", opt_type=OptionType.STRING, required=True)
@slash_option(name="link", description="Video link", opt_type=OptionType.STRING, required=True)
async def submit_video(ctx, guards, intruders, link):
    if await league.submit_video(ctx, guards, intruders, link, True):
        await bot.get_channel(vars.guilds[ctx.guild.id]['picsnvids_channel']).send("Submitted by: <@" + str(ctx.author.id) + ">\n\n" + guards.upper() + " vs " + intruders.upper() + "\n\n" + link)

@slash_command(name="rules", description="Links the ICL rulebook", scopes=vars.guilds.keys())
async def rules(ctx):
    await ctx.send("https://bit.ly/ICL_Rulebook", ephemeral=True)

bot.start(vars.bot_token)
