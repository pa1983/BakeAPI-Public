import re

from bs4 import BeautifulSoup
import requests
import json

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
}

product_code = '12050'
base_url = f'https://www.brake.co.uk/search?text='
url = f'{base_url}{product_code}'
html_doc = requests.get(url, headers=headers).text

# Use the lxml parser for efficiency
soup = BeautifulSoup(html_doc, 'lxml')


# Use the lxml parser for efficiency

# Dictionary to hold the extracted data
product_data = {}

# --- Extraction Logic ---

# 1. Title
try:
    title_element = soup.find('h1', class_='product-details__name')
    product_data['title'] = title_element.text.strip()
except AttributeError:
    product_data['title'] = None

# 2. Product Code
try:
    code_element = soup.find('div', class_='product-details__code')
    # Clean up the text, removing the "C " prefix and non-breaking spaces
    product_data['product_code'] = code_element.text.strip().replace('C\xa0', '')
except AttributeError:
    product_data['product_code'] = None

# 3. Description
try:
    desc_element = soup.find('div', class_='js-productDetailsDescText')
    product_data['description'] = desc_element.text.strip()
except AttributeError:
    product_data['description'] = None

# 4. Ingredients
try:
    ingredients_container = soup.find('div', id='collapse3')
    p_tag = ingredients_container.find('p', string=re.compile(r'Ingredients:'))
    product_data['ingredients'] = p_tag.text.replace('Ingredients:', '').strip()
except AttributeError:
    product_data['ingredients'] = None

# 5. Product Data PDF URL
# This page does not contain a link to a PDF datasheet.
product_data['product_data_pdf_url'] = None

# 6. Image URL
# The image URL must be constructed from data found in a script tag.
image_url = None
try:
    # Find the script tag containing the 'mediaList'
    script_tag = soup.find('script', string=re.compile(r'window\.ecommBridge'))
    if script_tag:
        # Use regex to extract the JSON array for mediaList
        match = re.search(r'mediaList:\s*(\[.*?\])', script_tag.string)
        if match:
            media_list_str = match.group(1)
            # Parse the JSON string into a Python list
            media_list = json.loads(media_list_str)
            if media_list and 'name' in media_list[0]:
                image_name = media_list[0]['name']
                # Construct the full URL
                image_url = f"https://cdn.media.amplience.net/i/Brakes/{image_name}"
    product_data['image_url'] = image_url
except (AttributeError, json.JSONDecodeError):
    product_data['image_url'] = None

# 7. Nutritional Information
# Scraped from the table within the nutrition accordion
nutritional_info = {}
try:
    nutritional_table = soup.find('div', id='collapse2').find('table')
    if nutritional_table:
        rows = nutritional_table.find_all('tr')
        for row in rows:
            key_element = row.find('th')
            value_element = row.find('td')
            if key_element and value_element:
                key = key_element.text.strip()
                value = value_element.text.strip()
                nutritional_info[key] = value
except AttributeError:
    pass # If the table isn't found, the dictionary will remain empty
product_data['nutritional_information'] = nutritional_info

# 8. Allergens
# This page provides a text summary instead of icons.
allergens = {
    'summary': None
}
try:
    allergen_container = soup.find('div', id='collapse3')
    if allergen_container:
        p_tag = allergen_container.find('p', string=re.compile(r'Contains :'))
        if p_tag:
            allergens['summary'] = p_tag.text.replace('Contains :', '').strip()

except AttributeError:
    pass # If the allergen info isn't found, the dictionary will remain empty
product_data['allergens'] = allergens


# --- Output the results ---
# Use json.dumps for a clean, readable printout.
print(json.dumps(product_data, indent=4))