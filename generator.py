from graph_read import *
from graph_compile import *
from graph_filter_paths import *
from generator_map import *

#GENERATOR CLASS = PIPELINE CALLING MAIN STEPS

#load rules -> create graphs -> start map generation
#actual graph-to-tilemap generation steps are included in generator_map (GeneratedMap class)


class Generator:
	def __init__(self, ruleFiles=[]):
		self.reset()

		#material (color) data never changes
		self.colorDc, self.colorKeys = getColorData() #material name to rgb
		self.reverseColorDc, self.reverseColorKeys = reverseColorDcDirection(self.colorDc) #rgb to material name

		#if rule files are included in the generator instance, load them
		if ruleFiles:
			self.loadRules(ruleFiles)


	def reset(self):
		self.prototypeDc, self.structureDc, self.templateDc, self.templatePool = {}, {}, {}, {}
		self.prototypeText, self.graphText, self.processedText = "", "", ""
		self.root = None #node tree
		self.currentMap = None #reference to GeneratedMap object
		self.generatedMap = None #reference to GeneratedMap's generatedStructure after generation


	def printCurrentGraph(self):
		print ("\n" + self.processedText + "\n")


	def printCurrentStructures(self):
		for key, value in sorted(self.structureDc.items()):
			print (" %s (%i, %i, %i)" % (key, value.w, value.h, value.margin))


	def loadRules(self, ruleFiles):
		self.reset()

		#make a table of node structure classes from files
		self.prototypeDc = getStructureDataFromTextFiles(ruleFiles, self.colorDc, self.colorKeys)
		self.prototypeText = structuresToString(self.prototypeDc, self.reverseColorDc, self.reverseColorKeys)

		#make a table of template rules (grammar) from files
		self.templateDc = getTemplatesFromTextFiles(ruleFiles, self.colorDc, self.colorKeys, {})

		#create an initial 'pool' of choices for each template
		#selected items may later be removed from the pool until the list is empty and reset
		#this (optional) mechanism prevents duplicates (e.g. 3 dungeon nodes = 3 different dungeons)
		self.templatePool = {}
		for key, values in self.templateDc.items():
			self.templatePool[key] = list(range(0, len(values)))


	def loadGraph(self, seed):
		if not self.templateDc:
			raise Exception("Generator rules are not loaded - run setup first!")
		if type(seed) != int:
			raise Exception("Generator seed must be an integer! (e.g. 100, 123, 574883...)")

		#select a graph, starting from root, representing one possible route to generate the map
		newRoot = createStructureFromTemplate("root", "root", True, self.templateDc, self.templatePool, seed, False, usePool=False)
		synthesizeStructure(newRoot, self.templateDc, self.templatePool, seed)

		#represent the graph as text again
		self.graphText = newRoot.structureToString(0, self.colorDc)

		#extend the table of node classes (prototypeDc) with template classes from templateDc
		expandPrototypeDcWithTemplates(self.prototypeDc, self.colorDc, self.colorKeys, self.templateDc)

		#create a table of pre-built leaf nodes (structureDc)
		self.structureDc = {}
		for label, prototype in self.prototypeDc.items():
			if prototype.w != 0 and prototype.h != 0:
				structure = Structure(prototype.category, prototype.w, prototype.h, prototype.margin, prototype.color)
				self.structureDc[label] = structure

		#remove outgoing paths which don't connect to anything outside
		self.graphText = filterPaths(self.graphText, self.prototypeDc, self.reverseColorDc)

		#combine all the data into text used to build final node graph
		self.processedText = "=== STRUCTURES ===\n\n%s\n\n=== TREE ===\n\n%s\n" % (self.prototypeText.strip(), self.graphText.strip())

		#build a node tree based on combined text
		self.root = Node("root", "root")
		buildTreeData(self.processedText, self.root, self.colorDc, self.colorKeys, self.prototypeDc)

		self.root.assignBasicStructures(self.structureDc)


	def generateMapFromCurrentGraph(self, seed, assignedRoot=None):
		#setup empty map referencing current graph and seed

		assignedRoot = self.root if assignedRoot is None else assignedRoot
		self.currentMap = GeneratedMap(assignedRoot, seed)

		invalidTerminalNodes = self.currentMap.getWrongTerminalNodes(self.structureDc)
		if invalidTerminalNodes:
			if invalidTerminalNodes[0] == "":
				raise Exception("Validation error - one of the nodes doesn't have a category")
			else:
				raise Exception("Validation error - '%s' can't appear as a final node" % invalidTerminalNodes[0])

		#generate structures

		self.currentMap.updateViable()
		self.currentMap.generateStructures(self.structureDc, self.prototypeDc)

		self.generatedMap = self.currentMap.generatedStructure #update reference


	def generateMap(self, seed):
		#combine main generation steps (if graph doesn't need to be drawn)

		self.loadGraph(seed)
		self.generateMapFromCurrentGraph(seed)

		self.generatedMap = self.currentMap.generatedStructure #update reference


	def addDetails(self):
		#postprocessing (results in wider set of tile values)

		self.currentMap.generatedStructure.tilesClear()
		self.currentMap.generatedStructure.tilesFill()
		self.currentMap.generatedStructure.tilesDelimit()
		self.currentMap.generatedStructure.clearLayermap()
		self.currentMap.tilePostprocessing()

		self.generatedMap = self.currentMap.generatedStructure #update reference