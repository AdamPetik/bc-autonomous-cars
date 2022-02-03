class UniqueID:
    counter = 0

    def getId(self):
        UniqueID.counter = UniqueID.counter + 1
        return UniqueID.counter
