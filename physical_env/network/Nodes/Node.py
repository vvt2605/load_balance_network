import random
import simpy
import numpy as np
from scipy.spatial.distance import euclidean
import sys
import os
sys.path.append(os.path.dirname(__file__))
from physical_env.network.Package import Package
import os


class Node:

    def __init__(self, location, phy_spe):
        self.env = None
        self.net = None
    
        self.location = np.array(location)
        self.energy = phy_spe['capacity']
        self.threshold = phy_spe['threshold']
        self.capacity = phy_spe['capacity']

        self.com_range = phy_spe['com_range']
        self.sen_range = phy_spe['sen_range']
        self.prob_gp = phy_spe['prob_gp']
        self.package_size = phy_spe['package_size']
        self.er = phy_spe['er']
        self.et = phy_spe['et']
        self.efs = phy_spe['efs']
        self.emp = phy_spe['emp']

        # energRR  : replenish rate
        self.energyRR = 0

        # energyCS: consumption rate
        self.energyCS = 0

        self.id = None
        self.level = None
        self.status = 1
        self.neighbors = []
        self.potentialSender = [] # là danh sách con của neighbors nhưng có khả năng gửi gói tin cho self
        self.listTargets = [] # danh sách các targets trong phạm vi có thể theo dõi, không tính tới việc sẽ theo dõi các targets này hay không
        self.listTotalTargets = [] # là danh sách con của target, là các target trong phạm vi nhưng nó theo dõi
        self.log = []
        self.log_energy = 0
        self.check_status()

        # self.send_cluster_idId = None
        # self.receive_cluster_idId = None

    def operate(self, t=1):
        """
        The operation of a node
        :param t:
        :returns yield t(s) to time management system every t(s)
        """
        self.probe_targets()
        self.probe_neighbors()
        while True:
            self.log_energy = 0
            # After 0.5 secs, node begin to calculate its energy and consider transmitting data
            yield self.env.timeout(t * 0.5)
            if self.status == 0:
                break
            self.energy = min(self.energy + self.energyRR * t * 0.5, self.capacity)
            if random.random() < self.prob_gp:
                self.generate_packages()

            # After another 0.5 secs (at the end of the second), node recalculate its energy
            yield self.env.timeout(t * 0.5)
            if self.status == 0:
                break
            self.energy = min(self.energy + self.energyRR * t * 0.5, self.capacity)

            len_log = len(self.log)
            if len_log < 10:
                self.log.append(self.log_energy)
                self.energyCS = (self.energyCS * len_log + self.log_energy) / (len_log + 1)
            else:
                self.energyCS = (self.energyCS * len_log - self.log[0] + self.log_energy) / len_log
                del self.log[0]
                self.log.append(self.log_energy)
        return

    def probe_neighbors(self):
        self.neighbors.clear()
        for node in self.net.listNodes:
            if self != node and euclidean(node.location, self.location) <= self.com_range:
                self.neighbors.append(node)

    def probe_targets(self):
        self.listTargets.clear()
        # bổ sung 2 list target là các list target xung quanh (list total target) và list target theo dõi (list target)
        for target in self.net.listTargets:
            if euclidean(self.location, target.location) <= self.sen_range:
                self.listTotalTargets.append(target)
                if target.is_active == 0:
                    self.listTargets.append(target)
                    target.is_active = 1

    def generate_packages(self):
        for target in self.listTargets:
            self.send_package(Package(target.id, self.package_size))

    def send_package(self, package):
        d0 = (self.efs / self.emp) ** 0.5
        if euclidean(self.location, self.net.baseStation.location) > self.com_range:
            receiver = self.find_receiver()
        else:
            receiver = self.net.baseStation
        if receiver is not None:
            d = euclidean(self.location, receiver.location)
            e_send = ((self.et + self.efs * d ** 2) if d <= d0
                      else (self.et + self.emp * d ** 4)) * package.package_size
            
            
            if self.energy - self.threshold < e_send:
                self.energy = self.threshold
            else:
                self.energy -= e_send
                receiver.receive_package(package) #
                self.log_energy += e_send
        # else: 
        #     print(self.location)
        # print(self.id,receiver.id,self.location)
        self.check_status()


    def find_receiver(self):
        pass

    def receive_package(self, package):
        e_receive = self.er * package.package_size
        if self.energy - self.threshold < e_receive:
            self.energy = self.threshold
        else:
            self.energy -= e_receive
            self.send_package(package) #
            self.log_energy += e_receive
        self.check_status()

    # def charger_connection(self, mc):
    #     if self.status == 0:
    #         return
    #     tmp = mc.alpha / (euclidean(self.location, mc.location) + mc.beta) ** 2
    #     self.energyRR += tmp
    #     mc.chargingRate += tmp

    # def charger_disconnection(self, mc):
    #     if self.status == 0:
    #         return
    #     tmp = mc.alpha / (euclidean(self.location, mc.location) + mc.beta) ** 2
    #     self.energyRR -= tmp
    #     mc.chargingRate -= tmp

    def check_status(self):
        if self.energy <= self.threshold:
            self.status = 0
            self.energyCS = 0
