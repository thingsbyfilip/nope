from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
import re
from collections import defaultdict

#IMPORTANT:
#needs to swap directions for connecting path parents!

#CONCEPT:
#outgoing paths are optional by default
#if there is a connecting path, freeze all child outgoing paths
#if no parent connecting path freezes an outgoing path, remove it

#PATH HIERARCHY:
#every path (connecting or outgoing) has subordinate paths (outgoing only)


def ignoreMaterial(path):
	return re.sub(r" *\(.+", "", path)


def getPredefinedAndInvisiblePaths(source, prototypeDc, reverseColorDc):
	predefinedPaths = set() #paths with specified material (e.g. x -> y (material) as opposed to just x -> y)
	invisiblePaths = set() #paths with material same as parent structure (e.g. grass paths in a grass container)
	lines = source.split("\n")

	for i, line in enumerate(lines):
		if str(line.strip()[:1]) == "@": #ignore paths
			continue
		if str(line.strip()) == "": #ignore empty
			continue

		lineIndentation = line.count("\t")
		lineLabel = line.strip().split("(")[0].strip()
		lineCategory = re.sub(r"\).*", "", line.strip().split("(")[1].strip())

		lineStructureMaterial = "???"
		if lineCategory in prototypeDc.keys() and prototypeDc[lineCategory].color in reverseColorDc.keys():
			lineStructureMaterial = reverseColorDc[prototypeDc[lineCategory].color]

		for j, otherLine in enumerate(lines[i+1:]):
			otherLineIndentation = otherLine.count("\t")

			if otherLine.strip() == "":
				continue
			if otherLineIndentation <= lineIndentation: #end of line's level in hierarchy (including the same level - means it's a sibling)
				break

			if otherLineIndentation == lineIndentation + 1 and str(otherLine.strip()[:1]) == "@":
				material = ""
				otherLine = otherLine.strip()[1:]
				if "(" in otherLine and ")" in otherLine:
					otherLine, material = otherLine[:-1].split(" (")
				pathSource, pathTarget = otherLine.strip().split(" -> ")

				childPathId = i+j+1
				if material != "":
					predefinedPaths.add(childPathId)
				if material == lineStructureMaterial:
					invisiblePaths.add(childPathId)

	return predefinedPaths, invisiblePaths


def getPathHierarchy(source):
	pathHierarchy = set()
	lines = source.split("\n")

	for i, line in enumerate(lines):
		if str(line.strip()[:1]) == "@": #ignore paths
			continue
		if str(line.strip()) == "": #ignore empty
			continue

		lineIndentation = line.count("\t")
		lineLabel = line.strip().split("(")[0].strip()

		#1. establish paths which connect the current (parent) structure with another one and their directions

		siblingPaths = []

		for j, otherLine in enumerate(lines[i:]):
			otherLineIndentation = otherLine.count("\t")

			if otherLine.strip() == "":
				continue
			if otherLineIndentation < lineIndentation: #end of line's level in hierarchy
				break

			elif otherLineIndentation == lineIndentation and str(otherLine.strip()[:1]) == "@": #note: still allows for wrong formatting and causes errors
				material = ""
				otherLine = otherLine.strip()[1:]
				if "(" in otherLine and ")" in otherLine:
					otherLine, material = otherLine[:-1].split(" (")
				pathSource, pathTarget = otherLine.strip().split(" -> ")

				if pathTarget in ("s","n","e","w"):
					sourceLabel, sourceDir = pathSource.split(".", 1)
					targetLabel, targetDir = "", pathTarget.strip()
				else:
					sourceLabel, sourceDir = pathSource.split(".", 1)
					targetLabel, targetDir = pathTarget.split(".", 1)

				if lineLabel == sourceLabel:
					siblingPaths.append(i+j)

				elif lineLabel == targetLabel:
					siblingPaths.append(i+j)


		#2. establish child paths, and consider them subordinates of sibling paths

		childPaths = []

		for j, otherLine in enumerate(lines[i+1:]):
			otherLineIndentation = otherLine.count("\t")

			if otherLine.strip() == "":
				continue
			if otherLineIndentation <= lineIndentation: #end of line's level in hierarchy (including the same level - means it's a sibling)
				break

			if otherLineIndentation == lineIndentation + 1 and str(otherLine.strip()[:1]) == "@":
				material = ""
				otherLine = otherLine.strip()[1:]
				if "(" in otherLine and ")" in otherLine:
					otherLine, material = otherLine[:-1].split(" (")
				pathSource, pathTarget = otherLine.strip().split(" -> ")

				if pathTarget in ("s","n","e","w"):
					childPathId = i+j+1
					childPaths.append(childPathId)


		#compare and establish hierarchy

		for siblingPathId in siblingPaths:
			siblingPath = lines[siblingPathId].strip()
			siblingPath = ignoreMaterial(siblingPath)

			source, target = siblingPath[1:].split(" -> ")

			for childPathId in childPaths:
				childPath = lines[childPathId].strip()
				childPath = ignoreMaterial (childPath)
				outgoingDirection = childPath.strip()[-1]

				comparedKey = "%s.%s" % (lineLabel, outgoingDirection)

				if comparedKey == source or comparedKey == target:
					pathHierarchy.add((siblingPathId, childPathId))

	return pathHierarchy


def pathAcceptable(lines, lineId, pathHierarchy, invisiblePaths):
	pathLine = lines[lineId]
	isOutgoing = str(pathLine.strip()[-2:]) in (" s", " n", " e", " w")

	if not isOutgoing:
		return True #keep connecting paths

	pathParents = set()
	for parentId, childId in sorted(pathHierarchy):
		if childId == lineId:
			pathParents.add(parentId)

	for parentId in sorted(pathParents):
		parentAcceptable = pathAcceptable(lines, parentId, pathHierarchy, invisiblePaths)
		parentInvisible = parentId in invisiblePaths #if parent connecting path is invisible, it doesn't count as a valid connection
		if parentAcceptable and not parentInvisible:
			return True

	return False


def filterPaths(source, prototypeDc, reverseColorDc):
	predefinedPaths, invisiblePaths = getPredefinedAndInvisiblePaths(source, prototypeDc, reverseColorDc)
	pathHierarchy = getPathHierarchy(source)

	#go line by line, based on hierarchy and check if a given path can be kept or removed:
	#	if path has predefined material, keep it (prevents deleting paths)
	#	if path is connecting 2 sibling structures, keep it
	#	if path is outgoing:
	#		trace its origins to the highest outgoing path or highest parent in hierarchy (paths can have multiple parents!)
	#		if path has at least one connecting ancestor, keep it (invisible connectors don't count)
	#		if any of its highest parents are outgoing and at indent level <=3, also keep it
	#		otherwise, remove it

	lines = source.split("\n")
	linesToKeep = []

	for lineId, line in enumerate(lines):
		if str(line.strip()[:1]) != "@": #ignore non-paths
			linesToKeep.append(line)

		else:
			if lineId in predefinedPaths or pathAcceptable(lines, lineId, pathHierarchy, invisiblePaths):
				linesToKeep.append(line)

	return "\n".join(linesToKeep)


if __name__ == '__main__':
	textFile = 'roadfiltertest.txt'
	outputFile = 'roadfiltertest_output.txt'

	fileText = open(textFile, 'r').read()
	newText = filterPaths(fileText, {}, {})

	with open(outputFile, 'w') as file:
		file.write(newText)