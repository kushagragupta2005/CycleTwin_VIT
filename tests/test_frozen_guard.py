from pathlib import Path
import tempfile
import unittest
from scripts.run_frozen import acquire_once_lock
import os


class FrozenGuardTests(unittest.TestCase):
    def test_frozen_run_lock_cannot_be_acquired_twice(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'once.lock'
            os.close(acquire_once_lock(path))
            with self.assertRaises(FileExistsError): acquire_once_lock(path)
