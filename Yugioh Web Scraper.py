import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Function to extract card information from a card page
def get_card_info(card_url, driver, page, intermediate_output):
    card_info = {}
    
    try:
        # Load the card page
        driver.get(card_url)
        
        # Wait for the card name and description to be present
        wait = WebDriverWait(driver, 20)  # Increase timeout if needed
        card_name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".column2 .card-name")))
        card_description_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".column2 .card-text")))
        
        # Get the card name and description
        card_info['Page Found'] = page
        card_info["Card Name"] = card_name_elem.text
        card_info["Card Description"] = card_description_elem.text
        
        # Wait for the card info list to be present
        card_info_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-data-info")))
        
        # Get the key-value pairs from the card info list
        info_headers = card_info_list.find_elements(By.CSS_SELECTOR, ".card-data-header")
        info_values = card_info_list.find_elements(By.CSS_SELECTOR, ".card-data-subheader")
        
        for header, value in zip(info_headers, info_values):
            key = header.text
            value_text = value.text
            card_info[key] = value_text
    
    except TimeoutException as e:
        print(f"TimeoutException occurred while processing {card_url}: {str(e)}")
        intermediate_output = True

    except Exception as e:
        print(f"Exception occurred while processing {card_url}: {str(e)}")
        intermediate_output = True

    return card_info, intermediate_output

# Function to extract card URLs from a page
def get_card_urls(driver, intermediate_output):
    try:
        # Wait for the loader to disappear and the content to load
        wait = WebDriverWait(driver, 20)  # Increase timeout if needed
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "loader")))
        
        # Now wait for the api-area-results to be present
        api_area_results = wait.until(EC.presence_of_element_located((By.ID, "api-area-results")))
        
        # Find all anchor tags within the api-area-results element
        card_links = api_area_results.find_elements(By.TAG_NAME, "a")
        
        # Extract all card URLs
        card_urls = []
        base_url = "https://ygoprodeck.com"
        
        for card_link in card_links:
            relative_url = card_link.get_attribute('href')
            # Ensure the URL starts with a single "/"
            if relative_url.startswith('/'):
                card_url = base_url + relative_url
            else:
                card_url = relative_url
            card_urls.append(card_url)
        
    except TimeoutException as e:
        print(f"TimeoutException occurred while fetching card URLs: {str(e)}")
        card_urls = []
        intermediate_output = True
    
    except Exception as e:
        print(f"Exception occurred while fetching card URLs: {str(e)}")
        card_urls = []
        intermediate_output = True
    
    return card_urls, intermediate_output

# URL of the main page
url_template = "https://ygoprodeck.com/card-database/?&num={}&offset={}"

# Set up Chrome options
options = Options()
options.add_argument("--headless")  # Run in headless mode, remove to see the browser
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Create a new instance of the Chrome driver
driver = webdriver.Chrome(options=options)

# Initialize an empty list to store all card information
cards_data = []
card_urls_output_ls = []

# Loop through all pages
total_pages = 133
cards_per_page = 100
card_counter = 0

for page in range(total_pages):
    #Track if an exception is thrown and if it is print out an intermediate output to ensure results aren't lost
    intermediate_output = False

    print('CURRENT PAGE', page)
    offset = page * cards_per_page
    num = cards_per_page
    url = url_template.format(num,offset)
    driver.get(url)
    
    # Extract card URLs from the current page
    redo_iteration = 0
    card_urls, intermediate_output = get_card_urls(driver, intermediate_output)

    #repeat get_card_urls if it returns an empty list to retry connection
    while len(card_urls) == 0 and redo_iteration < 5:
        redo_iteration += 1
        print('REDO ITERATION:', redo_iteration)
        card_urls, intermediate_output = get_card_urls(driver, intermediate_output)
    
    card_urls_output_ls.extend(card_urls)

    # Extract and store the card information
    for card_url in card_urls:
        card_counter += 1
        card_info, intermediate_output = get_card_info(card_url, driver, page, intermediate_output)
        cards_data.append(card_info)
        print("CURRENT CARD NUM:", card_counter, "Current Page", page, card_info)  # Print each card info for verification

    if intermediate_output:
        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(cards_data)

        # Write the DataFrame to a CSV file
        csv_file = f'yugioh_cards_data_full_{card_counter}_.csv'
        df.to_csv(csv_file, index=False)

        print(f"Data written to {csv_file}")

# Close the browser
driver.quit()

# Convert the list of dictionaries to a DataFrame
df = pd.DataFrame(cards_data)

df_url_output = pd.DataFrame()
df_url_output['scrapped_url'] = card_urls_output_ls

# Write the DataFrame to a CSV file
csv_file = 'yugioh_cards_data_full_2_.csv'
df.to_csv(csv_file, index=False)
df_url_output.to_csv('Scrapped_Urls.csv', index=False)

print(f"Data written to {csv_file}")