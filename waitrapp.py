from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import time
import gspread  # Gspread to access google sheets
from operator import itemgetter

def runAutomationWaitrapp(sheetKey, url):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    DRIVER_PATH = r"chromedriver"
    options.binary_location = (r"/Applications/Google Chrome 3.app/Contents/MacOS/Google Chrome")

    #remove default location
    prefs = {"profile.default_content_setting_values.geolocation" :2}
    options.add_experimental_option("prefs",prefs)

    driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)
    
    # Open google sheet
    gc = gspread.service_account(filename="../service_account.json")
    sh = gc.open(sheetKey)
    worksheet = sh.get_worksheet(1)

    driver.get(url)
    print("getting url ...")
    time.sleep(10)
    print("url done")
    driver.delete_all_cookies()

    #loop through menu tabs if they exist
    menus = driver.find_elements_by_class_name("tab.false")
    print("number of menus", len(menus))
    for menu in menus:
        try:
            #click on menu        
            driver.execute_script("arguments[0].click();", menu)
            print("Next menu clicked")
            time.sleep(7) 
            menuText = menu.text
            if menuText:
                menuTitle = "SEPARATE MENU " + "(" + menuText + ")"
                worksheet.append_row(values=[None, None, None, None, None, None, None, None, None, 0])
                worksheet.append_row(values=[None, None, None, None, None, None, None, None, None, 0])
                worksheet.append_row(values = [menuTitle, None, None, None, None, None, None, None, None, 0])
        except ElementNotInteractableException:
            print("No menu tab to click")
            pass

        categories = driver.find_elements_by_class_name("item_containers")
        print(len(categories))
        time.sleep(2)
        for category in categories:
            sectionName = category.find_element_by_class_name("h3_title").text
            if "Breakfast" in sectionName or "Lunch" in sectionName or "Dinner" in sectionName or "Catering" in sectionName:
                worksheet.append_row(values=[None, None, None, None, None, None, None, None, None, 0])
                worksheet.append_row(values=[None, None, None, None, None, None, None, None, None, 0])
                worksheet.append_row(values=["SPECIFIC MENU BEGINS HERE", None, None, None, None, None, None, None, None, 0])
                pass
            else:
                pass
            sectionList = ["Category", sectionName, None, None, None, None, None, None, None, 0]
            print("Category list", sectionList)
            worksheet.append_row(values=sectionList)  #append Category list to worksheet

            menuItems = category.find_elements_by_class_name("col-sm-6.col-xs-12.menu-item.card-bubble")
            for i, menuItem in enumerate(menuItems):
                items = category.find_elements_by_class_name("col-sm-6.col-xs-12.menu-item.card-bubble")
                itemName = items[i].find_element_by_tag_name("h3").text
                itemPrice = items[i].find_element_by_tag_name("span").text
                if itemPrice:
                    itemPrice = int(itemPrice.replace("$", "").replace(".", ""))
                else:
                    itemPrice = 0

                try:
                    itemDesc = items[i].find_element_by_class_name("block-with-text").text
                except NoSuchElementException:
                    pass

                if itemPrice != 0:
                    itemList = ["Item", itemName, itemDesc, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList) 
                    worksheet.append_row(values=itemList)
                    pass

                items[i].click()
                time.sleep(5)

                #get extra
                try:
                    extras = driver.find_elements_by_css_selector("#menu_item_form > div > div")
                    for extra in extras:
                        #get extraname and instructions
                        extraName = extra.find_element_by_tag_name("h3")
                        extraName_ = extraName.text
                        if 'Choose' in extraName_:
                            extraName_ = extraName_.split(' ', maxsplit=1)[1]
                            extraName_ = extraName_.replace(":*", "") 
                        if 'Add Extra' in extraName_:
                            extraName_ = extraName_.replace("Add Extra ", "")
                        if 'Add:' in extraName_:
                            extraName_ = extraName_.replace("Add:", "Side")
                        if 'Add / Extra:' in extraName_:
                            extraName_ = extraName_.replace(extraName_, "Side")
                        if ':' in extraName_:
                            extraName_ = extraName_.replace(":", "")
                        if '/' in extraName_:
                            extraName_ = extraName_.replace("/", "")
                        if '+' in extraName_:
                            extraName_ = extraName_.replace('+ ', "")  
                        if '*' in extraName_:
                            extraName_ = extraName_.replace('*', "")

                        options = extra.find_elements_by_class_name("col-mod-container")
                        num_options = int(len(options))

                        #Get miniumum and maximum options from instructions
                        instruction = extra.find_element_by_class_name("select_description").text
                        if 'Select' in instruction:
                            minOption = int(instruction.replace('Select', ""))
                            maxOption = minOption
                        if 'Select' in instruction and extraName_=="Side":
                            minOption = 0
                            maxOption = int(instruction.replace('Select', ""))
                        if 'Max' in instruction:
                            minOption = 0
                            maxOption = int(instruction.replace('Max', ""))
                        if 'Max' in instruction and 'Choose' in extraName.text:
                            minOption = 1
                            maxOption = int(instruction.replace('Max', ""))
                        if instruction == "":
                            minOption = 0
                            maxOption = num_options
                        if 'Add ' in extraName_:
                            extraName_ = extraName_.replace("Add ", "")
                            minOption = 0
                        if 'Extra' in extraName_:
                            extraName_ = extraName_.replace("Extra ", "")
                            minOption = 0


                        #modify extraname to include Choice, Addition or Additions
                        if minOption > 0:
                            extraName_ = extraName_ + " Choice"
                        else:
                            extraName_ = extraName_ + " Additions" 
                        if maxOption == 1:
                            extraName_ = extraName_.replace("Additions", "Addition")
                        if 'Substitute' in extraName_:
                            extraName_ = extraName_.replace(extraName_, "Substitute Option")
                            minOption = 0

                        extraList = ["Extra", extraName_, None, None, None, None, minOption, maxOption, 0, 0]
                        print("extra list", extraList)

                        #get options
                        allOptions = []
                        allOptionLists = []
                        for option in options:
                            optionName = option.text
                            optionPrice = 0
                            if '+ Extra' in optionName:
                                optionName = optionName.replace("+ Extra ", "") 
                            if '+' in optionName:
                                optionName = optionName.replace("+ ", "")

                            # Separate name from price in each option
                            if '|' in optionName:
                                optionPrice = optionName.split("|")[1]
                                optionPrice = int(optionPrice.replace("$", "").replace(".", ""))
                                optionName = optionName.split("|")[0]

                            #click on an option if it has suboptions
                            suboptions = option.find_elements_by_class_name("col-md-6.mod_button")
                            if suboptions:
                                #option click
                                optionClick = option.find_element_by_css_selector("input.visually-hidden")
                                driver.execute_script("arguments[0].click();", optionClick)
                                time.sleep(1)

                                for suboption in suboptions:
                                    suboptionName = suboption.find_element_by_class_name("mod_button_txt").get_attribute("data-txt")
                                    suboptionPrice = 0 
                                    if '+' in suboptionName:
                                        suboptionName = suboptionName.replace('+ ', "")
                                    if '|' in suboptionName:
                                        suboptionPrice = suboptionName.split("|")[1]
                                        suboptionPrice = int(suboptionPrice.replace("$", "").replace(".", ""))
                                        suboptionName = suboptionName.split("|")[0]
                                    if optionName != 'Fountain Drink ':
                                        suboptionName = optionName + " - " + suboptionName
                                    suboptionList = ["Option", suboptionName, None, optionPrice, None, None, None, None, None, 0]
                                    print("suboptionList", suboptionList)
                                    allOptionLists.append(suboptionList)
                            else:
                                optionList = ["Option", optionName, None, optionPrice, None, None, None, None, None, 0]
                                print("option List", optionList)
                                allOptions.append(optionList)
                                allOptionLists.append(optionList)

                        # rearrange options in ascending order of prices
                        if (itemPrice==0 and extra == extras[0]): #get prices from the first extra
                            try:
                                itemPrice_min = min(option_[3] for option_ in allOptions)
                                sortedOptions = sorted(allOptions, key=itemgetter(3))
                            except ValueError:
                                itemPrice_min = min(option_[3] for option_ in allOptionLists)
                                sortedOptions = sorted(allOptionLists, key=itemgetter(3))

                            for each_row in sortedOptions:
                                each_row[3] = each_row[3] - itemPrice_min

                            #append items
                            itemList = ["Item", itemName, itemDesc, itemPrice_min, None, None, None, None, None, 0]
                            worksheet.append_row(values=itemList)

                            #append extras
                            extraList = ["Extra", extraName_, None, None, None, None, minOption, maxOption, 0, 0]
                            worksheet.append_row(values= extraList)

                            #append sorted options
                            worksheet.append_rows(values= sortedOptions, value_input_option='RAW')

                        else:
                            #append extras
                            worksheet.append_row(values= extraList)

                            #append extras & options & suboptions
                            worksheet.append_rows(values= allOptionLists, value_input_option='RAW')
                except NoSuchElementException:
                    pass

                # Close Modal
                close_modal = driver.find_element_by_css_selector("div.close-x")
                driver.execute_script("arguments[0].click();", close_modal)
                print("Modal closed")
                print()
                time.sleep(2)
        time.sleep(5)
    # driver.quit()
    return "DONE"


# Run sample menu url
# runAutomationWaitrapp("WAITRAPP_1: 134404140", "https://waitrapp.com/restaurants/17152?$og_title=Order%20Fajita%20Kings%20on%20Waitr&amp;$og_description=Get%20Fajita%20Kings%20delivered%20to%20your%20door%20with%20Waitr&amp;$og_image_url=https%3A%2F%2Fmenu-images.waitrapp.com%2F17152%2Fcovers%2F5e860246e470e.j")
# runAutomationWaitrapp("WAITRAPP_9: 128792248", "https://waitrapp.com/restaurants/sc/florence/sweet-frog-pamplico-hwy/14925")
# runAutomationWaitrapp("WAITRAPP_10: 128808421", "https://waitrapp.com/restaurants/la/natchitoches/cane-rio-cafe/14927")  
# runAutomationWaitrapp("WAITRAPP_11: 128566871", "https://waitrapp.com/restaurants/la/breaux-bridge/glendas-creole-kitchen/7213")

# runAutomationWaitrapp("Waitrapp: 138110412", "https://waitrapp.com/restaurants/al/mobile/charm-thai-kitchen-sushi-bar/11484")
# runAutomationWaitrapp("Waitrapp: 138086260", "https://waitrapp.com/restaurants/la/houma/pvo-bistro-lounge/9011")