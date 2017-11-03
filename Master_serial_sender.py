import serial
import struct
import time
import math
BUAD = 2000000
PATH = "/dev/tty.usbmodem1411"
TIME_OUT = None
class AVR_Motion_Descriptor(object): # Motor time control
    """ AVR_Motion_Descriptor would construct a list from user-described motion.
        The list is composed by waiting time at each step.
        The waiting times are obtained by transfering X(t) to T(x).
        Then get time info from every 'x' sperated by a fixed interval that imply
        the step angle of the stepper motor.
        """
    def __init__(self):
        super(AVR_Motion_Descriptor, self).__init__()
        self.UINT = "SI, Kg-m-sec-degree"
        self.step_angle = 3.6 # The angle of rotation for each step in degree
        self.pitch = 0.02     # The pitch length of the rotating pole connected to the stroke
        self.single_step_length = self.pitch*self.step_angle/360.0
        self.pi = math.pi
        self.status = "None"
    def Set_step_angle(self,step_angle):
        self.step_angle = step_angle
        self.single_step_length = self.pitch*self.step_angle/360.0
    def Set_pitch(self, pitch):
        self.pitch = pitch
        self.single_step_length = self.pitch*self.step_angle/360.0

    def sine(self, stroke, omega, delta):
        """ X(t) = stroke*sin(omega*t + delta)
            inv(X(t)) = T(x) = (asin(x/stroke) - delta)/omega"""
        # self.sine_stroke = stroke
        # self.sine_omega = omega
        # self.sine_delta = delta
        listlen = 2*math.floor(stroke/self.single_step_length)
        func = lambda x: (math.asin(x/stroke) - delta)/omega
        self.T_list = []
        x_cur = -stroke
        for i  in range(0,listlen):
            x_cur += self.single_step_length
            self.T_list.append(func(x_cur))
            pass
        self.Wait_list = []
        T_last = self.T_list[0]
        for T_cur in self.T_list[1:]:
            self.Wait_list.append(["F",T_cur - T_last])
            T_last = T_cur
        T_last = self.T_list[0]
        for T_cur in self.T_list[1:]:
            self.Wait_list.append(["B",T_cur - T_last])
            T_last = T_cur



class AVR_State_Controler(AVR_Motion_Descriptor): # Motor event control
    """ AVR_State_Controler send control message to the Arduino FSM on a serial port."""
    def __init__(self, PORT, BUADRATE, timeout=None, name="Untitled AVR MOTOR"):
        super(AVR_State_Controler, self).__init__()
        print("Constructing a serial comunication at port %s with buadrate = %d bps" %(PORT, BUADRATE))
        self.serial = serial.Serial(PORT,BUADRATE,timeout=timeout)
        self.rotate = {'F':struct.pack('B',255),'B':struct.pack('B',0)}
        while True:
            ready = self.serial.read()
            if not struct.unpack('B',ready)[0]:
                print(name,'[Online]')
                break # MOTOR READY
    def wait(self,current_perf,delta_time,rotation): # single step control
        while time.perf_counter() - current_perf <= delta_time: # busy wait
            pass
        self.serial.write(self.rotate[rotation])
    def stop(self): # single step control
        #cut off the current flowing over the motor
        self.wait(time.perf_counter(),0.001,'B')
        self.serial.write(struct.pack('B',85))
    def resume(self): # single step control
        self.serial.write(self.rotate['F'])
    def close(self):
        self.stop()
        self.serial.close()
    def motion(self,wait_list):# continuous step control
        for timmer in wait_list:
            timmer_start = time.perf_counter()

            rotation = timmer[0]
            wait_time = timmer[1]

            self.serial.write(self.rotate[rotation])

            timmer_spent = time.perf_counter() - timmer_start
            while timmer_spent <= wait_time: # wait until time arrive
                timmer_spent = time.perf_counter() - timmer_start # update time spent




#INITIALIZE
arduino = AVR_State_Controler(PATH,BUAD,timeout=TIME_OUT,name="AVRMOTOR0")
###########


control_msg = '''Please Specify an Action of the MOTOR:
             \r[F]   : Forward motion with an uniform speed
             \r[B]   : Backward motion with an uniform speed
             \r[S]   : Generate a solitary wave
             \r[Sin] : Generate a sin wave
             \r[User]: User define function(x(t))
             \r[X]   : STOP the motor'''
while True:
    #CONTROL SIGNAL SELECT
    arduino.stop()
    while True:
        print(control_msg)
        control_signal = input("")
        if control_signal == "F" or\
           control_signal == "B" or\
           control_signal == "S" or\
           control_signal == "Sin" or\
           control_signal == "User" or\
           control_signal == "X":
            print("[%s] selected" % control_signal)
            break
    ######################

    #DO JOBs
    if control_signal == "F" or control_signal == "B":
        while True:
            try:
                speed = float(input("For uniform speed motion, please specify a positive speed: "))
                print("speed = %f,\nInsert a keyboard interrupt if you wish to stop the motor" % speed)
                arduino.resume()
                while True:
                    current_time = time.perf_counter()
                    arduino.wait(current_time,speed,control_signal)
                    pass
            except ValueError:
                print("[ERROR] unrecognized speed\n")
                arduino.stop()
            except KeyboardInterrupt:
                print("\nSTOPPING CURRENT MOTOR EVENT\n")
                arduino.stop()
                break
            else:
                print("[ERROR] unexpected error\nSTOPPING PROGRAM")
                arduino.close()
                raise

    elif control_signal == "Sin":
        while True:
            try:
                print("X(t) = (Half Stroke) * sin(omega * t + delta)")
                half_Stroke = float(input("Please specify:\nHalf Stroke:"))
                omega = float(input("omega(radius):"))
                delta = float(input("delta(radius):"))
                print("Creating signal set")
                arduino.sine(half_Stroke, omega, delta)
                print("Ready, Insert a keyboard interrupt if you wish to stop the motor")
                arduino.resume()
                while True:
                    arduino.motion(arduino.Wait_list)
            except ValueError:
                print("[ERROR] unrecognized inputs\n")
                arduino.stop()
            except KeyboardInterrupt:
                print("\nSTOPPING CURRENT MOTOR EVENT\n")
                arduino.stop()
                break
            else:
                print("[ERROR] unexpected error\nSTOPPING PROGRAM")
                arduino.stop()
                arduino.close()
                raise
    elif control_signal == "X":
        arduino.stop()
        arduino.close()
        break
    #######
