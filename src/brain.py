import sys
from src.ai.brain import *

sys.modules['src.brain'] = sys.modules['src.ai.brain']
