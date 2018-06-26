## Usage
### Requirement
TODO: clearify
`python-dateutil`


### Scripts

TODO: Auth for route-scripts

#### Run route
You can load a GPX and walk along it.
To do so, call
`./run_sim.py -i <ip> -p <port> -g <filepathTo.gpx> -s <speedInKmh>`

#### Run A to B
To simply walk from A to B, call
`./run_a_to_b.py -i <ip> -p <port> -c "startLat,startLng" -d "destLat,destLng" -s <speedInKmh>`