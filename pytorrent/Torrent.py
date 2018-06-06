__author__ = 'alexisgallepe'

import time
import bencode
import logging
import os
from . import utils


class Torrent(object):
    def __init__(self, path, file_store):
        self.file_store = file_store
        with open(path, 'r') as file:
            contents = file.read()

        self.torrentFile = bencode.bdecode(contents)
        self.totalLength = 0
        self.pieceLength = self.torrentFile['info']['piece length']
        self.pieces = self.torrentFile['info']['pieces']
        self.info_hash = utils.sha1_hash(str(
            bencode.bencode(self.torrentFile['info'])
        ))
        self.peer_id = self.generatePeerId()
        self.announceList = self.getTrakers()
        self.fileNames = []

        self.getFiles()

        if self.totalLength % self.pieceLength == 0:
            self.numberOfPieces = self.totalLength / self.pieceLength
        else:
            self.numberOfPieces = (self.totalLength / self.pieceLength) + 1

        logging.debug(self.announceList)
        logging.debug(self.fileNames)

        assert(self.totalLength > 0)
        assert(len(self.fileNames) > 0)

    def getFiles(self):
        root = self.file_store + self.torrentFile['info']['name'] #+ "/"
        if 'files' in self.torrentFile['info']:
            if not os.path.exists(root):
                os.mkdir(root, 0o766 )

            for f in self.torrentFile['info']['files']:
                pathFile = os.path.join(root, *f["path"])

                if not os.path.exists(os.path.dirname(pathFile)):
                    os.makedirs(os.path.dirname(pathFile))

                self.fileNames.append({"path": pathFile , "length": f["length"]})
                self.totalLength += f["length"]

        else:
            self.fileNames.append({"path": root , "length": self.torrentFile['info']['length']})
            self.totalLength = self.torrentFile['info']['length']

    def getTrakers(self):
        if 'announce-list' in self.torrentFile:
            return self.torrentFile['announce-list']
        else:
            return [[ self.torrentFile['announce'] ]]

    def generatePeerId(self):
        seed = str(time.time())
        return utils.sha1_hash(seed)