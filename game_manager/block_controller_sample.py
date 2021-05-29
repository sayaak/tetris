#!/usr/bin/python3
# -*- coding: utf-8 -*-

import math
from datetime import datetime
import numpy as np
import pprint

class Block_Controller(object):

    # init parameter
    board_backboard = 0
    board_data_width = 0
    board_data_height = 0
    ShapeNone_index = 0
    CurrentShape_class = 0
    NextShape_class = 0

    # GetNextMove is main function.
    # input
    #    nextMove : nextMove structure which is empty.
    #    GameStatus : block/field/judge/debug information. 
    #                 in detail see the internal GameStatus data.
    # output
    #    nextMove : nextMove structure which includes next shape position and the other.
    def GetNextMove(self, nextMove, GameStatus):

        t1 = datetime.now()

        # print GameStatus
        print("=================================================>")
        pprint.pprint(GameStatus, width = 61, compact = True)

        # get data from GameStatus
        # current shape info
        CurrentShapeDirectionRange = GameStatus["block_info"]["currentShape"]["direction_range"]
        self.CurrentShape_class = GameStatus["block_info"]["currentShape"]["class"]
        # next shape info
        NextShapeDirectionRange = GameStatus["block_info"]["nextShape"]["direction_range"]
        self.NextShape_class = GameStatus["block_info"]["nextShape"]["class"]
        # current board info
        self.board_backboard = GameStatus["field_info"]["backboard"]
        # default board definition
        self.board_data_width = GameStatus["field_info"]["width"]
        self.board_data_height = GameStatus["field_info"]["height"]
        self.ShapeNone_index = GameStatus["debug_info"]["shape_info"]["shapeNone"]["index"]

        # search best nextMove -->
        strategy = None
        LatestEvalValue = -100000
        # search with current block Shape
        for direction0 in CurrentShapeDirectionRange:
            # search with x range
            minX, maxX, _, _ = self.CurrentShape_class.getBoundingOffsets(direction0)
            for x0 in range(-minX, self.board_data_width - maxX):
                # get board data, as if dropdown block with candidate direction and x location. 
                board = self.calcBoard(self.board_backboard, self.CurrentShape_class, direction0, x0)
                EvalValue = self.calculateEvalValue(board)
                if EvalValue > LatestEvalValue:
                    strategy = (direction0, x0, 1, 1)
                    LatestEvalValue = EvalValue

                #for direction1 in NextShapeDirectionRange:
                #    minX, maxX, _, _ = self.NextShape_class.getBoundingOffsets(direction1)
                #    for x1 in range(-minX, self.board_data_width - maxX):
                #        board2 = self.calcBoard(board, self.NextShape_class, direction1, x1)
                #        EvalValue = self.calculateEvalValue(board2)
                #        if EvalValue > LatestEvalValue:
                #            strategy = (direction0, x0, 1, 1)
                #            LatestEvalValue = EvalValue
        # search best nextMove <--

        print("===", datetime.now() - t1)
        nextMove["strategy"]["direction"] = strategy[0]
        nextMove["strategy"]["x"] = strategy[1]
        nextMove["strategy"]["y_operation"] = strategy[2]
        nextMove["strategy"]["y_moveblocknum"] = strategy[3]
        print(nextMove)
        print("###### SAMPLE CODE ######")
        return nextMove

    def calcBoard(self, board_backboard, Shape_class, direction, x):
        board = np.array(board_backboard).reshape((self.board_data_height, self.board_data_width))
        _board = self.dropDown(board, Shape_class, direction, x)
        return _board

    def dropDown(self, board, Shape_class, direction, x):
        dy = self.board_data_height - 1
        for _x, _y in Shape_class.getCoords(direction, x, 0):
            _yy = 0
            while _yy + _y < self.board_data_height and (_yy + _y < 0 or board[(_y + _yy), _x] == self.ShapeNone_index):
                _yy += 1
            _yy -= 1
            if _yy < dy:
                dy = _yy
        _board = self.dropDownByDist(board, Shape_class, direction, x, dy)
        return _board

    def dropDownByDist(self, board, Shape_class, direction, x, dy):
        _board = board
        for _x, _y in Shape_class.getCoords(direction, x, 0):
            _board[_y + dy, _x] = Shape_class.shape
        return _board

    def calculateEvalValue(self, board):

        width = self.board_data_width
        height = self.board_data_height

        # evaluation paramters
        ## lines to be removed
        fullLines = 0
        ## number of holes or blocks in the line.
        vHoles, vBlocks = 0, 0
        ## how blocks are accumlated
        BlockMaxY = [0] * width
        holeCandidates = [0] * width
        holeConfirm = [0] * width

        ### check board
        # each y line
        for y in range(height - 1, 0, -1):
            hasHole = False
            hasBlock = False
            # each x line
            for x in range(width):
                ## check if hole or block..
                if board[y, x] == self.ShapeNone_index:
                    # hole
                    hasHole = True
                    holeCandidates[x] += 1  # just candidates in each column..
                else:
                    # block
                    hasBlock = True
                    BlockMaxY[x] = height - y    # update blockMaxY
                    if holeCandidates[x] > 0:
                        holeConfirm[x] += holeCandidates[x]  # update number of holes in target column..
                        holeCandidates[x] = 0                # reset
                    if holeConfirm[x] > 0:
                        vBlocks += 1                         # update number of isolated blocks

            if hasBlock == False:
                # no block line (and ofcourse no hole)
                continue
            if hasBlock == True and hasHole == False:
                # filled with block
                fullLines += 1

        vHoles += sum([abs(x) for x in holeConfirm])

        ### absolute differencial value of MaxY
        BlockMaxDy = [BlockMaxY[i] - BlockMaxY[i+1] for i in range(len(BlockMaxY) - 1)]
        absDy = sum([abs(x) for x in BlockMaxDy])
        ### maxDy
        maxDy = max(BlockMaxY) - min(BlockMaxY)
        ### maxHeight
        maxHeight = max(BlockMaxY) - fullLines

        # statistical data
        ### stdY
        if len(BlockMaxY) <= 0:
            stdY = 0
        else:
            stdY = math.sqrt(sum([y ** 2 for y in BlockMaxY]) / len(BlockMaxY) - (sum(BlockMaxY) / len(BlockMaxY)) ** 2)
        ### stdDY
        if len(BlockMaxDy) <= 0:
            stdDY = 0
        else:
            stdDY = math.sqrt(sum([y ** 2 for y in BlockMaxDy]) / len(BlockMaxDy) - (sum(BlockMaxDy) / len(BlockMaxDy)) ** 2)


        # calc Evaluation Value
        score = 0
        score = score + fullLines * 10.0           # try to delete line 
        score = score - vHoles * 1.0               # try not to make hole
        score = score - vBlocks * 1.0              # try not to make isolated block
        score = score - absDy * 1.0                # try to put block smoothly
        #score = score - maxDy * 0.3                # maxDy
        #score = score - maxHeight * 5              # maxHeight
        #score = score - stdY * 1.0                 # statistical data
        #score = score - stdDY * 0.01               # statistical data

        # print(score, fullLines, vHoles, vBlocks, maxHeight, stdY, stdDY, absDy, BlockMaxY)
        return score


BLOCK_CONTROLLER_SAMPLE = Block_Controller()

