from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
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
    worksheet = sh.get_worksheet(1)

    driver.get(url)
    time.sleep(10)


    #loop through menu tabs if they exist
    menus = driver.find_elements_by_class_name("menu-category-link")
    print("number of menus", len(menus))
    for menu in menus[1:]:
        try:
            #click on menu        
            driver.execute_script("arguments[0].click();", menu)
            print("Next menu clicked")
            time.sleep(5) 
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
        for category in categories:
            categoryName = category.find_element_by_class_name("menu-groupheader-name").text.strip()
            try:
                categoryDescription=category.find_element_by_class_name("menuSection-desc").text.strip() #####
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
                itemName = itemName.title().rstrip(".")
                try:
                    itemDescription=menuItem.find_elements_by_class_name("menu-item-link-itemdesc")[0].text.strip()
                except:
                    itemDescription=""

                itemPrice = menuItem.find_elements_by_class_name("menu-item-link-price")[0].text.strip()
                print("item price", itemPrice)
                itemPrice = int(itemPrice.replace("$", "").replace(".", "").replace("+", "").replace(",","").strip().lstrip("0"))

                #click on each item
                menuItem.click()
                time.sleep(3)


                #get size extras
                sizeOptions = driver.find_elements_by_class_name("mid-sizeradiobutton-wrapper")
                if len(sizeOptions) != 1:
                    #append item
                    itemList = ["Item", itemName, itemDescription, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList)
                    fullData.append(itemList)
                    itemData.append(itemList)

                    #append extra
                    sizeExtra = ["Extra", "Serving Choice", None, None, None, None, 1, 1, 0, 0]
                    fullData.append(sizeExtra)
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
                        #append options
                        optionList = ["Option", optionName, None, int(optionPrice - itemPrice), None, None, None, None, None, 0]
                        fullData.append(optionList)
                        itemData.append(optionList)   
                elif len(sizeOptions) ==1 and '[' in sizeOptions[0].text:
                    size = sizeOptions[0].text
                    print("size", size)
                    size = size.split("[")[0].strip()
                    itemDescription = size
                    itemList = ["Item", itemName, itemDescription, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList)
                    fullData.append(itemList)
                    itemData.append(itemList)

                else:
                    itemList = ["Item", itemName, itemDescription, itemPrice, None, None, None, None, None, 0]
                    print("Item List", itemList)
                    fullData.append(itemList)
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
                    if extraName == "Would You Like To Add Extras?":
                        extraName = "Side"
                    

                    if "Choose exactly" in extraInstructions:
                        maxOption = [int(word) for word in extraInstructions.split() if word.isdigit()]
                        maxOption = maxOption[0]
                        minOption = maxOption
                    if "Choose up to" in extraInstructions:
                        minOption = 0
                        maxOption = [int(word) for word in extraInstructions.split() if word.isdigit()]
                        maxOption = maxOption[0]


                    extraName = extraName.title()
                    extraName = extraName.replace("Choose", "").replace("Would You", "").replace("Add", "").replace("Like", "").replace("Prefer Only", "") \
                            .replace("Extra", "").replace('How', "").replace("?", "").lstrip("A ").lstrip("An ").strip()

                    #get options          
                    allOptions = extraSection.find_elements_by_css_selector("div:nth-child(3) > div > div:nth-child(1) > label")
                    num_options = len(allOptions)
                    print("Number of options", num_options)
                    if "Choose any you want" in extraInstructions:
                        maxOption = int(num_options)

                    # append choice, addition or additions to extra name    
                    if minOption > 0:
                        extraName = extraName + " Choice"
                    else:
                        extraName = extraName + " Additions" 
                    if maxOption == 1:
                        extraName = extraName.replace("Additions", "Addition")

                    if "Choice of" in extraName or "Make it" in extraName: #or "Serve With"
                        extraName = "Preparation Choice"
                    if "Serve With" in extraName:
                        extraName = "Side Choice"

                    extraList = ["Extra", extraName, None, None, None, None, minOption, maxOption, 0, 0]
                    fullData.append(extraList)
                    print("Extra List", extraList)
                    itemData.append(extraList)

                    optionBasePrice=0
                    for option in allOptions:
                        optionName=option.text
                        optionName = optionName.replace("Add", "").replace("[", "").replace("+", "").replace("]", "")
                        if "$" in optionName:
                            optionPrice = optionName.split("$")[1]
                            optionPrice = optionPrice.replace(".", "").replace("+", "").replace(",","").strip().lstrip("0")
                            optionName = optionName.split("$")[0].strip()
                        else:
                            optionPrice = 0
                        optionList = ["Option", optionName, None, int(optionPrice) - optionBasePrice, None, None, None, None, None, 0]
                        fullData.append(optionList)
                        print("Option List", optionList)
                        itemData.append(optionList)
                        time.sleep(1.1)  

                time.sleep(1.5)
                driver.find_element_by_class_name("mid-close-button-container").click()
                print("ITEM DONE! Modal closed.")
                time.sleep(3)
                print()

                worksheet.append_rows(values=itemData, value_input_option='RAW')

        # worksheet.append_rows(values=fullData, value_input_option='RAW')
        time.sleep(3)

    driver.quit()

    fullData=None

    print("FINISHED")
    return "DONE"

#run sample menu
# runAutomationBeyondMenu("BeyondMenu 1", "https://www.beyondmenu.com/54514/robbinsville/bagels-n--cream-robbinsville-08691.aspx")

# runAutomationBeyondMenu("Beyond: 136678225", "https://www.beyondmenu.com/30494/san-francisco/punjab-kabab-house-san-francisco-94102.aspx?utm_source=satellite&utm_medium=menu_group&pk_vid=c601f0d4697912f21603216176aaddfb#group_2659835")
runAutomationBeyondMenu("Beyond: 136267330", "https://www.beyondmenu.com/23590/tahlequah/asian-star-tahlequah-74464.aspx?utm_source=satellite&utm_medium=menu_btn_order&pk_vid=26bbf217afd93933160269586946db1b")