#functions related to converting material tiles into specific tile coordinates from the tileset (tiles for material transitions, edges, etc.)

def get_label_dc():
	colorWater = (64, 128, 160)
	colorWater2 = (65, 128, 160) #unused
	colorLand = (128, 180, 96)
	colorCliff = (128, 128, 128)
	colorLedge = (96, 144, 96) #unused
	colorRamp = (90, 140, 90) #unused
	colorForest = (32, 128, 96)
	colorRock = (72, 72, 72)
	colorSolidRock = (64, 64, 64)
	colorDestructible = (31, 15, 15)
	colorBuilding = (80, 80, 80)
	colorWall = (96, 96, 96)
	colorFence = (99, 99, 99)
	colorPlaza = (180, 180, 180)
	colorRoad = (255, 255, 255)
	colorField = (180, 224, 128) #unused
	colorDirt = (32, 16, 16)
	colorDoor = (255, 245, 235)
	colorNull = (0, 0, 0)

	colorPillarNE = (0, 2, 2)
	colorPillarNW = (0, 2, 98)
	colorPillarSE = (0, 98, 2)
	colorPillarSW = (0, 98, 98)
	colorTreeNE = (0, 1, 1)
	colorTreeNW = (0, 1, 99)
	colorTreeSE = (0, 99, 1)
	colorTreeSW = (0, 99, 99)
	colorTreeSmall = (1, 2, 3)
	colorRockSmall = (3, 2, 1)
	colorRockSmallDirt = (4, 2, 1)

	labelDc = {}
	labelDc[colorWater] = "water"
	labelDc[colorWater2] = "water2"
	labelDc[colorLand] = "land"
	labelDc[colorCliff] = "cliff"
	labelDc[colorLedge] = "ledge"
	labelDc[colorRamp] = "ramp"
	labelDc[colorForest] = "forest"
	labelDc[colorRock] = "rock"
	labelDc[colorSolidRock] = "rock"
	labelDc[colorDestructible] = "destructible"
	labelDc[colorBuilding] = "building"
	labelDc[colorWall] = "wall"
	labelDc[colorFence] = "fence"
	labelDc[colorPlaza] = "plaza"
	labelDc[colorRoad] = "road"
	labelDc[colorField] = "field"
	labelDc[colorDirt] = "dirt"
	labelDc[colorDoor] = "door"

	labelDc[colorPillarNE] = "pillarNE"
	labelDc[colorPillarNW] = "pillarNW"
	labelDc[colorPillarSE] = "pillarSE"
	labelDc[colorPillarSW] = "pillarSW"
	labelDc[colorTreeNE] = "treeNE"
	labelDc[colorTreeNW] = "treeNW"
	labelDc[colorTreeSE] = "treeSE"
	labelDc[colorTreeSW] = "treeSW"
	labelDc[colorTreeSmall] = "treeSmall"
	labelDc[colorRockSmall] = "rockSmall"
	labelDc[colorRockSmallDirt] = "rockSmallDirt"

	return labelDc


def get_tile_targets_dc():
	target_tile_keys = set(["land", "field", "cliff", "wall", "building", "rock", "solidrock", "destructible", "plaza"])
	targetDc = {}
	conflatedDc = {}

	targetDc["land"] = set(["water", "plaza", "road"])
	conflatedDc["land"] = set(["ledge","treeSmall","rockSmall","fence"])

	targetDc["field"] = set(["land"])
	conflatedDc["field"] = set(["ledge", "cliff"])

	targetDc["cliff"] = set(["water"])
	conflatedDc["cliff"] = set([])

	targetDc["wall"] = set(["water", "land", "plaza", "road", "dirt", "forest", "rock", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW"])
	conflatedDc["wall"] = set(["plaza", "road", "dirt", "cliff", "ledge", "forest", "fence", "rock", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW", "pillarNE", "pillarNW", "pillarSE", "pillarSW", "building", "door"])

	targetDc["building"] = set(["water", "land", "plaza", "road", "dirt", "forest", "rock", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW"])
	conflatedDc["building"] = set(["plaza", "road", "dirt", "cliff", "ledge", "forest", "fence", "rock", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW", "pillarNE", "pillarNW", "pillarSE", "pillarSW", "wall"])

	targetDc["rock"] = set(["land", "forest", "plaza", "road", "dirt", "cliff", "ledge"])
	conflatedDc["rock"] = set(["forest", "plaza", "road", "cliff", "ledge", "building", "wall", "fence", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW", "pillarNE", "pillarNW", "pillarSE", "pillarSW"])

	targetDc["solidrock"] = set(["land", "forest", "plaza", "road", "dirt", "cliff", "ledge"])
	conflatedDc["solidrock"] = set(["forest", "plaza", "road", "cliff", "ledge", "building", "wall", "fence", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW", "pillarNE", "pillarNW", "pillarSE", "pillarSW"])

	targetDc["destructible"] = set(["land", "forest", "plaza", "road", "dirt", "cliff", "ledge"])
	conflatedDc["destructible"] = set(["forest", "plaza", "road", "cliff", "ledge", "building", "wall", "fence", "treeSmall", "rockSmall", "treeNE", "treeNW", "treeSE", "treeSW", "pillarNE", "pillarNW", "pillarSE", "pillarSW"])

	targetDc["plaza"] = set([])
	conflatedDc["plaza"] = set([])

	return targetDc, conflatedDc, target_tile_keys


def tag_tile(tilemap, heightmap, w, h, x, y, labelDc, targetDc, conflatedDc, target_tile_keys):
	def get_label(x, y):
		if x >= 0 and y >= 0 and x < w and y < h:
			color = tilemap[x,y]
			if color in labelDc.keys():
				return labelDc[color]
			else:
				return ""
		else:
			return "boundary"

	def process_label(label, conflated):
		if label == "water2":
			return "water"
		if label == "plaza": #conflating plaza and road causes issues?
			return "road"
		# if label == "destructible":
			# return "rock"
		if label == "rockSmallDirt" and "rockSmall" in conflated:
			return "dirt"
		if label in conflated:
			return "land"
		else:
			return label

	#get label

	tile = get_label(x, y)

	#handle unchanging tiles first

	# if tile in ("water", "road", "fence", "rockSmall", "rockSmallDirt"):
	if tile in ("water", "road", "fence", "rockSmall", "rockSmallDirt","treeNE","treeNW","treeSE","treeSW","treeSmall"):
		return tile

	if tile == "plaza":
		return "road"

	#handle other tiles

	tag = ""

	if tile in target_tile_keys:
		targets = targetDc[tile]
		conflated = conflatedDc[tile]
	else:
		targets = set()
		conflated = set()

	tile_n = process_label(get_label(x, y-1), conflated)
	tile_s = process_label(get_label(x, y+1), conflated)
	tile_w = process_label(get_label(x-1, y), conflated)
	tile_e = process_label(get_label(x+1, y), conflated)

	tile_nw = process_label(get_label(x-1, y-1), conflated)
	tile_ne = process_label(get_label(x+1, y-1), conflated)
	tile_sw = process_label(get_label(x-1, y+1), conflated)
	tile_se = process_label(get_label(x+1, y+1), conflated)

	#water/road/fence/rockSmall/rockSmallDirt/plaza ignored at this point

	if tile == "cliff":
		if "plaza" in (tile_n, tile_s, tile_w, tile_e, tile_nw, tile_ne, tile_sw, tile_se) or "road" in (tile_n, tile_s, tile_w, tile_e, tile_nw, tile_ne, tile_sw, tile_se):
			tileName = "roadcliff"
		elif "dirt" in (tile_n, tile_s, tile_w, tile_e, tile_nw, tile_ne, tile_sw, tile_se):
			tileName = "dirtcliff"
		else:
			tileName = tile
	elif tile in ("pillarSE", "pillarSW", "pillarNE", "pillarNW"):
		if "plaza" in (tile_n, tile_s, tile_w, tile_e, tile_nw, tile_ne, tile_sw, tile_se) or "road" in (tile_n, tile_s, tile_w, tile_e, tile_nw, tile_ne, tile_sw, tile_se):
			tileName = "road" + tile
		elif "dirt" in (tile_n, tile_s, tile_w, tile_e, tile_nw, tile_ne, tile_sw, tile_se):
			tileName = "dirt" + tile
		else:
			tileName = tile
	else:
		tileName = tile

	#corner tiles
	if (tile_n in (tile,"boundary") or not tile_n in targets) and (tile_s in (tile,"boundary") or not tile_s in targets) and (tile_w in (tile,"boundary") or not tile_w in targets) and (tile_e in (tile,"boundary") or not tile_e in targets):

		if (tile_w == tile_s == tile and tile_sw in targets):
			tag = tileName + "_swc_" + tile_sw
		elif (tile_e == tile_s == tile and tile_se in targets):
			tag = tileName + "_sec_" + tile_se
		elif (tile_w == tile_n == tile and tile_nw in targets):
			tag = tileName + "_nwc_" + tile_nw
		elif (tile_e == tile_n == tile and tile_ne in targets):
			tag = tileName + "_nec_" + tile_ne

		else:
			tag = tileName

		#fix for diagonal rock paths

		if tag == "rock_swc_land" or tag == "rock_swc_dirt":
			if tile_sw in targets and tile_ne in targets:
				tag = "rock_dgf_land"
			if tile_nw in targets and tile_se in targets:
				tag = "rock_dgr_land"

	else:
		if tile_nw != tile_se and tile_nw == tile_n == tile_w and tile != tile_nw:
			tag = tileName + "_nw_" + tile_nw
		elif tile_sw != tile_ne and tile_ne == tile_n == tile_e and tile != tile_ne:
			tag = tileName + "_ne_" + tile_ne
		elif tile_ne != tile_sw and tile_sw == tile_s == tile_w and tile != tile_sw:
			tag = tileName + "_sw_" + tile_sw
		elif tile_nw != tile_se and tile_se == tile_s == tile_e and tile != tile_se:
			tag = tileName + "_se_" + tile_se

		elif tile_s != tile_n and tile_n != tile and tile_n == "water":
			tag = tileName + "_n_" + tile_n
		elif tile_n != tile_s and tile_s != tile and tile_s == "water":
			tag = tileName + "_s_" + tile_s
		elif tile_e != tile_w and tile_w != tile and tile_w == "water":
			tag = tileName + "_w_" + tile_w
		elif tile_w != tile_e and tile_e != tile and tile_e == "water":
			tag = tileName + "_e_" + tile_e

		elif tile == tile_e == tile_w == tile_n and tile_s != tile and tile_ne != tile and tileName != "land":
			tag = tileName + "_se_" + tile_s
		elif tile == tile_w == tile_e == tile_n and tile_s != tile and tile_nw != tile and tileName != "land":
			tag = tileName + "_sw_" + tile_s
		elif tile == tile_e == tile_w == tile_s and tile_n != tile and tile_se != tile and tileName != "land":
			tag = tileName + "_ne_" + tile_n
		elif tile == tile_w == tile_e == tile_s and tile_n != tile and tile_sw != tile and tileName != "land":
			tag = tileName + "_nw_" + tile_n

		elif tile_s != tile_n and tile_n != tile and tile_n in targets:
			tag = tileName + "_n_" + tile_n
		elif tile_n != tile_s and tile_s != tile and tile_s in targets:
			tag = tileName + "_s_" + tile_s
		elif tile_e != tile_w and tile_w != tile and tile_w in targets:
			tag = tileName + "_w_" + tile_w
		elif tile_w != tile_e and tile_e != tile and tile_e in targets:
			tag = tileName + "_e_" + tile_e

		#fix for water edges near one another

		if tile_s in targets and tile_e in targets and tile_se == tile: #se
			tag = tileName + "_se_" + tile_s
		if tile_s in targets and tile_w in targets and tile_sw == tile: #sw
			tag = tileName + "_sw_" + tile_s
		if tile_n in targets and tile_e in targets and tile_ne == tile: #ne
			tag = tileName + "_ne_" + tile_n
		if tile_n in targets and tile_w in targets and tile_nw == tile: #nw
			tag = tileName + "_nw_" + tile_n

		if tile_n == tile and tile_e in targets and tile_nw in targets:
			tag = tileName + "_ne_" + tile_nw
		if tile_n == tile and tile_w in targets and tile_ne in targets:
			tag = tileName + "_nw_" + tile_ne
		if tile_s == tile and tile_e in targets and tile_sw in targets:
			tag = tileName + "_se_" + tile_sw
		if tile_s == tile and tile_w in targets and tile_se in targets:
			tag = tileName + "_sw_" + tile_se

		#fix for rock edges at cave/grass boundaries

		if tile_nw in targets and tile_n == tile_nw and tile_e == tile and tile_w != tile and tile_w != tile_nw:
			tag = tileName + "_nw_" + tile_nw
		if tile_ne in targets and tile_n == tile_ne and tile_w == tile and tile_e != tile and tile_e != tile_ne:
			tag = tileName + "_ne_" + tile_ne

		if tile_sw in targets and tile_w == tile_sw and tile_n == tile and tile_s != tile and tile_s != tile_sw:
			tag = tileName + "_sw_" + tile_sw
		if tile_se in targets and tile_e == tile_se and tile_n == tile and tile_s != tile and tile_s != tile_se:
			tag = tileName + "_se_" + tile_se

	#postprocessing (use tiles for assessing context, not tags)

	if tile == "rock":
		#fix cave entrance (land/dirt transition)

		if tile_s == "land" and tile_e == "dirt" and tile_se == "land":
			tag = "rock_se_dirt"
		elif tile_s == "land" and tile_w == "dirt" and tile_sw == "land":
			tag = "rock_sw_dirt"
		elif tile_n == "land" and tile_e == "dirt" and tile_ne == "land":
			tag = "rock_ne_dirt"
		elif tile_n == "land" and tile_w == "dirt" and tile_nw == "land":
			tag = "rock_nw_dirt"

		elif tile_e == "land" and tile_n == "dirt" and tile_ne == "land":
			tag = "rock_ne_dirt"
		elif tile_e == "land" and tile_s == "dirt" and tile_se == "land":
			tag = "rock_se_dirt"
		elif tile_w == "land" and tile_n == "dirt" and tile_nw == "land":
			tag = "rock_nw_dirt"
		elif tile_w == "land" and tile_s == "dirt" and tile_sw == "land":
			tag = "rock_sw_dirt"

		#fix rock/destructible transition

		if tile_e == "destructible" and tile_n == "land" and (tile_w == "rock" or tile_w == "destructible"):
			tag = "rock_n_land"
		elif tile_w == "destructible" and tile_n == "land" and (tile_e == "rock" or tile_e == "destructible"):
			tag = "rock_n_land"
		elif tile_s == "destructible" and tile_e == "land" and (tile_n == "rock" or tile_n == "destructible"):
			tag = "rock_e_land"
		elif tile_s == "destructible" and tile_w == "land" and (tile_n == "rock" or tile_n == "destructible"):
			tag = "rock_w_land"

		elif tile_e == "destructible" and tile_n == "dirt" and (tile_w == "rock" or tile_w == "destructible"):
			tag = "rock_n_dirt"
		elif tile_w == "destructible" and tile_n == "dirt" and (tile_e == "rock" or tile_e == "destructible"):
			tag = "rock_n_dirt"
		elif tile_s == "destructible" and tile_e == "dirt" and (tile_n == "rock" or tile_n == "destructible"):
			tag = "rock_e_dirt"
		elif tile_s == "destructible" and tile_w == "dirt" and (tile_n == "rock" or tile_n == "destructible"):
			tag = "rock_w_dirt"

	#no building postprocessing

	if tag == "": #sometimes happens to land near roads
		tag = tile

	return tag


def tweak_building_faces(tilemap, heightmap, w, h, x, y, labelDc, targetDc, conflatedDc, target_tile_keys, original_tag):
	#original_tag can be 'building', 'building_s_land', etc.
	#needs to have all buildings tagged in advance

	labelDc = get_label_dc()
	tag_s = tag_tile(tilemap, heightmap, w, h, x, y+1, labelDc, targetDc, conflatedDc, target_tile_keys)

	if tag_s in ['building_s_land', 'building_s_road', 'door']:
		if y-1 >= 0 and labelDc[tilemap[x,y-1]] == "building":
			return 'roof_s'
		else:
			return 'roof_sn'

	if tag_s == 'building_se_land':
		if y-1 >= 0 and labelDc[tilemap[x,y-1]] == "building":
			return 'roof_e'
		else:
			return 'roof_sne'

	if tag_s == 'building_sw_land':
		if y-1 >= 0 and labelDc[tilemap[x,y-1]] == "building":
			return 'roof_w'
		else:
			return 'roof_snw'

	tag_w = tag_tile(tilemap, heightmap, w, h, x-1, y, labelDc, targetDc, conflatedDc, target_tile_keys)
	tag_e = tag_tile(tilemap, heightmap, w, h, x+1, y, labelDc, targetDc, conflatedDc, target_tile_keys)

	if tag_w == "door" and "building" in tag_e:
		return "door_right"
	if tag_e == "door" and "building" in tag_w:
		return "door_left"

	if original_tag == 'building' and tag_s == 'building_sec_land':
		return "roof_swc"
	if original_tag == 'building' and tag_s == 'building_swc_land':
		return "roof_sec"

	if original_tag == 'building_n_land' and tag_s == 'building_sec_land':
		return 'roof_snwc'
	if original_tag == 'building_n_land' and tag_s == 'building_swc_land':
		return 'roof_snec'

	# return "water"
	return original_tag


def tile_dictionary():
	tileDc = {}
	tileDc[""] = (0, 1)

	tileDc["land"] = (1, 1)

	tileDc["water"] = (2, 4)
	tileDc["water2"] = (2, 4)

	tileDc["cliff"] = (3, 1)
	tileDc["roadcliff"] = (15, 7)
	tileDc["dirtcliff"] = (15, 7)

	tileDc["fence"] = (9, 1)

	tileDc["plaza"] = (14, 8)
	tileDc["dirt"] = (2, 20)

	#cliffs

	tileDc["cliff_n_water"] = (2, 5)
	tileDc["cliff_s_water"] = (2, 3)
	tileDc["cliff_w_water"] = (3, 4)
	tileDc["cliff_e_water"] = (1, 4)
	tileDc["cliff_nw_water"] = (6, 4)
	tileDc["cliff_ne_water"] = (5, 4)
	tileDc["cliff_sw_water"] = (6, 3)
	tileDc["cliff_se_water"] = (5, 3)

	tileDc["cliff_nwc_water"] = (3, 5)
	tileDc["cliff_nec_water"] = (1, 5)
	tileDc["cliff_swc_water"] = (3, 3)
	tileDc["cliff_sec_water"] = (1, 3)

	tileDc["roadcliff_n_water"] = (22, 7)
	tileDc["roadcliff_s_water"] = (22, 5)
	tileDc["roadcliff_w_water"] = (23, 6)
	tileDc["roadcliff_e_water"] = (21, 6)
	tileDc["roadcliff_nw_water"] = (22, 9)
	tileDc["roadcliff_ne_water"] = (21, 9)
	tileDc["roadcliff_sw_water"] = (22, 8)
	tileDc["roadcliff_se_water"] = (21, 8)

	tileDc["roadcliff_nwc_water"] = (23, 7)
	tileDc["roadcliff_nec_water"] = (21, 7)
	tileDc["roadcliff_swc_water"] = (23, 5)
	tileDc["roadcliff_sec_water"] = (21, 5)

	tileDc["dirtcliff_n_water"] = (26, 7)
	tileDc["dirtcliff_s_water"] = (26, 5)
	tileDc["dirtcliff_w_water"] = (27, 6)
	tileDc["dirtcliff_e_water"] = (25, 6)
	tileDc["dirtcliff_nw_water"] = (26, 9)
	tileDc["dirtcliff_ne_water"] = (25, 9)
	tileDc["dirtcliff_sw_water"] = (26, 8)
	tileDc["dirtcliff_se_water"] = (25, 8)

	tileDc["dirtcliff_nwc_water"] = (27, 7)
	tileDc["dirtcliff_nec_water"] = (25, 7)
	tileDc["dirtcliff_swc_water"] = (27, 5)
	tileDc["dirtcliff_sec_water"] = (25, 5)

	#roads

	tileDc["road"] = (15, 7)
	tileDc["plaza"] = (15, 7)

	tileDc["land_n_road"] = (15, 8)
	tileDc["land_s_road"] = (15, 6)
	tileDc["land_w_road"] = (16, 7)
	tileDc["land_e_road"] = (14, 7)

	tileDc["land_nw_road"] = (20, 5)
	tileDc["land_ne_road"] = (19, 5)
	tileDc["land_sw_road"] = (20, 6)
	tileDc["land_se_road"] = (19, 6)

	tileDc["land_nwc_road"] = (16, 8)
	tileDc["land_nec_road"] = (14, 8)
	tileDc["land_swc_road"] = (16, 6)
	tileDc["land_sec_road"] = (14, 6)

	#rock (diagonal versions of rock unused)

	tileDc["rockSmall"] = (5, 1)
	tileDc["rockSmallDirt"] = (7, 1)

	tileDc["rock"] = (2, 8)

	tileDc["rock_n_land"] = (2, 7)
	tileDc["rock_s_land"] = (2, 9)
	tileDc["rock_w_land"] = (1, 8)
	tileDc["rock_e_land"] = (3, 8)
	tileDc["rock_nw_land"] = (1, 7)
	tileDc["rock_ne_land"] = (3, 7)
	tileDc["rock_sw_land"] = (1, 9)
	tileDc["rock_se_land"] = (3, 9)
	tileDc["rock_nwc_land"] = (5, 7)
	tileDc["rock_nec_land"] = (6, 7)
	tileDc["rock_swc_land"] = (5, 8)
	tileDc["rock_sec_land"] = (6, 8)

	tileDc["rock_n_dirt"] = (6, 30)
	tileDc["rock_s_dirt"] = (6, 32)
	tileDc["rock_w_dirt"] = (5, 31)
	tileDc["rock_e_dirt"] = (7, 31)
	tileDc["rock_nw_dirt"] = (5, 30)
	tileDc["rock_ne_dirt"] = (7, 30)
	tileDc["rock_sw_dirt"] = (5, 32)
	tileDc["rock_se_dirt"] = (7, 32)

	tileDc["rock_nwc_dirt"] = (5, 7)
	tileDc["rock_nec_dirt"] = (6, 7)
	tileDc["rock_swc_dirt"] = (5, 8)
	tileDc["rock_sec_dirt"] = (6, 8)

	tileDc["destructible"] = (9, 12)

	tileDc["destructible_n_dirt"] = (20, 11)
	tileDc["destructible_s_dirt"] = (20, 13)
	tileDc["destructible_w_dirt"] = (19, 12)
	tileDc["destructible_e_dirt"] = (21, 12)

	tileDc["destructible_n_land"] = (9, 11)
	tileDc["destructible_s_land"] = (9, 13)
	tileDc["destructible_w_land"] = (8, 12)
	tileDc["destructible_e_land"] = (10, 12)
	tileDc["destructible_nw_land"] = (8, 11)
	tileDc["destructible_ne_land"] = (10, 11)
	tileDc["destructible_sw_land"] = (8, 13)
	tileDc["destructible_se_land"] = (10, 13)

	tileDc["destructible_ne_dirt"] = (21, 11)

	tileDc["destructible_nec_dirt"] = (9, 12)
	tileDc["destructible_nwc_dirt"] = (9, 12)
	tileDc["destructible_sec_dirt"] = (9, 12)
	tileDc["destructible_swc_dirt"] = (9, 12)
	tileDc["destructible_nw_dirt"] = (19, 11)
	tileDc["destructible_ne_dirt"] = (21, 11)
	tileDc["destructible_sw_dirt"] = (19, 13)
	tileDc["destructible_se_dirt"] = (21, 13)

	tileDc["rock_dgr_land"] = (8, 7)
	tileDc["rock_dgf_land"] = (10, 7)

	#trees

	tileDc["treeSmall"] = (3, 1)
	tileDc["forest"] = (21, 1)

	tileDc["treeNE"] = (21, 1)
	tileDc["treeNW"] = (22, 1)
	tileDc["treeSE"] = (21, 2)
	tileDc["treeSW"] = (22, 2)

	#buildings

	tileDc["building"] = (26, 15)

	tileDc["building_n_land"] = (26, 14)
	# tileDc["building_n_land"] = (10, 7)

	tileDc["building_w_land"] = (25, 15)
	tileDc["building_e_land"] = (27, 15)
	tileDc["building_nw_land"] = (25, 14)
	tileDc["building_ne_land"] = (27, 14)

	tileDc["building_n_road"] = (26, 14)
	tileDc["building_w_road"] = (25, 15)
	tileDc["building_e_road"] = (27, 15)
	tileDc["building_nw_road"] = (25, 14)
	tileDc["building_ne_road"] = (27, 14)

	tileDc["building_s_land"] = (19, 16)
	tileDc["building_sw_land"] = (19, 15)
	tileDc["building_se_land"] = (23, 15)

	tileDc["building_s_road"] = (19, 16)
	tileDc["building_sw_road"] = (19, 15)
	tileDc["building_se_road"] = (23, 15)

	tileDc["building_nwc_land"] = (27, 22)
	tileDc["building_nec_land"] = (25, 22)
	tileDc["building_swc_land"] = (25, 15)
	tileDc["building_sec_land"] = (25, 20)

	tileDc["building_nwc_road"] = (27, 22)
	tileDc["building_nec_road"] = (25, 22)
	tileDc["building_swc_road"] = (25, 15)
	tileDc["building_sec_road"] = (25, 20)

	tileDc["roof_s"] = (26, 16)
	tileDc["roof_w"] = (25, 16)
	tileDc["roof_e"] = (27, 16)

	tileDc["roof_swc"] = (25, 21)
	tileDc["roof_sec"] = (27, 21)

	tileDc["roof_sn"] = (26, 18)
	tileDc["roof_snw"] = (25, 18)
	tileDc["roof_sne"] = (27, 18)
	tileDc["roof_snwc"] = (25, 19)
	tileDc["roof_snec"] = (27, 19)

	tileDc["door"] = (21, 16)
	tileDc["door_left"] = (20, 16)
	tileDc["door_right"] = (22, 16)

	tileDc["pillarNE"] = (19, 18)
	tileDc["pillarNW"] = (20, 18)
	tileDc["pillarSE"] = (19, 19)
	tileDc["pillarSW"] = (20, 19)

	tileDc["roadpillarNE"] = (21, 18)
	tileDc["roadpillarNW"] = (22, 18)
	tileDc["roadpillarSE"] = (21, 19)
	tileDc["roadpillarSW"] = (22, 19)

	tileDc["dirtpillarNE"] = (23, 18)
	tileDc["dirtpillarNW"] = (24, 18)
	tileDc["dirtpillarSE"] = (23, 19)
	tileDc["dirtpillarSW"] = (24, 19)

	#walls

	tileDc["wall"] = (2, 24)

	tileDc["wall_nw_land"] = (1, 23)
	tileDc["wall_w_land"] = (1, 24)
	tileDc["wall_sw_land"] = (1, 25)
	tileDc["wall_n_land"] = (2, 23)
	tileDc["wall_s_land"] = (2, 25)
	tileDc["wall_ne_land"] = (3, 23)
	tileDc["wall_e_land"] = (3, 24)
	tileDc["wall_se_land"] = (3, 25)

	tileDc["wall_s_road"] = (2, 25)

	tileDc["wall_nw_road"] = (1, 23)
	tileDc["wall_w_road"] = (1, 24)
	tileDc["wall_sw_road"] = (1, 25)
	tileDc["wall_n_road"] = (2, 23)
	tileDc["wall_ne_road"] = (3, 23)
	tileDc["wall_e_road"] = (3, 24)
	tileDc["wall_se_road"] = (3, 25)

	tileDc["wall_nwc_land"] = (5, 24)
	tileDc["wall_nec_land"] = (6, 24)
	tileDc["wall_swc_land"] = (5, 23)
	tileDc["wall_sec_land"] = (6, 23)

	tileDc["wall_nwc_road"] = (5, 24)
	tileDc["wall_nec_road"] = (6, 24)
	tileDc["wall_swc_road"] = (5, 23)
	tileDc["wall_sec_road"] = (6, 23)

	#fix missing tiles

	tileDc["land_se_rock"] = (1, 1)
	tileDc["land_sw_rock"] = (1, 1)
	tileDc["land_ne_rock"] = (1, 1)
	tileDc["land_nw_rock"] = (1, 1)


	return tileDc
