""" request beast, parsing monster, a core at it's best """
import multiprocessing
from time import sleep
import concurrent.futures as cf
import os
from re import sub as re_sub
#import sqlite3

import requests

from helpers import safety_wrapper, HLogger, PATHSEP, DANGER_CHARS
from album import Album
from messagehandler import MessageHandler
from htmlparser import parse_album_metadata, parse_albums, parse_maxpages, parse_tags, parse_downloadable_tracks
from messages import Msg, MsgGetTags, MsgPutAlbums, MsgPutFetchTags, MsgPutTags, MsgDownloadAlbums, MsgFinishedDownloads, MsgPause, MsgSetProgress, MsgQuit

LOGGER = HLogger(name="rbmd.webcon")

class Connector(multiprocessing.Process):
    """ Connector Class """

    # pylint: disable=too-many-instance-attributes

    @safety_wrapper
    def __init__(self, connectionParams: dict):
        """ init init init """
        multiprocessing.Process.__init__(self)
        self.executor: cf.ThreadPoolExecutor = None
        self.messagehandler: MessageHandler = None
        self.connectionParams: dict = connectionParams

        # TODO: optimize the events away # maybe except pause event
        self.get_genres_event: multiprocessing.Event = multiprocessing.Event()
        self.get_albums_event: multiprocessing.Event = multiprocessing.Event()
        self.pause_fetch: multiprocessing.Event = multiprocessing.Event()
        self.pause_fetch.clear()

        self.taglist: set = set()
        self.stop: bool = False
        self.session: requests.Session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Android 12; Mobile; rv:97.0) Gecko/97.0 Firefox/97.0"})
        self.apiurl: str = "https://bandcamp.com/tag/%s?page=%s"  # tag, pagenum
        self.start()

    @safety_wrapper
    def __del__(self):
        """ delet dis """
        if self.messagehandler:
            self.messagehandler.__del__()
        if self.executor:
            self.executor.shutdown()
        self.stop = True

    @safety_wrapper
    def download_file(self, srcfile, srcurl):
        """Function to Downloadad and verify downloaded Files"""
        if not os.path.exists(srcfile): # check if file exsists
            LOGGER.debug(f"Downloading {srcurl} as {srcfile}")
            try:
                response: requests.Response = self.session.get(srcurl) # get request
                with open(srcfile, "wb") as fifo: # open in binary write mode
                    fifo.write(response.content) # write to file
            except FileNotFoundError as excp:
                LOGGER.exception(f"Tried to download {srcfile}:\n{excp}")

    @safety_wrapper
    def get_genres(self):
        """ func to request + parse bandcamps default tags """
        self.get_genres_event.clear() # TODO: optimize for no event
        LOGGER.debug("Obtaining Tags")
        resp: requests.Response = self.session.get("https://bandcamp.com/tags") # fetch all tags from the tags page
        tags: list = parse_tags(resp.text.split("\n")) # parse them
        self.messagehandler.send(MsgPutTags(data=tags)) # return them
        LOGGER.debug("Msg sent")

    @safety_wrapper
    def get_fetch_tags(self, msg):
        """ updates the list of tags that need to be fetched during current/next iteration """
        self.taglist: set = set(msg.data)
        LOGGER.debug(f"got tags from Msg {self.taglist}")
        self.get_albums_event.set()

    @safety_wrapper
    def get_albums(self):
        """ func grabs albums based on fetch-tags, parses and adds sprinkles of metadata on them """
        LOGGER.debug(f"Getting Albums for Tags: {self.taglist}")
        self.get_albums_event.clear()
        for tag in self.taglist: # iterate the tags
            # check albums from db
            resp1: requests.Response = self.session.get(self.apiurl % (tag, "0")) # get the first page of /tag/XXX and parse the maximum pages
            maxpages: int = parse_maxpages(
                resp1.text.split("\n"))
            self.messagehandler.send(MsgSetProgress(0, maxpages, f"{tag}: Fetching Page 0/{maxpages}"))
            for num in range(1, maxpages+1): # repeat fetching+parsing the tags page
                if not self.pause_fetch.is_set(): # TODO: should this be a while-loop
                    resp2: requests.Response = self.session.get(self.apiurl % (tag, num)) # fetch the current tag page
                    albums: set = parse_albums(
                        resp2.text.split("\n")) # parse the fetched page for albums
                    future_metadata = {self.executor.submit( # TODO: optimize this
                        self.update_album_metadata, album): album for album in albums} # add the albums to the threadpool executor
                    for future in cf.as_completed(future_metadata): # iterate and wait for executor completion
                        supposed_album = future_metadata[future]
                        try:
                            future.result() # check the executors results
                        except Exception as excp:
                            LOGGER.exception(
                                f"{supposed_album} has thrown Exception:\n{excp}")
                    albumdata: set = {tag: albums} # save the albums in relation to its tags
                    self.messagehandler.send(MsgSetProgress(num, maxpages, f"{tag}: Fetching Page {num}/{maxpages}"))
                    self.messagehandler.send(MsgPutAlbums(data=albumdata))
                    #LOGGER.debug(f"{albums}")
                    # add albums to db
                else:
                    sleep(1)
                    return None
        return None

    @safety_wrapper
    def update_album_metadata(self, album: Album) -> Album:  # get pictures too
        """ func that grabs+parses album metadata """
        LOGGER.debug(f"Updating Tags for {album.name}")
        resp: requests.Response = self.session.get(album.url) # get the albums linked tags
        album.genre = parse_album_metadata(
            resp.text.split("\n"))
        resp2: requests.Response = self.session.get(album.cover_url) # get the albums cover
        album.cover = resp2.content
        return album

    #def add_album_to_db(self, album):
    #    """ func to smartly insert new albums into db """
    #    pass

    @safety_wrapper
    def download_albums(self, msg):
        """ downloads all albums from message """
        albumlist: list = msg.get_data()
        self.messagehandler.send(MsgSetProgress(0, len(albumlist), f"Downloading Album 0/{len(albumlist)}"))
        for album in albumlist:
            location: str = f"Albums{PATHSEP}{re_sub(DANGER_CHARS, '_', album.__str__()).strip('.')}{PATHSEP}"
            if not os.path.exists(location): # check & create the download location
                os.makedirs(location)
            if album.cover: # save the cover from the album
                with open(f"{location}cover.jpg", "w+b") as cover:
                    cover.write(album.cover)
            resp: requests.Response = self.session.get(album.url) # request the album
            tracklist: list = parse_downloadable_tracks(resp.text.split("\n"))
            for track in tracklist: # iterate and download
                self.download_file(f"{location}{track[0]}.mp3", track[1])
            index: int = albumlist.index(album) + 1 # update the UI
            self.messagehandler.send(MsgSetProgress(index , len(albumlist), f"Downloading Album {index}/{len(albumlist)}"))
        self.messagehandler.send(MsgFinishedDownloads(None))

    @safety_wrapper
    def analyze(self, msg: Msg):
        """ generic "callback" to check msgs and set flags and call functions """
        if msg is not None:
            if isinstance(msg, MsgGetTags):
                self.get_genres_event.set()
            elif isinstance(msg, MsgPutFetchTags):
                self.get_fetch_tags(msg)
            elif isinstance(msg, MsgDownloadAlbums):
                self.download_albums(msg)
            elif isinstance(msg, MsgPause):
                self.pause_fetch.set()
            elif isinstance(msg, MsgQuit):
                self.__del__()
            else:
                LOGGER.error(f"Unknown Message:\n{msg}")

    @safety_wrapper
    def run(self):
        """ RUN! """
        # little hack the avoids pickling a queue when forking ;)
        self.executor = cf.ThreadPoolExecutor(max_workers=15)
        self.messagehandler = MessageHandler(self.connectionParams, type(self).__name__, isClient=True)
        while not self.stop:
            if not self.messagehandler: # if the messagehandler "disappers", expect the connection to be lost/the other side crashed/closed forcefully
                self.__del__() # and close this to prevent this process running indefinetely in the background
            self.analyze(self.messagehandler.recieve())
            if self.get_genres_event.is_set():
                self.get_genres()
            elif self.get_albums_event.is_set():
                self.get_albums()
            sleep(0.1)
