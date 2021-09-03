# beacon2map

beacon2map is a visual aid for keeping track of location markers in 3D space.

Coordinates in x & y are calculated from readings of distance, depth and bearing to a central reference beacon. Markers hold names and descriptions and can be filtered in a variety of ways. They can be added, edited or deleted from inside the application and are saved to a JSON file.

This app was designed as an exploration aid for the video game Subnautica, which by design doesn't include a map. It complements, rather than interferes with, the exploration of the game world.

Requirements: Qt6 (PySide6)

![beacon2map](https://github.com/Merkwurdichliebe/beacon2map/blob/master/img/beacon2map-screen.jpg?raw=true)

Valid marker types are: pod, wreck, biome, interest, alien and default. Currently only limited error checking or data validation is performed on the JSON file.