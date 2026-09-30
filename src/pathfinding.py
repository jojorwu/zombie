import sys
from src.ai.pathfinding import *

sys.modules['src.pathfinding'] = sys.modules['src.ai.pathfinding']
