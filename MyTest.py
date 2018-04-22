import threading

class MyTest:
    def __init__(self):
        self.timmer = threading.Timer(5, self.startJob)
        self.timmer.start()

    def startJob(self):
        self.func()
        print threading.active_count()
        timmer = threading.Timer(5, self.startJob)
        timmer.start()

    def func(self):
        print "hello world"

if __name__ == '__main__':
    t = MyTest()
