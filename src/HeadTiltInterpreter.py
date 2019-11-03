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

    @staticmethod
    def make_move_decision(dominant_axis, x_ra, z_ra, calibration_data):
        # if x axis is dominant
        if dominant_axis == 'x':
            if x_ra > calibration_data['x_max']:
                print(config.MOVE_LEFT_MSG)
            elif x_ra < calibration_data['x_min']:
                print(config.MOVE_RIGHT_MSG)
            else:
                print(config.CONTINUE_MSG)

        # if z axis is dominant
        elif dominant_axis == 'z':
            if z_ra > calibration_data['z_max']:
                print(config.MOVE_FORWARD_MSG)
            elif z_ra < calibration_data['z_min']:
                print(config.MOVE_BACKWARD_MSG)
            else:
                print(config.CONTINUE_MSG)
        else:
            print('Mistake? Continue?')

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
        while True:
            x_ra, y_ra, z_ra = self.get_cluster_avg(sock)  # Rolling averages for live clusters
            dominant = self.calc_dominant_axis(x_ra, z_ra, axis_ranges)
            self.make_move_decision(dominant, x_ra, z_ra, axis_ranges)


if __name__ == '__main__':
    interpreter = HeadTiltInterpreter()
    interpreter.run()

