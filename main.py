from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
from copy import copy, deepcopy
import pygame
import sys, os, time

from generator import Generator
from drawn_map import DrawnMap, load_tile_table

#PYGAME-BASED VISUAL INTERFACE
#the generator can be used without it (see e.g. ascii_level_example.py)


#parameters for drawing graphs
minNodeHeight = 29
maxHeight = 250
nodeRadius = 10
spaceX = 90

xOffset = 96
yOffset = 96


#file paths
settingsPath = "resources/settings.ini"
iconPath = "resources/chest_icon.png"
tilesetPath = "resources/tileset.png"


#SETUP

class DrawnTree:
	def __init__(self):
		self.drawnNodes = []
		self.drawnNodeDc = {}
		self.selectedNode = None


	def updatePathConnections(self):
		drawnNodeDcKeys = set(self.drawnNodeDc.keys())

		for drawnNode in self.drawnNodes:
			drawnNode.pathConnections = []

		for drawnNode in self.drawnNodes:
			currentNode = drawnNode.node
			parentNode = drawnNode.parentNode

			if parentNode != None:
				for childNode in parentNode.childNodes:
					if childNode.label == currentNode.label:
						break

				for pathSource, pathTarget, pathColor, pathSpecifiedMaterial in parentNode.childPaths:
					sourceLabel, sourceDirection = pathSource
					targetLabel, targetDirection = pathTarget

					if sourceLabel == currentNode.label:
						if targetLabel == None: #connects to parent
							drawnParent = self.drawnNodeDc[parentNode]
							drawnNode.pathConnections.append(drawnParent)
							drawnParent.pathConnections.append(drawnNode)

						else: #connects to sibling
							node2 = None
							for childNode in parentNode.childNodes:
								if childNode.label == targetLabel:
									node2 = childNode
									break

							if not node2 in drawnNodeDcKeys: #wrong label in path
								continue

							drawnNode2 = self.drawnNodeDc[node2]

							if drawnNode != None and drawnNode2 != None:
								drawnNode.pathConnections.append(drawnNode2)
								drawnNode2.pathConnections.append(drawnNode)

					elif targetLabel != None:
						if targetLabel == currentNode.label:
							node2 = None
							for childNode in parentNode.childNodes:
								if childNode.label == sourceLabel:
									node2 = childNode
									break

							if not node2 in drawnNodeDcKeys: #wrong label in path
								continue

							drawnNode2 = self.drawnNodeDc[node2]

							if drawnNode != None and drawnNode2 != None:
								drawnNode.pathConnections.append(drawnNode2)
								drawnNode2.pathConnections.append(drawnNode)


class DrawnNode:
	def __init__(self, label, node, x, y, h, w, parentNode, parentOffset, parentSize, prototypeDc):
		self.label = label
		self.node = node
		self.x, self.y, self.w, self.h = x, y, w, h
		self.parentNode = parentNode
		self.parentOffset = parentOffset
		self.parentSize = parentSize
		self.prototypeDc = prototypeDc
		self.pathConnections = []


	def drawPaths(self, screen, nodeRadius, xOffset, yOffset, tree, color):
		for connected in self.pathConnections:
			if self.x == connected.x:
				midpoint = min(self.x, connected.x)-48
			else:
				midpoint = min(self.x, connected.x)

			pygame.draw.line(screen, color, (self.x+xOffset,self.y+yOffset), (midpoint+xOffset,self.y+yOffset), 3)
			pygame.draw.line(screen, color, (connected.x+xOffset,connected.y+yOffset), (midpoint+xOffset,connected.y+yOffset), 3)
			pygame.draw.line(screen, color, (midpoint+xOffset,self.y+yOffset), (midpoint+xOffset,connected.y+yOffset), 3)


	def drawLinks(self, screen, nodeRadius, xOffset, yOffset, tree, color):
		global screenH

		if self.parentNode:
			sourceY = self.parentOffset + self.parentSize/2

			if sourceY+yOffset < 0 and self.y+yOffset < 0:
				return
			if sourceY+yOffset > screenH and self.y+yOffset > screenH:
				return

			parts = 160
			yPrev = -999
			for i in range(parts):
				progress = float(i) / float(parts)
				increment = 1. / float(parts)

				x1 = self.x - (progress*90) -nodeRadius/2
				x2 = x1 + (increment*90)

				progress = progress**2
				y1 = (self.y + (sourceY-self.y) * progress)
				y2 = (self.y + (sourceY-self.y) * progress) + (sourceY-self.y) * increment
				if yPrev != -999:
					y1 = yPrev

				pygame.draw.line(screen, color, (x2+xOffset,y1+yOffset), (x1+xOffset,y2+yOffset), 2)
				yPrev = y2


	def draw(self, screen, nodeRadius, xOffset, yOffset, tree):
		# after drawing a map, nodes are assigned structures for arrangements which they previously don't have
		global screenH

		if self.y+yOffset-self.h/2 > -32 and self.y+yOffset+self.h/2 < screenH+32:
			if self.node.structure != None and self.node.structure.__class__.__name__ == "Structure":
				nodeColor = self.node.structure.color
			elif self.label in self.prototypeDc.keys():
				nodeColor = self.prototypeDc[self.label].color
			else:
				nodeColor = (100, 96, 96)

			nodeColor = (min(230,nodeColor[0]+64),min(230,nodeColor[1]+64),min(230,nodeColor[2]+64))
			nodeColorDark = nodeColor
			nodeColorDot = (255,255,255)

			if self == tree.selectedNode:
				nodeColorDark = (0,160,224)

			pygame.draw.rect(screen, nodeColorDark, (xOffset+self.x-(self.w/2)-self.h/2, self.y+yOffset-self.h/2, self.w+self.h, self.h), 0, border_radius=999)
			pygame.draw.rect(screen, nodeColor, (xOffset+self.x-(self.w/2)+2-self.h/2, self.y+yOffset-(self.h-4)/2, self.w-4+self.h, self.h-4), 0, border_radius=999)

			if '!' in self.node.properties:
				if self.h > 32:
					pygame.draw.circle(screen, nodeColorDot, (xOffset+self.x-36, self.y+yOffset), 4, 0)
				else:
					pygame.draw.circle(screen, nodeColorDot, (xOffset+self.x-28, self.y+yOffset), 4, 0)

			textsurface = FONT.render(str(self.label)[:10], True, (0, 0, 0))
			screen.blit(textsurface, (self.x+xOffset-self.w/2, self.y+yOffset-8))

			if self.h > 32:
				textsurface = FONT4.render(str(self.node.category)[:30], True, (0, 0, 0))
				screen.blit(textsurface, (self.x+xOffset-self.w/2-2, self.y+yOffset+5))


def saveNode(screen, nodeRadius, node, parentNode, layer, layer_dc, nodeNumber, spaceX, xOffset, yOffset, parentOffset, parentSize, treeNodes, prototypeDc, drawnNodeDc):
	minHeight = getMinHeight(node)
	x = 0

	layerHeight = 0
	previousNodesHeight = 0
	if parentNode != None:
		for i, anyNode in enumerate(parentNode.childNodes):
			currentHeight = getMinHeight(anyNode)
			layerHeight += currentHeight
			if i < nodeNumber:
				previousNodesHeight += currentHeight
	else:
		layerHeight = minHeight

	previousArea = float(previousNodesHeight) / float(layerHeight)

	areaStart = parentOffset + int( previousArea * parentSize )
	areaSize = minHeight

	y = areaStart + areaSize / 2

	for childNodeNumber, childNode in enumerate(node.childNodes):
		heightDiff = 0

		childHeightsCollected = max(minNodeHeight, sum([getMinHeight(childNode2) for childNode2 in node.childNodes]))
		childHeights = max(minNodeHeight, childHeightsCollected)

		heightDiff = childHeights - minHeight

		saveNode(screen, nodeRadius, childNode, node, layer+1, layer_dc, childNodeNumber, spaceX, xOffset, yOffset, int(areaStart-heightDiff/2), int(areaSize+heightDiff), treeNodes, prototypeDc, drawnNodeDc)

	rectHeight = minNodeHeight-4
	if getMinHeightAltered(node, 0) > minNodeHeight:
		rectHeight = minNodeHeight*2-16

	rectWidth = 44
	x = layer*spaceX

	drawnNode = DrawnNode(node.label, node, x, y, rectHeight, rectWidth, parentNode, parentOffset, parentSize, prototypeDc)
	drawnNodeDc[node] = drawnNode
	treeNodes.append(drawnNode)


#create arrangement

def collectNodes(node, depth, layer_dc):
	if depth in layer_dc.keys():
		layer_dc[depth].append(node)
	else:
		layer_dc[depth] = [node]

	for childNode in node.childNodes:
		collectNodes(childNode, depth+1, layer_dc)


def getMinHeight(node):
	if node.childNodes:
		childHeights = sum([getMinHeight(childNode) for childNode in node.childNodes])
		return max(minNodeHeight, childHeights)
	else:
		return minNodeHeight


def getMinHeightAltered(node, margin):
	if node.childNodes:
		childHeights = sum([getMinHeightAltered(childNode, margin) for childNode in node.childNodes])
		return max(minNodeHeight, childHeights-margin)
	else:
		return minNodeHeight


def generateDrawnTree(root, prototypeDc):
	tree = DrawnTree()
	tree.drawnNodes = []
	tree.drawnNodeDc = {}
	layer_dc = {}

	collectNodes(root, 0, layer_dc)
	saveNode(screen, nodeRadius, root, None, 0, layer_dc, 0, spaceX, xOffset, yOffset, 0, maxHeight, tree.drawnNodes, prototypeDc, tree.drawnNodeDc)
	tree.updatePathConnections()

	return tree


class Path:
	def __init__(self, pathData):
		self.data = pathData
		self.targetIsParent = False
		self.reverseDirection = False
		self.itemId = 0

		self.source = None
		self.sourceLabel = ''
		self.sourceDirection = 's'

		self.target = None
		self.targetLabel = ''
		self.targetDirection = 's'


def getSettings(settingsPath):
	setting_flags = {}
	if os.path.isfile(settingsPath):
		with open(settingsPath, 'r') as file:
			for line in file.readlines():
				if "=" in line:
					key, value = line.split("=", 1)
					setting_flags[key.strip()] = value.strip()
	return setting_flags


def updateSettings(settingsPath, setting_flags, setting_keys, autosave, key, value):
	if autosave and os.path.isfile(settingsPath):
		setting_keys.add(key)
		setting_flags[key] = value

		with open(settingsPath, 'w') as file:
			setting_tileSize = int(setting_flags['tileSize']) if 'tileSize' in setting_keys else 8
			setting_seedSelected = int(setting_flags['seedSelected']) if 'seedSelected' in setting_keys else 122
			setting_mapSelected = setting_flags['mapSelected'] if 'mapSelected' in setting_keys else ""

			contents = ["autosave=%i\n" % 1,
						"tileSize=%i\n" % setting_tileSize,
						"seedSelected=%i\n" % setting_seedSelected,
						"mapSelected=%s" % setting_mapSelected
						]

			file.writelines(contents)


class Interface:
	def __init__(self, screen, surface, screenW, screenH, nodeRadius, xOffset, yOffset):
		self.screen, self.surface, self.screenW, self.screenH = screen, surface, screenW, screenH
		self.nodeRadius = nodeRadius
		self.xOffset, self.yOffset = xOffset, yOffset
		self.xOffsetOrigin, self.yOffsetOrigin = self.xOffset, self.yOffset

		self.mapDirectory = "maps"
		self.currentMapDirectory = ""
		self.currentMapName = ""
		self.ms_names = []
		self.map_selection = False

		self.button_text = ["LOAD MAP", "GENERATE", "ADD DETAILS", "EXPORT TXT", "EXPORT PNG"]
		self.button_active = [True, False, False, False, False]

		self.setupUI()
		self.setupCurrentZoom()
		self.setupCurrentSeed()
		self.setupMapSelection()

		self.overlay_alpha = 32 #darkening the screen slightly while something is loading
		self.overlay = pygame.Surface((screenW,screenH))
		self.overlay.fill((0,0,0))
		self.overlay.set_alpha(self.overlay_alpha)

		self.tree = None
		self.currentPaths = []

		self.generator = Generator()
		self.drawnMap = None

		self.displayTiles = False

		#read settings from settings.ini, if it exists

		self.setting_flags = getSettings(settingsPath)
		self.setting_keys = set(self.setting_flags.keys())

		self.autosaveSettings = 'autosave' in self.setting_flags and self.setting_flags['autosave'] == '1'

		#tile size

		self.tileSizes = [1,2,3,4,6,8,12,16]
		self.tileSizeSelected = 5

		if 'tileSize' in self.setting_keys:
			tileSizeSetting = int(self.setting_flags['tileSize']) if self.setting_flags['tileSize'].isdigit() else 8
			if tileSizeSetting in self.tileSizes:
				self.tileSizeSelected = self.tileSizes.index(tileSizeSetting)

		self.tileSize = self.tileSizes[self.tileSizeSelected]

		#seed

		self.SEED = 122
		if 'seedSelected' in self.setting_keys:
			self.SEED = int(self.setting_flags['seedSelected']) if self.setting_flags['seedSelected'].isdigit() else 122

		#load map (if map name is saved in settings)

		mapSelected = ""
		if 'mapSelected' in self.setting_keys:
			mapSelected = self.setting_flags['mapSelected']

		if mapSelected:
			self.currentMapName = mapSelected
			self.currentMapDirectory = self.mapDirectory + "/" + self.currentMapName

			setupSuccessful = self.setup(self.currentMapDirectory, self.SEED)

			if setupSuccessful:
				self.generateDrawnTree()

				self.button_active[1] = True
				self.button_active[2] = False
			else:
				self.generator.reset()
				self.tree = None


	def loadMap(self, mapNumber):
		global popup

		#close level selection and current map when a new map is loaded
		self.map_selection = False
		self.drawnMap = None
		self.generator.reset()

		self.currentMapName = self.ms_names[mapNumber]
		self.currentMapDirectory = self.mapDirectory + "/" + self.currentMapName

		setupSuccessful = self.setup(self.currentMapDirectory, self.SEED)

		if setupSuccessful:
			self.generateDrawnTree()
			popup = False

			self.xOffset, self.yOffset = self.xOffsetOrigin, self.yOffsetOrigin
			self.button_active[1] = True
			self.button_active[2] = False

			updateSettings(settingsPath, self.setting_flags, self.setting_keys, self.autosaveSettings, 'mapSelected', self.currentMapName)
			print ("\nLOADED MAP: %s" % self.currentMapName)

		else:
			self.generator.reset()
			self.tree = None


	def setup(self, directoryName, selectionSeed):
		global popup, popupTimer, popupsurface

		try:
			#load map rules, create graph for given seed

			textFiles = [os.path.join(directoryName, filePath) for filePath in os.listdir(directoryName) if os.path.isfile(os.path.join(directoryName, filePath)) and filePath[-4:] == ".txt"]

			self.generator.loadRules(textFiles)
			self.generator.loadGraph(selectionSeed)

			# self.generator.printCurrentGraph()
			# self.generator.printCurrentStructures()

			return True

		#interface error messages

		except IndexError as missingDefinition:
			popup, popupTimer = True, 100
			popupsurface = FONT3.render("ERROR - map doesn't contain any structures for: %s" % str(missingDefinition), True, (0, 0, 0))
			print ("ERROR - map doesn't contain any structures for: %s" % str(missingDefinition))
			return False

		except KeyError as missingKey:
			missingLabel, missingCategory = str(missingKey)[1:-1].rsplit("#", 1)
			popup, popupTimer = True, 100
			if missingCategory == "":
				popupsurface = FONT3.render("ERROR - label doesn't have any category: %s (???)" % missingLabel, True, (0, 0, 0))
				print ("ERROR - structure label doesn't have a category: %s" % missingLabel)
			else:
				popupsurface = FONT3.render("ERROR - category '%s' is not defined: %s (%s)" % (missingCategory, missingLabel, missingCategory), True, (0, 0, 0))
				print ("ERROR - map doesn't define structure: %s" % missingCategory)
			return False

		except FileNotFoundError:
			popup, popupTimer = True, 100
			popupsurface = FONT3.render("ERROR - couldn't find the map folder", True, (0, 0, 0))
			print ("ERROR - couldn't find the map folder")
			return False

		except:
			popup, popupTimer = True, 100
			popupsurface = FONT3.render("UNKNOWN ERROR - possibly missing root or wrong path formatting?", True, (0, 0, 0))
			print ("UNKNOWN ERROR - possibly missing root or wrong path formatting?")
			return False


	def generateDrawnTree(self):
		self.tree = generateDrawnTree(self.generator.root, self.generator.prototypeDc)
		self.tree.selectedNode = None


	def getCurrentPaths(self):
		self.currentPaths = []

		if self.tree.selectedNode != None and self.tree.selectedNode.label != "root":
			parentNode = self.tree.selectedNode.parentNode
			currentNode = self.tree.selectedNode.node

			for itemId, pathData in enumerate(parentNode.childPaths):
				pathSource, pathTarget, pathColor, pathSpecifiedMaterial = pathData
				sourceLabel, sourceDirection = pathSource
				targetLabel, targetDirection = pathTarget

				if targetLabel == None:
					targetLabel = parentNode.label

				if self.tree.selectedNode.label == sourceLabel:
					#source -> target
					path = Path(pathData)

					path.reverseDirection = False
					path.targetIsParent = targetLabel == None
					path.itemId = itemId
					path.source, path.sourceLabel, path.sourceDirection = None, sourceLabel, sourceDirection
					path.target, path.targetLabel, path.targetDirection = None, targetLabel, targetDirection
					if path.targetIsParent:
						path.targetLabel = "PARENT"

					self.currentPaths.append(path)

				elif self.tree.selectedNode.label == targetLabel:
					#target -> source (flipped)
					path = Path(pathData)

					path.reverseDirection = True
					path.targetIsParent = False
					path.itemId = itemId
					path.source, path.sourceLabel, path.sourceDirection = None, sourceLabel, sourceDirection
					path.target, path.targetLabel, path.targetDirection = None, targetLabel, targetDirection

					self.currentPaths.append(path)


	def centerText(self, text, font, color, x, y):
		message = font.render(text, True, color)
		rect = message.get_rect(center=(x, y))
		self.screen.blit(message, (rect[0], y))


	def setupMapSelection(self):
		if os.path.isdir(self.mapDirectory):
			self.ms_names = [directoryName for directoryName in os.listdir(self.mapDirectory) if os.path.isdir(os.path.join(self.mapDirectory, directoryName))]
		else:
			self.ms_names = []

		self.ms_bounds = []
		self.ms_text_positions = []

		button_h = 64
		button_spacing = 16
		button_padding = 40

		for i in range(len(self.ms_names)):
			selection_y = button_padding + (button_h+button_spacing) * i
			ms_bounds = (self.ms_button_x-self.ms_button_width/2, selection_y, self.ms_button_width, button_h)
			ms_text_position = self.ms_button_x, selection_y+20
			self.ms_bounds.append(ms_bounds)
			self.ms_text_positions.append(ms_text_position)


	def setupCurrentSeed(self):
		if self.button_bounds:
			self.seed_bounds = (self.screenW-113, self.button_bounds[0][1]-53, 100, 35)
			self.seed_text_position = (self.screenW-66, self.seed_bounds[1]+9)
		else:
			self.seed_bounds = (self.screenW-113, 75, 100, 35)
			self.seed_text_position = (self.screenW-66, self.seed_bounds[1]+9)


	def setupCurrentZoom(self):
		if self.button_bounds:
			self.zoom_bounds = (self.screenW-113, self.button_bounds[0][1]-53-60, 100, 35)
			self.zoom_text_position = (self.screenW-66, self.zoom_bounds[1]+9)
		else:
			self.zoom_bounds = (self.screenW-113, 75-60, 100, 35)
			self.zoom_text_position = (self.screenW-66, self.zoom_bounds[1]+9)


	def drawCurrentSeed(self):
		pygame.draw.rect(self.screen, (255, 255, 255), self.seed_bounds, 0)
		self.centerText("seed", FONT2, (0,0,0), self.seed_text_position[0], self.seed_text_position[1]-28)
		self.centerText(str(self.SEED), FONT2, (0,0,0), self.seed_text_position[0], self.seed_text_position[1])

		pygame.draw.polygon(self.screen, (0, 0, 0), [(self.seed_text_position[0]-28-12, self.seed_text_position[1]+8), (self.seed_text_position[0]-28, self.seed_text_position[1]+8-8), (self.seed_text_position[0]-28, self.seed_text_position[1]+8+8)])
		pygame.draw.polygon(self.screen, (0, 0, 0), [(self.seed_text_position[0]+28+12, self.seed_text_position[1]+8), (self.seed_text_position[0]+28, self.seed_text_position[1]+8-8), (self.seed_text_position[0]+28, self.seed_text_position[1]+8+8)])


	def drawCurrentZoom(self):
		pygame.draw.rect(self.screen, (255, 255, 255), self.zoom_bounds, 0)
		self.centerText("tile size", FONT2, (0,0,0), self.zoom_text_position[0], self.zoom_text_position[1]-28)
		self.centerText(str(self.tileSize), FONT2, (0,0,0), self.zoom_text_position[0], self.zoom_text_position[1])

		pygame.draw.polygon(self.screen, (0, 0, 0), [(self.zoom_text_position[0]-28-12, self.zoom_text_position[1]+8), (self.zoom_text_position[0]-28, self.zoom_text_position[1]+8-8), (self.zoom_text_position[0]-28, self.zoom_text_position[1]+8+8)])
		pygame.draw.polygon(self.screen, (0, 0, 0), [(self.zoom_text_position[0]+28+12, self.zoom_text_position[1]+8), (self.zoom_text_position[0]+28, self.zoom_text_position[1]+8-8), (self.zoom_text_position[0]+28, self.zoom_text_position[1]+8+8)])


	def setupUI(self):
		#UI background
		x1, y1 = self.screenW-128, 0
		x2, y2 = self.screenW, self.screenH
		self.ui_bounds = (x1, y1, x2-x1, y2-y1)

		#buttons
		button_w = 160
		button_h = 80
		button_offset, button_text_offset = 0, 0
		button_spacing = 12
		button_padding = 32 +96 +24

		self.button_bounds = []
		self.button_text_positions = []
		self.button_selected = -1

		for i in range(len(self.button_text)):
			button_x = self.ui_bounds[0]+self.ui_bounds[2]/2 - button_w/2
			button_y = button_padding + (button_h+button_spacing)*i

			#hacky change: shrink size of export buttons
			if i >= 3:
				button_h_multiplier = .5
			else:
				button_h_multiplier = 1
			if i >= 4:
				button_y -= button_h/2

			self.button_bounds.append( (button_x+button_offset, button_y, button_w, button_h*button_h_multiplier) )
			self.button_text_positions.append( (button_x+button_text_offset+button_w/2-4, button_y+button_h*button_h_multiplier/2-10) )

		#map selection
		self.ms_button_width = 400
		self.ms_button_selected = -1

		ms_x1, ms_y1 = 0, 0
		ms_x2, ms_y2 = self.screenW, self.screenH

		self.map_selection_bounds = (ms_x1, ms_y1, ms_x2-ms_x1, ms_y2-ms_y1)
		self.ms_button_x = self.map_selection_bounds[0]+self.map_selection_bounds[2]/2


	def drawUI(self):
		#colors
		column_color = (224, 224, 224)
		outline_color = (64, 64, 64)
		bg_color = (192, 192, 192)

		#map selection
		if self.map_selection:
			pygame.draw.rect(self.screen, bg_color, self.map_selection_bounds, 0)

			for i in range(len(self.ms_names)):
				if i == self.ms_button_selected:
					button_color = (192, 224, 255)
					button_text_color = (0, 0, 128)
				else:
					button_color = (240, 240, 240)
					button_text_color = (0, 0, 0)

				pygame.draw.rect(self.screen, button_color, self.ms_bounds[i], 0)
				pygame.draw.rect(self.screen, outline_color, self.ms_bounds[i], 1)
				self.centerText(self.ms_names[i], FONT3, button_text_color, self.ms_text_positions[i][0], self.ms_text_positions[i][1])

		#UI background
		pygame.draw.rect(self.screen, column_color, self.ui_bounds, 0)
		pygame.draw.rect(self.screen, outline_color, (self.ui_bounds[0]-1, self.ui_bounds[1], 1, self.ui_bounds[3]), 0)

		#buttons
		for i in range(len(self.button_text)):
			if i == self.button_selected:
				button_color = (192, 224, 255)
				button_text_color = (0, 0, 128)
			elif self.button_active[i]:
				button_color = (240, 240, 240)
				button_text_color = (0, 0, 0)
			else:
				button_color = (192, 192, 192)
				button_text_color = (144, 144, 144)

			if self.button_text[i] == "LOAD MAP" and self.drawnMap:
				button_text = "RETURN"
			else:
				button_text = self.button_text[i]

			pygame.draw.rect(self.screen, button_color, self.button_bounds[i], 0, border_radius=8)
			pygame.draw.rect(self.screen, outline_color, self.button_bounds[i], 1, border_radius=8)
			self.centerText(button_text, FONT3, button_text_color, self.button_text_positions[i][0], self.button_text_positions[i][1])


	def updateButtonHover(self, mousePos):
		self.button_selected = -1
		self.ms_button_selected = -1
		mouseX, mouseY = mousePos

		for i in range(len(self.button_text)):
			if self.button_active[i] and self.button_bounds[i][0] < mouseX < self.button_bounds[i][0]+self.button_bounds[i][2] and self.button_bounds[i][1] < mouseY < self.button_bounds[i][1]+self.button_bounds[i][3]:
				self.button_selected = i

		if self.map_selection:
			for i in range(len(self.ms_names)):
				if self.ms_bounds[i][0]-8 < mouseX < self.ms_bounds[i][0]+self.ms_bounds[i][2]+8 and self.ms_bounds[i][1]-8 < mouseY < self.ms_bounds[i][1]+self.ms_bounds[i][3]+8:
					self.ms_button_selected = i


	def backToGraph(self):
		self.generator.root.clearStructures()
		self.button_active[1] = True
		self.button_active[2] = False
		self.button_active[3] = False
		self.button_active[4] = False


	def leftClick(self, mousePos):
		global popup, popupTimer, popupsurface

		# otherKeys=pygame.key.get_pressed()
		mouseX, mouseY = mousePos
		clickedMap = False

		if self.map_selection:
			clickedMap = True
			if self.ms_button_selected != -1:
				self.loadMap(self.ms_button_selected)
			else:
				self.map_selection = not self.map_selection

		if self.button_selected != -1:
			if self.button_selected == 0:
				if self.drawnMap:
					self.backToGraph()
					self.drawnMap = None
				else:
					if self.ms_names:
						self.map_selection = not self.map_selection
					else:
						popup, popupTimer = True, 50
						popupsurface = FONT3.render("ERROR - directory named 'maps' not found!", True, (0, 0, 0))
						print ("ERROR - directory named 'maps' not found!")

			elif self.button_selected == 1:
				self.map_selection = False
				self.button_active[1] = False
				self.button_active[2] = True
				self.drawnMap = self.generateCurrentMap()

			elif self.button_selected == 2:
				self.map_selection = False
				self.button_active[1] = False
				self.button_active[2] = False
				self.drawnMap = self.addDetailsToCurrentMap(self.drawnMap)

			elif self.button_selected == 3:
				self.save_level_tilemap()
				self.button_active[3] = False

			elif self.button_selected == 4:
				self.save_level_image()
				self.button_active[4] = False

		if not clickedMap and not self.drawnMap and mouseX < self.screenW-120 and self.tree != None: #node graph #update this section
			self.tree.selectedNode = None
			self.currentPaths = []

			for drawnNode in reversed(self.tree.drawnNodes):
				xOffset, yOffset = self.xOffset, self.yOffset

				if drawnNode.y+yOffset-(drawnNode.h+8)/2 <= mouseY and drawnNode.y+yOffset+(drawnNode.h+8)/2 >= mouseY and drawnNode.x+xOffset-(drawnNode.w+24)/2 <= mouseX and drawnNode.x+xOffset+(drawnNode.w+24)/2 >= mouseX:
					self.tree.selectedNode = drawnNode
					self.getCurrentPaths()
					break

		else:
			#change seed

			if not self.drawnMap or (not self.displayTiles and (self.tree.selectedNode == None or self.tree.selectedNode.label == "root")):
				seedLeftRect = pygame.Rect(self.seed_bounds[0], self.seed_bounds[1], 50, self.seed_bounds[3])
				seedRightRect = pygame.Rect(self.seed_bounds[0]+50, self.seed_bounds[1], 50, self.seed_bounds[3])

				if seedLeftRect.collidepoint(mousePos): #seed -1
					self.SEED -= 1
					updateSettings(settingsPath, self.setting_flags, self.setting_keys, self.autosaveSettings, 'seedSelected', str(self.SEED))

					if self.currentMapDirectory != "":
						self.setup(self.currentMapDirectory, self.SEED)
						self.generateDrawnTree()
						if self.drawnMap:
							self.drawnMap = self.generateCurrentMap()

				elif seedRightRect.collidepoint(mousePos): #seed +1
					self.SEED += 1
					updateSettings(settingsPath, self.setting_flags, self.setting_keys, self.autosaveSettings, 'seedSelected', str(self.SEED))

					if self.currentMapDirectory != "":
						self.setup(self.currentMapDirectory, self.SEED)
						self.generateDrawnTree()
						if self.drawnMap:
							self.drawnMap = self.generateCurrentMap()

			#change tile size

			zoomLeftRect = pygame.Rect(self.zoom_bounds[0], self.zoom_bounds[1], 50, self.zoom_bounds[3])
			zoomRightRect = pygame.Rect(self.zoom_bounds[0]+50, self.zoom_bounds[1], 50, self.zoom_bounds[3])

			if zoomLeftRect.collidepoint(mousePos) and self.tileSizeSelected > 0: #tileSize +1
				self.tileSizeSelected -= 1
				self.tileSize = self.tileSizes[self.tileSizeSelected]
				updateSettings(settingsPath, self.setting_flags, self.setting_keys, self.autosaveSettings, 'tileSize', str(self.tileSize))

				if self.currentMapDirectory != "":
					if self.drawnMap:
						self.drawnMap.mapDrawn = False

			elif zoomRightRect.collidepoint(mousePos) and self.tileSizeSelected < len(self.tileSizes)-1: #tileSize -1
				self.tileSizeSelected += 1
				self.tileSize = self.tileSizes[self.tileSizeSelected]
				updateSettings(settingsPath, self.setting_flags, self.setting_keys, self.autosaveSettings, 'tileSize', str(self.tileSize))

				if self.currentMapDirectory != "":
					if self.drawnMap:
						self.drawnMap.mapDrawn = False

		#update screen

		if self.drawnMap:
			self.drawnMap.drawScreen(screen, surface, screenW, screenH, self.tileSize, FONT, tileset, self.displayTiles)
			self.drawUIOverMap()
		else:
			self.drawScreen()


	def drawUIOverMap(self):
		self.updateButtonHover(pygame.mouse.get_pos())
		self.drawUI()
		self.drawCurrentZoom()
		if not self.displayTiles and (self.tree.selectedNode == None or self.tree.selectedNode.label == "root"):
			self.drawCurrentSeed()
		pygame.display.update()


	def generateCurrentMap(self):
		global popup, popupTimer, popupsurface
		if not self.tree or not self.generator.root:
			return None

		#if structure isn't a leaf node, place loading overlay
		if self.tree.selectedNode == None or not self.tree.selectedNode.node.category in self.generator.structureDc.keys():
			self.screen.blit(self.overlay, (0,0))
			pygame.display.update()

		start_time = time.time()

		try:
			if self.tree.selectedNode == None or self.tree.selectedNode.label == "root":
				self.generator.generateMapFromCurrentGraph(self.SEED)
			else:
				rootCopy = deepcopy(self.generator.root)
				rootCopy.childNodes = [ self.tree.selectedNode.node ]
				self.generator.generateMapFromCurrentGraph(self.SEED, rootCopy)

		except Exception as errorMessage:
			self.button_active[1] = True
			self.button_active[2] = False

			popup, popupTimer = True, 50
			popupsurface = FONT3.render("Error - " + str(errorMessage), True, (0, 0, 0))
			print ("Error - " + str(errorMessage))
			return None

		print ("\nGenerated in %.3f seconds" % ((time.time() - start_time)))

		self.displayTiles = False

		#draw update is done in click step

		drawnMap = DrawnMap(self.generator.generatedMap)
		return drawnMap


	def addDetailsToCurrentMap(self, drawnMap):
		if not self.tree or not self.generator.generatedMap or not drawnMap:
			return None

		#place loading overlay (hacky solution)
		self.screen.blit(self.overlay, (0,0))
		pygame.display.update()

		start_time = time.time()
		self.generator.addDetails()
		print ("\nAdded details in %.3f seconds" % ((time.time() - start_time)))

		self.displayTiles = True
		drawnMap.setStructure(self.generator.generatedMap)
		drawnMap.clearMap()

		start_time = time.time()
		drawnMap.drawScreen(screen, surface, screenW, screenH, self.tileSize, FONT, tileset, self.displayTiles)
		print ("\nDrawn map in %.3f seconds" % ((time.time() - start_time)))

		self.button_active[3] = True
		self.button_active[4] = True

		return drawnMap


	def drawScreen(self):
		bg_color = (192, 192, 192)
		self.screen.fill(bg_color)

		link_color = (172, 172, 172)
		path_color = (220, 220, 220)

		if self.tree != None:
			for drawnNode in self.tree.drawnNodes:
				drawnNode.drawLinks(self.screen, self.nodeRadius, self.xOffset, self.yOffset, self.tree, link_color)
			# for drawnNode in self.tree.drawnNodes:
				# drawnNode.drawPaths(self.screen, self.nodeRadius, self.xOffset, self.yOffset, self.tree, path_color)

			for drawnNode in self.tree.drawnNodes:
				drawnNode.draw(self.screen, self.nodeRadius, self.xOffset, self.yOffset, self.tree)

		#interface

		interface.drawUI()
		interface.drawCurrentZoom()
		interface.drawCurrentSeed()

		pygame.display.update()


	def save_level_tilemap(self):
		global popup, popupTimer, popupsurface
		file_name = "export_txt_%s.txt" % time.strftime('%Y-%m-%d_%H%M%S', time.gmtime(time.time()))

		# tilemap_text = self.generator.generatedMap.getTilemapText(simplify=False)
		tilemap_text = self.generator.generatedMap.getTilemapText(simplify=True)

		with open(file_name, 'w') as file:
			file.write(tilemap_text)

		print ("\nSaved tile map to file: %s" % file_name)
		popup, popupTimer = True, 30
		popupsurface = FONT3.render("Saved tile map to file: %s" % file_name, True, (0, 0, 0))


	def save_level_image(self):
		global popup, popupTimer, popupsurface
		if self.drawnMap == None or self.drawnMap.displayedStructure == None:
			return

		file_name = "export_png_%s.png" % time.strftime('%Y-%m-%d_%H%M%S', time.gmtime(time.time()))

		imageSurface = pygame.Surface((self.drawnMap.displayedStructure.w * self.tileSize, self.drawnMap.displayedStructure.h * self.tileSize))
		imageSurface.blit(self.drawnMap.mapSurface, (0, 0), (0, 0, imageSurface.get_width(), imageSurface.get_height()))
		pygame.image.save(imageSurface, file_name)

		print ("\nSaved map image to file: %s" % file_name)
		popup, popupTimer = True, 30
		popupsurface = FONT3.render("Saved map image to file: %s" % file_name, True, (0, 0, 0))


#LAUNCH

pygame.font.init()

FONT = pygame.font.SysFont('verdana', 11)
FONT2 = pygame.font.SysFont('verdana', 13)
FONT3 = pygame.font.SysFont('verdana', 16)
FONT4 = pygame.font.SysFont('verdana', 7)


screenW, screenH = 1280, 720
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (300, 150)

pygame.init()
clock = pygame.time.Clock()

screen = pygame.display.set_mode((screenW,screenH), pygame.RESIZABLE)
surface = pygame.Surface((110*32, 72*32))


pygame.display.set_caption("Node-Oriented Procedural Engine")

if os.path.isfile(iconPath):
	pygame.display.set_icon(pygame.image.load(iconPath))

tileset = []
if os.path.isfile(tilesetPath):
	tileset = load_tile_table(tilesetPath, 16, 16)

interface = Interface(screen, surface, screenW, screenH, nodeRadius, xOffset, yOffset)
interface.drawScreen()

popup = False
popupTimer = 0


#MAIN LOOP

running = True
while running:
	clock.tick(30)

	if interface.drawnMap:
		heldKeys=pygame.key.get_pressed()

		#do not re-draw the map unless position changes
		if heldKeys[pygame.K_s] or heldKeys[pygame.K_DOWN]:
			interface.drawnMap.yOffset -= 24
			interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles, updateDisplay=False)
		elif heldKeys[pygame.K_w] or heldKeys[pygame.K_UP]:
			interface.drawnMap.yOffset += 24
			interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles, updateDisplay=False)
		if heldKeys[pygame.K_d] or heldKeys[pygame.K_RIGHT]:
			interface.drawnMap.xOffset -= 24
			interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles, updateDisplay=False)
		elif heldKeys[pygame.K_a] or heldKeys[pygame.K_LEFT]:
			interface.drawnMap.xOffset += 24
			interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles, updateDisplay=False)

		interface.drawUIOverMap() #display update call happens here

	else:
		interface.updateButtonHover(pygame.mouse.get_pos())
		interface.drawScreen()

	for event in pygame.event.get():
		if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE and interface.map_selection:
			interface.map_selection = False

			if interface.drawnMap:
				interface.button_active[1] = False
				interface.button_active[2] = True
				interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles, updateDisplay=False)
				interface.drawUIOverMap() #display update call happens here
			else:
				interface.drawScreen()

		elif event.type==pygame.QUIT or (event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE and not interface.drawnMap):
			sys.exit()

		elif event.type == pygame.VIDEORESIZE:
			screenW, screenH = pygame.display.get_surface().get_size()

			if interface:
				interface.screenW = screenW
				interface.screenH = screenH

				interface.overlay = pygame.Surface((screenW,screenH))
				interface.overlay.set_alpha(interface.overlay_alpha)

				interface.setupUI()
				interface.setupCurrentZoom()
				interface.setupCurrentSeed()
				interface.setupMapSelection()

				if interface.drawnMap:
					interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles)
					interface.drawUIOverMap()
				else:
					interface.drawScreen()

		elif event.type==pygame.KEYDOWN:
			if interface.drawnMap:
				if event.key==pygame.K_ESCAPE:
					interface.drawnMap = None
					interface.backToGraph()
					interface.drawScreen()

			else:
				heldKeys=pygame.key.get_pressed()

				if not heldKeys[pygame.K_LCTRL]:
					if event.key==pygame.K_s or event.key==pygame.K_DOWN:
						interface.yOffset -= 100
						interface.drawScreen()
					if event.key==pygame.K_w or event.key==pygame.K_UP:
						interface.yOffset += 100
						interface.drawScreen()
					if event.key==pygame.K_a or event.key==pygame.K_LEFT:
						interface.xOffset += 100
						interface.drawScreen()
					if event.key==pygame.K_d or event.key==pygame.K_RIGHT:
						interface.xOffset -= 100
						interface.drawScreen()

		elif event.type == pygame.MOUSEBUTTONDOWN and not interface.drawnMap:
			if event.button == 1:
				interface.leftClick(pygame.mouse.get_pos())

			if event.button == 4 and not interface.drawnMap:
				interface.yOffset += 100
				interface.drawScreen()

			if event.button == 5 and not interface.drawnMap:
				interface.yOffset -= 100
				interface.drawScreen()

		elif event.type == pygame.MOUSEBUTTONDOWN and interface.drawnMap:
			if event.button == 1:
				interface.leftClick(pygame.mouse.get_pos())

	if popup:
		pygame.draw.rect(screen, (255,235,0), (10, 10, screenW-150, 60), 0)
		rect = popupsurface.get_rect(center=((10+screenW-150)/2, 30))
		screen.blit(popupsurface, (rect[0], 30))

		popupTimer -= 1
		if popupTimer <= 0:
			popupTimer = 0
			popup = False

			if interface.drawnMap:
				interface.drawnMap.drawScreen(screen, surface, screenW, screenH, interface.tileSize, FONT, tileset, interface.displayTiles, updateDisplay=False)
				interface.drawUIOverMap() #display update call happens here
			else:
				interface.drawScreen()

	pygame.display.update()