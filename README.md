# beacon2map

beacon2map creates a visual map based on marker locations read from a CSV file.

The markers hold names and descriptions and are based on readings of distance, depth and bearing to a central reference beacon.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 and Pandas

![beacon2map](https://github.com/Merkwurdichliebe/beacon2map/blob/master/img/beacon2map-screen.jpg?raw=true)

The CSV file should reside in the same folder as the script and contain data in the following format:

![beacon2map](https://github.com/Merkwurdichliebe/beacon2map/blob/master/img/csv-screen.jpg?raw=true)

Valid marker types are: pod, wreck, biome, interest, alien, misc. No error checking or data validation is performed on the CSV file.
