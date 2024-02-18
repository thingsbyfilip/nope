from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
from copy import copy, deepcopy
import sys, os, time, re, random
from collections import defaultdict
from graph_read import *

#TASKS:
#make sure reading graphs from files is more permissive (spaces between structures, comments, etc.)
#think of how to handle seeds (structure choice seed + structure seed)
#think of how to handle headers
#test out with various file formats


class StructurePrototype:
	def __init__(self, category, w, h, margin, color):
		self.category = category
		self.w, self.h = w, h
		self.margin = margin
		self.color = color


def getTemplates(treeText, colorDc, colorKeys, prototypeDc):
	templateDc = defaultdict(list)

	# treeText = re.sub(r"\=\=\=.*", "", treeText)
	treeText = re.sub(r"[ \t]+\#.*?\n", "\n", treeText)			#remove comments after line
	treeText = re.sub(r"\#.*", "", treeText)					#remove section header comments

	#ensure final structure gets counted
	# matchedDefinitions = re.findall(r'[^\t]\w.*?\n\n', treeText+"\n\n", re.DOTALL)
	matchedDefinitions = re.findall(r'\[\w.*?(?=\[)', treeText+"\n[", re.DOTALL) #must start with [ and reach until next [ or end of text, allows line breaks in between

	for i, definition in enumerate(matchedDefinitions):
		if not "\n" in definition.strip():
			continue #ignore [labels] without rules below

		header, structureText = definition.strip().split("\n", 1)
		headerName = header.strip()[1:-1]

		#structure nodes have 'root' as parent node, but it won't appear in text when structureToString() is called
		structureRoot = Node("root", "root")
		buildTreeDataFromText(structureText, structureRoot, colorDc, colorKeys, prototypeDc)

		structureCategory = structureRoot.childNodes[0].category

		templateDc[headerName].append(structureRoot)

	return templateDc


def removeTemplateTags(category):
	#return category without special symbols */% after name
	#(used for marking special pooling behaviour)
	if category != "":
		if category[-1] == "%":
			return category[:-1]
		elif category[-1] == "*":
			return category[:-1]
	return category


def selectTemplateNumber(category, templateDc, templatePool, usePool=False):
	#if category is followed by % or *, override default pooling setting
	if category != "":
		if category[-1] == "%":
			category = category[:-1]
			usePool = False
		elif category[-1] == "*":
			category = category[:-1]
			usePool = True

	if usePool: #drawing index from template pool to prevent repeating choices
		selection_number = random.choice(templatePool[category])

		templatePool[category].remove(selection_number)
		if len(templatePool[category]) == 0:
			templatePool[category] = list(range(0, len(templateDc[category])))

		return selection_number

	else: #select random template
		return random.randint(0, len(templateDc[category])-1)


def createStructureFromTemplate(category, label, isRoot, templateDc, templatePool, selectionSeed, alwaysPickLastOption, depth=0, categoryHistory=set(), usePool=False):
	category, categoryWithTags = removeTemplateTags(category), category #at this point, category key without special symbols becomes more important

	if alwaysPickLastOption:
		selection_number = len(templateDc[category])-1

		if len(templateDc[category]) > abs(selection_number):
			selection = templateDc[category][selection_number]
		else:
			raise IndexError(category)

	else:
		#select random based on seed
		random.seed(selectionSeed)

		selection_number = selectTemplateNumber(categoryWithTags, templateDc, templatePool, usePool=usePool)
		selection = templateDc[category][selection_number]
		selectionCategory = selection.childNodes[0].category

		#if the category of the expanded template's top node is ALSO a template, it needs to be immediately swapped for a random selection of that template!
		#make up to 10 substitutions, otherwise assume the labels are self-referential and an infinite loop may occur

		for i in range(0,10):
			if removeTemplateTags(selectionCategory) in templateDc.keys():
				category, categoryWithTags = removeTemplateTags(selectionCategory), selectionCategory

				random.seed(selectionSeed)
				selection_number = selectTemplateNumber(categoryWithTags, templateDc, templatePool, usePool=usePool)
				selection = templateDc[category][selection_number]
				selectionCategory = selection.childNodes[0].category

	if isRoot:
		return deepcopy(selection)
	else:
		if depth >= 5 and category in categoryHistory: #too much self-recursion - do not generate a structure
			return None

		else:
			structure = deepcopy(selection.childNodes[0])
			structure.category = category + "_%i" % (selection_number+1) #expanded structures have their definition label + number as category
			structure.label = label #keep same label as the one used in the parent node (required for paths to work)

		return structure


def synthesizeStructure(node, templateDc, templatePool, graphSeed, depth=0, categoryHistory=set(), usePool=False):
	nodeIndicesToRemove = []

	for i, childNode in enumerate(node.childNodes):
		if not childNode.childNodes and removeTemplateTags(childNode.category) in templateDc.keys(): #is leaf node or expandable node
			childProperties = childNode.properties #store any properties assigned by parent (e.g. central node)
			selectionSeed = "%s_%s_%i" % (node.label, node.category, graphSeed + i)

			newChildNode = createStructureFromTemplate(childNode.category, childNode.label, False, templateDc, templatePool, selectionSeed, False, depth=depth, categoryHistory=categoryHistory, usePool=usePool)

			if newChildNode: #generated expanded node using template
				node.childNodes[i] = newChildNode
				node.childNodes[i].properties = childProperties

			else: #too much self-recursion
				nodeIndicesToRemove.insert(0, i)

	if nodeIndicesToRemove:
		filterNodeChildren(node, nodeIndicesToRemove)

	for childNode in node.childNodes:
		recordCategory = re.sub(r"\_[0-9]+$", "", childNode.category)
		synthesizeStructure(childNode, templateDc, templatePool, graphSeed, depth=depth+1, categoryHistory=categoryHistory | set([recordCategory]), usePool=usePool)


def filterNodeChildren(node, nodeIndicesToRemove):
	for positionIndex in nodeIndicesToRemove:
		node.childNodes.pop(positionIndex)

	pathIndicesToRemove = []

	for i, childPath in enumerate(node.childPaths):
		sourceExists = False
		for childNode in node.childNodes:
			if childNode.label == childPath[0][0]:
				sourceExists = True
				break

		if childPath[1][0] == None:
			targetExists = True
		else:
			targetExists = False
			for childNode in node.childNodes:
				if childNode.label == childPath[1][0]:
					targetExists = True
					break

		if not sourceExists or not targetExists:
			pathIndicesToRemove.insert(0, i)

	for positionIndex in pathIndicesToRemove:
		node.childPaths.pop(positionIndex)


def getTemplatesFromTextFiles(textFiles, colorDc, colorKeys, prototypeDc):
	templateDc = defaultdict(list)

	for textFile in textFiles:
		fullText = open(textFile, 'r').read()
		colorText, structureText, graphText = getFileSections(fullText)
		fileTemplateToStructureDc = getTemplates(graphText, colorDc, colorKeys, prototypeDc)

		for key, nodes in fileTemplateToStructureDc.items():
			templateDc[key] += nodes

	return templateDc


def expandPrototypeDcWithTemplates(prototypeDc, colorDc, colorKeys, templateDc):
	for label, values in templateDc.items():
		for i, value in enumerate(values): #number possible structures
			mainNode = values[i].childNodes[0]

			if removeTemplateTags(mainNode.category) in prototypeDc.keys():
				reference = prototypeDc[mainNode.category]
				newPrototype = StructurePrototype(label + "_%i" % (i+1), reference.w, reference.h, reference.margin, reference.color) #label used as category
				prototypeDc[label + "_%i" % (i+1)] = newPrototype

			elif removeTemplateTags(mainNode.category) in templateDc.keys():
				#if the category of the expanded template's top node is ALSO a template:
				#add a 'featureless' prototype without reference to any particular template
				#the template-of-the-template will be randomly selected later at the createStructureFromTemplate step

				newPrototype = StructurePrototype(label + "_%i" % (i+1), 0, 0, 0, (0,0,0)) #label used as category
				prototypeDc[label + "_%i" % (i+1)] = newPrototype

			else:
				raise KeyError("%s#%s" % (label, mainNode.category))
