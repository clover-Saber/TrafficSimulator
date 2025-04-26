import unittest
import sys
import os
import networkx as nx
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
# 根据您的实际项目结构导入FleetManager和其他需要的类
from traffic_simulator.entity.TaxiEntity import TaxiEntity
from traffic_simulator.entity.OrderEntity import OrderEntity
from traffic_simulator.manager.FleetManager import FleetManager
from traffic_simulator.manager.OrderManager import OrderManager
from traffic_simulator.manager.RoadNetworkManager import RoadNetworkManager
from traffic_simulator.Simulator import TrafficSimulator

class TestTrafficSimulator(unittest.TestCase):
    """测试交通模拟器类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建一个简单的路网
        G= self.create_test_network(4, 5)
        orders_df = self.create_orders()
        
        # 创建模拟器
        self.simulator = TrafficSimulator(2, 0, 1, G, orders_df)
        
    def create_test_network(self, width, height, travel_time=1):
        """
        创建一个简单的网格路网，使用一维整数作为节点标识符
        参数:
            width: 网格宽度
            height: 网格高度
            travel_time: 相邻节点间的行驶时间（默认为1.0）
        返回:
            networkx.Graph: 创建的网格图
        """
        # 创建空图
        G = nx.Graph()
        
        # 添加节点 - 使用单一整数作为节点标识符
        # 节点编号从0开始，按行优先顺序排列
        for i in range(width * height):
            G.add_node(i)
        
        # 添加边 - 连接相邻节点
        for i in range(height):
            for j in range(width):
                node_id = i * width + j
                
                # 连接右侧节点
                if j < width - 1:
                    right_node_id = node_id + 1
                    G.add_edge(node_id, right_node_id, time=travel_time)
                
                # 连接下方节点
                if i < height - 1:
                    down_node_id = node_id + width
                    G.add_edge(node_id, down_node_id, time=travel_time)
        
        return G
    
    def create_orders(self):
        # 创建一个示例订单DataFrame
        orders_data = {
            'id': [1001, 1002, 1003, 1004, 1005],
            'pickup_node': [0, 1, 2, 3, 4],
            'dropoff_node': [6, 7, 8, 9, 10],
            'ot': [0, 2, 8, 10, 15],  # 出发时间
        }
        orders_df = pd.DataFrame(orders_data)
        return orders_df
    
    def test_complete_order_flow(self):
        """测试完整的订单流程"""
        
        # 运行足够长的模拟时间以完成订单
        self.simulator.run_simulation(until_time=30)


if __name__ == "__main__":
    unittest.main()
