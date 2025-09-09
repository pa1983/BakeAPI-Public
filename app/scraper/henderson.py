from bs4 import BeautifulSoup
import json
import requests

product_code = '908948'
url_base = r'https://www.henderson-foodservice.com/catalogsearch/result/?q='
url = f'{url_base}{product_code}'

html = requests.get(url).text
# Use the lxml parser for efficiency
soup = BeautifulSoup(html, 'lxml')

# Dictionary to hold the extracted data
product_data = {}

# --- Extraction Logic ---

# 1. Title
# The title is in an <h1> tag with the class 'page-title'
try:
    title_element = soup.find('h1', class_='page-title').find('span', class_='base')
    product_data['title'] = title_element.text.strip()
except AttributeError:
    product_data['title'] = None

# 2. Product Code
# Found in a div with itemprop="sku"
try:
    code_element = soup.find('div', itemprop='sku')
    product_data['product_code'] = code_element.text.strip()
except AttributeError:
    product_data['product_code'] = None

# 3. Description
# Found in a div with class 'overview_long_desc'
try:
    desc_element = soup.find('div', class_='overview_long_desc').find('div', class_='value')
    product_data['description'] = desc_element.text.strip()
except AttributeError:
    product_data['description'] = None

# 4. Ingredients
# Found in the div with id 'attributes.ingredients'
try:
    ingredients_element = soup.find('div', id='attributes.ingredients')
    # Clean up whitespace and join lines
    product_data['ingredients'] = ' '.join(ingredients_element.text.strip().split())
except AttributeError:
    product_data['ingredients'] = None

# 5. Product Data PDF URL
# Found in an anchor tag within the div with id 'attributes.downloads'
try:
    pdf_element = soup.find('div', id='attributes.downloads').find('a')
    product_data['product_data_pdf_url'] = pdf_element['href']
except (AttributeError, KeyError):
    product_data['product_data_pdf_url'] = None

# 6. Image URL
# The main image is reliably found in the 'og:image' meta tag
try:
    image_element = soup.find('meta', property='og:image')
    product_data['image_url'] = image_element['content']
except (AttributeError, KeyError):
    product_data['image_url'] = None

# 7. Nutritional Information
# Scraped from the table within the div with id 'attributes.nutritional'
nutritional_info = {}
try:
    nutritional_table = soup.find('div', id='attributes.nutritional').find('table')
    if nutritional_table:
        rows = nutritional_table.find_all('tr')
        for row in rows:
            # The key is in the table header (th) and the value is in the table data (td)
            key = row.find('th').text.strip()
            value = row.find('td').text.strip()
            nutritional_info[key] = value
except AttributeError:
    pass # If the table isn't found, the dictionary will remain empty
product_data['nutritional_information'] = nutritional_info

# 8. Allergens
# Scraped from the list within the div with id 'attributes.allergens.imgs'
# Use the class of the list item to determine if it contains, may contain, or does not contain the allergen.
allergens = {
    'contains': [],
    'may_contain': [],
    'does_not_contain': []
}
try:
    allergen_list_container = soup.find('div', id='attributes.allergens.imgs').find('ul', class_='allergens__wrapper')
    if allergen_list_container:
        list_items = allergen_list_container.find_all('li')
        for item in list_items:
            allergen_name = item.find('span').text.strip()
            # The class indicates the status
            item_classes = item.get('class', [])
            if 'allergen-red' in item_classes: #  used for 'Contains'
                allergens['contains'].append(allergen_name)
            elif 'allergen-yellow' in item_classes: #  used for 'May Contain'
                allergens['may_contain'].append(allergen_name)
            elif 'allergen-grey' in item_classes: #  used for 'Does Not Contain'
                allergens['does_not_contain'].append(allergen_name)

except AttributeError:
    pass # Fail gracefully -  If the allergen list isn't found, the dictionary will remain empty
product_data['allergens'] = allergens

print(json.dumps(product_data, indent=4))