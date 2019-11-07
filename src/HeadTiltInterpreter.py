from src import config
import socket
import json


# TODO: Drop Y axis from all functions
class HeadTiltInterpreter:
    @staticmethod
    def get_axis_values(accel_dict, print_values=config.PRINT_RAW_AXIS_VALUES):
        x = accel_dict['data'][0] + 1
        y = accel_dict['data'][1] + 1
        z = accel_dict['data'][2] + 1

        if print_values:
            print('x: {}, y: {}, z: {}'.format(x - 1, y - 1, z - 1))

        return x, y, z

    def get_cluster_avg(self, sock, cluster_size=config.NUM_POINTS_PER_ROLLING_AVG,
                        print_cluster=config.PRINT_CLUSTER_VALUES):
        # Axis totals for average
        xt = 0
        yt = 0
        zt = 0
        for i in range(0, cluster_size + 1):
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes

            acc_dict = json.loads(data)
            x, y, z = self.get_axis_values(acc_dict)
            xt += x
            yt += y
            zt += z

        # Axis averages
        xa = xt / cluster_size
        ya = yt / cluster_size
        za = zt / cluster_size

        if print_cluster:
            print('x_avg: {}, y_avg: {}, z_avg: {}'.format(xa - 1, ya - 1, za - 1))

        return xa, ya, za

    def run_calibration(self, sock):
        # Calibration: get mins and maxes for each axis
        print('Calibrating...')
        return self.get_cluster_avg(sock, config.NUM_CALIBRATION_POINTS)

    @staticmethod
    def calc_dominant_axis(x_ra, z_ra, calibration_data):
        x_delta = (x_ra - calibration_data['x_avg']) / calibration_data['x_avg']
        z_delta = (z_ra - calibration_data['z_avg']) / calibration_data['z_avg']

        deltas = [abs(x_delta), abs(z_delta)]

        dominant = deltas.index(max(deltas))  # 0 if x, 1 if z

        return 'x' if dominant == 0 else 'z'

    @staticmethod     # Returns Voltage To 2 Motors
    def make_move_decision(dominant_axis, x_ra, z_ra, last_xv, last_zv, calibration_data):
        # if x axis is dominant
        dom_delta, sub_delta = 0, 0

        if dominant_axis == 'x':
            if x_ra > calibration_data['x_max']:
                dom_delta = calibration_data['x_max'] - x_ra
                print(config.MOVE_LEFT_MSG)
            elif x_ra < calibration_data['x_min']:
                dom_delta = calibration_data['x_min'] - x_ra
                print(config.MOVE_RIGHT_MSG)
            else:
                print(config.CONTINUE_MSG)

        # if z axis is dominant
        elif dominant_axis == 'z':
            if z_ra > calibration_data['z_max']:
                dom_delta = calibration_data['z_max'] - z_ra
                print(config.MOVE_FORWARD_MSG)
            elif z_ra < calibration_data['z_min']:
                dom_delta = calibration_data['z_min'] - z_ra
                print(config.MOVE_BACKWARD_MSG)
            else:
                print(config.CONTINUE_MSG)
        else:
            print('Mistake? Continue?')

        dom_voltage, sub_voltage = 0, 0

        # Primary Voltage Equation: voltage = base voltage * multiplier * [1 or -1 to indicate direction]

        # Limiting Variable Groups:
        if abs(dom_delta) > config.DOM_HLV:
            dom_voltage = config.BASE_VOLTAGE * config.DOM_HLV_MULT * (dom_delta/abs(dom_delta))
        elif abs(dom_delta) > config.DOM_MLV:
            dom_voltage = config.BASE_VOLTAGE * config.DOM_MLV_MULT * (dom_delta/abs(dom_delta))
        elif abs(dom_delta) > config.DOM_LLV:
            dom_voltage = config.BASE_VOLTAGE * config.DOM_LLV_MULT * (dom_delta/abs(dom_delta))

        # Secondary Limiting Variable
        if abs(sub_delta) > config.SUB_LV:
            sub_voltage = abs(sub_delta)/abs(dom_delta) * (sub_delta/abs(sub_delta))

        x_voltage = dom_voltage if dominant_axis == 'x' else sub_voltage
        z_voltage = dom_voltage if dominant_axis == 'z' else sub_voltage

        # This allows driver to return to a relaxed position to continue in the same direction
        if last_xv > 0 and last_xv > x_voltage:
            x_voltage = last_xv
        elif last_xv < 0 and last_xv < x_voltage:
            x_voltage = last_xv

        if last_zv > 0 and last_zv > z_voltage:
            z_voltage = last_zv
        elif last_zv < 0 and last_zv < z_voltage:
            z_voltage = last_zv

        # TODO: How do we stop? => This currently will never return 0, 0 after it starts

        return x_voltage, z_voltage

    def run(self):
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
        sock.bind((config.UDP_IP, config.UDP_PORT))

        # Calibration Test to determine deadzone
        x_avg, y_avg, z_avg = self.run_calibration(sock)
        axis_ranges = {
            'x_min': x_avg * (1 - config.X_DELTA),
            'x_max': x_avg * (1 + config.X_DELTA),
            'x_avg': x_avg,
            'z_min': z_avg * (1 - config.Z_DELTA),
            'z_max': z_avg * (1 + config.Z_DELTA),
            'z_avg': z_avg
        }

        # Read data and decide movement
        temp_x_voltage, temp_z_voltage = 0, 0
        while True:
            x_ra, y_ra, z_ra = self.get_cluster_avg(sock)  # Rolling averages for live clusters
            dominant = self.calc_dominant_axis(x_ra, z_ra, axis_ranges)
            x_voltage, z_voltage = self.make_move_decision(
                dominant, x_ra, z_ra, temp_x_voltage, temp_z_voltage, axis_ranges)
            print('X Voltage: {} | Z Voltage: {}'.format(x_voltage, z_voltage))
            temp_x_voltage, temp_z_voltage = x_voltage, z_voltage


if __name__ == '__main__':
    interpreter = HeadTiltInterpreter()
    interpreter.run()

