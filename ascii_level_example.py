from generator import Generator

def get_ascii_map(source_map, tiles_to_ascii):
	#extra function for converting map into ASCII string based on conversion table
	#x and y axes must be swapped while 'drawing' map with text

	tile_conversion_keys = set(tiles_to_ascii.keys())
	w = len(source_map)
	h = len(source_map[0])

	ascii_map = ""
	for y in range(0, h):
		for x in range(0, w):
			tile = source_map[x][y]
			if tile in tile_conversion_keys:
				ascii_map += tiles_to_ascii[tile]
			else:
				ascii_map += tiles_to_ascii['other']
		if y != h-1:
			ascii_map += '\n'

	return ascii_map


#USE CASE: create an ASCII dungeon map for a roguelike game

#1. generate map from map template and seed

rule_files = ["maps/basic dungeon example (randomised)/templates.txt"]

generator = Generator(rule_files)
generator.generateMap(100) #seed=100, change or randomize for different maps

#2. get tile map and map size

tile_map = generator.generatedMap.getTilemapValues()
map_w = len(tile_map)
map_h = len(tile_map[0])

#3. get ascii representation of map

tiles_to_ascii = {
	'rock': '#',
	'rockSmall': '#',
	'wall': '#',
	'dirt': '.',
	'land': '.',
	'road': '-',
	'plaza': '-',
	'forest': 'T',
	'tree': 'T',
	'treeNW': 'T',
	'treeNE': 'T',
	'treeSW': 'T',
	'treeSE': 'T',
	'treeSmall': 'T',
	'water': '~',
	'cliff': '%',
	'building': '+',
	'pillar': '+',
	'pillarNW': '+',
	'pillarNE': '+',
	'pillarSW': '+',
	'pillarSE': '+',
	'door': '+',
	'other': '?'
}

ascii_map = get_ascii_map(tile_map, tiles_to_ascii)

#4. print result

print (ascii_map)
print ("\n---\nGenerated map (%i by %i tiles)" % (map_w, map_h))