from src import config
import zmq
import socket
import json


class HeadTiltInterpreter:
    @staticmethod
    def get_axis_values(accel_dict, print_values=config.PRINT_RAW_AXIS_VALUES):
        x = accel_dict['data'][0] + 1
        z = accel_dict['data'][2] + 1

        if print_values:
            print('x: {}, z: {}'.format(x - 1, z - 1))

        return x, z

    def get_cluster_avg(self, sock, cluster_size=config.NUM_POINTS_PER_ROLLING_AVG,
                        print_cluster=config.PRINT_CLUSTER_VALUES):
        # Axis totals for average
        xt = 0
        zt = 0

        # Read in data from OpenBCI
        for i in range(0, cluster_size + 1):
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes

            acc_dict = json.loads(data)
            x, z = self.get_axis_values(acc_dict)
            xt += x
            zt += z

        # Axis averages
        xa = xt / cluster_size
        za = zt / cluster_size

        if print_cluster:
            print('x_avg: {}, z_avg: {}'.format(xa - 1, za - 1))

        return xa, za

    def run_calibration(self, sock):
        # Calibration: get mins and maxes for each axis
        print('Calibrating...')
        avgs = self.get_cluster_avg(sock, config.NUM_CALIBRATION_POINTS)
        print('Calibration Complete')
        return avgs

    @staticmethod
    def calc_dominant_axis(x_ra, z_ra, calibration_data):
        x_delta = (x_ra - calibration_data['x_avg']) / calibration_data['x_avg']
        z_delta = (z_ra - calibration_data['z_avg']) / calibration_data['z_avg']

        deltas = [abs(x_delta), abs(z_delta)]

        dominant = deltas.index(max(deltas))  # 0 if x, 1 if z

        return 'x' if dominant == 0 else 'z'

    @staticmethod     # Returns Voltage To 2 Motors
    def get_axis_percentage(dominant_axis, x_ra, z_ra, calibration_data):
        # if x axis is dominant (roll)
        dom_delta, sub_delta = 0, 0

        if dominant_axis == 'x':
            if x_ra > calibration_data['x_max']:
                dom_delta = x_ra - calibration_data['x_max']
                # print(config.MOVE_LEFT_MSG)
            elif x_ra < calibration_data['x_min']:
                dom_delta = x_ra - calibration_data['x_min']
                # print(config.MOVE_RIGHT_MSG)
            else:
                pass
                # print(config.CONTINUE_MSG)
            if z_ra > calibration_data['z_max']:
                sub_delta = z_ra - calibration_data['z_max']
                # print(config.MOVE_FORWARD_MSG)
            elif z_ra < calibration_data['z_min']:
                sub_delta = z_ra - calibration_data['z_min']
                # print(config.MOVE_BACKWARD_MSG)
            else:
                pass

        # if z axis is dominant (tilt)
        elif dominant_axis == 'z':
            if z_ra > calibration_data['z_max']:
                dom_delta = z_ra - calibration_data['z_max']
                # print(config.MOVE_FORWARD_MSG)
            elif z_ra < calibration_data['z_min']:
                dom_delta = z_ra - calibration_data['z_min']
                # print(config.MOVE_BACKWARD_MSG)
            else:
                pass
                # print(config.CONTINUE_MSG)
            if x_ra > calibration_data['x_max']:
                sub_delta = x_ra - calibration_data['x_max']
                # print(config.MOVE_LEFT_MSG)
            elif x_ra < calibration_data['x_min']:
                sub_delta = x_ra - calibration_data['x_min']
                # print(config.MOVE_RIGHT_MSG)
            else:
                pass

        # Dom axis: x or z, sign, delta

        dom_delta *= config.DOM_DELTA_MULT
        sub_delta *= config.SUB_DELTA_MULT

        if dom_delta > 1:
            dom_delta = 1
        elif dom_delta < -1:
            dom_delta = -1

        if sub_delta > 1:
            sub_delta = 1
        if sub_delta < -1:
            sub_delta = -1

        sub_magnitude = abs(sub_delta / dom_delta) if dom_delta != 0 else 0
        if sub_delta != 0:
            sub_magnitude *= -1

        x_mag = dom_delta if 'x' is dominant_axis else sub_magnitude
        z_mag = dom_delta if 'z' is dominant_axis else sub_magnitude * -1

        if x_mag != 0:
            x_mag *= -1

        # TODO: It appears that when the dominant axis goes from z to x, the z percentage flips to negative
        #       It returns to positive when the tilt increases again.
        #       Might just be negative as soon as there is a non-zero roll value
        #       I THINK when z is the sub, it is negative
        #       I THINK line 123 acts as a temporary patch to this error.
        #       BACK LEFT still broken
        return round(x_mag, 3), round(z_mag, 3)

    def run(self):
        accel_socket = socket.socket(socket.AF_INET,  # Internet
                                     socket.SOCK_DGRAM)  # UDP
        accel_socket.bind((config.UDP_IP, config.UDP_ACCEL_PORT))

        context = zmq.Context()
        output_socket = context.socket(zmq.PAIR)
        output_socket.connect('tcp://{}:{}'.format(config.OUTPUT_IP, config.OUTPUT_PORT))

        # Calibration Test to determine deadzone
        x_avg, z_avg = self.run_calibration(accel_socket)
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
            x_ra, z_ra = self.get_cluster_avg(accel_socket)  # Rolling averages for live clusters
            dominant = self.calc_dominant_axis(x_ra, z_ra, axis_ranges)
            x_percentage, z_percentage = self.get_axis_percentage(
                dominant, x_ra, z_ra, axis_ranges)

            if config.OUTPUT_DATA:
                dict = {
                    'tilt': z_percentage,
                    'roll': x_percentage
                }
                send_json = json.dumps(dict)
                output_socket.send_json(send_json)

                if config.PRINT_OUT:
                    print(send_json)


if __name__ == '__main__':
    interpreter = HeadTiltInterpreter()
    interpreter.run()

