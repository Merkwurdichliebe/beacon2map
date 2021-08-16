# beacon2map

beacon2map creates a visual map based on marker locations read from a JSON file.

The markers hold names and descriptions and are based on readings of distance, depth and bearing to a central reference beacon, and can be filtered in a variety of ways.

This app was designed as an exploration aid for the video game Subnautica.

Requirements: Qt6 (PySide6)

![beacon2map](https://github.com/Merkwurdichliebe/beacon2map/blob/master/img/beacon2map-screen.jpg?raw=true)

Valid marker types are: pod, wreck, biome, interest, alien and default. Currently only limited error checking or data validation is performed on the JSON file.