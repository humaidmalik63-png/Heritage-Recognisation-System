import time
import sys
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Edge(options=options)
try:
    driver.get('http://127.0.0.1:5173/')
    time.sleep(3)
    
    logs = driver.get_log('browser')
    errors = [l for l in logs if l['level'] == 'SEVERE']
    print(f"Browser console errors: {len(errors)}")
    for e in errors:
        print("  Error:", e['message'])
        
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print("Page text snippet:", body_text[:180].replace('\n', ' '))
    
    cat_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Catalog')]")
    print(f"Catalog buttons found: {len(cat_buttons)}")
    for b in cat_buttons:
        print("  Button text:", b.text)
        
    if cat_buttons:
        cat_buttons[0].click()
        time.sleep(1.5)
        drawer_text = driver.find_element(By.TAG_NAME, 'body').text
        print("Drawer opened. Text has 'Authoritative 100-Site Catalogue':", "Authoritative 100-Site Catalogue" in drawer_text)
        print("Drawer has 'India (50)':", "India (50)" in drawer_text)
        print("Drawer has 'Global (50)':", "Global (50)" in drawer_text)
finally:
    driver.quit()

