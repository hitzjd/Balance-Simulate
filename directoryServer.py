import threading
from const import *
from kadNode import KadNode
import json
import logging

class InconsistentException(Exception):
    pass

class DirectoryServer:
    def __init__(self, k=2):
        self.k = k
        self.nodes = {}         # {id : instance of KadNode}
        self.loads = {}
        self.capacitys = {}
        self.bias = {}           # load/capacity  {id : bias}
        self.transferLoad = {}   # load need to transfer {id : load}
        self.totalLoads = 0.0
        self.totalCapacitys = 0.0
        self.deviationTable = None
        self.averBias = 0.0
        self.threshold = 0.0
        self.InitLogger()
        self._load()


    def InitLogger(self):
        self.logger = logging.getLogger('DirectoryServer')
        self.logger.setLevel(level=logging.DEBUG)
        handler = logging.FileHandler('DirectoryServer.log', mode='w')
        handler.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _load(self):
        with open('nodes.json', 'r') as load_f:
            json_dict = json.load(load_f)
        nodes = json_dict["nodes"]
        for node in nodes:
            self.nodes[node['id']] = KadNode(node['id'], self, node['capacity'], node['vsNum'])
        self.balanceJob = threading.Timer(5.0, self.startJob)
        self.balanceJob.start()

    def startJob(self):
        self.CalcuTransferLoad()
        self.DoTransfer()
        self.balanceJob = threading.Timer(BALANCE_INTERVAL, self.startJob)
        self.balanceJob.start()

    def CollectLoad(self, id, load, capacity):
        self.loads[id] = load
        self.capacitys[id] = capacity
        self.bias[id] = load/capacity
        self.totalLoads += load
        self.totalCapacitys += capacity

    def CalcuTransferLoad(self):
        if len(self.loads) != len(self.capacitys):
            raise InconsistentException()
        if len(self.loads) != len(self.bias):
            raise InconsistentException()

        variance = 0.0
        self.averBias = self.totalLoads/self.totalCapacitys
        if self.averBias <= 0.5:
            self.threshold = self.averBias/self.k
        else:
            self.threshold = abs(1-self.averBias)/self.k

        try:
            for id,bias in self.bias.items():
                variance += (self.averBias-bias)*(self.averBias-bias)
                if bias > self.averBias+self.threshold:
                    self.transferLoad[id] = int((bias-self.averBias-self.threshold)*self.capacitys[id])
                elif bias < self.averBias-self.threshold:
                    self.transferLoad[id] = int((bias-self.averBias+self.threshold)*self.capacitys[id])
                else:
                    self.transferLoad[id] = 0
        except:
            raise InconsistentException()
        else:
            # sort by transferLoad
            table = sorted(self.transferLoad.items(),key = lambda x:x[1],reverse = True)
            self.deviationTable = [[item[0], item[1]] for item in table]
            self.logger.info('average:%.2f threshold:%.2f variance:%.2f'%(self.averBias, self.threshold, variance))

    def DoTransfer(self):
        if not self.deviationTable:
            return

        # transferDif > 0 : transferOut > transferIn
        # transferDif < 0 : transferOut < transferIn
        transferDif = 0.0
        for item in self.deviationTable:
            transferDif += item[1]

        start = 0
        end = len(self.deviationTable)-1
        start, end = self.TraverseTable(start, end)

        if transferDif == 0:
            return
        elif transferDif > 0:
            end = len(self.deviationTable)-1
            while transferDif > 0:
                transferInId = self.deviationTable[end][0]
                if transferDif > self.threshold*self.capacitys[transferInId]:
                    self.deviationTable[end][1] =  int(-self.threshold*self.capacitys[transferInId])
                    transferDif -= self.threshold*self.capacitys[transferInId]
                    end -= 1
                else:
                    self.deviationTable[end][1] = int(-transferDif)
                    transferDif = 0
            end = len(self.deviationTable) - 1
        else:
            start = 0
            transferDif = -transferDif
            while transferDif > 0:
                transferOutId = self.deviationTable[start][0]
                if transferDif > self.threshold*self.capacitys[transferOutId]:
                    self.deviationTable[start][1] = int(self.threshold*self.capacitys[transferOutId])
                    transferDif -= self.threshold*self.capacitys[transferOutId]
                    start += 1
                else:
                    self.deviationTable[start][1] = int(transferDif)
                    transferDif = 0
            start = 0
        self.TraverseTable(start, end)

        # reset
        self.deviationTable = None
        self.totalLoads = 0.0
        self.totalCapacitys = 0.0
        self.loads.clear()
        self.capacitys.clear()
        self.bias.clear()
        self.transferLoad.clear()

    def TraverseTable(self, start, end):
        while start < end:
            transferOut = self.deviationTable[start][1]
            transferIn = self.deviationTable[end][1]
            transferOutId = self.deviationTable[start][0]
            transferInId = self.deviationTable[end][0]
            # when there is no overload or lessload node
            if transferOut == 0 or transferIn == 0:
                    break

            if transferOut+transferIn > 0:
                self.nodes[transferOutId].TransferLoad(self.nodes[transferInId], -transferIn)
                self.deviationTable[start][1] -= transferIn
                self.deviationTable[end][1] = 0
                end -= 1
            elif transferOut+transferIn < 0:
                self.nodes[transferOutId].TransferLoad(self.nodes[transferInId], transferOut)
                self.deviationTable[start][1] = 0
                self.deviationTable[end][1] += transferOut
                start += 1
            else:
                self.nodes[transferOutId].TransferLoad(self.nodes[transferInId], transferOut)
                self.deviationTable[start][1] = 0
                self.deviationTable[end][1] = 0
                start += 1
                end -= 1
        return start, end


if __name__ == '__main__':
    ds = DirectoryServer(5)

