## Stepper_Motor_Control
### `Master_serial_sender.py`
- The program count the waiting time from user specified function and send control messages to the Arduino (`AVR_serial_FSM.c`).
### `AVR_serial_FSM.c`
- It's a Finite State Machine for sending the input signals to make the stepper motor rotate in a specific way.
- State Diagram of the Arduino: ![](./FSM_diagram.png)
- Configuration of Output Sequences (True Value Table of the Motor): ![](./step-true-value.png)
