# Crumblepy
# Installation
Install the required packages:
```
pip install -r requirements.txt
```
Connect your Crumble controller via USB, connect a wire from the C output on the controller 
to the Red input on the Traffic component and a wire from the - (gnd) on the controller to the - (gnd) on the component.

Run the most basic test program:
```
python crumble_basic.py
```
If everything was done correctly, the red LED will light up on the component for 3 seconds and then turn off. 