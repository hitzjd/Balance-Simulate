import json
from random import randint

class CreateNodes:
    def __init__(self, size):
        self.data = {}
        self.size = size
        self.maxCap = 2000
        self.minCap = 100

    def create(self):
        nodes = []
        totalCapacity = 0
        minCapacity = self.maxCap
        for i in range(self.size):
            node = {}
            node['id'] = i
            capacity = randint(self.minCap,self.maxCap)
            if capacity < minCapacity:
                minCapacity = capacity
            totalCapacity += capacity
            node['capacity'] = capacity
            nodes.append(node)

        for node in nodes:
            node['vsNum'] = node['capacity']/minCapacity
        self.data["nodes"] = nodes
        with open('nodes.json', 'w') as f:
            json.dump(self.data, f, indent=4)


if __name__ == '__main__':
    cn = CreateNodes(10)
    cn.create()





