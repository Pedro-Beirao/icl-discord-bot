
from interactions import Embed, SlashCommandChoice
import random
import gspread
from PIL import Image, ImageDraw, ImageFont

gc = gspread.service_account()
workbook = gc.open_by_url("https://docs.google.com/spreadsheets/d/1UAyF4hEJ6XJz5VVdvXud4kYtNmB4kn0siHBMlbmpxUc")

leagues = []
sheets = {}

def load_worksheets():
    global leagues
    global sheets

    for w in workbook.worksheets():
        if (w.title.endswith("Info")):
            leagues.append(SlashCommandChoice(name=w.title[:-5], value=w.title[:-5]))

    for l in leagues:
        sheets[str(l.name)] = {"info": workbook.worksheet(str(l.name)+" Info"), "teams": workbook.worksheet(str(l.name)+" Teams"), "scores": workbook.worksheet(str(l.name)+" Scores")}

    leagues.append(SlashCommandChoice(name="any", value="any"))

load_worksheets()

def interpolate(f_co, t_co, interval):
    det_co =[(t - f) / interval for f , t in zip(f_co, t_co)]
    for i in range(interval):
        yield [round(f + det * i) for f, det in zip(f_co, det_co)]

def get_scores_teams_aux(league, team1, team2):
    es = []
    fs = []
        
    sheet_scores = sheets[league]["scores"].get_values(major_dimension="COLUMNS", value_render_option="UNFORMATTED_VALUE")

    for i in range(0, len(sheet_scores[0]), 4):
        if (sheet_scores[0][i+1].upper() == team1.upper() and sheet_scores[0][i+2].upper() == team2.upper()) or (sheet_scores[0][i+1].upper() == team2.upper() and sheet_scores[0][i+2].upper() == team1.upper()):
            
            emb = Embed(title=league, description="", color=0x3498db)
            emb.add_field(name=sheet_scores[0][i] + " - " + sheet_scores[1][i], value="Map: " + sheet_scores[2][i], inline=False)

            t1 = sheet_scores[0][i+1]
            t2  = sheet_scores[0][i+2]

            
            image = Image.new('RGB', (270, 100))

            draw = ImageDraw.Draw(image, 'RGBA')

            f_co = (0, 0, 0)
            t_co = (0, 0, 0)

            colors = [
                [[53, 53, 53], (105, 105, 105)]
            ]

            choice = random.choice(colors)
            f_co = choice[0]
            t_co = choice[1]

            for e, color in enumerate(interpolate(f_co, t_co, image.width * 2)):
                draw.line([(0, e), (e, 0)], tuple(color), width=1)

            draw.polygon([(10, 25), (120, 25), (120, 10), (260, 10), (260, 90), (10, 90)], fill=(100,100,100,75), outline=(255,255,255,100)) # main polygon
            draw.rectangle([121, 26, 164, 89], fill=(78, 67, 72, 120)) # dark
            draw.rectangle([166, 11, 209, 24], fill=(78, 67, 72, 120)) # dark
            draw.rectangle([211, 26, 259, 89], fill=(78, 67, 72, 120)) # dark


            font = ImageFont.truetype('Arial.ttf', 15)
            font_small = ImageFont.truetype('Arial.ttf', 9)

            draw.text( (30, 34), t1, fill=(255, 255, 255), font=font) # team 1
            draw.text( (30, 66), t2, fill=(255, 255, 255), font=font) # team 2
            draw.text( (130, 13), "SET 1", font=font_small) # set 1
            draw.text( (175, 13), "SET 2", font=font_small) # set 2
            draw.text( (214, 13), "TIEBREAK", font=font_small) # set 3
            draw.text( (138, 34), str(sheet_scores[1][i+1]), font=font) # score team 1 set 1
            draw.text( (138, 66), str(sheet_scores[1][i+2]), font=font) # score team 2 set 1
            
            if (sheet_scores[3][i+1] == 0 and sheet_scores[3][i+2] == 0): # no tiebreaker
                if (sheet_scores[2][i+1] > sheet_scores[2][i+2]): # team 1 won
                    draw.text( (183, 34), str(sheet_scores[2][i+1]), font=font, fill=(0,255,0)) # score team 1 set 2
                    draw.text( (183, 66), str(sheet_scores[2][i+2]), font=font) # score team 2 set 2
                else: # team 2 won
                    draw.text( (183, 34), str(sheet_scores[2][i+1]), font=font) # score team 1 set 2
                    draw.text( (183, 66), str(sheet_scores[2][i+2]), font=font, fill=(0,255,0)) # score team 2 set 2
                draw.text( (231, 34), str(sheet_scores[3][i+1]), font=font) # score team 1 tiebreaker
                draw.text( (231, 66), str(sheet_scores[3][i+2]), font=font) # score team 2 tiebreaker
            else: # tiebreaker
                if (sheet_scores[3][i+1] > sheet_scores[3][i+2]): # team 1 won
                    draw.text( (231, 34), str(sheet_scores[3][i+1]), font=font, fill=(0,255,0)) # score team 1 tiebreaker
                    draw.text( (231, 66), str(sheet_scores[3][i+2]), font=font) # score team 2 tiebreaker   
                else: # team 2 won
                    draw.text( (231, 34), str(sheet_scores[3][i+1]), font=font) # score team 1 tiebreaker
                    draw.text( (231, 66), str(sheet_scores[3][i+2]), font=font, fill=(0,255,0)) # score team 2 tiebreaker   
                draw.text( (183, 34), str(sheet_scores[2][i+1]), font=font) # score team 1 set 2
                draw.text( (183, 66), str(sheet_scores[2][i+2]), font=font) # score team 2 set 2

            draw.line([10, 57.5, 260, 57.5], fill=(255,255,255,50)) # middle line

            emb.set_image(url="attachment://"+str(i)+"score.png")
            es.append(emb)
            fs.append([str(i)+"score.png", image])

    return es, fs
