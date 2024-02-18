from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
import sys, os, time, re
from calc import getDistance, getAngle, getPositionAtAngle


def tiles_replace_stranded(placed, tilemap):
	colorWater = (64, 128, 160)
	colorLand = (128, 180, 96)
	colorRock = (72, 72, 72)
	colorForest = (32, 128, 96)
	colorRoad = (255, 255, 255)
	colorDirt = (32, 16, 16)
	colorPlaza = (180, 180, 180)
	colorBuilding = (80, 80, 80)
	colorWall = (96, 96, 96)

	changelist = []
	changedTiles = set()

	for tileX in range(0, int(placed.w)):
		for tileY in range(0, int(placed.h)):
			if tilemap[tileX,tileY] == colorRock or tilemap[tileX,tileY] == colorBuilding or tilemap[tileX,tileY] == colorWall:

				orphaned = False
				thisTile = tilemap[tileX,tileY]

				if tileX > 0 and tileX < placed.w-1 and tilemap[tileX-1,tileY] != tilemap[tileX,tileY] and tilemap[tileX+1,tileY] != tilemap[tileX,tileY] and tilemap[tileX-1,tileY] != thisTile and tilemap[tileX+1,tileY] != thisTile:
					orphaned = True
					target = tilemap[tileX+1,tileY]
					
				if tileY > 0 and tileY < placed.h-1 and tilemap[tileX,tileY-1] != tilemap[tileX,tileY] and tilemap[tileX,tileY+1] != tilemap[tileX,tileY] and tilemap[tileX,tileY-1] != thisTile and tilemap[tileX,tileY+1] != thisTile:
					orphaned = True
					target = tilemap[tileX,tileY+1]

				if orphaned:
					target = tilemap[tileX,tileY]
					replacements = set()

					for xd in range(-1,2):
						for yd in range(-1,2):
							if tileX+xd > 0 and tileX+xd < placed.w-1 and tileY+yd > 0 and tileY+yd < placed.h-1:
								if tilemap[tileX+xd,tileY+yd] != thisTile:
									replacements.add(tilemap[tileX+xd,tileY+yd])

					if colorForest in replacements:
						target = colorForest
					elif colorRoad in replacements:
						target = colorRoad
					elif colorLand in replacements:
						target = colorLand

					changedTiles.add((tileX,tileY))
					changelist.append((tileX,tileY,target))

	for tileX, tileY, target in changelist:
		if (tileX-1,tileY) in changedTiles or (tileX+1,tileY) in changedTiles or (tileX,tileY-1) in changedTiles or (tileX,tileY+1) in changedTiles: #ignore if the are other fences nearby
			continue

		# tilemap[tileX,tileY] = colorDirt
		tilemap[tileX,tileY] = target


def tiles_smooth(placed, tilemap):
	colorWater = (64, 128, 160)
	colorLand = (128, 180, 96)
	colorRock = (72, 72, 72)
	colorForest = (32, 128, 96)
	colorRoad = (255, 255, 255)
	colorDirt = (32, 16, 16)
	colorPlaza = (180, 180, 180)

	changelist = []

	for tileX in range(0, int(placed.w)):
		for tileY in range(0, int(placed.h)):

			if tilemap[tileX,tileY] == colorLand or tilemap[tileX,tileY] == colorRock:
				if tilemap[tileX,tileY] == colorLand:
					targets = set([colorRoad, colorDirt])
				elif tilemap[tileX,tileY] == colorRock:
					targets = set([colorRoad, colorDirt, colorPlaza, colorForest])

				orphaned = False
				target = tilemap[tileX,tileY]

				if tileX > 0 and tileX < placed.w-1 and tilemap[tileX-1,tileY] != tilemap[tileX,tileY] and tilemap[tileX+1,tileY] != tilemap[tileX,tileY] and tilemap[tileX-1,tileY] in targets and tilemap[tileX+1,tileY] in targets:
					orphaned = True
					target = tilemap[tileX+1,tileY]
					
				if tileY > 0 and tileY < placed.h-1 and tilemap[tileX,tileY-1] != tilemap[tileX,tileY] and tilemap[tileX,tileY+1] != tilemap[tileX,tileY] and tilemap[tileX,tileY-1] in targets and tilemap[tileX,tileY+1] in targets:
					orphaned = True
					target = tilemap[tileX,tileY+1]

				#fixes for cave entrance - instead, find dominant surrounding tile?

				if tileY > 0 and tileY < placed.h-1 and tilemap[tileX,tileY] == colorRock and tilemap[tileX,tileY-1] == colorDirt and tilemap[tileX,tileY+1] == colorLand:
					orphaned = True
					target = tilemap[tileX,tileY-1]

				if tileY > 0 and tileY < placed.h-1 and tilemap[tileX,tileY] == colorRock and tilemap[tileX,tileY+1] == colorDirt and tilemap[tileX,tileY-1] == colorLand:
					orphaned = True
					target = tilemap[tileX,tileY+1]

				if orphaned:
					changelist.append((tileX,tileY,target))

	for tileX, tileY, target in changelist:
		tilemap[tileX,tileY] = target

def add_doors(placed, tilemap):
	colorBuilding = (80, 80, 80)
	colorRoad = (255, 255, 255)
	colorDoor = (255, 245, 235)

	for tileX in range(1, int(placed.w)-1):
		for tileY in range(1, int(placed.h)-1):
			if tilemap[tileX,tileY] == colorBuilding:

				if tilemap[tileX,tileY+1] == colorRoad and tilemap[tileX-1,tileY+1] != colorRoad and tilemap[tileX+1,tileY+1] != colorRoad:
					tilemap[tileX,tileY] = colorDoor


def add_pillars(placed, tilemap):
	colorBuilding = (80, 80, 80)
	colorPillarNE = (0, 2, 2)
	colorPillarNW = (0, 2, 98)
	colorPillarSE = (0, 98, 2)
	colorPillarSW = (0, 98, 98)

	pillarEdgeTiles = set()

	for tileX in range(2, int(placed.w-2)):
		for tileY in range(2, int(placed.h-2)):

			if tilemap[tileX,tileY] == colorBuilding and tilemap[tileX+1,tileY] == colorBuilding and tilemap[tileX,tileY+1] == colorBuilding and tilemap[tileX+1,tileY+1] == colorBuilding:
				if tilemap[tileX+2,tileY] != colorBuilding and tilemap[tileX,tileY+2] != colorBuilding and tilemap[tileX-1,tileY] != colorBuilding and tilemap[tileX,tileY-1] != colorBuilding:
					pillarEdgeTiles.add((tileX,tileY))

	for tileX, tileY in pillarEdgeTiles:
		tilemap[tileX,tileY] = colorPillarNE
		tilemap[tileX+1,tileY] = colorPillarNW
		tilemap[tileX,tileY+1] = colorPillarSE
		tilemap[tileX+1,tileY+1] = colorPillarSW



def add_trees(placed, tilemap):
	colorForest = (32, 128, 96)
	colorTreeNE = (0, 1, 1)
	colorTreeNW = (0, 1, 99)
	colorTreeSE = (0, 99, 1)
	colorTreeSW = (0, 99, 99)
	colorTreeSmall = (1, 2, 3)

	treeTiles = set()
	forestTiles = set()

	for tileX in range(0, int(placed.w-1)):
		for tileY in range(0, int(placed.h-1)):

			if tilemap[tileX,tileY] == colorForest and tilemap[tileX+1,tileY] == colorForest and tilemap[tileX,tileY+1] == colorForest and tilemap[tileX+1,tileY+1] == colorForest:
				treeTiles.add((tileX,tileY))
			if tilemap[tileX,tileY] == colorForest:
				forestTiles.add((tileX,tileY))


	distanceToBorder = {}

	for tileX, tileY in treeTiles:
		distanceToBorder[(tileX,tileY)] = 9999

		for d in range(100):
			for xd in range(-d, d+1):
				for yd in [-d,d+1]:
					if (tileX+xd,tileY+yd) != (tileX,tileY) and (tileX+xd,tileY+yd) != (tileX+1,tileY) and (tileX+xd,tileY+yd) != (tileX,tileY+1) and (tileX+xd,tileY+yd) != (tileX+1,tileY+1) and tileX+xd > 1 and tileY+yd > 1 and tileX+xd < placed.w-1 and tileY+yd < placed.h-1:
						if (tileX+xd,tileY+yd) not in forestTiles:
							distanceToBorder[(tileX,tileY)] = min(distanceToBorder[(tileX,tileY)], getDistance(tileX+.5, tileY+.5, tileX+xd, tileY+yd))
			for yd in range(-d, d+1):
				for xd in [-d,d+1]:
					if (tileX+xd,tileY+yd) != (tileX,tileY) and (tileX+xd,tileY+yd) != (tileX+1,tileY) and (tileX+xd,tileY+yd) != (tileX,tileY+1) and (tileX+xd,tileY+yd) != (tileX+1,tileY+1) and tileX+xd > 1 and tileY+yd > 1 and tileX+xd < placed.w-1 and tileY+yd < placed.h-1:
						if (tileX+xd,tileY+yd) not in forestTiles:
							distanceToBorder[(tileX,tileY)] = min(distanceToBorder[(tileX,tileY)], getDistance(tileX+.5, tileY+.5, tileX+xd, tileY+yd))
			if distanceToBorder[(tileX,tileY)] != 9999:
				break

	# sortedTreeTiles = sorted(list(treeTiles), key=lambda tile: distanceToBorder[(tile[0], tile[1])])
	sortedTreeTiles = sorted(list(treeTiles), key=lambda tile: -distanceToBorder[(tile[0], tile[1])])


	trees = set()
	occupiedByTree = set()

	for tileX, tileY in sortedTreeTiles:
		if not (tileX,tileY) in occupiedByTree and not (tileX+1,tileY) in occupiedByTree and not (tileX,tileY+1) in occupiedByTree and not (tileX+1,tileY+1) in occupiedByTree:
			trees.add((tileX,tileY))
			occupiedByTree.add((tileX,tileY))
			occupiedByTree.add((tileX+1,tileY))
			occupiedByTree.add((tileX,tileY+1))
			occupiedByTree.add((tileX+1,tileY+1))


	for tileX, tileY in trees:
		tilemap[tileX,tileY] = colorTreeNE
		tilemap[tileX+1,tileY] = colorTreeNW
		tilemap[tileX,tileY+1] = colorTreeSE
		tilemap[tileX+1,tileY+1] = colorTreeSW

	for tileX in range(0, int(placed.w)):
		for tileY in range(0, int(placed.h)):
			if tilemap[tileX,tileY] == colorForest and not (tileX,tileY) in occupiedByTree:
				tilemap[tileX,tileY] = colorTreeSmall


def tweak_trees(placed, tilemap):
	colorTreeSmall = (1, 2, 3)
	colorTreeNE = (0, 1, 1)
	colorTreeNW = (0, 1, 99)
	colorTreeSE = (0, 99, 1)
	colorTreeSW = (0, 99, 99)
	colorLand = (128, 180, 96)

	tilesToTweak = set()

	for tileX in range(0, int(placed.w-4)):
		for tileY in range(0, int(placed.h-4)):

			if tilemap[tileX,tileY] == colorTreeSmall and tilemap[tileX,tileY+1] == colorTreeSmall and tilemap[tileX+1,tileY] == colorTreeNE and tilemap[tileX+3,tileY] == colorTreeSmall and tilemap[tileX+3,tileY+1] == colorTreeSmall:
				tilesToTweak.add((tileX,tileY))

	for tileX, tileY in tilesToTweak:
		if tilemap[tileX,tileY] == colorTreeSmall and tilemap[tileX,tileY+1] == colorTreeSmall and tilemap[tileX+1,tileY] == colorTreeNE and tilemap[tileX+3,tileY] == colorTreeSmall and tilemap[tileX+3,tileY+1] == colorTreeSmall:
			tilemap[tileX,tileY] = colorTreeNE
			tilemap[tileX,tileY+1] = colorTreeSE
			tilemap[tileX+1,tileY] = colorTreeNW
			tilemap[tileX+1,tileY+1] = colorTreeSW
			tilemap[tileX+2,tileY] = colorTreeNE
			tilemap[tileX+2,tileY+1] = colorTreeSE
			tilemap[tileX+3,tileY] = colorTreeNW
			tilemap[tileX+3,tileY+1] = colorTreeSW


def prune_trees(placed, tilemap):
	colorTreeSmall = (1, 2, 3)
	colorTreeNE = (0, 1, 1)
	colorTreeNW = (0, 1, 99)
	colorTreeSE = (0, 99, 1)
	colorTreeSW = (0, 99, 99)
	colorLand = (128, 180, 96)

	tilesToClear = set()

	for tileX in range(0, int(placed.w)):
		for tileY in range(0, int(placed.h)):

			if tilemap[tileX,tileY] == colorTreeSmall:
				landNeighbours = 0
				treeNeighbours = 0

				for xd, yd in [(1,0), (-1,0), (-1,-1), (-1,1), (1,1), (1,-1), (0,1), (0,-1)]:
					if tileX+xd > 1 and tileY+yd > 1 and tileX+xd < placed.w-1 and tileY+yd < placed.h-1 and tilemap[tileX+xd,tileY+yd] == colorLand:
						landNeighbours += 1
					elif tileX+xd > 1 and tileY+yd > 1 and tileX+xd < placed.w-1 and tileY+yd < placed.h-1 and tilemap[tileX+xd,tileY+yd] in [colorTreeNE, colorTreeNW, colorTreeSE, colorTreeSW]:
						treeNeighbours += 1

				# if landNeighbours > 0:
				# if landNeighbours > 3:
				if landNeighbours > 3 and treeNeighbours > 0:
					tilesToClear.add((tileX,tileY))

	for tileX, tileY in tilesToClear:
		tilemap[tileX,tileY] = colorLand


def add_fences(placed, tilemap):
	colorBuilding = (80, 80, 80)
	colorWall = (96, 96, 96)
	colorFence = (99, 99, 99)

	colorsWall = set([colorBuilding, colorWall])

	isolatedWallTiles = set()

	for tileX in range(1, int(placed.w)-1):
		for tileY in range(1, int(placed.h)-1):

			if tilemap[tileX,tileY] in (colorBuilding, colorWall):
				# isolatedWallTiles.add((tileX,tileY))

				if tileX > 1 and tilemap[tileX-1,tileY] not in colorsWall and tileX < placed.w-1 and tilemap[tileX+1,tileY] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				elif tileY > 1 and tilemap[tileX,tileY-1] not in colorsWall and tileY < placed.h-1 and tilemap[tileX,tileY+1] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				#S-shapes

				elif tileX > 1 and tilemap[tileX,tileY+1] in colorsWall and tilemap[tileX-1,tileY] not in colorsWall and tilemap[tileX+1,tileY+1] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				elif tileX > 1 and tilemap[tileX,tileY+1] in colorsWall and tilemap[tileX-1,tileY+1] not in colorsWall and tilemap[tileX+1,tileY] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				#advanced S-shapes

				elif tileY > 1 and tileX > 1 and tilemap[tileX-1,tileY] in colorsWall and tilemap[tileX-1,tileY-1] not in colorsWall and tilemap[tileX,tileY+1] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				elif tileY > 1 and tileX > 1 and tilemap[tileX+1,tileY] in colorsWall and tilemap[tileX,tileY-1] not in colorsWall and tilemap[tileX+1,tileY+1] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				elif tileY > 1 and tileX > 1 and tilemap[tileX-1,tileY] in colorsWall and tilemap[tileX,tileY-1] not in colorsWall and tilemap[tileX-1,tileY+1] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

				elif tileY > 1 and tileX > 1 and tilemap[tileX+1,tileY] in colorsWall and tilemap[tileX+1,tileY-1] not in colorsWall and tilemap[tileX,tileY+1] not in colorsWall:
					isolatedWallTiles.add((tileX,tileY))

	#assign fence tile to isolated tiles

	for tileX, tileY in isolatedWallTiles:
		#exception - if fence has 3 large wall tiles as diagonal neighbours, revert back

		if tilemap[tileX-1,tileY] in colorsWall and tilemap[tileX-1,tileY-1] in colorsWall and tilemap[tileX,tileY-1] in colorsWall:
			continue
		if tilemap[tileX+1,tileY] in colorsWall and tilemap[tileX+1,tileY+1] in colorsWall and tilemap[tileX,tileY+1] in colorsWall:
			continue
		if tilemap[tileX,tileY-1] in colorsWall and tilemap[tileX-1,tileY-1] in colorsWall and tilemap[tileX-1,tileY] in colorsWall:
			continue
		if tilemap[tileX,tileY+1] in colorsWall and tilemap[tileX+1,tileY+1] in colorsWall and tilemap[tileX+1,tileY] in colorsWall:
			continue

		if tilemap[tileX-1,tileY] in colorsWall and tilemap[tileX-1,tileY+1] in colorsWall and tilemap[tileX,tileY+1] in colorsWall:
			continue
		if tilemap[tileX+1,tileY] in colorsWall and tilemap[tileX+1,tileY-1] in colorsWall and tilemap[tileX,tileY-1] in colorsWall:
			continue
		if tilemap[tileX,tileY-1] in colorsWall and tilemap[tileX+1,tileY-1] in colorsWall and tilemap[tileX+1,tileY] in colorsWall:
			continue
		if tilemap[tileX,tileY+1] in colorsWall and tilemap[tileX-1,tileY+1] in colorsWall and tilemap[tileX-1,tileY] in colorsWall:
			continue

		tilemap[tileX,tileY] = colorFence


def add_rocks(placed, tilemap):
	colorRock = (72, 72, 72)
	colorRockObject = (64, 64, 64)
	colorDestructible = (31, 15, 15)
	colorLand = (128, 180, 96)
	colorDirt = (32, 16, 16)
	colorRockSmall = (3, 2, 1)
	colorRockSmallDirt = (4, 2, 1)

	colorsRock = set([colorRock, colorRockObject, colorDestructible])

	isolatedRockTiles = set()

	for tileX in range(1, int(placed.w)-1):
		for tileY in range(1, int(placed.h)-1):
			if tilemap[tileX,tileY] in colorsRock:

				if not tilemap[tileX-1,tileY] in colorsRock and not tilemap[tileX+1,tileY] in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

				elif not tilemap[tileX,tileY-1] in colorsRock and not tilemap[tileX,tileY+1] in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

				#S-shapes
				# .x@
				# @@.

				elif tileX > 1 and tilemap[tileX,tileY+1] in colorsRock and tilemap[tileX-1,tileY] not in colorsRock and tilemap[tileX+1,tileY+1] not in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

				elif tileX > 1 and tilemap[tileX,tileY+1] in colorsRock and tilemap[tileX-1,tileY+1] not in colorsRock and tilemap[tileX+1,tileY] not in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

				elif tileY > 1 and tilemap[tileX+1,tileY] in colorsRock and tilemap[tileX,tileY-1] not in colorsRock and tilemap[tileX+1,tileY+1] not in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

				elif tileY > 1 and tilemap[tileX+1,tileY] in colorsRock and tilemap[tileX+1,tileY-1] not in colorsRock and tilemap[tileX,tileY+1] not in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

				#advanced S-shapes
				# -?
				# @x
				# ?-

				elif tileY > 1 and tileX > 1 and tilemap[tileX-1,tileY] in colorsRock and tilemap[tileX-1,tileY-1] not in colorsRock and tilemap[tileX,tileY+1] not in colorsRock:
					isolatedRockTiles.add((tileX,tileY))

	#assign tile to isolated tiles (dirt or land, depending on surroundings)

	for tileX, tileY in isolatedRockTiles:
		# tilemap[tileX,tileY] = colorRockSmallDirt #test

		landNeighbours = 0
		dirtNeighbours = 0

		#exception - if small rock has 3 large rock tiles as diagonal neighbours, revert back

		if tilemap[tileX-1,tileY] in colorsRock and tilemap[tileX-1,tileY-1] in colorsRock and tilemap[tileX,tileY-1] in colorsRock:
			continue
		if tilemap[tileX+1,tileY] in colorsRock and tilemap[tileX+1,tileY+1] in colorsRock and tilemap[tileX,tileY+1] in colorsRock:
			continue
		if tilemap[tileX,tileY-1] in colorsRock and tilemap[tileX-1,tileY-1] in colorsRock and tilemap[tileX-1,tileY] in colorsRock:
			continue
		if tilemap[tileX,tileY+1] in colorsRock and tilemap[tileX+1,tileY+1] in colorsRock and tilemap[tileX+1,tileY] in colorsRock:
			continue

		if tilemap[tileX-1,tileY] in colorsRock and tilemap[tileX-1,tileY+1] in colorsRock and tilemap[tileX,tileY+1] in colorsRock:
			continue
		if tilemap[tileX+1,tileY] in colorsRock and tilemap[tileX+1,tileY-1] in colorsRock and tilemap[tileX,tileY-1] in colorsRock:
			continue
		if tilemap[tileX,tileY-1] in colorsRock and tilemap[tileX+1,tileY-1] in colorsRock and tilemap[tileX+1,tileY] in colorsRock:
			continue
		if tilemap[tileX,tileY+1] in colorsRock and tilemap[tileX-1,tileY+1] in colorsRock and tilemap[tileX-1,tileY] in colorsRock:
			continue

		#otherwise, decide if it's land or dirt

		for xd, yd in [(1,0), (-1,0), (-1,-1), (-1,1), (1,1), (1,-1), (0,1), (0,-1)]:
			if tilemap[tileX+xd,tileY+yd] == colorLand:
				landNeighbours += 1
			elif tilemap[tileX+xd,tileY+yd] == colorDirt:
				dirtNeighbours += 1

		if dirtNeighbours > landNeighbours:
			tilemap[tileX,tileY] = colorRockSmallDirt
		else:
			tilemap[tileX,tileY] = colorRockSmall


def add_cliffs(placed, tilemap):
	colorWater = (64, 128, 160)
	colorWater2 = (65, 128, 160)
	colorCliff = (128, 128, 128)

	shoreTiles = set()

	for tileX in range(0, int(placed.w)):
		for tileY in range(0, int(placed.h)):

			if tilemap[tileX,tileY] == colorWater or tilemap[tileX,tileY] == colorWater2:
				for xd in range(-1, 2):
					for yd in range(-1, 2):
						if (xd != 0 or yd != 0) and tileX+xd >= 0 and tileY+yd >= 0 and tileX+xd < placed.w and tileY+yd < placed.h and tilemap[tileX+xd,tileY+yd] != colorWater and tilemap[tileX+xd,tileY+yd] != colorWater2:
							shoreTiles.add((tileX,tileY))

	for tileX, tileY in shoreTiles:
		tilemap[tileX,tileY] = colorCliff
