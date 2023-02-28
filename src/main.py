from vex import *
import time

left_wheel_1 = Motor(Ports.PORT1, GearSetting.RATIO_6_1, True)
left_wheel_2 = Motor(Ports.PORT2, GearSetting.RATIO_6_1, True)
left_wheel_3 = Motor(Ports.PORT3, GearSetting.RATIO_6_1, False)
left_wheels = MotorGroup(left_wheel_1, left_wheel_2, left_wheel_3)

right_wheel_1 = Motor(Ports.PORT4, GearSetting.RATIO_6_1, False)
right_wheel_2 = Motor(Ports.PORT5, GearSetting.RATIO_6_1, False)
right_wheel_3 = Motor(Ports.PORT6, GearSetting.RATIO_6_1, True)
right_wheels = MotorGroup(left_wheel_1, left_wheel_2, left_wheel_3)

brain = Brain()
controller = Controller()
inertial_sensor = Inertial(Ports.PORT7)
distance_sensor = Distance(Ports.PORT13)
optical_sensor = Optical(Ports.PORT14)
drivetrain = SmartDrive(left_wheels, right_wheels, inertial_sensor)
flywheel = Motor(Ports.PORT12, GearSetting.RATIO_6_1)
intake = Motor(Ports.PORT11, GearSetting.RATIO_6_1)
indexer = DigitalOut(brain.three_wire_port.a)
auton_selector = Bumper(brain.three_wire_port.b)
expansion = DigitalOut(brain.three_wire_port.c)

class Robot():
    def __init__(self):
        Competition(self.driver_controlled, self.auton)

        self.DRIVE_MULTIPLER = 1
        self.TURN_MULTIPLER = 1
        self.target_heading = 0
        self.is_turn_pid_active = False

        self.FLYWHEEL_FAR = 390
        self.FLYWHEEL_CLOSE = 360 # prev 335
        self.FLYWHEEL_OFF = 0
        self.FLYWHEEL_SPEED_DIFFERENCE = 20
        self.MAX_LAUNCHES = 45
        self.IS_BUMP_ACTIVE = True
        self.flywheel_speed = 0
        self.is_pid_active = True
        self.remaining_launches = int(self.MAX_LAUNCHES)

        self.selected_auton = 0
        self.autons = [
            {'name': 'LEFT SINGLE', 'action': self.left_single}, 
            {'name': 'LEFT DOUBLE', 'action': self.left_double}, 
            {'name': 'PROG SKILLS', 'action': self.prog_skills},
            {'name': 'NO AUTON', 'action': self.no_auton},
        ]

        self.pre_auton()

    # auton

    def pre_auton(self):
        auton_selector.pressed(self.select_auton)

        drivetrain.set_stopping(COAST)

        inertial_sensor.calibrate()
        while inertial_sensor.is_calibrating():
            wait(0.1, SECONDS)
        inertial_sensor.set_heading(0, DEGREES)

        print('Ready')

        Thread(self.update_brain)

        while True:
            optical_sensor.set_light(100)
            color = optical_sensor.
            print(color)

            if distance_sensor.is_object_detected():
                distance = round(distance_sensor.object_distance(INCHES), 1)

            wait(0.5, SECONDS)

    def driver_controlled(self):
        controller.axis1.changed(self.on_controller_changed)
        controller.axis3.changed(self.on_controller_changed)

        controller.buttonL1.pressed(self.intake_forward)
        controller.buttonL1.released(self.intake_off)
        controller.buttonL2.pressed(self.intake_reverse)
        controller.buttonL2.released(self.intake_off)
        controller.buttonR1.pressed(self.launch)
        controller.buttonRight.pressed(self.flywheel_far)
        controller.buttonUp.pressed(self.flywheel_close)
        controller.buttonDown.pressed(self.flywheel_off)
        controller.buttonX.pressed(self.expand)

        # self.flywheel_close()
        # Thread(self.flywheel_pid)
        # Thread(self.drivetrain_pid)

        # drivetrain.drive_for(FORWARD, 24, INCHES, 25, PERCENT)

    def _move(self, distance, velocity):
        drivetrain.drive_for(FORWARD, distance, INCHES, velocity, PERCENT)

    def _turn(self, heading, velocity):
        drivetrain.turn_to_heading(heading, DEGREES, velocity, PERCENT)

    def _intake(self, duration):
        intake.spin_for(FORWARD, duration, SECONDS, 100, PERCENT)

    def left_single(self):
        pass

    def left_double(self):
        pass

    def prog_skills(self):
        pass

    def no_auton(self):
        pass

    def auton(self):
        start_time = time.time()
        self.autons[self.selected_auton]['action']()
        auton_duration = time.time() - start_time
        print('Auton Elapsed Duration: {} sec'.format(auton_duration))

    def select_auton(self):
        if self.selected_auton == len(self.autons) - 1:
            self.selected_auton = 0
        else:
            self.selected_auton += 1

    # control

    def turn_pid(self):
        inertial_sensor.calibrate()
        while inertial_sensor.is_calibrating():
            wait(0.1, SECONDS)
        inertial_sensor.set_heading(0, DEGREES)

        Kp = 0.3
        Ki = 0.0000001
        Kd = 0.25

        last_error = 0
        total_error = 0

        self.target_heading = 180
        self.is_turn_pid_active = True

        headings = []
        for second in range(30):
            wait(0.1, SECONDS)

            heading = round(inertial_sensor.heading(DEGREES), 1)

            error = self.target_heading - heading
            total_error += error
            derivative = error - last_error
            power = (error * Kp) + (total_error * Ki) + (derivative * Kd)
            last_error = error

            headings.append(heading)

            left_wheel_1.spin(FORWARD, power, VOLT)
            left_wheel_2.spin(FORWARD, power, VOLT)
            left_wheel_3.spin(FORWARD, power, VOLT)
            right_wheel_1.spin(FORWARD, -power, VOLT)
            right_wheel_2.spin(FORWARD, -power, VOLT)
            right_wheel_3.spin(FORWARD, -power, VOLT)

        drivetrain.stop(COAST)
        print(*headings)

    def drivetrain_pid(self):
        Kp = 0.8
        Ki = 0
        Kd = 0

        last_error = 0
        total_error = 0

        self.target_distance = 24

        distances = []
        for second in range(30):
            wait(0.1, SECONDS)

            l1 = left_wheel_1.position(DEGREES)
            l3 = left_wheel_3.position(DEGREES)
            r2 = right_wheel_2.position(DEGREES)
            r3 = right_wheel_3.position(DEGREES)
            average_position = (l1 + l3 + r2 + r3) / 4
            distance = round(average_position * 0.02, 1)

            error = self.target_distance - distance
            total_error += error
            derivative = error - last_error
            power = (error * Kp) + (total_error * Ki) + (derivative * Kd)
            last_error = error

            distances.append(distance) ####

            print(power)
            left_wheel_1.spin(FORWARD, power, VOLT)
            left_wheel_2.spin(FORWARD, power, VOLT)
            left_wheel_3.spin(FORWARD, power, VOLT)
            right_wheel_1.spin(FORWARD, power, VOLT)
            right_wheel_2.spin(FORWARD, power, VOLT)
            right_wheel_3.spin(FORWARD, power, VOLT)

        drivetrain.stop(COAST)
        print(*distances)

    def intake_forward(self):
        intake.set_max_torque(100, PERCENT)
        intake.spin(FORWARD, 12, VOLT)

    def intake_reverse(self):
        intake.set_max_torque(100, PERCENT)
        intake.spin(REVERSE, 12, VOLT)

    def intake_off(self):
        intake.stop(COAST)

    def launch(self):
        self.remaining_launches -= 1
        indexer.set(True)
        
        if self.IS_BUMP_ACTIVE == True:
            self.is_pid_active = False
            flywheel.spin(FORWARD, 12, VOLT)

        wait(0.15, SECONDS)
        indexer.set(False)

        # bump
        wait(0.15, SECONDS)
        self.is_pid_active = True

    def expand(self):
        expansion.set(True)
        controller.rumble('-')

    def on_controller_changed(self):
        x_power = controller.axis1.position() * self.TURN_MULTIPLER
        y_power = controller.axis3.position() * self.DRIVE_MULTIPLER

        left_wheel_1.spin(FORWARD, (y_power + x_power) / 12, VOLT)
        left_wheel_2.spin(FORWARD, (y_power + x_power) / 12, VOLT)
        left_wheel_3.spin(FORWARD, (y_power + x_power) / 12, VOLT)
        right_wheel_1.spin(FORWARD, (y_power - x_power) / 12, VOLT)
        right_wheel_2.spin(FORWARD, (y_power - x_power) / 12, VOLT)
        right_wheel_3.spin(FORWARD, (y_power - x_power) / 12, VOLT)

    # flywheel

    def flywheel_far(self):
        self.flywheel_speed = self.FLYWHEEL_FAR

    def flywheel_close(self):
        self.flywheel_speed = self.FLYWHEEL_CLOSE

    def flywheel_off(self):
        self.flywheel_speed = 0

    def flywheel_pid(self):
        Kp = 0.05
        Ki = 0.003
        Kd = 0

        last_error = 0
        total_error = 0

        while True:
            velocity = round(flywheel.velocity(RPM))

            error = self.flywheel_speed - velocity
            total_error += error
            derivative = error - last_error
            power = (error * Kp) + (total_error * Ki) + (derivative * Kd)
            last_error = error

            if self.flywheel_speed == 0:
                flywheel.stop(COAST)
            else:
                flywheel.spin(FORWARD, power, VOLT)

            wait(0.1, SECONDS)

    # brain

    def update_brain(self):
        while True:
            brain.screen.clear_screen()
            brain.screen.set_cursor(1, 1)
            brain.screen.set_font(FontType.MONO30)

            flywheel_velocity = flywheel.velocity(RPM)
            is_flywheel_ready = abs(flywheel_velocity - self.flywheel_speed) <= self.FLYWHEEL_SPEED_DIFFERENCE
            brain.screen.draw_rectangle(0, 0, 480, 240, is_flywheel_ready and Color.CYAN or Color.BLACK)

            values = [
                ['Drivetrain: ', drivetrain.temperature(PERCENT), 70, Color.YELLOW, Color.GREEN],
                ['Intake: ', intake.temperature(PERCENT), 70, Color.RED, Color.GREEN],
                ['Flywheel: ', flywheel.temperature(PERCENT), 70, Color.RED, Color.GREEN],
                ['Air', self.remaining_launches / self.MAX_LAUNCHES * 100, 15, Color.GREEN, Color.RED],
                ['Battery: ', brain.battery.capacity(), 20, Color.GREEN, Color.RED],
            ]

            for value in values:
                brain.screen.set_pen_color(value[1] >= value[2] and value[3] or value[4])
                brain.screen.print(value[0], round(value[1]))
                brain.screen.next_row()

            auton = self.autons[self.selected_auton]['name']
            brain.screen.set_pen_color(Color.WHITE)
            brain.screen.set_font(FontType.MONO60)
            brain.screen.print(auton)

            wait(0.25, SECONDS)

if __name__ == '__main__':
    Robot()