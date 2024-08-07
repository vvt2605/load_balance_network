from physical_env.network.utils.clustering.kmean_plus_plus import clustering
from physical_env.network.utils.create_edges.basic import createEdges
from physical_env.network.utils.create_node_in_cluster.basic import createNodeInCluster
from physical_env.network.utils.create_node_between_cluster.basic import createNodeBetweenCluster
import warnings
warnings.filterwarnings("ignore")

class Network:
    def __init__(self, env, baseStation, listTargets ,max_time,phy):
        self.env = env
        self.baseStation = baseStation
        self.listTargets = listTargets
        self.phy = phy
        self.targets_active = [1 for _ in range(len(self.listTargets))]
        # bổ sung
        # for target in self.listTargets:
        #     target.is_active = 1

        self.alive = 1
        self.found = []
        self.Alpha = 0.8
        baseStation.env = self.env
        baseStation.net = self
        self.max_time = max_time
        it = 0

        for target in listTargets:
            target.id = it
            it += 1
        
        self.listNodes = []
        self.listClusters = []
        self.listEdges = []
        self.createNodes()
        for cluster in self.listClusters:
            for node in cluster.listNodes:
                    node.cluster_id = cluster.id

        self.num_targets_per_cluster = None
    
    def createNodes(self):
        self.listClusters = clustering(self)
        self.listEdges, self.num_targets_per_cluster = createEdges(self)
        nodeInsideCluster = createNodeInCluster(self)
        nodeBetweenCluster = createNodeBetweenCluster(self)
        self.listNodes = nodeBetweenCluster + nodeInsideCluster
        self.listNodes.reverse() # đảo ngược lại danh sách để xét các node nhận target theo thứ tự từ sensor, in, out, relay

    def setLevels(self):
        # hàm này có hai chức năng, một chức năng dùng để kiểm tra đường truyền hợp lệ từ các sensor về base station
        # chức năng thứ hai là kiểm tra các target trong mạng có được theo dõi (có được các sensor có đường truyền hợp lệ về base station theo dõi không)
        for node in self.listNodes:
            node.level = -1
        tmp1 = []
        tmp2 = []
        for node in self.baseStation.direct_nodes:
            if node.status == 1:
                node.level = 1
                tmp1.append(node)

        for i in range(len(self.targets_active)):
            self.targets_active[i] = 0
        # bổ sung
        for target in self.listTargets:
            target.is_active = 0

        while True:
            if len(tmp1) == 0:
                break
            # For each node, we set value of target covered by this node as 1
            # For each node, if we have not yet reached its neighbor, then level of neighbors equal this node + 1
            for node in tmp1:
 
                for target in node.listTargets:
                    self.targets_active[target.id] = 1
                    # bổ sung
                    self.listTargets[target.id].is_active = 1
                    target.is_active = 1

                for neighbor in node.potentialSender:
                    if neighbor.status == 1 and neighbor.level == -1:
                        tmp2.append(neighbor)
                        neighbor.level = node.level + 1

            # Once all nodes at current level have been expanded, move to the new list of next level
            tmp1 = tmp2[:]
            tmp2.clear()
        
        #############
        # set level lần hai để gán lại các target không được theo dõi
        for node in self.listNodes:
            node.level = -1
        tmp1 = []
        tmp2 = []
        for node in self.baseStation.direct_nodes:
            if node.status == 1:
                node.level = 1
                tmp1.append(node)

        while True:
            if len(tmp1) == 0:
                break
            # For each node, we set value of target covered by this node as 1
            # For each node, if we have not yet reached its neighbor, then level of neighbors equal this node + 1
            for node in tmp1:
                #print(node.location[0],node.location[1])
                for target in node.listTotalTargets:
                    if target.is_active == 0:
                        self.targets_active[target.id] = 1
                        target.is_active = 1
                        self.listTargets[target.id].is_active = 1
                        node.listTargets.append(target)

                for neighbor in node.potentialSender:
                    if neighbor.status == 1 and neighbor.level == -1:
                        tmp2.append(neighbor)
                        neighbor.level = node.level + 1

            # Once all nodes at current level have been expanded, move to the new list of next level
            tmp1 = tmp2[:]
            tmp2.clear()

        return

    def operate(self, t=1):
        for node in self.listNodes:
            self.env.process(node.operate(t=t))
            self.env.process(self.baseStation.operate(t=t))
        while True:
            yield self.env.timeout(t / 10.0)
            self.setLevels()
            self.alive = self.check_targets()
            yield self.env.timeout(9.0 * t / 10.0)

            # # kiểm tra xem các target có được theo dõi đúng bới 1 sensor thôi không không
            # check_target = 0
            # for node in self.listNodes:
            #     check_target += len(node.listTargets)
            # print(check_target)
            ### chuẩn, một target chỉ được theo dõi bởi một sensor, nếu sensor chết sẽ chuyển target cho sensor khác
            
            if self.alive == 0 or self.env.now >= self.max_time:
                print("Network dies")
                print(self.env.now,self.check_nodes(),self.check_targets())
                break         
        return

    def check_targets(self):
        for target in self.listTargets:
            if target.is_active == 0:
                return 0
        return 1
        # return min(self.targets_active)
    
    def check_nodes(self):
        tmp = 0
        for node in self.listNodes:
            if node.status == 0:
                tmp += 1
        return tmp
    
    def get_dead_nodes(self):
        list_dead_nodes = []
        for node in self.listNodes:
            if node.status == 0:
                list_dead_nodes.append(node)
        return list_dead_nodes
