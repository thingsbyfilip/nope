from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
import sys, os, re


def getCategoryName(nodeName):
	in_brackets = re.findall(r'\(.*\)', nodeName)
	if in_brackets:
		return in_brackets[0][1:-1]
	return ""


class Node:
	def __init__(self, label, category):
		self.label = label
		self.category = category
		self.childNodes = []
		self.childPaths = []
		self.properties = set()
		self.structure = None

	def printStructure(self, depth):
		print ( "  " * depth + "%s (%i), properties: %s" % (self.label, self.structure != None, str(self.properties)) )
		for node in self.childNodes:
			node.printStructure(depth+1)

	def structureToString(self, depth, colorDc):
		text = ""

		if depth > 0:
			text += "\t" * (depth-1) + "%s (%s)" % (self.label, self.category)
			if self.properties:
				text += ", " + ", ".join(sorted(self.properties))
			text += "\n"

		for node in self.childNodes:
			text += node.structureToString(depth+1, colorDc)

		for pathSource, pathTarget, pathColor, pathMaterialSpecified in self.childPaths:
			text += "\t" * (depth) + "@"
			sourceLine = pathSource[0] + "." + pathSource[1]

			if pathTarget[0] == None:
				targetLine = pathSource[1]
			else:
				targetLine = pathTarget[0] + "." + pathTarget[1]

			roadColor = ""
			if pathMaterialSpecified:
				for colorKey, colorValue in colorDc.items():
					if pathColor == colorValue:
						roadColor = " (%s)" % colorKey
						break

			text += sourceLine + " -> " + targetLine + roadColor + "\n"

		return text

	def collectStructures(self, L):
		L.append(self)
		for node in self.childNodes:
			node.collectStructures(L)

	def assignBasicStructures(self, structureDc):
		if self.label in structureDc.keys():
			self.structure = structureDc[self.label]
		else:
			for childNode in self.childNodes:
				childNode.assignBasicStructures(structureDc)

	def clearStructures(self):
		self.structure = None
		for childNode in self.childNodes:
			childNode.clearStructures()

	def searchViable(self, L):
		if self.structure == None:
			canBeGenerated = True
			for childNode in self.childNodes:
				if childNode.structure == None:
					canBeGenerated = False
					break

			if canBeGenerated:
				L.append(self)
			else:
				for childNode in self.childNodes:
					childNode.searchViable(L)

	def clearViable(self):
		self.structure = None
		for childNode in self.childNodes:
			childNode.clearViable()


class StructurePrototype:
	def __init__(self, category, w, h, margin, color):
		self.category = category
		self.w, self.h = w, h
		self.margin = margin
		self.color = color


def reverseColorDcDirection(colorDc):
	reverseColorDc = {}
	for key, value in colorDc.items():
		reverseColorDc[value] = key
	return reverseColorDc, set(reverseColorDc.keys())


def colorsToString(colorDc, colorKeys):
	text = ""
	for colorKey in sorted(colorKeys):
		text += "%s\t%i,%i,%i\n" % (colorKey, colorDc[colorKey][0], colorDc[colorKey][1], colorDc[colorKey][2])
	return text + "\n"


def structuresToString(prototypeDc, reverseColorDc, reverseColorKeys):
	text = ""
	for prototypeKey in sorted(prototypeDc.keys()):
		if prototypeDc[prototypeKey].color in reverseColorKeys:
			colorLabel = reverseColorDc[prototypeDc[prototypeKey].color]
		else:
			colorLabel = "green"
		text += "%s\t%i/%i/%i, %s\n" % (prototypeKey, prototypeDc[prototypeKey].w, prototypeDc[prototypeKey].h, prototypeDc[prototypeKey].margin, colorLabel)
	return text + "\n"


def getColorData():
	colorDc = {}

	colorDc['bg'] = (144, 128, 128)
	colorDc['road'] = (255, 255, 255)

	colorDc['building'] = (80, 80, 80)
	colorDc['wall'] = (96, 96, 96)
	colorDc['plaza'] = (180, 180, 180)

	colorDc['rock'] = (64, 64, 64)
	colorDc['mountain'] = (72, 72, 72)
	colorDc['destructible'] = (31, 15, 15)
	colorDc['dirt'] = (32, 16, 16)

	colorDc['grass'] = (128, 180, 96)
	colorDc['forest'] = (32, 128, 96)
	colorDc['lightgrass'] = (180, 224, 128)

	colorDc['water'] = (64, 128, 160)
	colorDc['water2'] = (65, 128, 160)

	colorDc['chest'] = (32, 64, 160)
	colorDc['chest_bombs'] = (32, 64, 161)
	colorDc['chest_canoe'] = (32, 64, 162)
	colorDc['chest_key'] = (32, 64, 163)
	colorDc['chest_money'] = (32, 64, 164)
	colorDc['chest_heart'] = (32, 64, 165)

	colorDc['pc'] = (33, 64, 161)
	colorDc['npc'] = (33, 64, 163)
	colorDc['npc2'] = (33, 64, 164)
	colorDc['npc3'] = (33, 64, 165)
	colorDc['enemy'] = (34, 64, 160)
	colorDc['boss'] = (33, 64, 162)

	colorKeys = set(colorDc.keys())
	return colorDc, colorKeys


def getStructureDataFromTextFiles(textFiles, colorDc, colorKeys):
	structurePrototypeDc = {}

	for textFile in textFiles:
		fullText = open(textFile, 'r').read()
		colorText, structureText, graphText = getFileSections(fullText)

		for line in structureText.split("\n"):
			lineRaw = line.strip()
			tabSplit = re.split('\t+', lineRaw)
			if len(tabSplit) == 2 and lineRaw[0] != "":
				label, propertyText = tabSplit

				w, h, m = 0, 0, 0
				color = (128, 128, 128)

				propertyLines = propertyText.split(",")
				for propertyLine in propertyLines:
					propertyLineRaw = propertyLine.strip()

					if re.match(r'[0-9]+\/[0-9]+\/[0-9]+', propertyLineRaw):
						w, h, m = (int(number) for number in propertyLineRaw.split("/"))
					elif propertyLineRaw in colorKeys:
						color = colorDc[propertyLineRaw]

				structurePrototype = StructurePrototype(label, w, h, m, color)
				structurePrototypeDc[label] = structurePrototype

	return structurePrototypeDc


def getFileSections(fullText):
	sections = {"colors": "", "structures": "", "tree": ""}

	currentSection = "tree"
	for line in fullText.split("\n"):
		if re.match(r'\=\=\= ?TREE ?\=\=\=.*', line):
			currentSection = "tree"
		elif re.match(r'\=\=\= ?COLOU?RS ?\=\=\=.*', line):
			currentSection = "colors"
		elif re.match(r'\=\=\= ?STRUCTURES ?\=\=\=.*', line):
			currentSection = "structures"
		else:
			sections[currentSection] += line + "\n"

	return sections["colors"].strip(), sections["structures"].strip(), sections["tree"].strip()


def buildTreeDataFromText(treeText, root, colorDc, colorKeys, prototypeDc):
	nodeAtDepth = {}
	nodeAtDepth[0] = root

	#nodeAtDepth is a temporary variable keeping track of last node at given level of indentation
	#(it's used to trace child nodes back to parent nodes)

	rockMaterials = set([(64, 64, 64), (72, 72, 72), (31, 15, 15), (32, 16, 16)])

	for line in treeText.split("\n"):
		if line != "" and line != "=== TREE ===" and line.strip()[0] != "#":
			lineDepth = 1 + len(re.findall(r'\t', line))
			lineRaw = line.strip()

			if lineRaw[0] != '@': #is structure
				lineSplit = re.split(r'\, *', lineRaw)
				nodeName, properties = lineSplit[0], lineSplit[1:]
				category = getCategoryName(nodeName)
				label = nodeName.split("(", 1)[0][:-1]

				# print (label, category, properties)

				currentNode = Node(label, category)
				for property in properties:
					currentNode.properties.add(property)

				nodeAtDepth[lineDepth] = currentNode
				nodeAtDepth[lineDepth-1].childNodes.append(currentNode)

			else: #is path
				contentLine = lineRaw[1:]
				materialName = getCategoryName(contentLine)

				if materialName != "":
					specifiedMaterial = True
					contentLine = contentLine.split("(", 1)[0][:-1]
					if materialName in colorDc.keys():
						material = colorDc[materialName]
					else:
						if lineDepth > 1 and nodeAtDepth[lineDepth-1].category in prototypeDc.keys() and prototypeDc[nodeAtDepth[lineDepth-1].category].color in rockMaterials: #parent is rock/dirt
							material = (32,16,16)
						else:
							material = (255,255,255)
				else:
					specifiedMaterial = False
					if lineDepth > 1 and nodeAtDepth[lineDepth-1].category in prototypeDc.keys() and prototypeDc[nodeAtDepth[lineDepth-1].category].color in rockMaterials: #parent is rock/dirt
						material = (32,16,16)
					else:
						material = (255,255,255)

				sourceText, targetText = re.split(r' *\-\> *', contentLine)
				sourceSplit = re.split(r'\. *', sourceText)
				targetSplit = re.split(r'\. *', targetText)

				if len(sourceSplit) == 2:
					source = (sourceSplit[0], sourceSplit[1])
				else:
					print ("path source has wrong formatting: %s" % lineRaw)

				if len(targetSplit) == 2:
					target = (targetSplit[0], targetSplit[1])
				elif len(targetSplit) == 1:
					target = (None, targetSplit[0])
				else:
					print ("path target has wrong formatting: %s" % lineRaw)

				currentPath = (source, target, material, specifiedMaterial)
				nodeAtDepth[lineDepth-1].childPaths.append(currentPath)


def buildTreeData(fullText, root, colorDc, colorKeys, prototypeDc):
	#get section containing tree data

	matchedTreeSections = re.findall(r'\=\=\= TREE \=\=\=.*', fullText, re.DOTALL)
	if matchedTreeSections:
		treeText = matchedTreeSections[0]
	else:
		treeText = ""

	#build tree data from that section

	buildTreeDataFromText(treeText, root, colorDc, colorKeys, prototypeDc)