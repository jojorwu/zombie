class TileType:
    GRASS = 0
    ROAD = 1
    BUILDING_WALL = 2
    BUILDING_FLOOR = 3
    WATER = 4
    FOREST = 5
    FURNITURE = 6
    DOOR = 7
    STAIRS = 8
    AIR = 9
    BRIDGE = 10
    UNDERGROUND_WALL = 11
    UNDERGROUND_FLOOR = 12
    LADDER = 13
    PARKING = 14
    ROOF = 15
    TRASH_CAN = 16
    CONTAINER_BOX = 17
    MAILBOX = 18
    ROAD_HIGHWAY = 19
    SIDEWALK = 20
    CROSSWALK = 21
    DIRT_ROAD = 22
    FOREST_DENSE = 23
    FOREST_SPARSE = 24
    DEAD_TREE = 25
    GRASS_DENSE = 26
    GRASS_DRY = 27
    SAND = 28

    TABLE = 29
    CHAIR = 30
    SOFA = 31
    BED = 32
    CABINET = 33
    REFRIGERATOR = 34
    KITCHEN_COUNTER = 35


class BuildingType:
    SUPERMARKET = "supermarket"
    STORE = "store"
    HOSPITAL = "hospital"
    POLICE_STATION = "police_station"
    GAS_STATION = "gas_station"
    GUN_STORE = "gun_store"
    RESIDENTIAL = "residential"
    DORMITORY = "dormitory"
    SCHOOL = "school"
    WAREHOUSE = "warehouse"
    FACTORY = "factory"


TILE_COLORS = {
    TileType.GRASS: (34, 139, 34),
    TileType.ROAD: (105, 105, 105),
    TileType.BUILDING_WALL: (100, 50, 20),
    TileType.BUILDING_FLOOR: (210, 180, 140),
    TileType.WATER: (65, 105, 225),
    TileType.FOREST: (0, 100, 0),
    TileType.FURNITURE: (139, 115, 85),
    TileType.DOOR: (160, 82, 45),
    TileType.STAIRS: (255, 140, 0),
    TileType.AIR: (15, 15, 25),
    TileType.BRIDGE: (139, 90, 43),
    TileType.UNDERGROUND_WALL: (50, 50, 55),
    TileType.UNDERGROUND_FLOOR: (90, 90, 100),
    TileType.LADDER: (218, 165, 32),
    TileType.PARKING: (70, 70, 75),
    TileType.ROOF: (160, 140, 120),
    TileType.TRASH_CAN: (80, 90, 80),
    TileType.CONTAINER_BOX: (180, 130, 70),
    TileType.MAILBOX: (70, 130, 180),
    TileType.ROAD_HIGHWAY: (50, 50, 55),
    TileType.SIDEWALK: (180, 180, 185),
    TileType.CROSSWALK: (220, 220, 220),
    TileType.DIRT_ROAD: (139, 105, 20),
    TileType.FOREST_DENSE: (0, 70, 0),
    TileType.FOREST_SPARSE: (46, 139, 87),
    TileType.DEAD_TREE: (100, 80, 60),
    TileType.GRASS_DENSE: (0, 110, 0),
    TileType.GRASS_DRY: (189, 183, 107),
    TileType.SAND: (238, 214, 139),
    TileType.TABLE: (160, 120, 80),
    TileType.CHAIR: (180, 140, 90),
    TileType.SOFA: (100, 60, 140),
    TileType.BED: (70, 110, 160),
    TileType.CABINET: (120, 80, 40),
    TileType.REFRIGERATOR: (220, 225, 230),
    TileType.KITCHEN_COUNTER: (150, 150, 150),
}

BUILDING_COLORS = {
    BuildingType.SUPERMARKET: (255, 215, 0),
    BuildingType.STORE: (240, 230, 140),
    BuildingType.HOSPITAL: (220, 240, 255),
    BuildingType.POLICE_STATION: (180, 200, 230),
    BuildingType.GAS_STATION: (255, 220, 180),
    BuildingType.GUN_STORE: (180, 160, 140),
    BuildingType.RESIDENTIAL: (210, 180, 140),
    BuildingType.DORMITORY: (190, 160, 120),
    BuildingType.SCHOOL: (200, 190, 170),
    BuildingType.WAREHOUSE: (120, 110, 100),
    BuildingType.FACTORY: (140, 130, 110),
}

TILE_WALKABLE = {
    TileType.GRASS: True,
    TileType.ROAD: True,
    TileType.BUILDING_WALL: False,
    TileType.BUILDING_FLOOR: True,
    TileType.WATER: False,
    TileType.FOREST: True,
    TileType.FURNITURE: False,
    TileType.DOOR: True,
    TileType.STAIRS: True,
    TileType.AIR: False,
    TileType.BRIDGE: True,
    TileType.UNDERGROUND_WALL: False,
    TileType.UNDERGROUND_FLOOR: True,
    TileType.LADDER: True,
    TileType.PARKING: True,
    TileType.ROOF: False,
    TileType.TRASH_CAN: False,
    TileType.CONTAINER_BOX: False,
    TileType.MAILBOX: False,
    TileType.ROAD_HIGHWAY: True,
    TileType.SIDEWALK: True,
    TileType.CROSSWALK: True,
    TileType.DIRT_ROAD: True,
    TileType.FOREST_DENSE: True,
    TileType.FOREST_SPARSE: True,
    TileType.DEAD_TREE: False,
    TileType.GRASS_DENSE: True,
    TileType.GRASS_DRY: True,
    TileType.SAND: True,
    TileType.TABLE: False,
    TileType.CHAIR: True,
    TileType.SOFA: False,
    TileType.BED: False,
    TileType.CABINET: False,
    TileType.REFRIGERATOR: False,
    TileType.KITCHEN_COUNTER: False,
}

TILE_SPEED_MODIFIERS = {
    TileType.ROAD_HIGHWAY: 1.25,
    TileType.ROAD: 1.1,
    TileType.CROSSWALK: 1.1,
    TileType.SIDEWALK: 1.05,
    TileType.PARKING: 1.05,
    TileType.BRIDGE: 1.0,
    TileType.BUILDING_FLOOR: 1.0,
    TileType.UNDERGROUND_FLOOR: 1.0,
    TileType.GRASS: 0.95,
    TileType.GRASS_DRY: 0.9,
    TileType.DIRT_ROAD: 0.9,
    TileType.FOREST_SPARSE: 0.85,
    TileType.SAND: 0.8,
    TileType.GRASS_DENSE: 0.75,
    TileType.FOREST: 0.75,
    TileType.FOREST_DENSE: 0.6,
}
