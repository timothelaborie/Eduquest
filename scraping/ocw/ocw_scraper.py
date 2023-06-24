import time
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import PyPDF2
from bs4 import BeautifulSoup
import numpy as np
import os
import requests
import spacy
import re
from PIL import Image
import io
import pandas as pd
import imghdr
from urllib.parse import urlparse


nlp = spacy.load('en_core_web_sm')

def extract_questions(text):
    # Split text into sentences
    sentences = re.split('[?.!]', text)
    
    # Initialize empty list for questions
    questions = []
    
    # Iterate over each sentence and extract questions
    for sentence in sentences:
        # Remove leading/trailing whitespace and convert to lowercase
        sentence = sentence.strip().lower()
        
        # Check if sentence ends with a question mark
        if sentence.endswith('?'):
            # Use spaCy to parse the sentence and extract noun chunks
            doc = nlp(sentence)
            noun_chunks = list(doc.noun_chunks)
            
            # Iterate over each noun chunk and check if it is a valid question
            for chunk in noun_chunks:
                # Extract the root verb of the noun chunk
                root_verb = None
                for token in chunk:
                    if token.dep_ == 'ROOT' and token.pos_ == 'VERB':
                        root_verb = token.lemma_
                        break
                
                # Check if the root verb is a question word or a verb that implies a question
                if root_verb in ['what', 'where', 'when', 'who', 'why', 'how', 'carry', 'perform', 'write', 'find', 'compute']:
                    # Append the question to the list
                    questions.append(chunk.text.strip())
    
    # Return the list of questions
    return questions

def base_extractor(driver):
    # Find all links ending with "(PDF)"
    links = driver.find_elements(By.XPATH, "//a[contains(., 'PDF')]")
    for i, link in enumerate(links):
        links[i] = links[i].get_attribute("href")

    notes = []
    images = []

    for link in links:
        driver.get(str(link))

    #  Find the "Download File" button
        try:
            download_button = driver.find_element(By.XPATH, "//a[contains(., 'Download File')]")
        except:
            print("No Download Button")
            continue

        # Click on the button to download the PDF file
        download_button.click()
        new_url = driver.current_url

        response = requests.get(new_url)
        with open('lecture.pdf', 'wb') as f:
            f.write(response.content)

        with open('lecture.pdf', 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ''
            for page in pdf_reader.pages:
                # Check if the page has images
                if '/XObject' in page['/Resources']:
                    x_objects = page['/Resources']['/XObject'].get_object()
                    if isinstance(x_objects, PyPDF2.generic.DictionaryObject):
                        for i, obj in enumerate(x_objects):
                            if x_objects[obj]['/Subtype'] == '/Image':
                                # Save the image
                                try:
                                    img_data = x_objects[obj].get_data()
                                    img_stream = io.BytesIO(img_data)
                                    img_stream.seek(0)
                                    images += [img_stream]
                                except:
                                    print(f"Error downloading image {i} on page")
                # Extract the text
                text += page.extract_text()
        notes += [text]
    return notes

def question_extractor(driver):
    # Find all links ending with "(PDF)"
    links = driver.find_elements(By.XPATH, "//a[contains(., 'PDF')]")
    for i, link in enumerate(links):
        links[i] = links[i].get_attribute("href")

    notes = []
    images = []

    for link in links:
        driver.get(str(link))

# Find the "Download File" button
        try:
            download_button = driver.find_element(By.XPATH, "//a[contains(., 'Download File')]")
        except:
            print("No Download Button")
            continue

        # Click on the button to download the PDF file
        download_button.click()
        new_url = driver.current_url

        response = requests.get(new_url)
        with open('lecture.pdf', 'wb') as f:
            f.write(response.content)

        with open('lecture.pdf', 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ''
            for page in pdf_reader.pages:
                # Check if the page has images
                if '/XObject' in page['/Resources']:
                    x_objects = page['/Resources']['/XObject'].get_object()
                    if isinstance(x_objects, PyPDF2.generic.DictionaryObject):
                        for i, obj in enumerate(x_objects):
                            if x_objects[obj]['/Subtype'] == '/Image':
                                # Save the image
                                try:
                                    img_data = x_objects[obj].get_data()
                                    img_stream = io.BytesIO(img_data)
                                    img_stream.seek(0)
                                    images += [img_stream]
                                except:
                                    print(f"Error downloading image {i} on page")
                # Extract the text
                text += page.extract_text()
            questions = extract_questions(text)
            if questions == []:
                questions.append(text)
        notes += questions
        #print(text)
    return notes

def find_menu_button(url = "https://ocw.mit.edu/courses/1-00-introduction-to-computers-and-engineering-problem-solving-spring-2012/"):
    # Given course link list, start extracting stuff

    # Set up Selenium web driver
    driver = webdriver.Chrome()
    driver.get(str(url))

    # Wait for the page to load
    # time.sleep(5)

    # Find the menu button and click it
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    menu_button = None
    for button in buttons:
        try:
            if "Menu" in button.find_element(By.TAG_NAME, "span").text:
                menu_button = button
                break
        except selenium.common.exceptions.NoSuchElementException:
            continue

    if menu_button is None:
        print("Could not find menu button")
    else:
        menu_button.click()
    return driver

base_url = "https://ocw.mit.edu"

# Create list of course links, if they do not exists
if os.path.isfile("links.npy"):
    course_links = np.load("links.npy").tolist()
else:
    driver = webdriver.Chrome()

    # Load the webpage
    driver.get(base_url)

    # Wait for the webpage to load
    time.sleep(5)

    # Get the HTML content of the webpage
    html_content = driver.page_source

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all course links on the MIT OCW website
    course_links = []
    while len(course_links) < 2048:
        for link in soup.find_all('a'):
            if '/courses/' in link.get('href') and link.get('href') not in course_links:
                course_links.append(link.get('href'))
                if len(course_links) == 2048:
                    break
        # Scroll down to the bottom of the page to load more courses. Terrible way, but best I found to do it
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        # Get the updated HTML content of the webpage
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

    # Quit the driver
    driver.quit()

    # Print the list of course links
    print(course_links)

    # Save the list of course links
    np.save("links.npy", np.array(course_links))

for url in course_links[1512:]:
    lec, ass, ex = None, None, None
    assignments = []
    exams = []
    print(base_url + url)


    driver = find_menu_button(base_url + url)
    try:
        assignments_link = driver.find_element(By.XPATH, "//a[contains(., 'Assignments')]")
        ass = True
        assignments_url = assignments_link.get_attribute("href")
        print(assignments_url)
        driver.get(assignments_url)
        assignments = question_extractor(driver)
    except selenium.common.exceptions.NoSuchElementException:
        ass = None


    driver = find_menu_button(base_url + url)
    try:
        exams_link = driver.find_element(By.XPATH, "//a[contains(., 'Exams')]")
        ex = True
        exams_url = exams_link.get_attribute("href")
        print(exams_url)
        driver.get(exams_url)
        exams = question_extractor(driver)
    except selenium.common.exceptions.NoSuchElementException:
        ex = None

    if (ex == None and ass == None):
        continue
    if (len(exams) == 0 and len(assignments) == 0):
        continue

    driver = find_menu_button(base_url + url)
    # Find the links
    try:
        lecture_notes_link = driver.find_element(By.XPATH, "//a[contains(., 'Lecture Notes')]")
        lec = True
    except selenium.common.exceptions.NoSuchElementException:
        #No lecture notes means this is irrelevant
        continue

    # Get the href attribute of the links
    lecture_notes_url = lecture_notes_link.get_attribute("href")
    driver.get(lecture_notes_url)

    course_notes = base_extractor(driver)
    print(len(course_notes))

    url_parts = url.split("/")
    new_url_parts = [part for part in url_parts if part and part != ":"]
    new_url = "/".join(new_url_parts[new_url_parts.index("courses") + 1:])

    chapter_list = [new_url for i in range(len(course_notes) + len(assignments) + len(exams))]
    text = course_notes + assignments + exams
    is_question = [False for i in range(len(course_notes))] + [True for i in range(len(assignments) + len(exams))]
    is_exam = [False for i in range(len(course_notes) + len(assignments))] + [True for i in range(len(exams))]

    print("course notes: ", len(course_notes))
    print("assignments: ", len(assignments))
    print("exams: ", len(exams))
    # Create DataFrame from the lists
    df = pd.DataFrame({
        "Chapter": chapter_list,
        "text": text,
        "is_question": is_question,
        "is_exam": is_exam
    })

    df.to_parquet(f"MIT_Processed/{new_url}.parquet")

# Wait for the page to load


# close the driver
driver.quit()

