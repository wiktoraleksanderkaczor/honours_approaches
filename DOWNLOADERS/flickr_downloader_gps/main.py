"""
    Putting everything together in main.py we have.
"""

from flickr import get_urls
from downloader import download_images
from topics import geosearch
import os
import time

all_topics = ["statue of liberty", "eiffel tower", "great wall of china",
    "pyramid of giza", "leaning tower of pisa", "kremlin", "machu picchu", 
    "sydney opera house", "taj mahal", "easter island moai", "colosseum", 
    "empire state building", "hollywood sign", "golden gate bridge", "notre dame",
    "tokyo tower", "london eye", "st peter basilica", "sagrada familia", "little mermaid", 
    "st basil cathedral", "arc de triomphe", "berlin wall", "stonehenge", "kilimanjaro",
    "uluru ayers rock", "the great sphinx", "tower bridge", "the forbidden city china",
    "mount everest", "capitol hill", "wilis tower sears tower", "brooklyn bridge", 
    "burj al arab hotel", "acropolis greece", "trevi fountain", "st mark basilica", 
    "st mark campanile", "times square", "the white house", "louvre museum",
    "manneken pis brussels", "buckingham palace", "versailles", "neuschwanstein castle",
    "matterhorn", "pompeii", "florence cathedral", "christ the redeemer rio de janerio brazil",
    "CN tower", "the grand canyon", "niagara falls", "burj khalifa", "tower of london", 
    "madrid palace", "mont st michel france", "las vegas", "petronas twin towers",
    "windsor castle", "sacre coeur paris", "st paul cathedral", "central park", 
    "mount rushmore", "mount fuji", "rialto bridge", "arena di verona", "space needle", 
    "westminster abbey", "rock of gibraltar", "alcatraz", "white cliffs of dover", 
    "iguazu national park argentina", "washington monument", "the shard", "the gherkin",
    "moai", "temple of luxor", "brandenburg gate berlin", "cologne cathedral", "pentagon",
    "vesuvio", "mayan pyramids of chichen itza", "cloud gate chicago", "angkor wat cambodia",
    "victoria falls", "terracotta warriors", "potala palace lhasa", "petra", "yellowstone national park",
    "hagia sophia", "oriental pearl tower", "nyhavn", "ponte vecchio", "wailing wall", "loch ness",
    "mecca", "sydney harbor bridge", "sistine chapel", "spanish steps", "bridge of sighs",
    "pompidue center", "summer palace imperial garden beijing", "mount etna", "lascaux caves france", 
    "bryce canyon national park", "great buddha", "freedom tower ground zero", "kronborg castle", 
    "gateway arch", "shanghai world financial center", "moulin rouge", "redwood national park", "santorini",
    "mill complex kinderdijk", "monument valley navajo tribal park", "tsarskoye selo catherine palace st petersburg russia",
    "juliet balcony", "berlin cathedral", "helsinki cathedral", "tivoli gardens", "bath england", "brighton pier",
    "disneyland paris", "giant causeway", "everglades national park", "alhambra", "papel palace avignon", "pond du garre",
    "festung hohensalzburg", "bran castle", "prague castle", "chapel bridge", "piazza del campo siena", 
    "portofino", "table mountain", "atomium brussels", "guggenheim museum bilbao", "hollywood walk of fame", "death valley", 
    "winter palace", "amalienborg palace", "ellis island immigration museum", "british museum", "oxford university", "blue lagoon", 
    "blue mosque istanbul", "piccadilly circus", "trafalgar square", "millau bridge france", "newgrange"]

all_topics = ["eiffel tower"]

# Remove duplicates
all_topics = list(dict.fromkeys(all_topics))

images_per_topic = 500
print("Number of topics: " + str(len(all_topics)))
print("Images per topic: " + str(images_per_topic))
print("Total images: " + str(images_per_topic * len(all_topics)))

def download():
    for topic in all_topics:

        print("Getting urls for", topic)
        urls = get_urls(topic, images_per_topic)
        
        print("Downloading images for", topic)
        path = os.path.join("/home/badfox/Data/street_data", topic)

        download_images(urls, path)

if __name__=="__main__":

    start_time = time.time()

    # Download the images.
    download()

    print("Took", round(time.time() - start_time, 2), "seconds")
