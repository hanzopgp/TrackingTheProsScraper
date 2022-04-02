import numpy as np
from selenium import webdriver	
from selenium.webdriver.common.by import By
import time
from tqdm import tqdm
import pandas as pd


def init_driver(player_url=None):
	options = webdriver.ChromeOptions()
	options.add_experimental_option('excludeSwitches', ['enable-logging'])
	options.headless = True # Avoid google chrome GUI
	driver = webdriver.Chrome(options=options)
	chrome_prefs = {} # Avoid loading images to speed up scraping
	options.experimental_options["prefs"] = chrome_prefs
	chrome_prefs["profile.default_content_settings"] = {"images": 2}
	chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
	if player_url: # In case we init just a player url
		driver.get(player_url)
	else: # In case we are scraping the urls
		driver.get("https://www.trackingthepros.com/players/")
	time.sleep(1)
	return driver

def scrape_one_page(driver):
	one_page_players_url = []
	element = driver.find_elements(By.XPATH, "//tbody//tr")
	for x in element: 
		td = x.find_elements(By.XPATH, "td")
		a = td[0].text
		player_name = a[6:]
		player_link = f"https://www.trackingthepros.com/player/{player_name}/"
		one_page_players_url.append(player_link)
	# print("\n SCRAPED : ", len(one_page_players_url), "PRO PAGES")
	return one_page_players_url

def scrape_all_pages():
	print("SCRAPING ALL PLAYER URLS ON EACH PAGES ...")
	all_pages_players_url = []
	driver = init_driver() # Init our driver
	pagination = driver.find_element(By.CLASS_NAME, "pagination") # Gets the first occurence of .pagination
	last_page = int(pagination.text[-7:-4]) # Gets the last pages (the one before "next")
	# last_page = 2 # For debug purpose
	all_pages_players_url.append(scrape_one_page(driver)) # Scrapes first page
	for page_number in tqdm(range(2, last_page+1)):
		# print("SCRAPING PAGE NUMBER :", page_number)
		pagination = driver.find_element(By.CLASS_NAME, "pagination") # Refresh our pagination class
		lis = pagination.find_elements(By.TAG_NAME, "li") # Regresh our lists tag
		for x in lis:
			try: # Avoid debugging because the html of trackingthepros is kinda clunky
				links = x.find_elements(By.TAG_NAME, "a")
				for link in links:
					case_found = int(link.get_attribute("data-dt-idx")) # Gets the index of the case
					if case_found > 5: case_found = 5 # The index is the same than the page until page 5, where the next case index will always be 5
					if case_found == page_number or case_found == 5: # Check that we are going to click and scrape the right page
						# time.sleep(1)
						# print("CLICKED ON PAGE :", page_number)
						link.click() # Click to next page
						# time.sleep(1)
						all_pages_players_url.append(scrape_one_page(driver)) # Scrape the page
			except:
				pass
	driver.close() # Close the page since now we are going to go through all the player pages to get their informations
	return np.array(all_pages_players_url).flatten() # Flatten because we don't care about the pages number

def scrape_one_player_infos(player_driver):
	player_infos = []
	url_str = str(player_driver.current_url)
	name = url_str.split("/")[-2]
	if name == "player": # Sometimes there is a player in table but url doesn't work
		return [] # So we return empty array
	player_infos.append(name)
	trs = player_driver.find_elements(By.XPATH, "//tbody//tr")
	country = "MISSING"
	age = "MISSING"
	server = "MISSING"
	role = "MISSING"
	residency = "MISSING"
	summoner_names = []
	for tr in trs: 
		tds = tr.find_elements(By.XPATH, "td") 
		for i, td in enumerate(tds):
			if td.text == "Birthplace":
				country = tds[i+1].text
			elif td.text == "Birthday":
				age_string = tds[i+1].text
				age = int(age_string[age_string.find('(')+1:age_string.find(')')])
			elif "[" in td.text:
				string = tds[i].text
				server = string[string.find('[')+1:string.find(']')] # Server is between [ ]
				summoner_name = string.replace(server, "").replace("]", "").replace("[", "").lstrip()
				summoner_names.append(summoner_name)
			elif td.text == "Role":
				role = tds[i+1].text.lstrip()
			elif td.text == "Residency":
				residency = tds[i+1].text.lstrip()
	player_infos.append(role)
	player_infos.append(age)
	player_infos.append(country)
	player_infos.append(residency)
	player_infos.append(server)
	player_infos.append(summoner_names)
	return player_infos

def scrape_players_infos(all_players_pages):
	print("SCRAPING EACH PLAYER INFOS ON THEIR PERSONAL PAGES ...")
	all_data = []
	for player_url in tqdm(all_players_pages):
		player_driver = init_driver(player_url)
		all_data.append(scrape_one_player_infos(player_driver))
		player_driver.close()
	return all_data

def save_data(data):
	print("SAVING DATA ...")
	df = pd.DataFrame(data)
	df.to_csv('data.csv')
	print("DONE !!!")

all_players_pages = scrape_all_pages() # Scrapes all the url pages of the pro players
all_data = scrape_players_infos(all_players_pages) # Gets all the data per pro player
save_data(all_data) # Saves the data in a csv file


