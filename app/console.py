class Console:
    def print(self, *args, end='\n', **kwargs):
        if args:
            print(*args, end=end)
        else:
            print(end=end)
