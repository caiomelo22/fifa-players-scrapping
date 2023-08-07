import time
import pandas as pd
from helpers import ImageHelper
from requests.exceptions import ConnectionError
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from services import MySQLService
import undetected_chromedriver as uc
from dotenv import load_dotenv

load_dotenv()

positions_dict = {
    "Goalkeepers": "GK",
    "Center Backs": "CB",
    "Full Backs": "RB,LB, RWB, LWB",
    "Defensive Midfielders": "CDM,CM",
    "Ofensive Midfielders": "CAM",
    "Wingers": "LW,LF,LM,RF,RW,RM",
    "Attackers": "ST,CF",
}

base_url = (
    "https://www.futbin.com/players?page=1&version=gold_rare&pos_type=all&position="
)

image_helper = ImageHelper()

objects = {
    "position": [],
    "nation": [],
    "league": [],
    "team": [],
    "player": [],
}

options = uc.ChromeOptions()
options.headless = True
driver = uc.Chrome(use_subprocess=True, options=options)
driver.maximize_window()

for index, name in enumerate(positions_dict):
    objects["position"].append(
        {"id": index + 1, "name": name, "specific_positions": positions_dict[name]}
    )

    for page in range(1, 4):
        url = base_url + positions_dict[name]

        url = f"{url}&page={page}"
        print(f"\n{url}")

        driver.get(url)

        driver.maximize_window()
        time.sleep(8)

        players_1 = driver.find_elements(By.CLASS_NAME, "player_tr_1")
        players_2 = driver.find_elements(By.CLASS_NAME, "player_tr_2")
        players_trs = players_1 + players_2

        for p in players_trs:
            player = {"position_id": objects["position"][-1]["id"]}

            tds = p.find_elements(By.TAG_NAME, "td")

            try:
                player["id"] = (
                    tds[0].find_element(By.TAG_NAME, "div").get_attribute("data-playerid")
                )
            except NoSuchElementException:
                continue

            player["name"] = tds[1].find_element(By.XPATH, "div[2]/div[1]/a").text
            similar_players = [p for p in objects["player"] if p['name'] == player['name']]
            if not similar_players:
                pass
            elif similar_players and similar_players[0]["id"] < player["id"]:
                objects["player"].remove(similar_players[0])
            else:
                continue

            print(f"{player['name']} loaded")

            players_club_nation = (
                tds[1]
                .find_element(By.XPATH, "div[2]/div[2]/span")
                .find_elements(By.TAG_NAME, "a")
            )
            player["team_origin_id"] = players_club_nation[0].get_attribute(
                "data-original-title"
            )
            player["nation_id"] = players_club_nation[1].get_attribute(
                "data-original-title"
            )
            player["league_id"] = players_club_nation[2].get_attribute(
                "data-original-title"
            )
            player["specific_position"] = ",".join(
                [div.text for div in tds[3].find_elements(By.TAG_NAME, "div")]
            )
            player["skills"] = tds[6].text
            player["weak_foot"] = tds[7].text
            player["work_rate"] = tds[8].text

            player["pace"] = int(tds[9].find_element(By.TAG_NAME, "span").text)
            player["shooting"] = int(tds[10].find_element(By.TAG_NAME, "span").text)
            player["passing"] = int(tds[11].find_element(By.TAG_NAME, "span").text)
            player["dribbling"] = int(tds[12].find_element(By.TAG_NAME, "span").text)
            player["defending"] = int(tds[13].find_element(By.TAG_NAME, "span").text)
            player["physical"] = int(tds[14].find_element(By.TAG_NAME, "span").text)

            try:
                nation = image_helper.extract_save_img(
                    players_club_nation[1],
                    player["nation_id"],
                    objects["nation"],
                    "images/nations",
                )
                league = image_helper.extract_save_img(
                    players_club_nation[2],
                    player["league_id"],
                    objects["league"],
                    "images/leagues",
                    {"nation_id": nation["id"]},
                )
                team = image_helper.extract_save_img(
                    players_club_nation[0],
                    player["team_origin_id"],
                    objects["team"],
                    "images/teams",
                    {"league_id": league["id"]},
                )
                player["team_origin_id"] = team["id"]
                player["league_id"] = league["id"]
                player["nation_id"] = nation["id"]

                player_img = image_helper.get_img_url(
                    tds[1].find_element(By.XPATH, "div[1]")
                )
                file_path = image_helper.save_image(
                    player_img,
                    "images/players",
                    f"{player['name'].replace(' ', '')}_{player['id']}.png",
                )
            except ConnectionError:
                continue

            player["image_path"] = file_path

            del player["league_id"]

            objects["player"].append(player)

driver.quit()

mysql_service = MySQLService()

for obj in objects:
    data_df = pd.DataFrame(objects[obj])
    mysql_service.create_table_from_df(obj, data_df)
    mysql_service.insert_multiple_rows_from_dataframe(obj, data_df)

mysql_service.close()
