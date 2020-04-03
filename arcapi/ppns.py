from arcapi import config
import compose
import dbm


class PpnDB(compose.Struct):
    db = ...
    curkey = None

    @classmethod
    def frompath(cls, dbpath):
        return cls(dbm.open(str(dbpath), "c"))

    def __getitem__(self, key):
        return self.db[key].decode()

    def __setitem__(self, key, value):
        self.db[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __next__(self):
        while True:
            if not self.curkey:
                ppn = self.db.firstkey()
            else:
                ppn = self.db.nextkey(self.curkey)
            self.curkey = ppn
            if not ppn:
                return next(self)
            if not self[ppn]:
                return ppn.decode()

    def __iter__(self):
        return self


ppns = PpnDB.frompath(config.project_dir / "ppns.dbm")
