# import web scraping library
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException
)
import time
import gspread  # Gspread to access google sheets
from operator import itemgetter


def runAutomationMenuLog(sheetKey, url):
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

   #switch to pickup
    try:
        pickup = driver.find_element_by_css_selector("input#ms-collection-Basket.btnToggle-input")
        driver.execute_script("arguments[0].click();", pickup)
        print("Switched to pickup")
        time.sleep(2)
    except:
        print("No option to switch to pickup, restaurant might be closed")
    time.sleep(5)

    # scraping
    categories = driver.find_elements_by_class_name("menuCard-category.accordion.accordion--ruled.is-open")
    for category in categories:
        categoryName = category.find_element_by_class_name("menuCard-category-title.gamma.accordion-header.icon").text
        try:
            categoryDescription=category.find_element_by_class_name("menuCard-category-description").text.strip() #####
        except:
            categoryDescription=None
        sectionList = ["Category", categoryName, categoryDescription, None, None, None, None, None, None, 0]
        print(sectionList)
        worksheet.append_row(values=sectionList)  # append Category Names to worksheet

        menuItems = category.find_elements_by_class_name("menu-product.product.u-separated--dash")
        for i, menuItem in enumerate(menuItems):
            items = category.find_elements_by_class_name("menu-product.product.u-separated--dash")
            itemName = items[i].find_element_by_class_name("product-title").text
            itemPrice = items[i].find_element_by_class_name("product-price.u-noWrap").text
            itemPrice = int(itemPrice.replace("$", "").replace(".", ""))

            try:
                itemDesc = items[i].find_element_by_class_name("product-description").text
            except NoSuchElementException:
                itemDesc = ""

            #extract first set of options visible with corresponding items
            try:
                options = items[i].find_elements_by_class_name("product-synonym")
                if options:
                    allOptions = []
                    for option in options:
                        optionName = option.find_element_by_class_name("product-synonym-name").text
                        optionPrice = option.find_element_by_class_name("product-price.u-noWrap").text
                        optionPrice = int(optionPrice.replace("$", "").replace(".", ""))
                        optionList = ["Option", optionName, None, optionPrice, None, None, None, None, None, 0]
                        allOptions.append(optionList)
                    itemPrice_min = min(option_[3] for option_ in allOptions)
                    sortedOptions = sorted(allOptions, key=itemgetter(3))
                    for each_row in sortedOptions:
                        each_row[3] = each_row[3] - itemPrice_min

                    #if there is only one single option, skip extras & options
                    if len(sortedOptions) != 1:  
                        #append items
                        itemList = ["Item", itemName, itemDesc, itemPrice_min, None, None, None, None, None, 0]
                        worksheet.append_row(values=itemList)

                        #append extras
                        extraList = ["Extra", "Item Selection", None, None, None, None, 1, 1, 0, 0]
                        worksheet.append_row(values= extraList)

                        #append options
                        worksheet.append_rows(values= sortedOptions, value_input_option='RAW')
                    else:
                        itemName = itemName + " (" + optionName + ")"
                        #append items
                        itemList = ["Item", itemName, itemDesc, itemPrice_min, None, None, None, None, None, 0]
                        worksheet.append_row(values=itemList)
                        pass

                else:
                    itemList = ["Item", itemName, itemDesc, itemPrice, None, None, None, None, None, 0]
                    worksheet.append_row(values=itemList)
            except NoSuchElementException:
                pass            
            

            #click each item to extract options
            items[i].click()
            time.sleep(2)

            extras = driver.find_elements_by_class_name("accessories-option.accordion.accordion--ruled.accordion--autotoggle")
            if extras:
                time.sleep(3)
                for extra in extras:
                    extraName_ = ""  
                    options_ = extra.find_elements_by_class_name("box.accessory-name")
                    allOptions2 = []
                    for option_ in options_:
                        optionContent = option_.find_element_by_class_name("box-grow-1")   #each option
                        optionName_ = optionContent.text
                        if ": " in optionName_:
                            extraName_ = optionName_.split(": ")[0]
                            if 'Add' in extraName_:
                                extraName_ = extraName_.replace("Add ", "")
                            if 'Choice of' in extraName_:
                                extraName_ = extraName_.replace("Choice of ", "")
                            if 'Choice' in extraName_:
                                extraName_ = extraName_.replace("Choice", "")
                            extraName_ = extraName_ + " Choice"
                            optionName_ = optionName_.split(": ")[1].title()
                        if optionName_ == "":   #account for error in getting option name
                            optionList_ = ["Option", "Get option name", None, None, None, None, None, None, None, 0]
                        else:
                            try:
                                optionPrice_ = option_.find_element_by_class_name("u-noWrap").text
                                optionPrice_ = int(optionPrice_.replace("$", "").replace(".", ""))
                            except NoSuchElementException: 
                                optionPrice_= 0
                                pass
                            optionList_ = ["Option", optionName_, None, optionPrice_, None, None, None, None, None, 0]      
                        allOptions2.append(optionList_)

                    #get min & max options from instructions
                    instruction = extra.find_element_by_class_name("accordion-header").text
                    if instruction == "Choose one" or "Choose option" in instruction:
                        minOption = 1
                        maxOption = 1
                    
                    #assign names for Extras
                    if allOptions2[0][1] == "BBQ":
                        extraName_ = "Sauce Choice"
                    if extraName_ == "":
                        extraName_ = "Item Selection"  

                    #try option click to see more options    
                    try:
                        optionClick = extra.find_elements_by_class_name("box-grow-1")[0]
                        driver.execute_script("arguments[0].click();", optionClick)
                        print("option clicked")
                        time.sleep(2)
                    except ElementNotInteractableException:
                        print("not clickable")
                        continue  

                    #append extra
                    extraList2 = ["Extra", extraName_, None, None, None, None, minOption, maxOption, 0, 0]
                    worksheet.append_row(values= extraList2)

                    #append options
                    worksheet.append_rows(values= allOptions2, value_input_option='RAW')

                #close modal
                driver.find_element_by_xpath("//*[@id='menuContainer']/div[2]/div[2]/div/div[1]").click()
                print("Modal Closed")
                time.sleep(3)
            else: pass

    driver.quit()
    return "DONE"

# Run sample menu url
# runAutomationMenuLog("MenuLOG_1: 134503242", "https://www.menulog.com.au/restaurants-kukulas-canberra/menu?utm_source=google&amp;utm_medium=organic&amp;utm_campaign=orderaction")
# runAutomationMenuLog("MenuLOG_5: 134293252", "https://www.menulog.com.au/restaurants-wendys-riverside-kialla/menu")


# runAutomationMenuLog("Menulog: 137771198", "https://www.menulog.com.au/restaurants-kung-fu-dumplings-gurwood-st/menu?utm_source=google&utm_medium=organic&utm_campaign=orderaction")
# runAutomationMenuLog("Menulog: 137771658", "https://www.menulog.com.au/restaurants-kung-fu-dumplings-sturt-mall/")
# runAutomationMenuLog("Menulog: 138196682", "https://www.menulog.com.au/restaurants-joeys-pizza-pasta-gelato/menu?utm_source=joeyspizzapasta.com.au&utm_medium=microsites&utm_campaign=microsites")
# runAutomationMenuLog("Menulog: 138867419", "https://www.menulog.com.au/restaurants-king-of-kebabs-penrith/menu?utm_source=google&utm_medium=organic&utm_campaign=orderaction")
# runAutomationMenuLog("Extraction: 139050206 -- June 2020 V1.2", "https://www.menulog.com.au/restaurants-battambang-restaurant-i/menu?utm_source=google&utm_medium=organic&utm_campaign=orderaction")
# runAutomationMenuLog("Extraction: 139520378 -- June 2020 V1.2", "https://www.menulog.com.au/restaurants-delish-pork-roll-newtown/menu/")
# runAutomationMenuLog("Extraction: 134916995 -- June 2020 V1.2", "https://www.menulog.com.au/restaurants-mr-noodles/menu/collection?preorderAgreed=true")
# runAutomationMenuLog("Extraction: 137994844 -- June 2020 V1.2", "https://www.menulog.com.au/restaurants-golden-barbeque-karawara/menu/collection?preorderAgreed=true")

# runAutomationMenuLog("Extraction: 139143202 -- June 2020 V1.2", "https://www.menulog.com.au/restaurants-masala-indian-cuisine-rockhampton/menu")
runAutomationMenuLog("Extraction: 139347723 -- June 2020 V1.2", "https://www.menulog.com.au/restaurants-scarfacepizzeria-northcote/menu/collection?preorderAgreed=true")