__author__ = 'alexisgallepe'

import math
import time
import logging

from . import utils
from pubsub import pub

BLOCK_SIZE = 2 ** 14

class Piece(object):
    def __init__(self, pieceIndex, pieceSize, pieceHash):
        self.pieceIndex = pieceIndex
        self.pieceSize = pieceSize
        self.pieceHash = pieceHash
        self.finished = False
        self.files = []
        self.pieceData = b""
        self.BLOCK_SIZE = BLOCK_SIZE
        self.num_blocks = int(math.ceil( float(pieceSize) / BLOCK_SIZE))
        self.blocks = []
        self.initBlocks()

    def initBlocks(self):
        self.blocks = []

        if self.num_blocks > 1:
            for i in range(self.num_blocks):
                    self.blocks.append(["Free", BLOCK_SIZE, b"",0])

            # Last block of last piece, the special block
            if (self.pieceSize % BLOCK_SIZE) > 0:
                self.blocks[self.num_blocks-1][1] = self.pieceSize % BLOCK_SIZE

        else:
            self.blocks.append(["Free", int(self.pieceSize), b"",0])

    def setBlock(self, offset, data, write=True):
        if not self.finished:
            if offset == 0:
                index = 0
            else:
                index = int(offset / BLOCK_SIZE)

            self.blocks[index][2] = data
            self.blocks[index][0] = "Full"
            self.isComplete(write=write)

    def getBlock(self, block_offset,block_length):
        return self.pieceData[block_offset:block_length]

    def getEmptyBlock(self):
        if not self.finished:
            blockIndex = 0
            for block in self.blocks:
                if block[0] == "Free":
                    block[0] = "Pending"
                    block[3] = int(time.time())
                    return self.pieceIndex, blockIndex * BLOCK_SIZE, block[1]
                blockIndex+=1
        return False


    def freeBlockLeft(self):
        for block in self.blocks:
            if block[0] == "Free":
                return True
        return False


    def isCompleteOnDisk(self):
        block_offset = 0
        data = b''
        for f in self.files:
            try:
                f_ptr = open(f["path"],'rb')
            except IOError:
                all_files_finished = False
                break
            f_ptr.seek(f["fileOffset"])
            data += f_ptr.read(f["length"])
            f_ptr.close()
            block_offset += f['length']
        if self.isHashPieceCorrect(data):
            for block in range(self.num_blocks):
                start_offset = block*BLOCK_SIZE
                end_offset = block*BLOCK_SIZE + BLOCK_SIZE
                self.setBlock(offset=start_offset, data=data[start_offset: end_offset], write=False)


    def isComplete(self, write=True):
        # If there is at least one block Free|Pending -> Piece not complete -> return false
        for block in self.blocks:
            if block[0] == "Free" or block[0] == "Pending":
                return False

        # Before returning True, we must check if hashes match
        data = self.assembleData()
        if self.isHashPieceCorrect(data):
            self.finished = True
            self.pieceData = data
            if write:
                self.writeFilesOnDisk()
            pub.sendMessage('PiecesManager.PieceCompleted',pieceIndex=self.pieceIndex)
            return True

        else:
            return False


    def writeFunction(self,pathFile,data,offset):
        try:
            f = open(pathFile,'r+b')
        except IOError:
            f = open(pathFile,'wb')
        f.seek(offset)
        f.write(data)
        f.close()

    def writeFilesOnDisk(self):
        for f in self.files:
            pathFile = f["path"]
            fileOffset = f["fileOffset"]
            pieceOffset = f["pieceOffset"]
            length = f["length"]

            self.writeFunction(pathFile, self.pieceData[pieceOffset: pieceOffset + length], fileOffset)


    def assembleData(self):
        buf = b""
        for block in self.blocks:
            buf+=block[2]
        return buf

    def isHashPieceCorrect(self,data):
        if utils.sha1_hash(data) == self.pieceHash:
            return True
        else:
            #logging.warning("Error Piece Hash")
            #logging.debug("{0} : {1}".format(utils.sha1_hash(data), self.pieceHash))
            self.initBlocks()
            return False
