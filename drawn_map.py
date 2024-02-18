from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
import pygame
from tilemap_drawing import tag_tile, tile_dictionary, get_label_dc, get_tile_targets_dc, tweak_building_faces


def load_tile_table(filename, width, height):
	#pygame-dependent function for converting a tileset file into a table of tiles
	#largely adopted from http://sheep.art.pl/Tiled%20Map%20in%20PyGame

	image = pygame.image.load(filename).convert()
	image_width, image_height = image.get_size()

	tile_table = []

	for tile_x in range(0, int(image_width/width)):
		line = []
		tile_table.append(line)
		for tile_y in range(0, int(image_height/height)):
			rect = (tile_x*width, tile_y*height, width, height)
			line.append(image.subsurface(rect))

	return tile_table


#DRAWN MAP CLASS (pygame-dependant)
#used to draw the tilemap

class DrawnMap:
	def __init__(self, structure):
		self.displayedStructure = structure
		self.xOffset, self.yOffset = 3, 3

		self.mapSurface = pygame.Surface((8000,8000))
		self.mapDrawn = False

	def setStructure(self, structure):
		self.displayedStructure = structure

	def clearMap(self):
		self.mapDrawn = False


	def draw(self, screen, surface, tileSize, x, y, font, tileset, display_tiles, displayedStructure, scale=1):
		#draw outlines and basic color map

		bg_color = (144, 128, 128)
		screen.fill(bg_color)

		pygame.draw.rect(screen, (64,64,64), (x*tileSize*scale, y*tileSize*scale, displayedStructure.w*tileSize*scale, displayedStructure.h*tileSize*scale), 1)

		for placed in displayedStructure.structures:
			x1, y1 = x+placed.x, y+placed.y

			pygame.draw.rect(screen, placed.structure.color, (x1*tileSize*scale, y1*tileSize*scale, placed.w*tileSize*scale, placed.h*tileSize*scale), 0)

			if placed.structure.tilemap != None:
				for xd in range(0, placed.w):
					for yd in range(0, placed.h):
						x1d, y1d = x1+xd, y1+yd
						pygame.draw.rect(screen, placed.structure.tilemap[xd,yd], (x1d*tileSize*scale, y1d*tileSize*scale, tileSize*scale, tileSize*scale), 0)

			pygame.draw.rect(screen, (64,64,64), (x1*tileSize*scale, y1*tileSize*scale, placed.w*tileSize*scale, placed.h*tileSize*scale), 1)

			if placed.index:
				xc, yc = x+placed.centerXFloat-.25 + placed.centerOffsetX, y+placed.centerYFloat-.5

				textsurface = font.render(str(placed.index), False, (0, 0, 0))
				screen.blit(textsurface, (xc*tileSize, yc*tileSize))

		for xd, yd in displayedStructure.occupied:
			pygame.draw.line(screen, (64,64,64), ((x+xd)*tileSize*scale, (y+yd)*tileSize*scale), ((x+xd+1)*tileSize*scale, (y+yd+1)*tileSize*scale))
			pygame.draw.line(screen, (64,64,64), ((x+xd)*tileSize*scale, (y+yd+1)*tileSize*scale), ((x+xd+1)*tileSize*scale, (y+yd)*tileSize*scale))

		for xd, yd in displayedStructure.paths:
			pygame.draw.rect(screen, (255,255,255), ((x+xd)*tileSize*scale,(y+yd)*tileSize*scale, tileSize*scale, tileSize*scale), 0)

		if displayedStructure.exits:
			pygame.draw.rect(screen, (64,64,64), ((x+displayedStructure.exits['n'][0])*tileSize*scale, (y+displayedStructure.exits['n'][1])*tileSize*scale, tileSize*scale, tileSize*scale), 1)
			pygame.draw.rect(screen, (64,64,64), ((x+displayedStructure.exits['s'][0])*tileSize*scale, (y+displayedStructure.exits['s'][1])*tileSize*scale, tileSize*scale, tileSize*scale), 1)
			pygame.draw.rect(screen, (64,64,64), ((x+displayedStructure.exits['w'][0])*tileSize*scale, (y+displayedStructure.exits['w'][1])*tileSize*scale, tileSize*scale, tileSize*scale), 1)
			pygame.draw.rect(screen, (64,64,64), ((x+displayedStructure.exits['e'][0])*tileSize*scale, (y+displayedStructure.exits['e'][1])*tileSize*scale, tileSize*scale, tileSize*scale), 1)

		pygame.draw.rect(screen, (255,255,255), ((x+displayedStructure.centerX)*tileSize*scale, (y+displayedStructure.centerY)*tileSize*scale, tileSize*scale, tileSize*scale), 1)


		#draw grid (how deeply nested structures are)

		if not display_tiles:
			for placed in displayedStructure.structures:
				if placed.structure.depthmap != None:
					x1, y1 = x+placed.x, y+placed.y-1

					for xd in range(0, placed.w):
						for yd in range(0, placed.h):
							depth = placed.structure.depthmap[xd,yd]

							tx, ty = x1+xd-.5, y1+yd+.5

							size = min(.9, .1*depth)
							color = (200,200,200)
							color = (placed.structure.tilemap[xd,yd][0] * (1-size/2), placed.structure.tilemap[xd,yd][1] * (1-size/2), placed.structure.tilemap[xd,yd][2] * (1-size/2))
							pygame.draw.rect(screen, color, (tx*tileSize*scale+tileSize*(1-size), ty*tileSize*scale+tileSize*(1-size), tileSize*scale*size, tileSize*scale*size), 0)


		#draw tiles

		if display_tiles and displayedStructure.structures:
			placed = displayedStructure.structures[0]
			taggedAsBuilding = set([]) #for postprocessing

			tile_dc = tile_dictionary()
			label_dc = get_label_dc()
			targetDc, conflatedDc, target_tile_keys = get_tile_targets_dc()

			for xd in range(0, placed.w):
				for yd in range(0, placed.h):
					tag = tag_tile(placed.structure.tilemap, placed.structure.heightmap, placed.w, placed.h, xd, yd, label_dc, targetDc, conflatedDc, target_tile_keys)

					if placed.structure.tilemap[xd,yd] == (80, 80, 80):
						taggedAsBuilding.add((xd, yd, tag))
						continue #only draw tiles after postprocessing

					if tag in tile_dc.keys():
						tileXY = tile_dc[tag]
						tile = tileset[tileXY[0]][tileXY[1]]
					else:
						tile = tileset[0][0]

					if (tile != tileset[0][1]):
						tx, ty = x1+xd, y1+yd
						screen.blit(pygame.transform.scale(tile, (tileSize, tileSize)), (tx*tileSize, ty*tileSize))

			#postprocessing (building faces)

			for xd, yd, original_tag in taggedAsBuilding:
				tag = tweak_building_faces(placed.structure.tilemap, placed.structure.heightmap, placed.w, placed.h, xd, yd, label_dc, targetDc, conflatedDc, target_tile_keys, original_tag)

				if tag in tile_dc.keys():
					tileXY = tile_dc[tag]
					tile = tileset[tileXY[0]][tileXY[1]]
				else:
					tile = tileset[0][0]

				if (tile != tileset[0][1]):
					tx, ty = x1+xd, y1+yd
					screen.blit(pygame.transform.scale(tile, (tileSize, tileSize)), (tx*tileSize, ty*tileSize))


		#draw objects

		if display_tiles:
			for placed in displayedStructure.structures:
				if placed.structure.objectmap != None:
					x1, y1 = x+placed.x, y+placed.y
					for xd in range(1, placed.w):
						for yd in range(1, placed.h):
							tx, ty = x1+xd, y1+yd

							if placed.structure.objectmap[xd,yd][:5] == "chest":
								if placed.structure.objectmap[xd-1,yd][:5] != "chest" and placed.structure.objectmap[xd,yd-1][:5] != "chest":
									colorDirt = (32, 16, 16)
									colorPlaza = (180, 180, 180)
									colorRoad = (255, 255, 255)

									if placed.structure.tilemap != None and placed.structure.tilemap[xd,yd] in (colorDirt, colorPlaza, colorRoad):
										screen.blit(pygame.transform.scale(tileset[16][16], (tileSize, tileSize)), (tx*tileSize, ty*tileSize))
										screen.blit(pygame.transform.scale(tileset[17][16], (tileSize, tileSize)), ((tx+1)*tileSize, ty*tileSize))
										screen.blit(pygame.transform.scale(tileset[16][17], (tileSize, tileSize)), (tx*tileSize, (ty+1)*tileSize))
										screen.blit(pygame.transform.scale(tileset[17][17], (tileSize, tileSize)), ((tx+1)*tileSize, (ty+1)*tileSize))
									else:
										screen.blit(pygame.transform.scale(tileset[14][16], (tileSize, tileSize)), (tx*tileSize, ty*tileSize))
										screen.blit(pygame.transform.scale(tileset[15][16], (tileSize, tileSize)), ((tx+1)*tileSize, ty*tileSize))
										screen.blit(pygame.transform.scale(tileset[14][17], (tileSize, tileSize)), (tx*tileSize, (ty+1)*tileSize))
										screen.blit(pygame.transform.scale(tileset[15][17], (tileSize, tileSize)), ((tx+1)*tileSize, (ty+1)*tileSize))

							elif placed.structure.objectmap[xd,yd] == "npc":
								if placed.structure.objectmap[xd-1,yd] != "npc" and placed.structure.objectmap[xd,yd-1] != "npc":
									screen.blit(pygame.transform.scale(tileset[20][22], (tileSize, tileSize)), (tx*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[20][21], (tileSize, tileSize)), (tx*tileSize, (ty-1)*tileSize))

							elif placed.structure.objectmap[xd,yd] == "npc2":
								if placed.structure.objectmap[xd-1,yd] != "npc2" and placed.structure.objectmap[xd,yd-1] != "npc2":
									screen.blit(pygame.transform.scale(tileset[21][22], (tileSize, tileSize)), (tx*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[21][21], (tileSize, tileSize)), (tx*tileSize, (ty-1)*tileSize))

							elif placed.structure.objectmap[xd,yd] == "npc3":
								if placed.structure.objectmap[xd-1,yd] != "npc3" and placed.structure.objectmap[xd,yd-1] != "npc3":
									screen.blit(pygame.transform.scale(tileset[22][22], (tileSize, tileSize)), (tx*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[22][21], (tileSize, tileSize)), (tx*tileSize, (ty-1)*tileSize))

							elif placed.structure.objectmap[xd,yd] == "enemy":
								if placed.structure.objectmap[xd-1,yd] != "enemy" and placed.structure.objectmap[xd,yd-1] != "enemy":
									screen.blit(pygame.transform.scale(tileset[23][22], (tileSize, tileSize)), (tx*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[23][21], (tileSize, tileSize)), (tx*tileSize, (ty-1)*tileSize))

							elif placed.structure.objectmap[xd,yd] == "pc":
								if placed.structure.objectmap[xd-1,yd] != "pc" and placed.structure.objectmap[xd,yd-1] != "pc":
									screen.blit(pygame.transform.scale(tileset[18][22], (tileSize, tileSize)), ((tx)*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[17][22], (tileSize, tileSize)), ((tx-1)*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[18][21], (tileSize, tileSize)), ((tx)*tileSize, (ty-1)*tileSize))

							elif placed.structure.objectmap[xd,yd] == "boss":
								if placed.structure.objectmap[xd-1,yd] != "boss" and placed.structure.objectmap[xd,yd-1] != "boss":
									screen.blit(pygame.transform.scale(tileset[15][22], (tileSize, tileSize)), ((tx)*tileSize, (ty)*tileSize))
									screen.blit(pygame.transform.scale(tileset[15][21], (tileSize, tileSize)), ((tx)*tileSize, (ty-1)*tileSize))
									screen.blit(pygame.transform.scale(tileset[14][21], (tileSize, tileSize)), ((tx-1)*tileSize, (ty-1)*tileSize))
									screen.blit(pygame.transform.scale(tileset[16][21], (tileSize, tileSize)), ((tx+1)*tileSize, (ty-1)*tileSize))


	def drawScreen(self, screen, surface, screenW, screenH, tileSize, font, tileset, display_tiles, scale=1, updateDisplay=True):
		bg_color = (144, 128, 128)
		screen.fill(bg_color)

		if not self.mapDrawn:
			self.mapDrawn = True
			self.draw(self.mapSurface, surface, tileSize, 0, 0, font, tileset, display_tiles, self.displayedStructure, scale=scale)

		if self.mapDrawn:
			screen.blit(self.mapSurface, (self.xOffset*scale, self.yOffset*scale))

		if updateDisplay: #can be set to False if something should be drawn over the map before refreshing display
			pygame.display.update()
