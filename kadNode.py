import threading
from random import randint
from const import *
import logging

class KadNode:
    def __init__(self, id, server, capacity, vsNum):
        self.id = id
        self.server = server                                    # instance of directory Server
        self.vsNum = vsNum                                      # num of vs
        self.nextId = vsNum
        self.totalLoad = 0.0
        self.loads = {i:0 for i in range(vsNum)}              #{vs id : load}
        self.capacity = capacity                                # node's capacity
        self.InitLogger()
        self.Churn()
        self.Upload()

    def InitLogger(self):
        self.logger = logging.getLogger('KadNode'+str(self.id))
        self.logger.setLevel(level=logging.DEBUG)
        handler = logging.FileHandler('KadNode'+str(self.id)+'.log', mode='w')
        handler.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    # upload node's current load
    def Upload(self):
        self.totalLoads = 0.0
        log_info = ""
        for k,v in self.loads.items():
            self.totalLoads += v
            log_info += str(k) + ' : ' + str(v) + ' , '
        self.server.CollectLoad(self.id, self.totalLoads, self.capacity)
        self.logger.info(log_info+'total : '+str(self.totalLoads)+'/'+str(self.capacity)+':%.2f'%(self.totalLoads/self.capacity))
        self.uploadJob = threading.Timer(UPLOAD_INTERVAL, self.Upload)
        self.uploadJob.start()

    # resize every vs's load
    def Churn(self):
        self.logger.debug('===========Churn===========')
        for k,v in self.loads.items():
            self.loads[k] = randint(0, self.capacity/self.vsNum)
        self.churnJob = threading.Timer(CHURN_INTERVAL, self.Churn)
        self.churnJob.start()

    # called by directoryServer
    # recver : to whom load transfer
    # load : how much load to transfer
    # aver_e : average deviation rate of network
    # max_e : max deviation rate of network for normal(not overload) node
    def TransferLoad(self, recver, load):
        self.logger.debug('Transfer to node'+str(recver.id)+' load '+ str(load))
        targetVs, tip = self.FindOptimalVs(load)
        if targetVs != None:
            transferLoad = self.loads[targetVs]
            self.totalLoad -= transferLoad
            self.vsNum -= 1
            del(self.loads[targetVs])
            recver.AddLoad(transferLoad, tip, self)

    # return optimal vs which load is lt and closest to load
    def FindOptimalVs(self, load):
        target = None        # target vs id
        optimalLoad = None   # target vs load
        minLoad = None       # min vs load
        minId = None         # min vs load's id
        for k,v in self.loads.items():
            if minLoad == None or v < minLoad:
                minId = k
                minLoad = v
            if v > load:
                continue
            if target == None or load-v < load-optimalLoad:
                target = k
                optimalLoad = v

        if target == None:
            target = minId
            optimalLoad = minLoad

        tip = optimalLoad-load
        return target, tip

    # called by other kadNode
    def AddLoad(self, load, out, sender):
        self.totalLoad += load
        self.vsNum += 1
        self.loads[self.nextId] = load
        self.nextId += 1
        if out > 0:
            targetVs, tip = self.FindOptimalVs(out)
            if tip <= 0:
                self.logger.debug('Compensate to node' + str(sender.id) + ' load ' + str(out+tip))
                sender.AddLoad(out+tip, tip, self)


if __name__ == '__main__':
    node0 = KadNode(0, None, 100, 2)
    node1 = KadNode(1, None, 200, 2)
    node0.TransferLoad(node1, 10)





