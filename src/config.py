# I/O Settings
UDP_IP = '127.0.0.1'
UDP_PORT = 12345

# Run Settings
AXIS_VALUE_ROUNDING = 3
PRINT_RAW_AXIS_VALUES = False
PRINT_CLUSTER_VALUES = False

# Calculation Variables
NUM_CALIBRATION_POINTS = 45  # 300
NUM_POINTS_PER_ROLLING_AVG = 15  # 5
X_DELTA = 0.3
Z_DELTA = 0.3
DOM_HLV = 0.6  # Dominant High Limiting Value
DOM_MLV = 0.4  # Dominant Medium Limiting Value
DOM_LLV = 0.3  # Dominant Low Limiting Value
SUB_LV = 0.15  # Sub-dominant MLV
DOM_HLV_MULT = 1  # DOM_HLV Multiplier
DOM_MLV_MULT = .5  # DOM_MLV Multiplier
DOM_LLV_MULT = 0.25  # DOM_LLV Multiplier
BASE_VOLTAGE = 12

# String Constants
MOVE_FORWARD_MSG = 'LETS FLY!!'
MOVE_BACKWARD_MSG = 'DIVE!!!'
MOVE_RIGHT_MSG = 'RIGHT 4 REALZ'
MOVE_LEFT_MSG = 'LEFT'
CONTINUE_MSG = 'CONTINUE'
