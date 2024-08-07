from scipy.spatial.distance import euclidean
import numpy as np
 
class BaseStation:
    def __init__(self, location):
        """
        The initialization for basestation
        :param location: the coordinate of a basestation
        """
        # controlling timeline
        self.env = None
        self.id = 0
        # include all components in our network
        self.net = None

        self.location = np.array(location)
        self.monitored_target = []
        self.direct_nodes = []

    def probe_neighbors(self):
        self.direct_nodes.clear()
        for node in self.net.listNodes:
            if euclidean(self.location, node.location) <= node.com_range:
                # sửa : bs chỉ nhận gói tin từ các relay node
                if (node.__class__.__name__ == "RelayNode" or node.__class__.__name__ == "OutNode"):
                    self.direct_nodes.append(node)
                    # print(node.__class__.__name__)

    def receive_package(self, package):
        return

    def operate(self, t=1):
        self.probe_neighbors()
        while True:
            yield self.env.timeout(t)