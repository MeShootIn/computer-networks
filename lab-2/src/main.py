from math import inf
import random

import matplotlib.pyplot as plt
import numpy as np

max_num = 5

class Topology:
    def __init__(self, num):
        self.num = num
        self.points = []
        self.build(num)

    def dist(self, i, j):
        dist = ((self.points[i][0] - self.points[j][0])**2 + (self.points[i][1] - self.points[j][1])**2)**0.5
        return round(dist, 5)

    def build(self, num):
        pass


def buildRing(num):
    points = []
    angles = np.linspace(np.pi / 2, 2 * np.pi+np.pi/2 , num, endpoint=False)
    for a in angles:
        x = max_num * np.cos(a)
        y = max_num * np.sin(a)
        points.append([x, y])
    return points


class TopologyLine(Topology):
    def build(self, num):
        coords = np.linspace(-max_num, max_num, num)
        for coord in coords:
            self.points.append([coord, coord])

    def deleteMid(self):
        del self.points[int(self.num / 2)]

class TopologyRing(Topology):
    def build(self, num):
        self.points = buildRing(num)

    def deleteMid(self):
        del self.points[int(self.num / 2)]

class TopologyStar(Topology):
    def build(self, num):
        self.points = buildRing(num-1)
        self.points.append([0,0])

    def deleteMid(self):
        self.points.pop()


class Network():
    def __init__(self, topology, communication_rad):
        self.topology = topology
        self.communication_rad = communication_rad
        self.communication = []
        self.build_communication()

    def build_communication(self):
        points = self.topology.points
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                if self.topology.dist(i, j) <= self.communication_rad:
                    self.communication.append([i, j])
        print(self.communication)

    def draw(self, label, img_save_dst):
        points = self.topology.points
        for c in self.communication:
            p1 = points[c[0]]
            p2 = points[c[1]]
            plt.plot([p1[0], p2[0]], [p1[1], p2[1]], color='blue')
        for i in range(len(points)):
            plt.plot(points[i][0], points[i][1], 'o', color='red')
            plt.annotate(str(i), (points[i][0] - 0.2, points[i][1] + 0.2))
        plt.savefig(img_save_dst + label + '.png')
        plt.clf()

    def OSPF(self):
        all_path=[]
        for start_point in range(len(self.topology.points)):
            distances = [inf for i in range(len(self.topology.points))]
            distances[start_point] = 0
            visited = [False for i in range(len(self.topology.points))]
            path = [[] for i in range(len(self.topology.points))]
            vertex = [[start_point, 0]]
            while len(vertex)>0:
                min_dist = inf
                min_vert = -1
                for i in range(len(vertex)):
                    v = vertex[i]
                    if v[1] < min_dist:
                        min_dist = v[1]
                        min_vert = v[0]
                        min_idx = i
                del vertex[min_idx]
                if visited[min_vert]:
                    continue
                visited[min_vert] = True
                for c in self.communication:
                    if c[0] == min_vert or c[1] == min_vert:
                        w = c[1] if c[0] == min_vert else c[0]
                        dist = self.topology.dist(c[0], c[1])
                        if  distances[w] > distances[min_vert] + dist:
                            distances[w] = distances[min_vert] + dist
                            vertex.append([w, distances[w]])
                            path[w] = path[min_vert] + [min_vert]
            for i in range(len(path)):
                if distances[i] < inf:
                    path[i].append(i)
            all_path.append(path)

        for i in range(len(self.topology.points)):
            for ap in all_path:
                print(ap[i])
            print()


def start(topology, rad, delete_one):
    img_save_dst = '../docs/images/'
    label = topology.__class__.__name__

    if delete_one:
        topology.deleteMid()
        label += ' corrupted'
    net = Network(topology, rad)
    net.OSPF()
    net.draw(label, img_save_dst)


if __name__ == '__main__':
    topology = [TopologyLine(5), TopologyRing(5), TopologyStar(5)]
    rad = [5, 6, 5]

    for delete_one in [False, True]:
        for i in range(len(topology)):
            start(topology[i], rad[i], delete_one)
