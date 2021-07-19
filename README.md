# beacon2map

beacon2map creates a visual map based on marker locations read from a CSV file.

The markers hold names and descriptions and are based on readings of distance, depth and bearing to a central reference beacon.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 and Pandas

![beacon2map](https://github.com/Merkwurdichliebe/beacon2map/blob/master/img/beacon2map-screen.jpg?raw=true)

The CSV file should reside in the same folder as the script and contain data in the following format:

![beacon2map](https://github.com/Merkwurdichliebe/beacon2map/blob/master/img/csv-screen.jpg?raw=true)

To add a new location to the CSV file:

- Place the reference beacon at the center of the aiming reticle.
- Note the heading as precisely as possible (North = 0, East = 90, South = 180; West = 270).
- Note the distance to the beacon.
- Note the current depth.
- Add a short name, a marker type and a description (optional). If the location needs to be marked as "Done", enter a lowercase 'x' in the Done column.

Valid marker types are: pod, wreck, biome, interest, alien, misc. No error checking or data validation is performed on the CSV file.
