import time
import pandas as pd
from helpers import ImageHelper
from requests.exceptions import ConnectionError
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from helpers.utils import get_asset_info
from services import MySQLService
import undetected_chromedriver as uc
from dotenv import load_dotenv
from unidecode import unidecode

load_dotenv()


def close_footer(driver):
    try:
        close_button = driver.find_element(By.CLASS_NAME, "vm-footer-close")
        close_button.click()
    except:
        pass


positions_dict = {
    "Goalkeepers": {"id": "GK", "n_pages": 1},
    "Center Backs": {"id": "CB", "n_pages": 3},
    "Full Backs": {"id": "RB,LB,RWB,LWB", "n_pages": 3},
    "Defensive Midfielders": {"id": "CDM,CM", "n_pages": 4},
    "Ofensive Midfielders": {"id": "CAM", "n_pages": 1},
    "Wingers": {"id": "LW,LF,LM,RF,RW,RM", "n_pages": 5},
    "Attackers": {"id": "ST,CF", "n_pages": 2},
}

stats = ["pace", "shooting", "passing", "dribbling", "defending", "physical"]

base_url = "https://www.fifacm.com/players?sort=overallrating&order=desc&position="

image_helper = ImageHelper()

objects = {
    "position": ([], "id"),
    "nation": ([], "name"),
    "team": ([], "name"),
    "player": ([], "id"),
}

options = uc.ChromeOptions()
# options.headless = True
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Multiple approaches to handle version mismatch
try:
    # Method 1: Force version 139
    driver = uc.Chrome(options=options, version_main=139)
except Exception as e:
    print(f"Method 1 failed: {e}")
    try:
        # Method 2: Let undetected_chromedriver auto-download the correct version
        driver = uc.Chrome(options=options, driver_executable_path=None)
    except Exception as e:
        print(f"Method 2 failed: {e}")
        try:
            # Method 3: Use patcher to force update
            driver = uc.Chrome(options=options, patcher_force_close=True)
        except Exception as e:
            print(f"All methods failed: {e}")
            raise

for index, name in enumerate(positions_dict):
    objects["position"][0].append(
        {
            "id": index + 1,
            "name": name,
            "specific_positions": positions_dict[name]["id"],
        }
    )

    for page in range(1, positions_dict[name]["n_pages"] + 1):
        url = base_url + positions_dict[name]["id"]

        url = f"{url}&page={page}"
        print(f"\n{url}")

        driver.get(url)

        # Add/set the gender cookie
        gender_cookie = driver.get_cookie('gender')
        if not gender_cookie:
            driver.add_cookie({
                'name': 'gender',
                'value': '0',
                'domain': '.fifacm.com',  # Note the dot prefix for subdomain inclusion
                'path': '/',
                'secure': True,  # Set to True for HTTPS sites
                'httpOnly': False  # Depends on your needs
            })
            driver.refresh()

        driver.maximize_window()
        time.sleep(8)

        players_trs = driver.find_elements(By.CLASS_NAME, "player-row")

        for p in players_trs:
            close_footer(driver)

            player = {"position_id": objects["position"][0][-1]["id"]}

            tds = p.find_elements(By.TAG_NAME, "td")
            main_td = tds[0]

            scroll_script = "window.scrollBy(0, 205);"
            driver.execute_script(scroll_script)

            stats_button = main_td.find_element(By.CLASS_NAME, "igs-btn")

            stats_button.click()

            try:
                player["id"] = stats_button.get_attribute("data-playerid")
            except NoSuchElementException:
                continue

            player_info_td = tds[1]

            player["name"] = unidecode(
                tds[1].find_element(By.XPATH, "div/div[3]/div/div[1]/a").text
            )

            similar_players = [
                p for p in objects["player"][0] if p["name"] == player["name"]
            ]

            if not similar_players:
                pass
            elif similar_players and similar_players[0]["id"] < player["id"]:
                objects["player"][0].remove(similar_players[0])
            else:
                continue

            overall_td = tds[2]

            player["overall"] = int(overall_td.text)

            player_nation_img = player_info_td.find_element(
                By.XPATH, "div/div[2]/div[2]/a/img"
            )
            player_nation_str, player_nation_img_src = get_asset_info(player_nation_img)

            player_team_img = player_info_td.find_element(
                By.XPATH, "div/div[2]/div[1]/a/img"
            )
            player_team_str, player_team_img_src = get_asset_info(player_team_img, prefix="l")

            player["specific_position"] = (
                player_info_td.find_element(By.CLASS_NAME, "player-position-cln")
                .text.split("|")[0]
                .strip()
            )

            try:
                nation = image_helper.extract_save_img(
                    player_nation_img_src,
                    player_nation_str,
                    objects["nation"],
                    "nations",
                )

                team = image_helper.extract_save_img(
                    player_team_img_src,
                    player_team_str,
                    objects["team"],
                    "teams",
                )

                player["team_origin"] = team["name"]

                player["nation"] = nation["name"]

                player_img = image_helper.get_img_url(
                    player_info_td.find_element(By.XPATH, "div/div[1]/img")
                )
                file_path = image_helper.save_image(
                    player_img,
                    "players",
                    f"{player['name'].replace(' ', '')}_{player['id']}.png",
                )
            except ConnectionError:
                continue

            time.sleep(1)

            try:
                player_stats_tr = driver.find_element(By.ID, f"player-{player['id']}")

                parent_div = player_stats_tr.find_element(By.CLASS_NAME, "player-stats")

                main_stats_values = parent_div.find_elements(
                    By.CLASS_NAME, "main-stat-rating-title"
                )

                for i in range(len(stats)):
                    player[stats[i]] = int(main_stats_values[i].text)
            except:
                print(f"Player {player['name']} could not be loaded.")
                continue

            player["image_path"] = file_path

            print(f"{player['name']} loaded")

            objects["player"][0].append(player)

driver.quit()

mysql_service = MySQLService()

for obj in objects:
    data_list, pk_column = objects[obj]
    data_df = pd.DataFrame(data_list)
    mysql_service.create_table_from_df(obj, data_df, pk_column=pk_column)
    mysql_service.insert_multiple_rows_from_dataframe(obj, data_df)

mysql_service.close()
