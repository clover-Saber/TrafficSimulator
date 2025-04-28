import networkx as nx
import random
from collections import deque
from typing import List, Dict, Tuple, Any

class RoadNetworkManager:
    """路网管理类"""
    
    def __init__(self, graph=None):
        """
        初始化路网管理器
        参数:
            graph: NetworkX图对象
        """
        self.graph = graph if graph else nx.Graph()
    
    def load_graph(self, graph):
        """
        加载路网图
        """
        self.graph = graph

    
    def get_random_node(self):
        """
        从路网中随机选择一个节点
        返回:
            随机选择的节点ID，如果路网为空则返回None
        """
        nodes = list(self.graph.nodes())
        if not nodes:
            print("警告：路网中没有节点")
            return None
        return random.choice(nodes)
    
    
    def get_random_node_in_time(self, node, time):
        """
        从路网中随机选择一个距离给定节点不超过指定时间的节点
        参数:
            node: 起始节点ID
            time: 最大旅行时间限制
        返回:
            随机选择的节点ID，如果没有符合条件的节点则返回None
        """
        if node not in self.graph.nodes():
            print(f"警告：起始节点 {node} 不在路网中")
            return None
        
        # 使用广度优先搜索找出所有在时间限制内可达的节点
        reachable_nodes = []
        visited = {node: 0}  # 节点ID -> 累计时间
        queue = deque([(node, 0)])  # (节点ID, 累计时间)
        
        while queue:
            current_node, current_time = queue.popleft()
            
            # 对当前节点的所有邻居进行遍历
            for neighbor in self.graph.neighbors(current_node):
                # 获取边的旅行时间
                edge_data = self.graph.get_edge_data(current_node, neighbor)
                travel_time = edge_data.get('time', 1)  # 默认为1，如果没有time属性
                
                # 计算到达邻居节点的总时间
                total_time = current_time + travel_time
                
                # 如果总时间在限制范围内且该节点未访问过或找到了更短的路径
                if total_time <= time and (neighbor not in visited or total_time < visited[neighbor]):
                    visited[neighbor] = total_time
                    queue.append((neighbor, total_time))
                    
                    # 将不是起始节点的节点添加到可达节点列表
                    if neighbor != node:
                        reachable_nodes.append(neighbor)
        
        # 如果没有可达节点，返回None
        if not reachable_nodes:
            print(f"警告：没有找到距离节点 {node} 不超过 {time} 时间单位的节点")
            return None
        
        # 随机选择一个可达节点
        return random.choice(reachable_nodes)


    
    def calculate_shortest_path(self, source_node, target_node, start_time):
        """
        计算最短路径
        参数:
            source_node: 起始节点
            target_node: 目标节点
            start_time: 出发时间
        返回:
            列表，每个元素是一个元组 (节点, 到达时间)，表示最短路径上的节点及到达该节点的时间
        """
        try:
            # 计算最短路径（节点序列）
            path_nodes = nx.shortest_path(self.graph, source=source_node, target=target_node, weight='time')
            
            if not path_nodes:
                return []
            
            # 计算到达每个节点的时间
            path_with_times = [(int(path_nodes[0]), start_time)]  # 起始节点的到达时间是出发时间
            current_time = start_time
            
            # 遍历路径中的每一对相邻节点
            for i in range(len(path_nodes) - 1):
                current_node = path_nodes[i]
                next_node = int(path_nodes[i + 1])
                
                # 获取边的行驶时间
                edge_data = self.graph.get_edge_data(current_node, next_node)
                travel_time = edge_data.get('time', 0)
                
                # 更新当前时间
                current_time += travel_time
                # 添加到路径列表
                path_with_times.append((next_node, current_time))
            
            return path_with_times
        
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            print(f"节点{source_node}和{target_node}之间无路线")
            return []
        
    def calculate_shortest_travel_time(self, source_node, target_node):
        """
        计算从起始节点到目标节点的最短旅行时间
        参数:
            source_node: 起始节点
            target_node: 目标节点
        返回:
            int: 最短旅行时间，如果不存在路径则返回 int('inf')
        """
        try:
            # 使用 networkx 的 shortest_path_length 函数直接计算最短路径长度（时间）
            travel_time = nx.shortest_path_length(
                self.graph, 
                source=source_node, 
                target=target_node, 
                weight='time'
            )
            return travel_time
        
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # 如果不存在路径或节点不存在，返回无穷大
            return float('inf')