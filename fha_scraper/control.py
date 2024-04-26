from selenium import webdriver


DRIVER_PATH = '/usr/bin/chromedriver'
service = webdriver.ChromeService(executable_path=DRIVER_PATH)
options = webdriver.ChromeOptions()

options.page_load_strategy = 'normal'
options.add_argument("--start-maximized")
options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=options, service=service)

def main():
    driver.get("https://exhibitors.informamarkets-info.com/event/Saladplate/en-US/category/71886,71887,71888,71889,71890,71891,71892,71893,71894,71895,71896/")
    print(driver.page_source)
    

def quit():
    driver.quit()

if __name__ == '__main__':
    main()