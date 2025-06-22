import os


class Scanner:
    """
    Scans a location to discover workflows
    """

    FILENAME = "ktests.yaml"

    def __init__(self, location: str) -> None:
        self._location = location

    @property
    def location(self):
        """
        Return the location this scanner works on
        """
        return self._location

    def scan(self):
        """
        Scan the location
        """
        specs = []
        for root, dirs, files in os.walk(self._location):
            if Scanner.FILENAME in files:
                specs.append(os.path.join(root, Scanner.FILENAME))
        return specs
