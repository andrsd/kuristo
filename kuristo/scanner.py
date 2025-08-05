import os
from pathlib import Path
import kuristo.config as config


class Scanner:
    """
    Scans a location to discover workflows
    """

    def __init__(self, location: str) -> None:
        self._location = location
        cfg = config.get()
        self._workflow_filename = cfg.workflow_filename

    @property
    def location(self):
        """
        Return the location this scanner works on
        """
        return self._location

    def scan(self) -> list[Path]:
        """
        Scan the location
        """
        specs = []
        for root, dirs, files in os.walk(self._location):
            if self._workflow_filename in files:
                specs.append(Path(os.path.join(root, self._workflow_filename)))
        return specs


def scan_locations(locations) -> list[Path]:
    """
    Scan the locations for the workflow files
    """
    workflow_files = []
    for loc in locations:
        if os.path.isdir(loc):
            scanner = Scanner(loc)
            workflow_files.extend(scanner.scan())
        elif os.path.isfile(loc):
            workflow_files.append(Path(loc))
        else:
            raise RuntimeError(f"No such file or directory: {loc}")
    return workflow_files
