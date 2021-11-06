#!/usr/bin/env python3

# REQUIREMENTS: pip install bs4 & pip install lxml

import sys
import csv
import requests
import re
from bs4 import BeautifulSoup


def load_page(url):
    """
    Get the source of the page at the specified url
    """
    with requests.get(url) as f:
        page = f.text
    return page


def get_element_text(element):
    """
    This function will try to get the text from an element which may or may not exist.
    If the element is not found, it will return an empty string.
    
    By using a function like this, we can be sure that our program doesn't
    crash if it can't find something.
    """
    try:
        return element.text.strip()
    except AttributeError as e:
        # This is the error python raises if a method is not available
        print('Element not found, error: {}'.format(e), file=sys.stderr)
        return ''


def get_songs(url):
    """
    Get a list containing information about songs. In this case, each item in
    the list is a dictionary, containing the name of a song, a link to the
    information page of the song, the name of the album where the song was
    first released, when the song was played first and last, and how many
    times a song has been played.
    
    If something goes wrong, and no list can be generated, the program will
    exit.
    """
    index_page = BeautifulSoup(load_page(url), 'lxml') # Parse the page
    print(index_page)
    exit()
    items = index_page.find(id='item-list') # Get the list on from the webpage
    if not items: # If the webpage does not contain the list, we should exit
        print('Something went wrong!', file=sys.stderr)
        sys.exit()
    data = list()
    for row in items.find_all(class_='line_detail'): # Go over the entries line-by-line
        # Get the text in the first element with the class 'song'
        # Note: we use class_ with an underscore, as class is already a
        # reserved python keyword. This means we can't use it as a
        # variable name.
        song = row.find(class_='song').find('a').text.strip() # Link text
        link = row.find(class_='song').find('a').get('href') # Link url
        album_name = row.find(class_='release').text.strip()
        first_played = row.find_all(class_='played')[0].text.strip()
        last_played = row.find_all(class_='played')[1].text.strip()
        times_played = row.find(class_='times').text.strip()
        # Store the data in a dictionary, and add that to our list
        data.append({
                     'song': song,
                     'link': link,
                     'album name': album_name,
                     'first played': first_played,
                     'last played': last_played,
                     'times played': times_played
                    })
    return data


def get_song_info(url):
    """
    Get information about a song if possible. This information will be returned
    as a dictionary containing the credits and lyrics of a song.
    """
    song_page = BeautifulSoup(load_page(url), 'lxml') # Parse the requested page
    # Get the part of the page where the interesting information is 'stored'
    interesting_html = song_page.find('article')
    if not interesting_html: # Check if an article tag was found, not all pages have one
        print('No information availible for song at {}'.format(url), file=sys.stderr)
        return {} # Return an empty dictionary
    # title = interesting_html.find('h2').text.strip() # We already have this information
    credits = get_element_text(interesting_html.find(class_='credit'))
    lyrics = get_element_text(interesting_html.find(class_='lyrics'))
    lyrics = lyrics.replace('\r\n', '\n') # Windows newline to Unix newline
    # After each song, there are a bunch of tabs, and a copyright notice.
    # We want that notice on a new line, as it is cleaner. To do this, we
    # can use a regular expression which finds any occurence of two or more
    # tabs directly after each other: '\t\t+'. The first \t is the first tab,
    # the second \t is the second tab, and the + means: 1 or more times, and
    # applies to the previous character (the second tab).
    lyrics = re.sub('\t\t+', '\n', lyrics)
    return {'credits': credits, 'lyrics': lyrics} # Return the data of interest


def main():

    index_url = 'https://es-jobs.about.ikea.com/buscar-trabajo?acm=ALL&alrpm=2510769&ascf=[%7B%22key%22:%22ALL%22,%22value%22:%22%22%7D]' # Contains a list of songs
    song_data = get_songs(index_url) # Get songs with metadata

    for row in song_data:
        print('Scraping info on {}.'.format(row['song'])) # Might be useful for debugging
        url = row['link']
        song_info = get_song_info(url) # Get lyrics and credits for this song, if available

        for key, value in song_info.items():
            row[key] = value # Add the new data to our dictionary

            
            
    with open('songs.csv', 'w', encoding='utf-8') as f: # Open a csv file for writing
        fieldnames=['song', 'album name', 'first played', 'last played',
                    'times played', 'credits', 'lyrics'] # These are the values we want to store
        writer = csv.DictWriter(f,
                                delimiter=',', # Common delimiter
                                quotechar='"', # Common quote character
                                quoting=csv.QUOTE_NONNUMERIC, # Make sure that all strings are quoted
                                fieldnames=fieldnames
                               )
        writer.writeheader() # Create headers in our csv file
        for row in song_data:
            # We have some data that we don't want to store, so we check for
            # each key in the dictionary if it is something we want to keep.
            # We do this with a dictionary comprehension, which does the following:
            # 
            # For each key, value pair in row.items():
            #   if the key occurs in fieldnames:
            #     put key: value in a new dictionary
            # return the new dictionary
            writer.writerow({k:v for k,v in row.items() if k in fieldnames})

if __name__ == '__main__':
    main()
