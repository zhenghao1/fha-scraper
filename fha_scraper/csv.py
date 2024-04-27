from typing import List
from bs4 import BeautifulSoup, Tag
import pandas as pd
import re
import logging

logging.basicConfig(level=logging.DEBUG)


def remove_non_ascii(text: str) -> str:
    """
    Removes non-ASCII characters from the given text.

    Args:
        text (str): The input text from which non-ASCII characters will be removed.

    Returns:
        str: The input text with non-ASCII characters replaced by spaces.
    """
    pattern: str = r"[^\x00-\x7F]"
    replacement: str = " "
    return re.sub(pattern, replacement, text)


def get_visitor_elements(html: str) -> List[Tag]:
    """
    Parses the HTML file and returns a list of visitor elements.

    Args:
        filename (str): The name of the HTML file.

    Returns:
        List[Tag]: A list of visitor elements.
    """
    soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
    visitor_elements: List[Tag] = soup.find_all("li", class_="p1")
    return visitor_elements


def generate_country_csv(html: str, output_filename: str):
    """
    Generates a CSV file containing visitor information for a given HTML file.

    Args:
        html (str): The HTML content to extract visitor information from.
        output_filename (str): The name of the output CSV file.

    Returns:
        None

    This function takes an HTML string as input and extracts visitor information from it. 
    It uses the `get_visitor_elements` function to find all visitor elements in the HTML. 
    For each visitor element, it extracts the name, title, and company information from the first `div` 
    element with the class `col-md-12`. The extracted information is stored in a list of lists called `visitors`. 
    After processing all visitor elements, a pandas DataFrame is created from the `visitors` list with 
    columns 'Name', 'Title', and 'Company'. The DataFrame is then saved as a CSV file with the specified 
    `output_filename`.

    Note: The function assumes that the HTML content contains visitor elements with the class `p1` and 
    that each visitor element has a first `div` element with the class `col-md-12`.
    """
    visitor_elements = get_visitor_elements(html)
    visitors = []
    logging.info("Beginning processing of visitors....")
    for visitor in visitor_elements:
        try:
            first_div = visitor.find_all("div", class_="col-md-12")[0]
        except:
            logging.debug("Unable to process a div")
            continue
        name_element = first_div.select_one(":nth-child(1)")
        title_element = first_div.select_one(":nth-child(2)")
        company_element = first_div.select_one(":nth-child(3)")
        logging.debug("Processing, name:  %s", name_element.text)
        if re.search(u'[\u4e00-\u9fff]', name_element.text):
            attendee_name = name_element.text
        else:
            attendee_name = remove_unicode(name_element.text)
        visitors.append(
            [
                attendee_name,
                remove_non_ascii(title_element.text.strip()),
                company_element.text.strip(),
            ]
        )
    logging.info("Processing of visitors completed!")
    df = pd.DataFrame(visitors, columns=["Name", "Title", "Company"])
    df.to_csv(output_filename, index=False)

def remove_unicode(name: str) -> str:
    """
    Removes unicode characters from the given name, encodes it in ASCII, and capitalizes the result.

    Args:
        name (str): The name to remove unicode characters from.

    Returns:
        str: The modified name with unicode characters removed and capitalized.
    """
    return name.strip().encode('ascii', 'ignore').decode().capitalize()
