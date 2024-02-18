from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
import numpy as np
import time, re, random

from astar import astar_path
from calc import getDistance, getAngle, getPositionAtAngle, getAngleDistance
from tilemap_drawing import tag_tile, tile_dictionary, get_label_dc, get_tile_targets_dc
from tilemap_postprocessing import tiles_smooth, tiles_replace_stranded, add_trees, tweak_trees, prune_trees, add_fences, add_rocks, add_cliffs, add_doors, add_pillars
from generator_separation import *


class Structure:
	def __init__(self, category, w, h, margin, color):
		self.category = category
		self.w, self.h = w, h
		self.margin = margin
		self.color = color
		self.tilemap = None
		self.objectmap = None
		self.heightmap = None
		self.layermap = None
		self.depthmap = None
		self.properties = set()


class Placement:
	def __init__(self, label, structure, container, x, y):
		self.structure = structure
		self.category = structure.category
		self.label = label

		self.x, self.y = x, y
		self.w, self.h = self.structure.w, self.structure.h
		self.margin = self.structure.margin

		self.centerOffsetX, self.centerOffsetY = 0, 0
		self.connectsToPath = False

		self.originX, self.originY = self.x, self.y
		self.updateCenter()

		self.offsetX, self.offsetY = 0, 0
		self.offsetW, self.offsetH = 0, 0

		if self.x - self.margin < 0:
			self.offsetX = self.x - self.margin
		if self.y - self.margin < 0:
			self.offsetY = self.y - self.margin

		if self.x + self.w + self.margin >= container.w:
			self.offsetW = (self.x + self.w + self.margin) - container.w
		if self.y + self.h + self.margin >= container.h:
			self.offsetH = (self.y + self.h + self.margin) - container.h

	def updateCenter(self):
		self.centerX, self.centerY = self.x +self.w/2, self.y +self.h/2
		self.centerXFloat, self.centerYFloat = self.x + self.w*.5, self.y + self.h*.5

	def isAcceptable(self, container):
		for x in range(self.x, self.x+self.w):
			for y in range(self.y, self.y+self.h):
				if (x,y) in container.occupied:
					return False
		return True

	def isAcceptableAt(self, container, xs, ys):
		for x in range(xs, xs+self.w):
			for y in range(ys, ys+self.h):
				if (x,y) in container.occupied:
					return False
		return True

	def getDirectionCoordinates(self, direction):
		self.x1, self.y1, self.x2, self.y2 = self.getBounds(self.w, self.h) #added

		if direction == 'n':
			return (self.x, self.y1)
		if direction == 's':
			return (self.x, self.y2)
		if direction == 'e':
			return (self.x2, self.y)
		if direction == 'w':
			return (self.x1, self.y)
		return (self.x, self.y)

	def getBounds(self, w, h):
		x1 = round(self.x - w/2 - .5)
		y1 = round(self.y - h/2 - .5)
		x2 = round(self.x + w/2 + .5)
		y2 = round(self.y + h/2 + .5)
		return (x1, y1, x2, y2)


class Arrangement:
	def __init__(self):
		self.structures = []
		self.paths = []
		self.pathMaterials = []
		self.occupied = set()

		self.requiredPaths = []
		self.numberOfPaths = 0

		self.w, self.h = 0, 0
		self.centerX, self.centerY = 0, 0
		self.exits = {}


	def generateExits(self):
		self.centerX, self.centerY = round(self.w/2), round(self.h/2)

		self.exits['n'] = (self.centerX, 0)
		self.exits['s'] = (self.centerX, self.h-1)
		self.exits['w'] = (0, self.centerY)
		self.exits['e'] = (self.w-1, self.centerY)


	def translateExits(self, xOffset, yOffset):
		self.exits['n'] = (self.exits['n'][0]+xOffset, 0)
		self.exits['s'] = (self.exits['s'][0]+xOffset, self.h-1)
		self.exits['w'] = (0, self.exits['w'][1]+yOffset)
		self.exits['e'] = (self.w-1, self.exits['e'][1]+yOffset)

		self.centerX, self.centerY = self.exits['n'][0], self.exits['w'][1]


	def assignRequiredPath(self, pathData):
		source, target, pathMaterial, pathSpecifiedMaterial = pathData
		sourceLabel, sourceDirection = source
		targetLabel, targetDirection = target

		sourceStructure = None
		targetStructure = None

		#find source
		for placed in self.structures:
			if placed.label == sourceLabel:
				sourceStructure = placed
				break

		if sourceStructure == None:
			print ("failed to find source structure: %s" % str(source))

		#find target
		if targetLabel != None:
			for placed in self.structures:
				if placed.label == targetLabel:
					targetStructure = placed
					break

			if targetStructure == None:
				print ("failed to find target structure: %s" % str(target))

		#add path
		if sourceStructure != None:
			self.requiredPaths.append( (sourceStructure, sourceDirection, targetStructure, targetDirection, pathMaterial, pathData) )


	def generateStructures(self, childNodes, generatedNode, structureDc, prototypeDc):
		structuresToGenerate = []

		# print ("generating for (%i) childNodes of %s" % (len(childNodes), generatedNode.category))

		for childNode in childNodes:
			if childNode.category in structureDc.keys():
			# if not childNode.childNodes:

				predefinedStructure = structureDc[childNode.category]

				structureColor = prototypeDc[childNode.category].color
				structureTilemap, structureObjectmap = childNode.structure.getStructureTilemap(predefinedStructure, structureColor)
				predefinedStructure.tilemap = structureTilemap
				predefinedStructure.objectmap = structureObjectmap

				predefinedStructure.heightmap = {}
				predefinedStructure.layermap = {}
				predefinedStructure.depthmap = {}
				for tileX in range(0, int(predefinedStructure.w)):
					predefinedStructure.heightmap[tileX] = {}
					predefinedStructure.layermap[tileX] = {}
					predefinedStructure.depthmap[tileX] = {}
					for tileY in range(0, int(predefinedStructure.h)):
						predefinedStructure.heightmap[tileX,tileY] = 1
						predefinedStructure.layermap[tileX,tileY] = 2
						predefinedStructure.depthmap[tileX,tileY] = 1

				structuresToGenerate.append((predefinedStructure, childNode.label, childNode.properties, (0,0)))

			else:
				proceduralStructure = Structure(childNode.category, int(childNode.structure.w), int(childNode.structure.h), prototypeDc[childNode.category].margin, (96,96,96))
				structureColor = prototypeDc[childNode.category].color

				if "%" in generatedNode.properties:
					proceduralStructure.margin = 7

				if childNode.category == "water":
					padding = 2
				elif '%' in generatedNode.properties:
					padding = 2
				else:
					padding = 0

				if generatedNode.category == "root":
					cropping = (0, 0, 0, 0)
				else:
					cropping = childNode.structure.getRepeatingBorders(structureColor, childNode.category)

				proceduralStructure.w = proceduralStructure.w + padding*2 - cropping[0] - cropping[2]
				proceduralStructure.h = proceduralStructure.h + padding*2 - cropping[1] - cropping[3]

				childNode.structure.w = childNode.structure.w + padding*2 - cropping[0] - cropping[2]
				childNode.structure.h = childNode.structure.h + padding*2 - cropping[1] - cropping[3]

				childNode.structure.centerX = childNode.structure.centerX + padding - cropping[0]
				childNode.structure.centerY = childNode.structure.centerY + padding - cropping[1]

				structureTilemap, structureObjectmap = childNode.structure.getTilemap(structureColor, padding, cropping)

				structureHeightmap = childNode.structure.getHeightmap(0, padding, cropping) #unused

				if '%' in childNode.properties: #structure is marked as overworld
					structureLayermap = childNode.structure.getLayermap(1, padding, cropping)
				else:
					structureLayermap = childNode.structure.getLayermap(2, padding, cropping)

				structureDepthmap = childNode.structure.getDepthmap(padding, cropping)

				proceduralStructure.tilemap = structureTilemap
				proceduralStructure.objectmap = structureObjectmap
				proceduralStructure.heightmap = structureHeightmap
				proceduralStructure.layermap = structureLayermap
				proceduralStructure.depthmap = structureDepthmap

				structuresToGenerate.append((proceduralStructure, childNode.label, childNode.properties, (childNode.structure.centerX, childNode.structure.centerY)))

		self.addStructures(structuresToGenerate, generatedNode)


	def shrink(self, extraMargin, onlyPathless):
		#bring generated structures closer together, AFTER roads are added (generator_separation functions assume no roads)

		cx, cy = self.w/2, self.h/2
		arrangementFromCenter, distances, angle_difference, distance_difference = self.getArrangementFromCenter(cx, cy, self.structures)
		arrangementFromCenter.sort(key = lambda data: distances[data[0]])

		#start with ones with most roads?

		for placement, sourcePosition, boundaryOffset, distance, angle in arrangementFromCenter:

			newOccupied = set()
			for otherPlacement in self.structures:
				if placement != otherPlacement:
					margin = max(otherPlacement.margin+extraMargin, placement.margin+extraMargin)

					for x in range(int(otherPlacement.x)-margin, int(otherPlacement.x)+otherPlacement.w+margin):
						for y in range(int(otherPlacement.y)-margin, int(otherPlacement.y)+otherPlacement.h+margin):
							newOccupied.add((x,y))
			for px, py in self.paths:
				for x in range(int(px)-1, int(px)+2):
					for y in range(int(py)-1, int(py)+2):
						newOccupied.add((x,y))

			self.occupied = newOccupied
			placement.updateCenter()

			#shrinking down here (done per structure)

			pathDistancesBefore = self.getPathDistances(placement)

			if (onlyPathless and len(pathDistancesBefore) == 0) or (not onlyPathless and not placement.connectsToPath):
				#get roads
				#estimate best angles for roads? (probably not the best solution)

				for sourceStructure, sourceDirection, targetStructure, targetDirection, pathMaterial, pathData in self.requiredPaths:
					if placement == sourceStructure or placement == targetStructure:
						sourceCategory = sourceStructure.category;
						if targetStructure == None:
							targetCategory = "None"
						else:
							targetCategory = targetStructure.category

						# print ( "  %s.%s -> %s.%s" % (sourceCategory, sourceDirection, targetCategory, targetDirection) )


				for i in range(100, 0, -5):
					interpolation = i * .01 - .01

					newDistance = interpolation * distance
					newPosition = getPositionAtAngle(cx, cy, newDistance, angle)

					targetX = int(round( newPosition[0] + boundaryOffset[0] ))
					targetY = int(round( newPosition[1] + boundaryOffset[1] ))

					#should be able to cross over roads, but not over structures
					if placement.isAcceptableAt(self, targetX, targetY):
						placement.x, placement.y = targetX, targetY
						placement.updateCenter()
					else:
						break

		#update boundaries

		newOffsets = (self.w, self.h, -self.w, -self.h) #x, y, w, h

		for placed in self.structures:
			newOffsets = (min(newOffsets[0], placed.x - placed.margin),
							min(newOffsets[1], placed.y - placed.margin),
							max(newOffsets[2], (placed.x + placed.w + placed.margin) - self.w),
							max(newOffsets[3], (placed.y + placed.h + placed.margin) - self.h))

		for placed in self.structures:
			placed.x -= newOffsets[0]
			placed.y -= newOffsets[1]
			placed.updateCenter()

		newPaths = []
		for pathX, pathY in self.paths:
			newPaths.append((pathX-newOffsets[0], pathY-newOffsets[1]))
		self.paths = newPaths

		self.w += newOffsets[2] - newOffsets[0]
		self.h += newOffsets[3] - newOffsets[1]

		self.translateExits(-newOffsets[0], -newOffsets[1])

		#add a function for this (or entire update boundaries part)?

		newOccupied = set()
		for placed in self.structures:
			for x in range(int(placed.x)-placed.margin, int(placed.x)+placed.w+placed.margin):
				for y in range(int(placed.y)-placed.margin, int(placed.y)+placed.h+placed.margin):
					newOccupied.add((x,y))
		self.occupied = newOccupied


	def checkCentralStructure(self, structuresToGenerate):
		for i, structureData in enumerate(structuresToGenerate):
			properties = structureData[2]
			if '!' in properties:
				return True, i
		return False, -1


	def addStructures(self, structuresToGenerate, parentNode):
		if not structuresToGenerate: #terminal node - only boundary decides shape
			finalPlacements = []

		elif len(structuresToGenerate) == 1: #one child node only - boundary around one structure
			structures = [s for s, l, p, c in structuresToGenerate]
			labels = [l for s, l, p, c in structuresToGenerate]
			centers = [c for s, l, p, c in structuresToGenerate]

			structure = structures[0]
			label = labels[0]
			placement = Placement(label, structure, self, 0, 0)

			spaceBounds = (99999, 99999, -99999, -99999)

			placement.label = label
			placement.category = structure.category
			placement.w, placement.h = structure.w, structure.h

			placement.x1, placement.y1, placement.x2, placement.y2 = placement.getBounds(placement.w, placement.h)
			spaceBounds = (min(spaceBounds[0], int(placement.x1)), min(spaceBounds[1], int(placement.y1)), max(spaceBounds[2], int(placement.x2)), max(spaceBounds[3], int(placement.y2)))

			finalPlacements = [placement]
			finalCenters = [centers[0]]

		else: #arrangement of structures
			structures = [s for s, l, p, c in structuresToGenerate]
			labels = [l for s, l, p, c in structuresToGenerate]
			centers = [c for s, l, p, c in structuresToGenerate]

			structureDc = {}
			centerDc = {}
			labelDc = {}

			hasCentralStructure, centralStructureIndex = self.checkCentralStructure(structuresToGenerate)

			#adding region structures

			regionStructures = []
			for i, structure in enumerate(structures):
				label = labels[i]

				isCentral = i == centralStructureIndex
				regionStructure = RegionStructure(structure.w, structure.h, structure.margin, label, isCentral, [])
				regionStructures.append(regionStructure)

				structure.identifier = i
				regionStructure.identifier = i
				structureDc[structure.identifier] = structure
				labelDc[structure.identifier] = label
				centerDc[structure.identifier] = centers[i]

			#assigning region paths

			edgeRegionStructuresDc = {'s': None, 'n': None, 'e': None, 'w': None}

			for sourcePath, targetPath, pathColor, pathSpecifiedMaterial in parentNode.childPaths:
				sourceLabel, sourceDirection = sourcePath
				targetLabel, targetDirection = targetPath

				if targetLabel != None: #road to structure
					for regionStructure in regionStructures:
						if regionStructure.label == sourceLabel:
							regionPath = (targetLabel, sourceDirection, targetDirection)
							regionStructure.connections.append(regionPath)
							break

					for regionStructure in regionStructures:
						if regionStructure.label == targetLabel:
							regionPath = (sourceLabel, targetDirection, sourceDirection)
							regionStructure.connections.append(regionPath)
							break

				else: #road to edge of parent
					sourceIsCentral = False
					for regionStructure in regionStructures:
						if regionStructure.label == sourceLabel and regionStructure.central:
							sourceIsCentral = True
							break
					if sourceIsCentral:
						continue

					targetCategoryDc = {'s': '_SOUTH_', 'n': '_NORTH_', 'e': '_EAST_', 'w': '_WEST_'}
					targetDirectionDc = {'s': 'n', 'n': 's', 'e': 'w', 'w': 'e'}

					for regionStructure in regionStructures:
						if regionStructure.label == sourceLabel:
							regionPath = (targetCategoryDc[targetDirection], sourceDirection, targetDirectionDc[targetDirection])
							regionStructure.connections.append(regionPath)
							break

					if edgeRegionStructuresDc[targetDirection] == None:
						if targetDirection == 's':
							edgeRegionStructuresDc[targetDirection] = RegionStructure(1, 1, 1, '_SOUTH_', False, [])
						elif targetDirection == 'n':
							edgeRegionStructuresDc[targetDirection] = RegionStructure(1, 1, 1, '_NORTH_', False, [])
						elif targetDirection == 'e':
							edgeRegionStructuresDc[targetDirection] = RegionStructure(1, 1, 1, '_EAST_', False, [])
						elif targetDirection == 'w':
							edgeRegionStructuresDc[targetDirection] = RegionStructure(1, 1, 1, '_WEST_', False, [])

					regionPath = (sourceLabel, targetDirectionDc[targetDirection], sourceDirection)
					edgeRegionStructuresDc[targetDirection].connections.append(regionPath)


			random.shuffle(regionStructures) #seed gets reset between generations of the same graph
			regionStructures.sort(key=lambda regionStructure: len(regionStructure.connections), reverse=True)
			regionStructures.sort(key=lambda regionStructure: regionStructure.central, reverse=True)

			maxRandomDistanceFromCenter = max( [max(regionStructure.w,regionStructure.h) for regionStructure in regionStructures] )

			for edgeDirection in ('s', 'n', 'e', 'w'):
				if edgeRegionStructuresDc[edgeDirection] != None:
					regionStructures.append(edgeRegionStructuresDc[edgeDirection])

			# arranging region structures

			regionStructureAngleDc = getRegionAngleDc(regionStructures)

			regionPlacements = []
			for i, regionStructure in enumerate(regionStructures):
				place(regionPlacements, len(regionStructures), maxRandomDistanceFromCenter, regionStructure, regionStructureAngleDc[i])

			adjustPlacements(regionPlacements)
			separate(regionPlacements)
			shrink(regionPlacements, 1) #things become slightly weird at this stage - e.g. dungeon finale can get moved to the bottom
			separate(regionPlacements)

			finalPlacements = []
			spaceBounds = (99999, 99999, -99999, -99999)

			placementIdentifiers = {}

			for regionPlacement in regionPlacements:
				if regionPlacement.label in ('_SOUTH_', '_NORTH_', '_EAST_', '_WEST_'):
					continue

				structure = structureDc[regionPlacement.structure.identifier]
				label = labelDc[regionPlacement.structure.identifier]
				placement = Placement(label, structure, self, int(regionPlacement.x), int(regionPlacement.y))

				if placement.isAcceptable(self):
					placement.label = label
					placement.category = structure.category
					placement.w, placement.h = structure.w, structure.h

					placement.x1, placement.y1, placement.x2, placement.y2 = placement.getBounds(placement.w, placement.h)
					spaceBounds = (min(spaceBounds[0], int(placement.x1)), min(spaceBounds[1], int(placement.y1)), max(spaceBounds[2], int(placement.x2)), max(spaceBounds[3], int(placement.y2)))

					finalPlacements.append(placement)
					placementIdentifiers[placement] = regionPlacement.structure.identifier #always unique (region structures have different identifiers assigned regardless of same type)

			#sort placements in accordance with original identifiers - otherwise roads get assigned to wrong structures!
			finalPlacements.sort(key=lambda placement: placementIdentifiers[placement])

			#centers in the same order as structures, because structures get sorted
			finalCenters = [c for s, l, p, c in structuresToGenerate]


		#place structures

		for newPlacement in finalPlacements:
			self.structures.append(newPlacement)
			newPlacement.index = len(self.structures)


		#update boundaries

		bounds = (99999, 99999, -99999, -99999)

		for newPlacement in finalPlacements:
			x1, y1, x2, y2 = newPlacement.getBounds(structure.w, structure.h)
			bounds = (min(bounds[0], int(x1)), min(bounds[1], int(y1)), max(bounds[2], int(x2)), max(bounds[3], int(y2)))

		self.w = bounds[2] - bounds[0]
		self.h = bounds[3] - bounds[1]

		offsetX = bounds[0]
		offsetY = bounds[1]

		for i, placed in enumerate(self.structures):
			placed.x = placed.x - offsetX - placed.w/2
			placed.y = placed.y - offsetY - placed.h/2

			center = finalCenters[i]
			if center[0] != 0 and center[1] != 0:
				centerOffsetX = center[0] - placed.w/2
				centerOffsetY = center[1] - placed.h/2

				placed.centerOffsetX = centerOffsetX
				placed.centerOffsetY = centerOffsetY


	def clearPaths(self):
		self.pathsSeparated = [] #may erase paths lower down in the tree?

		self.paths = []
		self.pathMaterials = []
		self.numberOfPaths = 0
		for placed in self.structures:
			placed.connectsToPath = False


	def getPath(self, sourceStructure, sourcePosition, sourcePathDirection, targetStructure, targetPosition, targetPathDirection, parentIsContinent):
		#changed order of lines, forced extending grid to fit sourcePosition and targetPosition

		sourcePosition = (int(sourcePosition[0])+2, int(sourcePosition[1])+2)
		targetPosition = (int(targetPosition[0])+2, int(targetPosition[1])+2)

		# grid = np.zeros((self.w+4, self.h+4)).astype(int)
		grid = np.zeros((max([self.w+4, sourcePosition[0]+2, targetPosition[0]+2]), max([self.h+4, sourcePosition[1]+2, targetPosition[1]+2]))).astype(int)

		for x, y in self.occupied:
			grid[x+2,y+2] = 1

		for x, y in self.paths:
			grid[x+2,y+2] = 0

		if targetStructure == None:
			if targetPathDirection in ('n','s'):
				grid[targetPosition[0]-1, targetPosition[1]] = 1
				grid[targetPosition[0]+1, targetPosition[1]] = 1
			elif targetPathDirection in ('w','e'):
				grid[targetPosition[0], targetPosition[1]-1] = 1
				grid[targetPosition[0], targetPosition[1]+1] = 1

		if sourcePathDirection == 's':
			for y in range(int(sourceStructure.y+sourceStructure.h)+2, int(sourcePosition[1]+sourceStructure.margin)):
				grid[sourcePosition[0],y] = 0
		elif sourcePathDirection == 'n':
			for y in range(int(sourceStructure.y-sourceStructure.margin)+2, int(sourcePosition[1])+1):
				grid[sourcePosition[0],y] = 0
		elif sourcePathDirection == 'e':
			for x in range(int(sourceStructure.x+sourceStructure.w)+2, int(sourcePosition[0]+sourceStructure.margin)):
				grid[x,sourcePosition[1]] = 0
		elif sourcePathDirection == 'w':
			for x in range(int(sourceStructure.x-sourceStructure.margin)+2, int(sourcePosition[0])+1):
				grid[x,sourcePosition[1]] = 0

		if targetStructure != None:
			if targetPathDirection == 's':
				for y in range(int(targetStructure.y+targetStructure.h)+2, int(targetPosition[1]+targetStructure.margin)):
					grid[targetPosition[0],y] = 0
			elif targetPathDirection == 'n':
				for y in range(int(targetStructure.y-targetStructure.margin)+2, int(targetPosition[1])+1):
					grid[targetPosition[0],y] = 0
			elif targetPathDirection == 'e':
				for x in range(int(targetStructure.x+targetStructure.w)+2, int(targetPosition[0]+targetStructure.margin)):
					grid[x,targetPosition[1]] = 0
			elif targetPathDirection == 'w':
				for x in range(int(targetStructure.x-targetStructure.margin)+2, int(targetPosition[0])+1):
					grid[x,targetPosition[1]] = 0

		path = astar_path(grid, sourcePosition, targetPosition)

		if path:
			returnedPath = [(pathX-2, pathY-2) for pathX, pathY in path]
			returnedPath.append((sourcePosition[0]-2, sourcePosition[1]-2))
			returnedPath.append((targetPosition[0]-2, targetPosition[1]-2))
			return returnedPath


	def testPath(self, sourceStructure, sourcePathDirection, targetStructure, targetPathDirection, pathMaterial, pathData, parentIsContinent):
		if sourcePathDirection == 's':
			sourcePosition = (sourceStructure.centerX+sourceStructure.centerOffsetX, sourceStructure.y+sourceStructure.h)
		elif sourcePathDirection == 'n':
			sourcePosition = (sourceStructure.centerX+sourceStructure.centerOffsetX, sourceStructure.y-1)
		elif sourcePathDirection == 'e':
			sourcePosition = (sourceStructure.x+sourceStructure.w, sourceStructure.centerY+sourceStructure.centerOffsetY)
		elif sourcePathDirection == 'w':
			sourcePosition = (sourceStructure.x-1, sourceStructure.centerY+sourceStructure.centerOffsetY)

		if targetStructure != None:
			if targetPathDirection == 's':
				targetPosition = (targetStructure.centerX+targetStructure.centerOffsetX, targetStructure.y+targetStructure.h)
			elif targetPathDirection == 'n':
				targetPosition = (targetStructure.centerX+targetStructure.centerOffsetX, targetStructure.y-1)
			elif targetPathDirection == 'e':
				targetPosition = (targetStructure.x+targetStructure.w, targetStructure.centerY+targetStructure.centerOffsetY)
			elif targetPathDirection == 'w':
				targetPosition = (targetStructure.x-1, targetStructure.centerY+targetStructure.centerOffsetY)

		else:
			self.generateExits()
			#missing this line caused outgoing paths to move away from centers (commenting it out causes paths to become more 'serpentine')
			#still not perfect - e.g. rock plain outgoing paths from waypoint towards s/n are ok, but adding w->e causes offset

			if targetPathDirection == 's':
				targetPosition = (self.exits['s'][0], self.exits['s'][1]+2)
			elif targetPathDirection == 'n':
				targetPosition = (self.exits['n'][0], self.exits['n'][1]-2)
			elif targetPathDirection == 'e':
				targetPosition = (self.exits['e'][0]+2, self.exits['e'][1])
			elif targetPathDirection == 'w':
				targetPosition = (self.exits['w'][0]-2, self.exits['w'][1])

		path = self.getPath(sourceStructure, sourcePosition, sourcePathDirection, targetStructure, targetPosition, targetPathDirection, parentIsContinent)

		if path:
			newPathSection = path

			self.paths += newPathSection
			self.pathsSeparated.append((pathData, newPathSection))

			for pathSection in newPathSection:
				self.pathMaterials.append(pathMaterial)

			sourceStructure.connectsToPath = True
			if targetStructure != None:
				targetStructure.connectsToPath = True
			self.numberOfPaths += 1

			return True

		else:
			return False


	def reconstructRegions(self, marginIncrease=0):
		structures = [s for s in self.structures]

		regionPlacements = []
		for i, placed in enumerate(structures):
			regionStructure = RegionStructure(placed.w, placed.h, placed.margin, placed.category, False, [])
			regionPlacement = RegionPlacement(regionStructure, placed.x, placed.y)
			regionPlacements.append(regionPlacement)

		#separate again at this stage just to make sure there are no collisions
		#increase margins if necessary (expand to accomodate roads)
		#idea: apply margin increase selectively, only to structures which can't get connected?

		for regionPlacement in regionPlacements:
			regionPlacement.margin += marginIncrease
			regionPlacement.x += regionPlacement.w/2
			regionPlacement.y += regionPlacement.h/2

		separate(regionPlacements)

		for regionPlacement in regionPlacements:
			regionPlacement.margin -= marginIncrease
			regionPlacement.x -= regionPlacement.w/2
			regionPlacement.y -= regionPlacement.h/2

		#update placements

		for i, placement in enumerate(self.structures):
			regionPlacement = regionPlacements[i]
			boundaryOffset = (0, 0)

			newPosition = regionPlacement.x, regionPlacement.y

			targetX = int( newPosition[0] + boundaryOffset[0] )
			targetY = int( newPosition[1] + boundaryOffset[1] )

			placement.x, placement.y = targetX, targetY
			placement.updateCenter()

		#update boundaries
		#applies to structures after shift - region irrelevant at this point?

		newOffsets = (self.w, self.h, -self.w, -self.h) #x, y, w, h

		for placed in self.structures:
			newOffsets = (min(newOffsets[0], placed.x - placed.margin),
							min(newOffsets[1], placed.y - placed.margin),
							max(newOffsets[2], (placed.x + placed.w + placed.margin) - self.w),
							max(newOffsets[3], (placed.y + placed.h + placed.margin) - self.h))

		for placed in self.structures:
			placed.x -= newOffsets[0]
			placed.y -= newOffsets[1]
			placed.updateCenter()

		newPaths = []
		for pathX, pathY in self.paths:
			newPaths.append((pathX-newOffsets[0], pathY-newOffsets[1]))
		self.paths = newPaths

		self.w += newOffsets[2] - newOffsets[0]
		self.h += newOffsets[3] - newOffsets[1]

		self.translateExits(-newOffsets[0], -newOffsets[1])

		#add a function for this (or entire update boundaries part)?

		newOccupied = set()
		for placed in self.structures:
			for x in range(int(placed.x)-placed.margin, int(placed.x)+placed.w+placed.margin):
				for y in range(int(placed.y)-placed.margin, int(placed.y)+placed.h+placed.margin):
					newOccupied.add((x,y))
		self.occupied = newOccupied


	def connectAllPaths(self, viableLen, parentIsContinent):
		self.clearPaths()

		self.reconstructRegions()

		#set different margins for continent

		if parentIsContinent:
			#margin of overworld is set to 7 during generation, always mark terrain as solid up to 3 tiles away to allow for roads
			self.occupied = set()

			for placed in self.structures:
				for x in range(int(placed.x)-3, int(placed.x)+placed.w+3):
					for y in range(int(placed.y)-3, int(placed.y)+placed.h+3):
						self.occupied.add((x,y))

		#store initial values for area size, positions, paths, etc. for reference

		wOrigin, hOrigin = self.w, self.h
		occupiedOrigin = self.occupied.copy()

		pathsOrigin = []
		for path in self.paths:
			pathsOrigin.append(path)

		placedPositionsOrigin = []
		for placed in self.structures:
			placedPositionsOrigin.append((placed.x, placed.y, placed.centerX, placed.centerY, placed.centerXFloat, placed.centerYFloat))

		#try to add paths
		#if some paths can't be added, expand structure margins and try again

		for i in range(100):
			for sourceStructure, sourceDirection, targetStructure, targetDirection, pathMaterial, pathData in self.requiredPaths[:200]:
				pathAdded = self.testPath(sourceStructure, sourceDirection, targetStructure, targetDirection, pathMaterial, pathData, parentIsContinent)
				if not pathAdded:
					break
			if self.numberOfPaths == len(self.requiredPaths[:200]):
				break
			else:
				self.clearPaths()

				#reset source values
				for n, placed in enumerate(self.structures):
					placed.x, placed.y = placedPositionsOrigin[n][0], placedPositionsOrigin[n][1]
					placed.centerX, placed.centerY = placedPositionsOrigin[n][2], placedPositionsOrigin[n][3]
					placed.centerXFloat, placed.centerYFloat = placedPositionsOrigin[n][4], placedPositionsOrigin[n][5]

				self.paths = pathsOrigin
				self.occupied = occupiedOrigin
				self.w, self.h = wOrigin, hOrigin
				self.generateExits()

				#increase margins and expand to try and fit paths again
				self.reconstructRegions(marginIncrease=i+1)

		#shrink structures outside roads (necessary to properly assign borders)

		for i in range(2):
			self.shrink(0, True)


	def getArrangementFromCenter(self, cx, cy, placements):
		arrangementFromCenter = []
		distances = {}

		for placed in placements:
			sourceCx, sourceCy = placed.centerXFloat, placed.centerYFloat
			boundaryX, boundaryY = placed.x-placed.centerXFloat, placed.y-placed.centerYFloat

			distance = getDistance(cx, cy, sourceCx, sourceCy)
			angle = getAngle(cx, cy, sourceCx, sourceCy)

			arrangementFromCenter.append( (placed, (sourceCx, sourceCy), (boundaryX, boundaryY), distance, angle) )
			distances[placed] = distance

		#special case: if distances/angles end up too similar, two structures may end up 'stuck' when Arrangement.expand() is called
		#return lowest angle and distance difference to verify if this might happen and change arrangement
		#update: Arrangement.expand() is dead and buried, but I'm keeping this warning on the off chance it ever comes back from the grave

		shortest_angle_difference = 9999
		shortest_distance_difference = 9999

		for i, arrangement in enumerate(arrangementFromCenter):
			placed, sourcePosition, boundaryOffset, distance, angle = arrangement

			for j, previousArrangement in enumerate(arrangementFromCenter[:i]):
				previousPlaced, previousSourcePosition, previousBoundaryOffset, previousDistance, previousAngle = previousArrangement

				angle_difference = getAngleDistance(angle, previousAngle)
				if angle_difference < shortest_angle_difference:
					shortest_angle_difference = angle_difference
					shortest_distance_difference = abs(distance-previousDistance)

		return arrangementFromCenter, distances, shortest_angle_difference, shortest_distance_difference


	def getPathDistances(self, placement):
		placementPathDistances = []

		for sourceStructure, sourceDirection, targetStructure, targetDirection, pathMaterial, pathData in self.requiredPaths:
			if placement == sourceStructure or placement == targetStructure:
				sourceCategory = sourceStructure.category;
				sourcePosition = sourceStructure.getDirectionCoordinates(sourceDirection)

				if targetStructure == None:
					targetCategory = "None"
					boundaries = (99999, 99999, -99999, -99999)
					for anyPlacement in self.structures:
						x1, y1, x2, y2 = anyPlacement.x1, anyPlacement.y1, anyPlacement.x2, anyPlacement.y2
						boundaries = (min(boundaries[0], int(x1)), min(boundaries[1], int(y1)), max(boundaries[2], int(x2)), max(boundaries[3], int(y2)))
					xMin, yMin, xMax, yMax = boundaries

					if targetDirection == 'n':
						targetPosition = (0, yMin)
					elif targetDirection == 's':
						targetPosition = (0, yMax)
					elif targetDirection == 'e':
						targetPosition = (xMax, 0)
					elif targetDirection == 'w':
						targetPosition = (xMin, 0)

				else:
					targetCategory = targetStructure.category
					targetPosition = targetStructure.getDirectionCoordinates(targetDirection)

				distance = getDistance(sourcePosition[0], sourcePosition[1], targetPosition[0], targetPosition[1])
				description = "%s.%s -> %s.%s"  % (sourceCategory, sourceDirection, targetCategory, targetDirection)

				placementPathDistances.append((distance, description))

		return placementPathDistances


	def calcPathMargins(self):
		pathPoints = list(set(self.paths))

		minX, minY, maxX, maxY = 9999, 9999, -9999, -9999
		sPoints, nPoints, ePoints, wPoints = [], [], [], []

		for pathX, pathY in pathPoints:
			if pathY == maxY:
				sPoints.append((pathX,pathY))
			elif pathY > maxY:
				maxY = pathY
				sPoints = [(pathX,pathY)]

			if pathY == minY:
				nPoints.append((pathX,pathY))
			elif pathY < minY:
				minY = pathY
				nPoints = [(pathX,pathY)]

			if pathX == maxX:
				ePoints.append((pathX,pathY))
			elif pathX > maxX:
				maxX = pathX
				ePoints = [(pathX,pathY)]

			if pathX == minX:
				wPoints.append((pathX,pathY))
			elif pathX < minX:
				minX = pathX
				wPoints = [(pathX,pathY)]

		marginW, marginN, marginE, marginS = 1, 1, 1, 1
		if len(wPoints) != 1:
			marginW += 1
		if len(nPoints) != 1:
			marginN += 1
		if len(ePoints) != 1:
			marginE += 1
		if len(sPoints) != 1:
			marginS += 1

		return [marginW, marginN, marginE, marginS]


	def freeze(self):
		self.occupied = set()

		newOffsetX, newOffsetY = 0, 0
		newOffsetW, newOffsetH = 0, 0

		pathMargins = self.calcPathMargins()

		for pathX, pathY in self.paths:
			newOffsetX = min(newOffsetX, pathX + 1 - pathMargins[0])
			newOffsetY = min(newOffsetY, pathY + 1 - pathMargins[1])
			newOffsetW = max(newOffsetW, (pathX + pathMargins[2]) - self.w)
			newOffsetH = max(newOffsetH, (pathY + pathMargins[3]) - self.h)

		for placed in self.structures:
			placed.x -= newOffsetX
			placed.y -= newOffsetY
			placed.updateCenter()

		newPaths = []
		for pathX, pathY in self.paths:
			newPaths.append((pathX-newOffsetX, pathY-newOffsetY))
		self.paths = newPaths

		self.w += newOffsetW - newOffsetX
		self.h += newOffsetH - newOffsetY

		self.translateExits(-newOffsetX, -newOffsetY)


	def checkSameTiles(self, tilemap, tilesToCheck, offsetX, offsetY, roadsOnly):
		roads = 0
		for tileX, tileY in tilesToCheck:
			if tilemap[tileX,tileY] != tilemap[tileX+offsetX,tileY+offsetY]:
				return False
			if tilemap[tileX,tileY] == (255,255,255) or tilemap[tileX,tileY] == (32,16,16):
				roads += 1
		if roadsOnly and roads != 1:
			return False
		return True


	def getRepeatingBorders(self, bgColor, label):
		tilemap = {}
		structureX1, structureY1, structureX2, structureY2 = int(self.w), int(self.h), 0, 0

		for tileX in range(0, int(self.w)):
			tilemap[tileX] = {}
			for tileY in range(0, int(self.h)):
				tilemap[tileX,tileY] = bgColor

		for placed in self.structures:
			for x in range(int(placed.x), int(placed.x+placed.w)):
				for y in range(int(placed.y), int(placed.y+placed.h)):

					structureX1 = min(structureX1, int(placed.x))
					structureX2 = max(structureX2, int(placed.x+placed.w-1))
					structureY1 = min(structureY1, int(placed.y))
					structureY2 = max(structureY2, int(placed.y+placed.h-1))

					if placed.structure.tilemap != None:
						tilemap[x,y] = placed.structure.tilemap[x-int(placed.x),y-int(placed.y)]
					else:
						tilemap[x,y] = placed.structure.color

			for i, pathPoints in enumerate(self.paths):
				xd, yd = pathPoints
				tilemap[xd,yd] = self.pathMaterials[i]

		cropX1, cropY1, cropX2, cropY2 = 0, 0, 0, 0

		for tileX in range(1, structureX1):
			tilesToCheck = [(tileX,tileY) for tileY in range(0, int(self.h))]
			if not self.checkSameTiles(tilemap, tilesToCheck, -1, 0, True):
				break
			cropX1 += 1

		for tileX in range(int(self.w)-2, structureX2, -1):
			tilesToCheck = [(tileX,tileY) for tileY in range(0, int(self.h))]
			if not self.checkSameTiles(tilemap, tilesToCheck, 1, 0, True):
				break
			cropX2 += 1

		for tileY in range(1, structureY1):
			tilesToCheck = [(tileX,tileY) for tileX in range(0, int(self.w))]
			if not self.checkSameTiles(tilemap, tilesToCheck, 0, -1, True):
				break
			cropY1 += 1

		for tileY in range(int(self.h)-2, structureY2, -1):
			tilesToCheck = [(tileX,tileY) for tileX in range(0, int(self.w))]
			if not self.checkSameTiles(tilemap, tilesToCheck, 0, 1, True):
				break
			cropY2 += 1

		cropX1, cropY1, cropX2, cropY2 = max(0,min(2,cropX1)), max(0, min(2,cropY1)), max(0, min(2,cropX2)), max(0, min(2,cropY2))

		# return 0, 0, 0, 0
		return cropX1, cropY1, cropX2, cropY2


	def getTilemap(self, bgColor, padding, cropping):
		cropX, cropY = cropping[0], cropping[1]

		colorChest = (32, 64, 160)
		colorChestBombs = (32, 64, 161)
		colorChestCanoe = (32, 64, 162)
		colorChestKey = (32, 64, 163)
		colorChestMoney = (32, 64, 164)
		colorChestHeart = (32, 64, 165)
		colorPc = (33, 64, 161)
		colorNpc = (33, 64, 163)
		colorNpc2 = (33, 64, 164)
		colorNpc3 = (33, 64, 165)
		colorEnemy = (34, 64, 160)
		colorBoss = (33, 64, 162)

		tilemap = {}
		objectmap = {}

		objectTileDc = {colorChest: "chest", colorChestBombs: "chest_bombs", colorChestCanoe: "chest_canoe", colorChestKey: "chest_key", colorChestMoney: "chest_money", colorChestHeart: "chest_heart",
						colorNpc: "npc", colorNpc2: "npc2", colorNpc3: "npc3", colorPc: "pc", colorEnemy: "enemy", colorBoss: "boss"
						}
		objectTileKeys = set(objectTileDc.keys())

		for tileX in range(0, int(self.w)):
			tilemap[tileX] = {}
			objectmap[tileX] = {}
			for tileY in range(0, int(self.h)):
				tilemap[tileX,tileY] = bgColor
				objectmap[tileX,tileY] = ""

		for placed in self.structures:
			for x in range(int(placed.x), int(placed.x+placed.w)):
				for y in range(int(placed.y), int(placed.y+placed.h)):
					if placed.structure.tilemap != None:

						if placed.structure.tilemap[x-int(placed.x),y-int(placed.y)] in objectTileKeys:
							tilemap[x+padding-cropX,y+padding-cropY] = bgColor
							objectmap[x+padding-cropX,y+padding-cropY] = objectTileDc[placed.structure.tilemap[x-int(placed.x),y-int(placed.y)]]
						else:
							tilemap[x+padding-cropX,y+padding-cropY] = placed.structure.tilemap[x-int(placed.x),y-int(placed.y)]
							objectmap[x+padding-cropX,y+padding-cropY] = placed.structure.objectmap[x-int(placed.x),y-int(placed.y)]

					else:
						tilemap[x+padding-cropX,y+padding-cropY] = placed.structure.color

			for i, pathPoints in enumerate(self.paths):
				xd, yd = pathPoints
				tilemap[xd+padding-cropX,yd+padding-cropY] = self.pathMaterials[i]

				#this used to be buggy (cropX/cropY adjustment was originally missing)
				#it's probably still buggy, but it used be, too

				if padding > 0:
					if yd+padding-cropY == self.h-padding-1:
						for yd2 in range(int(yd+padding+1-cropY), int(self.h)):
							tilemap[xd+padding-cropX,yd2] = self.pathMaterials[i]

					elif xd+padding-cropX == self.w-padding-1:
						for xd2 in range(int(xd+padding+1-cropX), int(self.w)):
							tilemap[xd2,yd+padding-cropY] = self.pathMaterials[i]

					elif yd == 0:
						for yd2 in range(0, int(yd+padding)):
							tilemap[xd+padding-cropX,yd2] = self.pathMaterials[i]
					elif xd == 0:
						for xd2 in range(0, int(xd+padding)):
							tilemap[xd2,yd+padding-cropY] = self.pathMaterials[i]

		return tilemap, objectmap


	def getStructureTilemap(self, structure, bgColor):
		tilemap = {}
		objectmap = {}
		for tileX in range(0, int(structure.w)):
			tilemap[tileX] = {}
			objectmap[tileX] = {}
			for tileY in range(0, int(structure.h)):
				tilemap[tileX,tileY] = bgColor
				objectmap[tileX,tileY] = ""

		return tilemap, objectmap


	def getHeightmap(self, structureHeight, padding, cropping): #unused, all structureHeight values set to 0 elsewhere
		cropX, cropY = cropping[0], cropping[1]

		heightmap = {}
		for tileX in range(0, int(self.w)):
			heightmap[tileX] = {}
			for tileY in range(0, int(self.h)):
				heightmap[tileX,tileY] = structureHeight #container's height

		for placed in self.structures:
			for x in range(int(placed.x), int(placed.x+placed.w)):
				for y in range(int(placed.y), int(placed.y+placed.h)):
					if placed.structure.heightmap != None:
						heightmap[x+padding-cropX,y+padding-cropY] = placed.structure.heightmap[x-int(placed.x),y-int(placed.y)]
					else:
						heightmap[x+padding-cropX,y+padding-cropY] = structureHeight #drawn structure's height

		return heightmap


	def getLayermap(self, structureLayer, padding, cropping):
		cropX, cropY = cropping[0], cropping[1]

		layermap = {}
		for tileX in range(0, int(self.w)):
			layermap[tileX] = {}
			for tileY in range(0, int(self.h)):
				layermap[tileX,tileY] = structureLayer #container's layer

		for placed in self.structures:
			for x in range(int(placed.x), int(placed.x+placed.w)):
				for y in range(int(placed.y), int(placed.y+placed.h)):
					if placed.structure.layermap != None:
						layermap[x+padding-cropX,y+padding-cropY] = placed.structure.layermap[x-int(placed.x),y-int(placed.y)]
					else:
						layermap[x+padding-cropX,y+padding-cropY] = structureLayer #drawn structure's layer

		return layermap


	def getDepthmap(self, padding, cropping): #how deeply nested structures are
		cropX, cropY = cropping[0], cropping[1]

		max_child_depth = 0
		depthmap = {}
		for tileX in range(0, int(self.w)):
			depthmap[tileX] = {}
			for tileY in range(0, int(self.h)):
				depthmap[tileX,tileY] = 0

		for placed in self.structures:
			for x in range(int(placed.x), int(placed.x+placed.w)):
				for y in range(int(placed.y), int(placed.y+placed.h)):
					if placed.structure.depthmap != None:
						depthmap[x+padding-cropX,y+padding-cropY] = placed.structure.depthmap[x-int(placed.x),y-int(placed.y)]
						if depthmap[x+padding-cropX,y+padding-cropY] > max_child_depth:
							max_child_depth = depthmap[x+padding-cropX,y+padding-cropY]

		for tileX in range(0, int(self.w)):
			for tileY in range(0, int(self.h)):
				if depthmap[tileX,tileY] == 0:
					depthmap[tileX,tileY] = max_child_depth + 1

		return depthmap


	def tilesClear(self):
		colors = {'water': (64, 128, 160), 'land': (128, 180, 96), 'rock': (72, 72, 72), 'wall': (96, 96, 96), 'dirt': (32, 16, 16), 'plaza': (180, 180 ,180), 'road': (255, 255, 255), 'null': (100, 100, 100)}

		placed = self.structures[0]
		tilemap = placed.structure.tilemap
		objectmap = placed.structure.objectmap
		depthmap = placed.structure.depthmap

		tileLevels = set()
		tilesAtLevel = {}

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				depth = depthmap[tileX,tileY]

				# if not tilemap[tileX,tileY] in [colors['land'], colors['rock'], colors['water']]: #or objectmap != ""
				if not tilemap[tileX,tileY] in [colors['land'], colors['rock'], colors['water'], colors['wall']]: #or objectmap != ""
					depth = 1

				if depth not in tileLevels:
					tileLevels.add(depth)
					tilesAtLevel[depth] = []

				tilesAtLevel[depth].append((tileX,tileY))

		emptyTiles = set()
		doneTiles = set()

		#bottom-up tiling
		#separate blocked (e.g. plain surrounding rock) and non-blocked spaces?
		#rock is more likely to 'spread' when filling empty tiles, including across water
		#update treatment for walls/trees - top island should be covered in trees where inaccessible

		maxLevel = 9999

		for level in sorted(tileLevels):
			if level > maxLevel:
				break

			for tileX, tileY in tilesAtLevel[level]:

				if level == 1: #structures = always add surrounding tiles

					if tilemap[tileX,tileY] in [colors['dirt']]:
						distance = 0
						for xd in range(-distance, distance+1):
							for yd in range(-distance, distance+1):
								doneTiles.add((tileX+xd,tileY+yd))

					elif tilemap[tileX,tileY] in [colors['road'], colors['plaza']]:
						distance = 2
						for xd in range(-distance, distance+1):
							for yd in range(-distance, distance+1):
								doneTiles.add((tileX+xd,tileY+yd))

					else:
						distance = 2
						for xd in range(-distance, distance+1):
							for yd in range(-distance, distance+1):
								if (0 <= tileX+xd < placed.w) and (0 <= tileY+yd < placed.h) and (tilemap[tileX,tileY] == tilemap[tileX+xd,tileY+yd] or tilemap[tileX+xd,tileY+yd] in [colors['land']]):
									doneTiles.add((tileX+xd,tileY+yd))

				else:
					if tilemap[tileX,tileY] == colors['rock']:
						distance = 2
						neighboursOther = False
						for xd in range(-distance, distance+1):
							for yd in range(-distance, distance+1):

								if (0 <= tileX+xd < placed.w) and (0 <= tileY+yd < placed.h) and tilemap[tileX+xd,tileY+yd] != tilemap[tileX,tileY] and depthmap[tileX+xd,tileY+yd] < depthmap[tileX,tileY]:
									neighboursOther = True

						if neighboursOther:
							doneTiles.add((tileX,tileY))

					if tilemap[tileX,tileY] == colors['water']:
						distance = 2
						# neighboursOther = False
						neighboursOther = True #testing
						for xd in range(-distance, distance+1):
							for yd in range(-distance, distance+1):

								if (0 <= tileX+xd < placed.w) and (0 <= tileY+yd < placed.h) and tilemap[tileX+xd,tileY+yd] != tilemap[tileX,tileY] and depthmap[tileX+xd,tileY+yd] < depthmap[tileX,tileY]:
									neighboursOther = True

						if neighboursOther:
							doneTiles.add((tileX,tileY))

					if tilemap[tileX,tileY] == colors['wall']:
						distance = 2
						neighboursOther = False
						for xd in range(-distance, distance+1):
							for yd in range(-distance, distance+1):

								if (0 <= tileX+xd < placed.w) and (0 <= tileY+yd < placed.h) and tilemap[tileX+xd,tileY+yd] != tilemap[tileX,tileY] and depthmap[tileX+xd,tileY+yd] < depthmap[tileX,tileY]:
									neighboursOther = True

						if neighboursOther:
							doneTiles.add((tileX,tileY))

		#fill rest with void

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				if not (tileX,tileY) in doneTiles:
					emptyTiles.add((tileX,tileY))


		#fill void with rock if 2 tiles away from dirt path and 3 tiles away from rock

		emptyTilesToRemove = set()
		for tileX, tileY in emptyTiles:
			neighboursDirt = False
			neighboursRock = False
			distance = 2

			for xd in range(-distance, distance+1):
				for yd in range(-distance, distance+1):
					if (0 <= tileX+xd < placed.w-1) and (0 <= tileY+yd < placed.h-1) and tilemap[tileX+xd,tileY+yd] != tilemap[tileX,tileY] and tilemap[tileX+xd,tileY+yd] == colors['dirt']:
						neighboursDirt = True
						break

			for xd in range(-distance-1, distance+2):
				for yd in range(-distance-1, distance+2):
					if (0 <= tileX+xd < placed.w-1) and (0 <= tileY+yd < placed.h-1) and xd != 0 and yd != 0 and tilemap[tileX+xd,tileY+yd] == colors['rock']:
						neighboursRock = True
						break

			if neighboursDirt and neighboursRock:
				placed.structure.tilemap[tileX,tileY] = colors['rock']
				emptyTilesToRemove.add((tileX,tileY))

		emptyTiles = emptyTiles - emptyTilesToRemove

		#fill remaining void with null tiles

		for tileX, tileY in emptyTiles:
			placed.structure.tilemap[tileX,tileY] = colors['null']



	def tilesDelimit(self):
		#PART 1A: establish boundaries between areas
		#trees are included by accident (fix this later?)

		colors = {'water': (64, 128, 160), 'land': (128, 180, 96), 'rock': (72, 72, 72), 'forest': (32, 128, 96), 'wall': (96, 96, 96), 'null': (100, 100, 100), 'dirt': (32, 16, 16), 'plaza': (180, 180 ,180), 'road': (255, 255, 255)}
		placed = self.structures[0]
		tilemap = placed.structure.tilemap
		heightmap = placed.structure.heightmap
		layermap = placed.structure.layermap

		emptyTiles = set()
		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				if tilemap[tileX,tileY] == colors['forest'] or tilemap[tileX,tileY] == colors['rock'] or tilemap[tileX,tileY] == colors['water']:
					emptyTiles.add((tileX,tileY))

		markedTiles = set()
		borderTiles = set()

		for i in range(50):
			newEmptyTiles = set()

			for tileX, tileY in emptyTiles:
				# if layermap[tileX,tileY] != 1:
					# continue

				leftOccupied = (tileX-1,tileY) not in emptyTiles
				rightOccupied = (tileX+1,tileY) not in emptyTiles
				topOccupied = (tileX,tileY-1) not in emptyTiles
				bottomOccupied = (tileX,tileY+1) not in emptyTiles

				canBeDeleted = False

				if leftOccupied and not rightOccupied:
					canBeDeleted = True
				if rightOccupied and not leftOccupied:
					canBeDeleted = True
				if topOccupied and not bottomOccupied:
					canBeDeleted = True
				if bottomOccupied and not topOccupied:
					canBeDeleted = True

				neighbours = 0
				for xd in range(-1,2):
					for yd in range(-1,2):
						if xd == 0 and yd == 0:
							continue
						if ((tileX+xd,tileY+yd)) in emptyTiles:
							neighbours += 1

				if neighbours <= 3:
				# if neighbours == 1:
					canBeDeleted = False

				if not canBeDeleted:
					newEmptyTiles.add((tileX,tileY))

			emptyTiles = newEmptyTiles

		for tileX, tileY in emptyTiles:
			if layermap[tileX,tileY] != 1:
				continue
			if tilemap[tileX,tileY] == colors['water']:
				continue
			borderTiles.add((tileX,tileY))

		borderTilesBackup = set()
		for tile in borderTiles:
			borderTilesBackup.add(tile)


		#PART 1B: clear tiles some distance away from roads (add to border tiles)

		# distance = 16
		distance = 12
		# distance = 8

		# spacing = 8
		spacing = 4

		protectedTiles = set()

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				if tileX % spacing == 0 and tileY % spacing == 0 and tilemap[tileX,tileY] == colors['forest']:
					discarded = False

					for d in range(0, distance):
						checkTiles = [(tileX+d,tileY+d), (tileX+d,tileY-d), (tileX-d,tileY+d), (tileX-d,tileY-d)]

						for tx, ty in checkTiles:
							if 0 < tx < placed.w-1 and 0 < ty < placed.h-1:
								if tilemap[tx,ty] in [colors['land'], colors['wall'], colors['dirt'], colors['plaza'], colors['road']]:
									protectedTiles.add((tileX,tileY))
									discarded = True
									break
						if discarded:
							break

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				if tileX % spacing == 0 and tileY % spacing == 0 and tilemap[tileX,tileY] == colors['forest'] and not (tileX, tileY) in protectedTiles:
					borderTiles.add((tileX,tileY))

		# print ("borderTiles:", len(borderTiles))


		#PART 1C: mark tiles to adjust (fill with null)

		for tileX, tileY in borderTiles:
			# radius = random.randint(2, 6)
			radius = random.randint(4, 8)
			# radius = 32
			# radius = 8

			max_radius = radius

			for xd in range(-radius, radius):
				for yd in range(-radius, radius):
					if tileX+xd < 0 or tileY+yd < 0 or tileX+xd > placed.w-1 or tileY+yd > placed.h-1:
						continue

					# if layermap[tileX+xd,tileY+yd] != 1:
					# if tilemap[tileX+xd,tileY+yd] == colors['land']:
					if tilemap[tileX+xd,tileY+yd] in [colors['land'], colors['dirt'], colors['plaza'], colors['road'], colors['wall']]:
					# if tilemap[tileX+xd,tileY+yd] in [colors['land'], colors['dirt'], colors['plaza'], colors['road'], colors['water'], colors['wall']]:
						max_radius = min(max_radius, getDistance(tileX, tileY, tileX+xd, tileY+yd) - 1)

			radius = max(0, int(max_radius))


			for xd in range(-radius, radius):
				for yd in range(-radius, radius):
					if tileX+xd < 0 or tileY+yd < 0 or tileX+xd > placed.w-1 or tileY+yd > placed.h-1:
						continue
					if tilemap[tileX+xd,tileY+yd] == colors['water']:
						continue

					if getDistance(tileX, tileY, tileX+xd, tileY+yd) <= radius:
						# tilemap[tileX+xd,tileY+yd] = colors['null']
						tilemap[tileX+xd,tileY+yd] = colors['rock']
						# tilemap[tileX+xd,tileY+yd] = colors['water']


		#PART 2: ADJUST TERRAIN

		grassOrForest = set()

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				if tilemap[tileX,tileY] == colors['forest'] and layermap[tileX,tileY] == 1:
				# if tilemap[tileX,tileY] == colors['forest']:
					grassOrForest.add((tileX,tileY))

		for tileX, tileY in grassOrForest:
			tilemap[tileX,tileY] = colors['null']

		self.fillSelectedTilesNearPath(placed, tilemap, layermap, colors, set(), grassOrForest)

		# for tileX, tileY in borderTilesBackup:
			# tilemap[tileX,tileY] = colors['dirt']


	def clearLayermap(self):
		placed = self.structures[0]

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				placed.structure.layermap[tileX,tileY] = 1


	def fillSelectedTilesNearPath(self, placed, tilemap, layermap, colors, emptyTiles, tilesToFill):
		distanceToWater = {}
		distanceToLand = {}
		distanceToSolid = {}

		for tileX, tileY in tilesToFill:
			waterDistance = 9999
			landDistance = 9999
			solidDistance = 9999

			for d in range(1, 100):
				for xd in range(-d, d):
					for yd in [-d,d]:
						if (tileX+xd,tileY+yd) in emptyTiles:
							continue
						if tileX+xd <= 0 or tileX+xd >= placed.w-1 or tileY+yd <= 0 or tileY+yd >= placed.h-1:
							continue

						tileColor = tilemap[tileX+xd,tileY+yd]
						if tileColor == colors['rock'] or layermap[tileX+xd,tileY+yd] != 1:
							solidDistance = min(solidDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['land'] or tileColor == colors['wall']:
							landDistance = min(landDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['water']:
							waterDistance = min(waterDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))

				for yd in range(-d, d):
					for xd in [-d,d]:
						if (tileX+xd,tileY+yd) in emptyTiles:
							continue
						if tileX+xd <= 0 or tileX+xd >= placed.w-1 or tileY+yd <= 0 or tileY+yd >= placed.h-1:
							continue

						tileColor = tilemap[tileX+xd,tileY+yd]
						if tileColor == colors['rock'] or layermap[tileX+xd,tileY+yd] != 1:
							solidDistance = min(solidDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['land'] or tileColor == colors['wall']:
							landDistance = min(landDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['water']:
							waterDistance = min(waterDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))

				if waterDistance != 9999 or landDistance != 9999 or solidDistance != 9999:
					break

			distanceToLand[(tileX,tileY)] = landDistance
			distanceToSolid[(tileX,tileY)] = solidDistance
			distanceToWater[(tileX,tileY)] = waterDistance

		for tileX, tileY in tilesToFill:
			if distanceToWater[(tileX,tileY)] < distanceToLand[tileX,tileY] and distanceToWater[(tileX,tileY)] < distanceToSolid[tileX,tileY]:
				placed.structure.tilemap[tileX,tileY] = colors['water']
			elif distanceToSolid[(tileX,tileY)] < distanceToLand[tileX,tileY]:
				placed.structure.tilemap[tileX,tileY] = colors['forest']
			else:
				placed.structure.tilemap[tileX,tileY] = colors['land']


	def fillSelectedTiles(self, placed, tilemap, colors, emptyTiles, tilesToFill):
		distanceToWater = {}
		distanceToLand = {}
		distanceToRock = {}

		for tileX, tileY in tilesToFill:
			waterDistance = 9999
			landDistance = 9999
			rockDistance = 9999

			for d in range(1, 100):
				for xd in range(-d, d):
					for yd in [-d,d]:
						if (tileX+xd,tileY+yd) in emptyTiles:
							continue
						if tileX+xd <= 0 or tileX+xd >= placed.w-1 or tileY+yd <= 0 or tileY+yd >= placed.h-1:
							continue

						tileColor = tilemap[tileX+xd,tileY+yd]
						if tileColor == colors['water']:
							waterDistance = min(waterDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['land'] or tileColor == colors['wall']:
							landDistance = min(landDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['rock']:
							rockDistance = min(rockDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))

				for yd in range(-d, d):
					for xd in [-d,d]:
						if (tileX+xd,tileY+yd) in emptyTiles:
							continue
						if tileX+xd <= 0 or tileX+xd >= placed.w-1 or tileY+yd <= 0 or tileY+yd >= placed.h-1:
							continue

						tileColor = tilemap[tileX+xd,tileY+yd]
						if tileColor == colors['water']:
							waterDistance = min(waterDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['land'] or tileColor == colors['wall']:
							landDistance = min(landDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))
						elif tileColor == colors['rock']:
							rockDistance = min(rockDistance, getDistance(tileX, tileY, tileX+xd, tileY+yd))

				if waterDistance != 9999 or landDistance != 9999 or rockDistance != 9999:
					break

			distanceToWater[(tileX,tileY)] = waterDistance
			distanceToLand[(tileX,tileY)] = landDistance
			distanceToRock[(tileX,tileY)] = rockDistance

		for tileX, tileY in tilesToFill:
			if distanceToWater[(tileX,tileY)] < distanceToLand[tileX,tileY] and distanceToWater[(tileX,tileY)] < distanceToRock[tileX,tileY]:
				placed.structure.tilemap[tileX,tileY] = colors['water']
			elif distanceToRock[(tileX,tileY)] < distanceToLand[tileX,tileY]:
				placed.structure.tilemap[tileX,tileY] = colors['rock']
			else:
				placed.structure.tilemap[tileX,tileY] = (32, 128, 96)


	def tilesFill(self):
		colors = {'water': (64, 128, 160), 'land': (128, 180, 96), 'rock': (72, 72, 72), 'wall': (96, 96, 96), 'null': (100, 100, 100)}

		placed = self.structures[0]
		tilemap = placed.structure.tilemap

		#split tiles into empty tiles (all), selected (first batch, every gridSize tiles apart), remaining (rest to fill if necessary)
		gridSize = 4

		emptyTiles = set()
		selectedTiles = set()
		remainingTiles = set()

		for tileX in range(0, int(placed.w)):
			for tileY in range(0, int(placed.h)):
				if tilemap[tileX,tileY] == colors['null']:
					emptyTiles.add((tileX,tileY))
					if tileX % gridSize == 0 and tileY % gridSize == 0:
						selectedTiles.add((tileX,tileY))
					else:
						remainingTiles.add((tileX,tileY))

		#start with filling spots every N tiles (selectedTiles)
		self.fillSelectedTiles(placed, tilemap, colors, emptyTiles, selectedTiles)

		#fill every possible square formed by 4 corners with one specific tile
		for tileX, tileY in selectedTiles:
			if not (tileX-gridSize,tileY) in selectedTiles or (tileX,tileY-gridSize) not in selectedTiles or not (tileX-gridSize,tileY-gridSize) in selectedTiles:
				continue

			if tilemap[tileX,tileY] == tilemap[tileX-gridSize,tileY] == tilemap[tileX,tileY-gridSize] == tilemap[tileX-gridSize,tileY-gridSize]:
				canFill = True
				gridTiles = []
				for tileX2 in range(tileX-gridSize,tileX):
					for tileY2 in range(tileY-gridSize+1,tileY):
						gridTiles.append((tileX2,tileY2))
						if not tilemap[tileX2,tileY2] == colors['null']:
							canFill = False
							break
					if not canFill:
						break
				if not canFill:
					continue

				for (tileX2,tileY2) in gridTiles:
					placed.structure.tilemap[tileX2,tileY2] = tilemap[tileX,tileY]
					remainingTiles.discard((tileX2,tileY2))

		#fill in remaining tiles (more detailed analysis)
		self.fillSelectedTiles(placed, tilemap, colors, emptyTiles, remainingTiles)


	def getTilemapValues(self, simplify=True):
		tile_dc = tile_dictionary()
		label_dc = get_label_dc()
		targetDc, conflatedDc, target_tile_keys = get_tile_targets_dc()

		placed = self.structures[0]
		tag_map = {}

		special_cases = set(["roadcliff", "dirtcliff", "roadpillarSE", "roadpillarSW", "roadpillarNE", "roadpillarNW", "dirtpillarSE", "dirtpillarSW", "dirtpillarNE", "dirtpillarNW"])
		special_case_dc = {"roadcliff": "cliff", "dirtcliff": "cliff",
							"roadpillarSE": "pillarSE", "roadpillarSW": "pillarSW", "roadpillarNE": "pillarNE", "roadpillarNW": "pillarNW",
							"dirtpillarSE": "pillarSE", "dirtpillarSW": "pillarSW", "dirtpillarNE": "pillarNE", "dirtpillarNW": "pillarNW"}


		for x in range(0, placed.w):
			tag_map[x] = {}
			for y in range(0, placed.h):
				tag = tag_tile(placed.structure.tilemap, placed.structure.heightmap, placed.w, placed.h, x, y, label_dc, targetDc, conflatedDc, target_tile_keys)

				if simplify: #only keep general material, not exact tile reference considering neighbours
					tag = tag.split("_")[0]
					if tag in special_cases:
						tag = special_case_dc[tag]

				tag_map[x][y] = tag

		return tag_map


	def getTilemapText(self, simplify=True):
		placed = self.structures[0]
		tag_map = self.getTilemapValues(simplify=simplify)

		tag_map_text = ""
		for y in range(0, placed.h):
			for x in range (0, placed.w):
				tag_map_text += tag_map[x][y]
				if x != placed.w-1:
					tag_map_text += ", "
			if y != placed.h-1:
				tag_map_text += "\n"

		return tag_map_text


#MAP GENERATOR CLASS
#this is where most of actual map generation (building up areas from the node tree) takes place

#generatedStructure = top generated arrangement, i.e. complete map
#viable = list of nodes which can be generated (every required child is already generated)


class GeneratedMap:
	def __init__(self, root, seed):
		self.root = root
		self.seed = seed
		self.generatedStructure = None
		self.viable = []


	def getWrongTerminalNodes(self, structureDc):
		#find terminal (leaf) nodes in currently loaded self.root which are containers with no assigned size
		nodes = []
		self.root.collectStructures(nodes)
		nodeKeys = set(structureDc.keys())
		wrongNodes = []
		for node in nodes:
			if not node.childNodes and not node.category in nodeKeys:
				wrongNodes.append(node.category)
		return wrongNodes


	def updateViable(self):
		self.root.clearViable()
		random.seed(self.seed) #use instance's default seed again
		self.root.searchViable(self.viable)


	def generateStructures(self, structureDc, prototypeDc):
		# depth_limit = 320
		depth_limit = 100000

		for i in range(depth_limit):
			if self.viable:
				if i == depth_limit - 1:
					print ("Warning - structure limit reached!")
					# quit()

				generatedStructureIsContinent = self.generateNextViableNode(structureDc, prototypeDc)
				self.generatedStructure.connectAllPaths(len(self.viable), generatedStructureIsContinent)
				self.generatedStructure.freeze()

			else:
				break


	def tilePostprocessing(self):
		tiles_smooth(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_cliffs(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		self.adjustStrandedTiles()
		self.generateDetails()
		tweak_trees(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		prune_trees(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		prune_trees(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)


	def adjustStrandedTiles(self):
		tiles_replace_stranded(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		tiles_replace_stranded(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)


	def generateDetails(self):
		add_rocks(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_rocks(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_fences(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_fences(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_pillars(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_doors(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)
		add_trees(self.generatedStructure.structures[0], self.generatedStructure.structures[0].structure.tilemap)


	def generateNode(self, generatedNode, structureDc, prototypeDc):
		newArrangement = Arrangement()
		newArrangement.generateStructures(generatedNode.childNodes, generatedNode, structureDc, prototypeDc)

		for childPath in generatedNode.childPaths:
			newArrangement.assignRequiredPath(childPath)

		newArrangement.generateExits()
		newArrangement.freeze()

		generatedNode.structure = newArrangement


	def generateNextViableNode(self, structureDc, prototypeDc):
		random.seed(self.seed) #use instance's default seed again

		if self.viable:
			targetNode = self.viable[0]

			# print ("Generating targetNode: %s (%s), %s" % (targetNode.label, targetNode.category, str(list(targetNode.properties))))

			start_time = time.time()
			self.generateNode(targetNode, structureDc, prototypeDc)
			self.generatedStructure = targetNode.structure

			# print ("Generated node in %.3f seconds\n" % ((time.time() - start_time)))

		self.viable = []
		self.root.searchViable(self.viable)

		return "%" in targetNode.properties