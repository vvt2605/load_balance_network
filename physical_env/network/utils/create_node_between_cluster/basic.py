from scipy.spatial.distance import euclidean
from Nodes.RelayNode import RelayNode
from physical_env.network.utils.PointBetween import point_between

# Input net.listEdges
# Output # [relayNode1,relayNode2 , . . . ]

def createNodeBetweenCluster(net):
 
        epsilon = 1e-6
        ListRelayNode = []
        init_range = net.phy['com_range'] * net.Alpha
        com_range = net.phy['com_range'] * net.Alpha

        ID = 0
        for node in net.listNodes:
            if node.id > ID: 
                ID = node.id
                
        Cnt_in = [0] * (len(net.listClusters) + 1)
        Cnt_out =[0] * (len(net.listClusters) + 1)
        list_edge = []

        for edge in net.listEdges:
            if edge[1].__class__.__name__ == "Cluster":
                  list_edge.append((net.listClusters[edge[0].id],net.listClusters[edge[1].id]))
            else: list_edge.append((net.listClusters[edge[0].id],net.baseStation))
        
        for edge in list_edge:
            u = edge[0]
            v = edge[1]
            U = 0
            V = net.baseStation.location
            cnt = 0
            for node in u.listNodes:
                if(node.__class__.__name__ == "OutNode"):
                      if(cnt == Cnt_out[u.id]):
                          U = node.location.copy()
                          Cnt_out[u.id] += 1
                          break
                      cnt += 1
            cnt = 0
            if v.__class__.__name__ == "Cluster":
             for node in v.listNodes:
                if(node.__class__.__name__ == "InNode"):
                      if(cnt == Cnt_in[v.id]):
                          V = node.location.copy()
                          Cnt_in[v.id] += 1 
                          break
                      cnt += 1   
            # while True:
            #         distance = euclidean(U,V)

            #         # bổ sung: chỉnh range theo số cluster/ 20 target === 0.4; 0 target === 1
            #         # for cluster_id, number_cluster in net.num_targets_per_cluster:
            #         #      if v.id == cluster_id:
            #         #           range = init_range * (1 - 0.0075 * 2 * number_cluster)
            #         ####
            #         if(distance < range ):
            #             U[0], U[1] = point_between ( U, V , distance/2 - epsilon)
            #             ID += 1
            #             ListRelayNode.append(RelayNode([U[0],U[1]],ID,net.phy,u,v))
            #             break
            #         if(distance < 2*range):
            #             U[0], U[1] = point_between ( U, V , distance/2 - epsilon)
            #             ID += 1
            #             ListRelayNode.append(RelayNode([U[0],U[1]],ID,net.phy,u,v))
            #             break
            #         U[0], U[1] = point_between ( U, V , range - epsilon)
            #         ID += 1
            #         ListRelayNode.append(RelayNode([U[0],U[1]],ID,net.phy,u,v))

            distance_between_2_clusters = euclidean(U,V)
            num_relay_nodes = int(distance_between_2_clusters/com_range)

            if(num_relay_nodes == 0):
                U[0], U[1] = point_between ( U, V , distance_between_2_clusters/2 )
                ID += 1
                ListRelayNode.append(RelayNode([U[0],U[1]],ID,net.phy,u,v))

            else:
                new_range = distance_between_2_clusters/(num_relay_nodes + 1) # khoảng cách đặt relay node sao cho các relay cách đều nhau
                for i in range(0, num_relay_nodes):
                    
                    U[0], U[1] = point_between ( U, V , new_range)
                    ID += 1
                    ListRelayNode.append(RelayNode([U[0],U[1]],ID,net.phy,u,v))


        return ListRelayNode
    
