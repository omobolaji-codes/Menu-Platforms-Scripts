from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import time
import gspread  # Gspread to access google sheets
from operator import itemgetter

def runAutomationBeyondMenu(sheetKey, url):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    DRIVER_PATH = r"chromedriver"
    options.binary_location = (r"/Applications/Google Chrome 3.app/Contents/MacOS/Google Chrome")
    driver = webdriver.Chrome(executable_path=DRIVER_PATH, options=options)
    
    # Open google sheet
    gc = gspread.service_account(filename="../service_account.json")
    sh = gc.open(sheetKey)
    worksheet = sh.worksheet("Extraction")

    driver.get(url)
    time.sleep(10)


    #loop through menu tabs if they exist
    menus = driver.find_elements_by_class_name("menu-category-link")
    print("number of menus", len(menus))
    for menu in menus[2:]:
        try:
            #click on menu        
            driver.execute_script("arguments[0].click();", menu)
            print("Next menu clicked")
            time.sleep(3) 
            menuText = menu.text
            if menuText:
                menuTitle = "SEPARATE MENU " + "(" + menuText + ")"
                worksheet.append_row(values=[None, None, None, None, None, None, None, None, None, 0])
                worksheet.append_row(values = [menuTitle, None, None, None, None, None, None, None, None, 0])
        except ElementNotInteractableException:
            print("No menu tab to click")
            pass

        #scraping categories
        categories = driver.find_elements_by_class_name("menu-groupitem-wrapper")
        print("num categories", len(categories))
        fullData = []
        for category in categories[23:]:
            categoryName = category.find_element_by_class_name("menu-groupheader-name").text.strip()
            try:
                categoryDescription=category.find_element_by_class_name("menu-groupheader-desc").text.strip() #####
                print(categoryDescription)
            except:
                categoryDescription=None
            categoryList = ["Category", categoryName, categoryDescription, None, None, None, None, None, None, 0]
            fullData.append(categoryList)
            print(categoryList)

            worksheet.append_row(categoryList)

            #get items
            menuItems=category.find_elements_by_class_name("menu-item-link-wrapper")
            for menuItem in menuItems:
                itemData = []
                itemName=menuItem.find_elements_by_class_name("menu-item-link-itemname")[0].text.strip()
                itemName = itemName.rstrip(".")

                #convert first letter of each word to uppercase
                itemName_list = [word.capitalize() for word in itemName.split()]
                itemName = " ".join(itemName_list)

                try:
                    itemDescription=menuItem.find_elements_by_class_name("menu-item-link-itemdesc")[0].text.strip()
                except:
                    itemDescription=""

                # get spicy tag from item name & add it to description    
                if "Whatshot" in itemName:
                    itemName = itemName.replace("Whatshot", "")
                    itemDescription = "Spicy. " + itemDescription

                itemPrice = menuItem.find_elements_by_class_name("menu-item-link-price")[0].text.strip()
                print("item price", itemPrice)
                itemPrice = int(itemPrice.replace("$", "").replace(".", "").replace("+", "").replace(",","").strip().lstrip("0"))

                #click on each item
                menuItem.click()
                time.sleep(6)


                #get size extras
                sizeOptions = driver.find_elements_by_class_name("mid-sizeradiobutton-wrapper")
                if len(sizeOptions) != 1:
                    #append item
                    itemList = ["Item", itemName, itemDescription, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList)
                    # fullData.append(itemList)
                    itemData.append(itemList)

                    #append extra
                    sizeExtra = ["Extra", "Serving Choice", None, None, None, None, 1, 1, 0, 0]
                    # fullData.append(sizeExtra)
                    itemData.append(sizeExtra)
                    for sizeOption in sizeOptions:
                        optionName = sizeOption.text
                        optionName = optionName.replace("Add", "").replace("[", "").replace("+", "").replace("]", "")
                        if "$" in optionName:
                            optionPrice = optionName.split("$")[1]
                            optionPrice = int(optionPrice.replace(".", "").replace("+", "").replace(",","").strip().lstrip("0"))
                            optionName = optionName.split("$")[0].strip().title()
                        else:
                            optionPrice = 0

                        #convert sm to small & lg to large    
                        if optionName == "Sm" or optionName == "Sm.":
                            optionName = "Small"
                        if optionName == "Lg" or optionName == "Lg.":
                            optionName = "Large"

                        #convert pt to pint & Qt to Quart   
                        if optionName == "Pt":
                            optionName = "Pint"
                        if optionName == "Qt":
                            optionName = "Quart"

                        #append options
                        optionList = ["Option", optionName, None, int(optionPrice - itemPrice), None, None, None, None, None, 0]
                        # fullData.append(optionList)
                        itemData.append(optionList)   
                elif len(sizeOptions) ==1 and '[' in sizeOptions[0].text:
                    size = sizeOptions[0].text
                    print("size", size)
                    size = size.split("[")[0].strip()
                    itemDescription = itemDescription + " " + size
                    itemDescription = itemDescription.strip()
                    itemList = ["Item", itemName, itemDescription, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList)
                    # fullData.append(itemList)
                    itemData.append(itemList)

                else:
                    itemList = ["Item", itemName, itemDescription, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList)
                    # fullData.append(itemList)
                    itemData.append(itemList)



                #get extras
                extraSections=driver.find_elements_by_class_name("mid-modifiertype-container")
                for extraSection in extraSections:
                    extraName=extraSection.find_elements_by_class_name("mid-modifiertype-title")[0].text.strip()
                    try:
                        extraInstructions=extraSection.find_elements_by_class_name("mid-modifiertype-desc")[0].text.strip()
                        print(extraInstructions)
                    except:
                        extraInstructions=""

                    #get min & max options 
                    if "Choose" in extraName:
                        minOption = 1
                    if "Add" in extraName or "Extra" in extraName or "Extras" in extraName:
                        minOption = 0
                    if "Up To" in extraName:
                        maxOption = [word for word in extraName.split() if word.isdigit()]
                        maxOption = maxOption[0]
                        extraName = extraName.replace(maxOption, "").replace("Up To", "").strip()
                        maxOption = int(maxOption)
                    if extraName.lower() == "would you like to add extras?" or extraName.lower() == "would you like to add side?" or extraName.lower() == "would you like to add extra side?":
                        extraName = "Side"
                    

                    if "Choose exactly" in extraInstructions:
                        maxOption = [int(word) for word in extraInstructions.split() if word.isdigit()]
                        maxOption = maxOption[0]
                        minOption = maxOption
                    if "Choose up to" in extraInstructions:
                        minOption = 0
                        maxOption = [int(word) for word in extraInstructions.split() if word.isdigit()]
                        maxOption = maxOption[0]

                    if "Make it" in extraName: 
                        extraName = "Preparation"
                    if "Serve with" in extraName or "Choice of Side Order" in extraName:
                        extraName = "Side"  
                    if "Serve it" in extraName:
                        extraName = "Serving"

                    #convert first letter of each word to uppercase
                    extraName_list = [word.capitalize() for word in extraName.split()]
                    extraName = " ".join(extraName_list)

                    #replace unnecessary words with ""
                    extraName = extraName.replace("Choose", "").replace("Would You", "").replace("Add", "").replace("Like", "") \
                        .replace("Prefer", "").replace("Only", "").replace("Option", "").replace("For", "").replace("Extra", "") \
                        .replace('How', "").replace("?", "").replace("Choice Of", "").replace("Options", "").replace("Your", "") \
                        .lstrip("A ").lstrip("An ").lstrip("Of ").strip()

                    #get options          
                    allOptions = extraSection.find_elements_by_css_selector("div:nth-child(3) > div > div:nth-child(1) > label")
                    num_options = len(allOptions)
                    print("Number of options", num_options)
                    if "Choose any you want" in extraInstructions:
                        minOption = 0
                        maxOption = int(num_options)

                    if extraName == "":
                        extraName = "Side"

                    # append choice, addition or additions to extra name    
                    if minOption > 0:
                        extraName = extraName + " Choice"
                    else:
                        extraName = extraName + " Additions" 
                    if maxOption == 1:
                        extraName = extraName.replace("Additions", "Addition")

                    if "Substitution" in extraName:
                        extraName = extraName.replace(extraName, "Item Substitution")
                    if "Or" in extraName or "With" in extraName:
                        extraName = extraName.replace(extraName, "Item Selection")

                    extraList = ["Extra", extraName, None, None, None, None, minOption, maxOption, 0, 0]
                    # fullData.append(extraList)
                    print("Extra List", extraList)
                    itemData.append(extraList)

                    allOptions = extraSection.find_elements_by_css_selector("div:nth-child(3) > div > div:nth-child(1) > label")
                    optionBasePrice=0
                    for option in allOptions:
                        # allOption = extraSection.find_elements_by_css_selector("div:nth-child(3) > div > div:nth-child(1) > label")
                        optionName = option.text
                        optionName = optionName.title()
                        optionName = optionName.replace("Add", "").replace("Extra", "").replace("[", "").replace("+", "").replace("]", "")
                        if "$" in optionName:
                            optionPrice = optionName.split("$")[1]
                            optionPrice = optionPrice.replace(".", "").replace("+", "").replace(",","").strip().lstrip("0")
                            optionName = optionName.split("$")[0].strip()
                        else:
                            optionPrice = 0
                        optionList = ["Option", optionName, None, int(optionPrice) - optionBasePrice, None, None, None, None, None, 0]
                        # fullData.append(optionList)
                        print("Option List", optionList)
                        itemData.append(optionList)


                time.sleep(1)
                driver.find_element_by_class_name("mid-close-button-container").click()
                print("ITEM DONE! Modal closed.")
                time.sleep(2)
                print()

                worksheet.append_rows(values=itemData, value_input_option='RAW')

        # worksheet.append_rows(values=fullData, value_input_option='RAW')

    driver.quit()

    fullData=None

    print("FINISHED")
    return "DONE"

#run sample menu
# runAutomationBeyondMenu("BeyondMenu 1", "https://www.beyondmenu.com/54514/robbinsville/bagels-n--cream-robbinsville-08691.aspx")

#menu platforms test samples
# runAutomationBeyondMenu("Beyond: 136678225", "https://www.beyondmenu.com/30494/san-francisco/punjab-kabab-house-san-francisco-94102.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=c601f0d4697912f21603216176aaddfb#group_2659835")
# runAutomationBeyondMenu("Beyond: 136267330", "https://www.beyondmenu.com/23590/tahlequah/asian-star-tahlequah-74464.aspx?utm_source=satellite&utm_medium=menu_btn_order&pk_vid=26bbf217afd93933160269586946db1b")
# runAutomationBeyondMenu("Beyond: 134726330", "https://www.beyondmenu.com/36199/ellenton/tokyo-thai-ellenton-34222.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=cfba57db8a8da65c1602258871b67f75#group_2427776")
# runAutomationBeyondMenu("Beyond: 135168553", "https://www.beyondmenu.com/22861/san-francisco/jasmine-tea-house-san-francisco-94110.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=bcb68adf7a58cf091602261309e3f8f7#group_2210998")
# runAutomationBeyondMenu("Beyond: 134577832", "https://www.beyondmenu.com/28333/evans-mills/ruyi-sushi-evans-mills-13637.aspx")
# runAutomationBeyondMenu("Beyond: 133673107", "https://www.beyondmenu.com/23336/colorado-springs/thai-basil-colorado-springs-80920.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=e208fca70bd82d52160166097029cc7c#group_1842741")
# runAutomationBeyondMenu("Beyond: 133474485", "https://www.beyondmenu.com/25706/waco/summer-palace-chinese-buffet-waco-76710.aspx?utm_source=satellite&utm_medium=home_order&pk_vid=fcd4c39abbcac119160158788927159c")
# runAutomationBeyondMenu("Beyond: 131467665", "https://www.beyondmenu.com/53208/port-saint-lucie/ikura-sushi-and-hibachi-port-saint-lucie-34952.aspx")
# runAutomationBeyondMenu("Beyond: 133205999", "https://www.beyondmenu.com/34293/baltimore/darbar-baltimore-21231.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=89c125dc1c6ea08c16014966901767c7#group_2061306")
# runAutomationBeyondMenu("Beyond: 133239416", "https://www.beyondmenu.com/55015/brooklyn/i-love-dimsum-brooklyn-11223.aspx?utm_source=satellite&utm_medium=home_order&_")
# runAutomationBeyondMenu("Beyond: 132900648", "https://www.beyondmenu.com/53623/maryland-heights/china-1-maryland-heights-63043.aspx")
# runAutomationBeyondMenu("Beyond: 131713524", "https://www.beyondmenu.com/51129/yonkers/new-world-yonkers-10705.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=dd06049be5b26dde1601324137b67f75#group_2630084")


#run real samples
# runAutomationBeyondMenu("Beyond: 137836845", "https://www.beyondmenu.com/49420/tannersville/chopstick-tannersville-18372.aspx")
runAutomationBeyondMenu("Extraction: 139424452 -- June 2020 V1.2", "https://www.beyondmenu.com/27053/lake-mary/chopstix-sushi-chinese-restaurant-lake-mary-32746.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=6d4e82ff797f9ce9160390733302b6f5#group_1856114")