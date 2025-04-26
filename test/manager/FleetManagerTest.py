import unittest
import sys
import os
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# 根据您的实际项目结构导入FleetManager和其他需要的类
from traffic_simulator.manager.FleetManager import FleetManager
from traffic_simulator.entity.TaxiEntity import TaxiEntity
from traffic_simulator.entity.OrderEntity import OrderEntity

class TestFleetManager(unittest.TestCase):
    """测试FleetManager类的功能"""
    
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        print(f"\n开始测试: {self._testMethodName}")
        
        # 创建FleetManager实例
        self.fleet_manager = FleetManager()
        
        # 创建模拟的出租车
        self.taxi1 = Mock(spec=TaxiEntity)
        self.taxi1.taxi_id = 1
        self.taxi1.status = "idle"
        self.taxi1.position_node = 100
        self.taxi1.current_order = None
        self.taxi1.current_destination = None
        self.taxi1.current_route = None
        self.taxi1.order_history = []
        
        self.taxi2 = Mock(spec=TaxiEntity)
        self.taxi2.taxi_id = 2
        self.taxi2.status = "occupied"
        self.taxi2.position_node = 200
        self.taxi2.current_order = 2001
        self.taxi2.current_destination = 300
        self.taxi2.current_route = [(250, 120), (300, 150)]
        self.taxi2.order_history = [2001]
        
        self.taxi3 = Mock(spec=TaxiEntity)
        self.taxi3.taxi_id = 3
        self.taxi3.status = "enroute_pickup"
        self.taxi3.position_node = 400
        self.taxi3.current_order = 3001
        self.taxi3.current_destination = 500
        self.taxi3.current_route = [(450, 110), (500, 130)]
        self.taxi3.order_history = [3001]
        
        # 将出租车添加到FleetManager
        self.fleet_manager.taxis = {
            self.taxi1.taxi_id: self.taxi1,
            self.taxi2.taxi_id: self.taxi2,
            self.taxi3.taxi_id: self.taxi3
        }
        
        # 创建模拟的订单
        self.order1 = Mock(spec=OrderEntity)
        self.order1.order_id = 1001
        self.order1.pickup_node = 150
        self.order1.dropoff_node = 250
        self.order1.status = "waiting"
        
        self.order2 = Mock(spec=OrderEntity)
        self.order2.order_id = 1002
        self.order2.pickup_node = 350
        self.order2.dropoff_node = 450
        self.order2.status = "waiting"
        
        # 模拟_calculate_route方法
        self.fleet_manager._calculate_route = Mock(return_value=[(150, 120), (200, 140), (250, 160)])
        
        # 模拟_get_order_by_id方法
        def mock_get_order_by_id(order_id):
            if order_id == 1001:
                return self.order1
            elif order_id == 1002:
                return self.order2
            elif order_id == 2001:
                mock_order = Mock()
                mock_order.destination_node = 300
                return mock_order
            elif order_id == 3001:
                mock_order = Mock()
                mock_order.destination_node = 600
                return mock_order
            return None
            
        self.fleet_manager._get_order_by_id = mock_get_order_by_id
        
        print("测试环境准备完成")
    
    def tearDown(self):
        """每个测试方法执行后的清理工作"""
        print(f"测试完成: {self._testMethodName}")
    
    def test_get_idle_taxis(self):
        """测试获取空闲出租车功能"""
        print("测试获取空闲出租车...")
        
        idle_taxis = self.fleet_manager.get_idle_taxis()
        
        print(f"获取到的空闲出租车数量: {len(idle_taxis)}")
        for taxi in idle_taxis:
            print(f"  - 出租车ID: {taxi.taxi_id}, 状态: {taxi.status}")
        
        self.assertEqual(len(idle_taxis), 1)
        self.assertEqual(idle_taxis[0].taxi_id, self.taxi1.taxi_id)
        self.assertEqual(idle_taxis[0].status, "idle")
    
    def test_assign_order_to_taxi(self):
        """测试将订单分配给出租车功能"""
        print("测试将订单分配给出租车...")
        
        current_time = 100
        taxi_order_list = [(self.taxi1.taxi_id, self.order1)]
        
        bound_orders = self.fleet_manager.assign_order_to_taxi(taxi_order_list, current_time)
        
        print(f"成功绑定的订单数量: {len(bound_orders)}")
        for order in bound_orders:
            print(f"  - 订单ID: {order.order_id}")
        
        # 验证订单是否成功绑定
        self.assertEqual(len(bound_orders), 1)
        self.assertEqual(bound_orders[0].order_id, self.order1.order_id)
        
        # 验证出租车状态是否更新
        self.assertEqual(self.taxi1.status, "enroute_pickup")
        self.assertEqual(self.taxi1.current_order, self.order1.order_id)
        self.assertEqual(self.taxi1.current_destination, self.order1.pickup_node)
        self.assertEqual(self.taxi1.current_route, [(150, 120), (200, 140), (250, 160)])
        self.assertEqual(len(self.taxi1.order_history), 1)
        self.assertEqual(self.taxi1.order_history[0], self.order1.order_id)
        
        # 验证_calculate_route是否被正确调用
        self.fleet_manager._calculate_route.assert_called_once_with(
            self.taxi1.position_node, 
            self.order1.pickup_node, 
            current_time
        )
    
    def test_assign_order_to_nonexistent_taxi(self):
        """测试将订单分配给不存在的出租车"""
        print("测试将订单分配给不存在的出租车...")
        
        current_time = 100
        nonexistent_taxi_id = 999
        taxi_order_list = [(nonexistent_taxi_id, self.order1)]
        
        bound_orders = self.fleet_manager.assign_order_to_taxi(taxi_order_list, current_time)
        
        print(f"成功绑定的订单数量: {len(bound_orders)}")
        
        # 验证没有订单被绑定
        self.assertEqual(len(bound_orders), 0)
    
    def test_assign_order_to_busy_taxi(self):
        """测试将订单分配给忙碌的出租车"""
        print("测试将订单分配给忙碌的出租车...")
        
        current_time = 100
        taxi_order_list = [(self.taxi2.taxi_id, self.order1)]  # taxi2 is occupied
        
        bound_orders = self.fleet_manager.assign_order_to_taxi(taxi_order_list, current_time)
        
        print(f"成功绑定的订单数量: {len(bound_orders)}")
        
        # 验证没有订单被绑定
        self.assertEqual(len(bound_orders), 0)
        
        # 验证出租车状态没有改变
        self.assertEqual(self.taxi2.status, "occupied")
        self.assertEqual(self.taxi2.current_order, 2001)
    
    def test_update_enroute_pickup_taxis(self):
        """测试更新前往接客的出租车状态"""
        print("测试更新前往接客的出租车状态...")
        
        # 设置当前时间为出租车3到达接客点的时间
        current_time = 130
        
        self.fleet_manager.update_enroute_pickup_taxis(current_time)
        
        print(f"更新后出租车3的状态: {self.taxi3.status}")
        print(f"更新后出租车3的位置: {self.taxi3.position_node}")
        
        # 验证出租车3是否到达接客点并更新状态
        self.assertEqual(self.taxi3.status, "occupied")
        self.assertEqual(self.taxi3.position_node, 500)
        self.assertEqual(self.taxi3.current_destination, 600)  # 从mock_get_order_by_id设置的目的地
        
        # 验证_calculate_route是否被正确调用
        self.fleet_manager._calculate_route.assert_called_with(
            500,  # 当前位置
            600,  # 目的地
            current_time
        )
    
    def test_update_occupied_taxis(self):
        """测试更新载客中的出租车状态"""
        print("测试更新载客中的出租车状态...")
        
        # 设置当前时间为出租车2到达目的地的时间
        current_time = 150
        
        self.fleet_manager.update_enroute_pickup_taxis(current_time)
        
        print(f"更新后出租车2的状态: {self.taxi2.status}")
        print(f"更新后出租车2的位置: {self.taxi2.position_node}")
        
        # 验证出租车2是否到达目的地并更新状态
        self.assertEqual(self.taxi2.status, "idle")
        self.assertEqual(self.taxi2.position_node, 300)
        self.assertIsNone(self.taxi2.current_destination)
        self.assertIsNone(self.taxi2.current_route)
        self.assertIsNone(self.taxi2.current_order)
    
    def test_update_taxis_partial_route(self):
        """测试出租车在路线中途的更新"""
        print("测试出租车在路线中途的更新...")
        
        # 设置当前时间为出租车2在路线中途的时间
        current_time = 120
        
        self.fleet_manager.update_enroute_pickup_taxis(current_time)
        
        print(f"更新后出租车2的状态: {self.taxi2.status}")
        print(f"更新后出租车2的位置: {self.taxi2.position_node}")
        
        # 验证出租车2的位置是否更新到路线中的第一个节点
        self.assertEqual(self.taxi2.status, "occupied")  # 状态不变
        self.assertEqual(self.taxi2.position_node, 250)  # 更新到第一个节点
    
    def test_reposition_idle_taxis(self):
        """测试重新定位空闲出租车"""
        print("测试重新定位空闲出租车...")
        
        destination_node = 600
        route = [(400, 130), (500, 150), (600, 170)]
        strategy_list = [(self.taxi1.taxi_id, destination_node, route)]
        
        self.fleet_manager.reposition_idle_taxis(strategy_list)
        
        print(f"重新定位后出租车1的状态: {self.taxi1.status}")
        print(f"重新定位后出租车1的目的地: {self.taxi1.current_destination}")
        
        # 验证出租车1是否被重新定位
        self.assertEqual(self.taxi1.status, "repositioning")
        self.assertEqual(self.taxi1.current_destination, destination_node)
        self.assertEqual(self.taxi1.current_route, route)
    
    def test_reposition_nonexistent_taxi(self):
        """测试重新定位不存在的出租车"""
        print("测试重新定位不存在的出租车...")
        
        nonexistent_taxi_id = 999
        destination_node = 600
        route = [(400, 130), (500, 150), (600, 170)]
        strategy_list = [(nonexistent_taxi_id, destination_node, route)]
        
        self.fleet_manager.reposition_idle_taxis(strategy_list)
        
        # 不应该有任何异常发生
        print("测试通过，没有异常发生")
    
    def test_reposition_busy_taxi(self):
        """测试重新定位忙碌的出租车"""
        print("测试重新定位忙碌的出租车...")
        
        destination_node = 600
        route = [(400, 130), (500, 150), (600, 170)]
        strategy_list = [(self.taxi2.taxi_id, destination_node, route)]  # taxi2 is occupied
        
        self.fleet_manager.reposition_idle_taxis(strategy_list)
        
        print(f"尝试重新定位后出租车2的状态: {self.taxi2.status}")
        
        # 验证出租车2的状态没有改变
        self.assertEqual(self.taxi2.status, "occupied")
        self.assertNotEqual(self.taxi2.current_destination, destination_node)
        self.assertNotEqual(self.taxi2.current_route, route)

# 自定义TestRunner
class CustomTestRunner(unittest.TextTestRunner):
    def run(self, test):
        print("\n=== 开始测试车队管理类 ===\n")
        result = super().run(test)
        print("\n=== 测试完成 ===")
        print(f"运行测试: {result.testsRun}")
        print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"失败: {len(result.failures)}")
        print(f"错误: {len(result.errors)}")
        return result

if __name__ == '__main__':
    runner = CustomTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
