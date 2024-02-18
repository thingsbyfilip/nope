from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
from random import seed, randrange, randint
from calc import *

# coordinates rounded in separation
# random distances for unconnected structures in separation!

#alter placement when a structure is in the center!

def getDistance(x1, y1, x2, y2):
	return sqrt( (x2 - x1)**2 + (y2 - y1)**2 )

def normalizeVector(x, y):
	magnitude = getDistance(0, 0, x, y)
	return (x / magnitude, y / magnitude)


class RegionStructure:
	def __init__(self, w, h, margin, label, central, connections):
		self.w, self.h = w, h
		self.margin = margin
		self.label = label
		self.central = central
		self.connections = connections

		self.exitOffsets = {}
		self.exitOffsets['n'] = (0, -self.h/2)
		self.exitOffsets['s'] = (0, self.h/2)
		self.exitOffsets['w'] = (-self.w/2, 0)
		self.exitOffsets['e'] = (self.w/2, 0)


class RegionPlacement:
	def __init__(self, structure, x, y):
		self.structure = structure
		self.x, self.y = x, y
		self.w, self.h = structure.w, structure.h
		self.margin = structure.margin
		self.label = self.structure.label
		self.central = self.structure.central
		self.connections = self.structure.connections

		self.exits = {}
		self.exits['n'] = (self.x, self.y-self.h/2)
		self.exits['s'] = (self.x, self.y+self.h/2)
		self.exits['w'] = (self.x-self.w/2, self.y)
		self.exits['e'] = (self.x+self.w/2, self.y)

		self.generatedConnections = []


	def move(self, newX, newY):
		self.x = newX
		self.y = newY

		self.exits = {}
		self.exits['n'] = (self.x, self.y-self.h/2)
		self.exits['s'] = (self.x, self.y+self.h/2)
		self.exits['w'] = (self.x-self.w/2, self.y)
		self.exits['e'] = (self.x+self.w/2, self.y)


	def collides(self, otherRegionPlacement, margin):
		a_x1, a_x2, a_y1, a_y2 = self.x-float(self.w)/2, self.x+float(self.w)/2, self.y-float(self.h)/2, self.y+float(self.h)/2
		b_x1, b_x2, b_y1, b_y2 = otherRegionPlacement.x-float(otherRegionPlacement.w)/2, otherRegionPlacement.x+float(otherRegionPlacement.w)/2, otherRegionPlacement.y-float(otherRegionPlacement.h)/2, otherRegionPlacement.y+float(otherRegionPlacement.h)/2

		if round(a_x2) <= round(b_x1)-margin or round(a_x1) >= round(b_x2)+margin or round(a_y2) <= round(b_y1)-margin or round(a_y1) >= round(b_y2)+margin:
			return False

		return True


#during placements, connected segments should be closer to one another than to non-connected ones for separation to work properly

def place(placements, numberOfStructures, maxRandomDistanceFromCenter, structure, suggestedAngle):
	# if len(placements) == 0:
		# placements.append( RegionPlacement(structure, 0, 0) )
		# return

	placementLabels = [placement.label for placement in placements]
	structureConnections = [connection for connection in structure.connections if connection[0] in placementLabels]

	placementConnections = []
	for targetStructure, sourceDirection, targetDirection in structureConnections:
		target = None
		for placement in placements:
			if placement.label == targetStructure:
				target = placement
				break
		if target != None:
			placementConnections.append( (target, sourceDirection, targetDirection) )

	if structure.central:
		newPlacement = RegionPlacement(structure, 0, 0)
		newPlacement.generatedConnections = placementConnections
		placements.append(newPlacement)
		return

	if structure.label == '_NORTH_':
		placementsY = [placement.exits['n'][1] for placement in placements]
		newPlacement = RegionPlacement(structure, 0, min(placementsY) - 10)
		newPlacement.generatedConnections = placementConnections
		placements.append(newPlacement)
		return

	if structure.label == '_SOUTH_':
		placementsY = [placement.exits['s'][1] for placement in placements]
		newPlacement = RegionPlacement(structure, 0, max(placementsY) + 10)
		newPlacement.generatedConnections = placementConnections
		placements.append(newPlacement)
		return

	if structure.label == '_WEST_':
		placementsX = [placement.exits['w'][0] for placement in placements]
		newPlacement = RegionPlacement(structure, min(placementsX) - 10, 0)
		newPlacement.generatedConnections = placementConnections
		placements.append(newPlacement)
		return

	if structure.label == '_EAST_':
		placementsX = [placement.exits['e'][0] for placement in placements]
		newPlacement = RegionPlacement(structure, max(placementsX) + 10, 0)
		newPlacement.generatedConnections = placementConnections
		placements.append(newPlacement)
		return

	suggestedPlacements = []
	for target, sourceDirection, targetDirection in placementConnections:
		targetOffset = target.exits[targetDirection]
		sourceOffset = structure.exitOffsets[sourceDirection]
		placementX = targetOffset[0] - sourceOffset[0]
		placementY = targetOffset[1] - sourceOffset[1]

		suggestedPlacements.append((placementX, placementY))

	if len(suggestedPlacements) == 0 and not structure.central:
		# distance = maxRandomDistanceFromCenter
		distance = randint(1, maxRandomDistanceFromCenter)

		# angle = 360 * (float(len(placements)+1) / numberOfStructures)
		angle = suggestedAngle

		x, y = getPositionAtAngle(0, 0, distance, angle)

		placements.append( RegionPlacement(structure, x, y) )
		return

	averageX = sum([placement[0] for placement in suggestedPlacements]) / len(suggestedPlacements)
	averageY = sum([placement[1] for placement in suggestedPlacements]) / len(suggestedPlacements)

	newPlacement = RegionPlacement(structure, averageX, averageY)
	newPlacement.generatedConnections = placementConnections
	placements.append( newPlacement )


def adjustPlacements(placements):
	for i in range(100):
		for placement in placements:
			if placement.central or placement.label in ('_NORTH_', '_SOUTH_', '_EAST_', '_WEST_'):
				continue

			placementConnections = []
			for targetStructure, sourceDirection, targetDirection in placement.structure.connections:
				target = None
				for otherPlacement in placements:
					if otherPlacement.label == targetStructure and placement != otherPlacement:
						target = otherPlacement
						break

				if target:
					placementConnections.append( (target, sourceDirection, targetDirection) )

			suggestedPlacements = []
			for target, sourceDirection, targetDirection in placementConnections:
				targetOffset = target.exits[targetDirection]
				sourceOffset = placement.structure.exitOffsets[sourceDirection]
				placementX = targetOffset[0] - sourceOffset[0]
				placementY = targetOffset[1] - sourceOffset[1]

				suggestedPlacements.append((placementX, placementY))

			newX = sum( [suggestedPlacement[0] for suggestedPlacement in suggestedPlacements] + [placement.x] ) / (1 + len(suggestedPlacements))
			newY = sum( [suggestedPlacement[1] for suggestedPlacement in suggestedPlacements] + [placement.y] ) / (1 + len(suggestedPlacements))

			if abs(newX-placement.x) > 1 or abs(newY-placement.y) > 1:
				placement.move(newX, newY)

	# print ("adjustment completed in %i iterations" % (i+1,))


def shrink(placements, padding, max_steps=1000):
	for i in range(max_steps):
		regionsLocked = True

		for placement in placements:
			moveX = 0
			moveY = 0
			pullCount = 0

			collisions = 0
			for otherRegionPlacement in placements:
				if placement.collides(otherRegionPlacement, padding+max(placement.margin, otherRegionPlacement.margin)):
					if otherRegionPlacement == placement:
						continue
					collisions += 1

			if collisions >= 3:
				placement.x = round(placement.x)
				placement.y = round(placement.y)
				continue

			for otherRegionPlacement in placements:
				if otherRegionPlacement == placement:
					continue

				if placement.collides(otherRegionPlacement, padding+max(placement.margin, otherRegionPlacement.margin)):
					continue

				moveX += (placement.x - otherRegionPlacement.x)
				moveY += (placement.y - otherRegionPlacement.y)

				pullCount += 1
				# break

			if pullCount > 0:
				moveX *= -1
				moveY *= -1

				while moveX == 0 and moveY == 0:
					moveX = randrange(-1,1)
					moveY = randrange(-1,1)

				moveX, moveY = normalizeVector(moveX, moveY)

				previousX, previousY = placement.x, placement.y

				placement.move(placement.x+moveX, placement.y+moveY)

				anyCollision = False
				for otherRegionPlacement in placements:
					if placement.collides(otherRegionPlacement, padding+max(placement.margin, otherRegionPlacement.margin)):
						if otherRegionPlacement == placement:
							continue
						anyCollision = True
						break

				if anyCollision:
					placement.move(placement.x-moveX, placement.y-moveY)
					placement.x = round(placement.x)
					placement.y = round(placement.y)

				if placement.x != previousX or placement.y != previousY:
					regionsLocked = False

		if regionsLocked:
			break

	# print ("shrinking completed in %i iterations" % (i+1,))


def separate(placements, max_steps=1000):
	for i in range(max_steps):
		regionsLocked = True #lock by default, unlock if something moves

		for placement in placements: #apply separation to each placement one by one
			moveX = 0
			moveY = 0
			separationCount = 0 #count separation moves (collisions), only proceed with separation if at least one is counted

			if placement.central:
				continue

			for otherRegionPlacement in placements:
				#ignore collisions with self
				if otherRegionPlacement == placement:
					continue

				#ignore if there is no collision and placement isn't exit
				if not placement.collides(otherRegionPlacement, max(placement.margin, otherRegionPlacement.margin)):
					placement.x = round(placement.x)
					placement.y = round(placement.y)
					continue

				#default situation for collision:
				#move X, Y by offsets between placements (requires randomized placement first)

				moveX += (otherRegionPlacement.x - placement.x)
				moveY += (otherRegionPlacement.y - placement.y)

				separationCount += 1 #count separation moves

			if separationCount > 0:
				regionsLocked = False #region can't be locked yet

				#apply movement

				moveX *= -1
				moveY *= -1

				while moveX == 0 and moveY == 0:
					moveX = randrange(-1,1)
					moveY = randrange(-1,1)

				moveX, moveY = normalizeVector(moveX, moveY)

				placement.move(placement.x+moveX, placement.y+moveY) #move placement (done in order)

		if regionsLocked: #if no placements happen, freeze result
			break

	# print ("separation completed in %i iterations" % (i+1,))


def getAngles(numberOfStructures):
	angles = []
	for i in range(numberOfStructures):
		angle = float(360 / numberOfStructures) * float(i)
		angles.append(angle)
	return angles


def getRegionAngleDc(regionStructures):
	angleDc = {}

	numberOfStructures = len([regionStructure for regionStructure in regionStructures if not regionStructure.central])
	angles = getAngles(numberOfStructures)

	currentAngleId = 0
	for i, regionStructure in enumerate(regionStructures):
		if not regionStructure.central:
			angleDc[i] = angles[currentAngleId]
			currentAngleId += 1
		else:
			angleDc[i] = 0

	return angleDc