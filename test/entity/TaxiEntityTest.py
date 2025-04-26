# 2025.4.23 yh

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# 根据您的实际项目结构导入TaxiEntity
from traffic_simulator.entity.TaxiEntity import TaxiEntity

class TestTaxiEntity(unittest.TestCase):
    """测试TaxiEntity类的功能"""
    
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        print(f"\n开始测试: {self._testMethodName}")
        # 创建一个出租车实例，ID为1，初始位置在节点10
        self.taxi = TaxiEntity(taxi_id=1, position_node=10, driver_preference="短途优先")
        print(f"创建出租车: ID={self.taxi.taxi_id}, 位置={self.taxi.position_node}, 偏好={self.taxi.driver_preference}")
    
    def tearDown(self):
        """每个测试方法执行后的清理工作"""
        print(f"测试完成: {self._testMethodName}")
        print(f"出租车最终状态: {self.taxi.status}, 位置={self.taxi.position_node}")
    
    def test_initialization(self):
        """测试初始化是否正确"""
        print("验证初始化参数...")
        self.assertEqual(self.taxi.taxi_id, 1)
        self.assertEqual(self.taxi.position_node, 10)
        self.assertEqual(self.taxi.driver_preference, "短途优先")
        self.assertEqual(self.taxi.status, "idle")
        self.assertIsNone(self.taxi.current_order)
        self.assertIsNone(self.taxi.current_destination)
        self.assertIsNone(self.taxi.current_route)
        self.assertEqual(self.taxi.order_history, [])
        print("初始化参数验证通过!")
    
    def test_assign_order(self):
        """测试分配订单功能"""
        print("测试分配订单...")
        
        # 创建一个模拟路线，包含节点和到达时间
        route = [(10, 0), (15, 5), (20, 10)]
        print(f"模拟路线: {route}")
        
        # 分配订单
        print(f"尝试分配订单: ID=101, 接客点=20")
        result = self.taxi.assign_order(order_id=101, pickup_node=20, route=route)
        
        # 验证分配是否成功
        print(f"订单分配结果: {result}")
        print(f"出租车状态: {self.taxi.status}")
        print(f"当前订单: {self.taxi.current_order}")
        print(f"目的地: {self.taxi.current_destination}")
        print(f"订单历史: {self.taxi.order_history}")
        
        self.assertTrue(result)
        self.assertEqual(self.taxi.status, "enroute_pickup")
        self.assertEqual(self.taxi.current_order, 101)
        self.assertEqual(self.taxi.current_destination, 20)
        self.assertEqual(self.taxi.current_route, route)
        self.assertEqual(self.taxi.order_history, [101])
        
        # 测试已有订单的出租车不能再接单
        print("\n测试已有订单的出租车不能再接单...")
        result = self.taxi.assign_order(order_id=102, pickup_node=30, route=[(20, 0), (30, 5)])
        print(f"第二次分配结果: {result}")
        self.assertFalse(result)
    
    def test_arrive_at_pickup(self):
        """测试到达接客点功能"""
        print("测试到达接客点功能...")
        
        # 先分配订单
        print("先分配订单...")
        self.taxi.assign_order(order_id=101, pickup_node=20, route=[(10, 0), (15, 5), (20, 10)])
        print(f"出租车状态: {self.taxi.status}, 当前订单: {self.taxi.current_order}")
        
        # 定义到达目的地的路线
        dest_route = [(20, 0), (25, 5), (30, 10)]
        print(f"送客路线: {dest_route}")
        
        # 到达接客点
        print("模拟到达接客点...")
        result = self.taxi.arrive_at_pickup(destination_node=30, route=dest_route)
        
        # 验证状态更新
        print(f"到达接客点结果: {result}")
        print(f"出租车状态: {self.taxi.status}, 位置: {self.taxi.position_node}")
        print(f"目的地: {self.taxi.current_destination}, 路线: {self.taxi.current_route}")
        
        self.assertTrue(result)
        self.assertEqual(self.taxi.status, "occupied")
        self.assertEqual(self.taxi.position_node, 20)  # 位置应更新为接客点
        self.assertEqual(self.taxi.current_destination, 30)
        self.assertEqual(self.taxi.current_route, dest_route)
        
        # 测试非接客状态不能调用此方法
        print("\n测试非接客状态不能调用此方法...")
        taxi2 = TaxiEntity(taxi_id=2, position_node=10)
        print(f"创建出租车2: ID={taxi2.taxi_id}, 状态={taxi2.status}")
        result = taxi2.arrive_at_pickup(destination_node=30, route=dest_route)
        print(f"非接客状态调用结果: {result}")
        self.assertFalse(result)
    
    def test_complete_order(self):
        """测试完成订单功能"""
        print("测试完成订单功能...")
        
        # 先分配订单并到达接客点
        print("先分配订单...")
        self.taxi.assign_order(order_id=101, pickup_node=20, route=[(10, 0), (15, 5), (20, 10)])
        print("模拟到达接客点...")
        self.taxi.arrive_at_pickup(destination_node=30, route=[(20, 0), (25, 5), (30, 10)])
        print(f"出租车状态: {self.taxi.status}, 当前订单: {self.taxi.current_order}")
        
        # 完成订单
        print("完成订单...")
        result = self.taxi.complete_order()
        
        # 验证状态更新
        print(f"完成订单结果: {result}")
        print(f"出租车状态: {self.taxi.status}, 位置: {self.taxi.position_node}")
        print(f"当前订单: {self.taxi.current_order}, 目的地: {self.taxi.current_destination}")
        
        self.assertTrue(result)
        self.assertEqual(self.taxi.status, "idle")
        self.assertEqual(self.taxi.position_node, 30)  # 位置应更新为乘客目的地
        self.assertIsNone(self.taxi.current_order)
        self.assertIsNone(self.taxi.current_destination)
        self.assertIsNone(self.taxi.current_route)
        
        # 测试非载客状态不能完成订单
        print("\n测试非载客状态不能完成订单...")
        taxi2 = TaxiEntity(taxi_id=2, position_node=10)
        print(f"创建出租车2: ID={taxi2.taxi_id}, 状态={taxi2.status}")
        result = taxi2.complete_order()
        print(f"非载客状态完成订单结果: {result}")
        self.assertFalse(result)
    
    def test_repositioning(self):
        """测试重新定位功能"""
        print("测试重新定位功能...")
        
        # 定义重新定位路线
        repo_route = [(10, 0), (15, 5), (20, 10)]
        print(f"重新定位路线: {repo_route}")
        
        # 开始重新定位
        print("开始重新定位...")
        result = self.taxi.start_repositioning(destination_node=20, route=repo_route)
        
        # 验证状态更新
        print(f"开始重新定位结果: {result}")
        print(f"出租车状态: {self.taxi.status}, 目的地: {self.taxi.current_destination}")
        
        self.assertTrue(result)
        self.assertEqual(self.taxi.status, "repositioning")
        self.assertEqual(self.taxi.current_destination, 20)
        self.assertEqual(self.taxi.current_route, repo_route)
        
        # 完成重新定位
        print("\n完成重新定位...")
        result = self.taxi.complete_repositioning()
        
        # 验证状态更新
        print(f"完成重新定位结果: {result}")
        print(f"出租车状态: {self.taxi.status}, 位置: {self.taxi.position_node}")
        
        self.assertTrue(result)
        self.assertEqual(self.taxi.status, "idle")
        self.assertEqual(self.taxi.position_node, 20)  # 位置应更新为重新定位目标
        self.assertIsNone(self.taxi.current_destination)
        self.assertIsNone(self.taxi.current_route)
        
        # 测试非重新定位状态不能完成重新定位
        print("\n测试非重新定位状态不能完成重新定位...")
        result = self.taxi.complete_repositioning()
        print(f"非重新定位状态完成重新定位结果: {result}")
        self.assertFalse(result)
        
        # 测试非空闲状态不能开始重新定位
        print("\n测试非空闲状态不能开始重新定位...")
        self.taxi.assign_order(order_id=101, pickup_node=30, route=[(20, 0), (25, 5), (30, 10)])
        print(f"分配订单后状态: {self.taxi.status}")
        result = self.taxi.start_repositioning(destination_node=40, route=[(20, 0), (40, 10)])
        print(f"非空闲状态开始重新定位结果: {result}")
        self.assertFalse(result)
    
    def test_update_position(self):
        """测试根据时间更新位置功能"""
        print("测试根据时间更新位置功能...")
        
        # 分配订单，路线包含多个节点和到达时间
        route = [(10, 0), (15, 5), (20, 10), (25, 15)]
        print(f"分配订单，路线: {route}")
        self.taxi.assign_order(order_id=101, pickup_node=25, route=route)
        
        # 测试不同时间点的位置更新
        # 时间=0，应该在起点
        print("\n时间=0，测试位置更新...")
        result = self.taxi.update_position(current_time=0)
        print(f"更新结果: {result}, 当前位置: {self.taxi.position_node}")
        self.assertFalse(result)
        self.assertEqual(self.taxi.position_node, 10)
        
        # 时间=7，应该在第二个节点
        print("\n时间=7，测试位置更新...")
        result = self.taxi.update_position(current_time=7)
        print(f"更新结果: {result}, 当前位置: {self.taxi.position_node}")
        self.assertFalse(result)
        self.assertEqual(self.taxi.position_node, 15)
        
        # 时间=12，应该在第三个节点
        print("\n时间=12，测试位置更新...")
        result = self.taxi.update_position(current_time=12)
        print(f"更新结果: {result}, 当前位置: {self.taxi.position_node}")
        self.assertFalse(result)
        self.assertEqual(self.taxi.position_node, 20)
        
        # 时间=15，应该到达目的地
        print("\n时间=15，测试位置更新...")
        result = self.taxi.update_position(current_time=15)
        print(f"更新结果: {result}, 当前位置: {self.taxi.position_node}")
        self.assertTrue(result)
        self.assertEqual(self.taxi.position_node, 25)
        
        # 时间>15，应该仍在目的地
        print("\n时间=20，测试位置更新...")
        result = self.taxi.update_position(current_time=20)
        print(f"更新结果: {result}, 当前位置: {self.taxi.position_node}")
        self.assertTrue(result)
        self.assertEqual(self.taxi.position_node, 25)
    
    def test_get_methods(self):
        """测试获取信息的方法"""
        print("测试获取信息的方法...")
        
        print(f"状态: {self.taxi.get_status()}")
        print(f"位置: {self.taxi.get_position()}")
        print(f"当前订单: {self.taxi.get_current_order()}")
        print(f"订单历史: {self.taxi.get_order_history()}")
        
        self.assertEqual(self.taxi.get_status(), "idle")
        self.assertEqual(self.taxi.get_position(), 10)
        self.assertIsNone(self.taxi.get_current_order())
        self.assertEqual(self.taxi.get_order_history(), [])
        
        # 分配订单后再测试
        print("\n分配订单后再测试...")
        self.taxi.assign_order(order_id=101, pickup_node=20, route=[(10, 0), (15, 5), (20, 10)])
        
        print(f"状态: {self.taxi.get_status()}")
        print(f"当前订单: {self.taxi.get_current_order()}")
        print(f"订单历史: {self.taxi.get_order_history()}")
        
        self.assertEqual(self.taxi.get_status(), "enroute_pickup")
        self.assertEqual(self.taxi.get_current_order(), 101)
        self.assertEqual(self.taxi.get_order_history(), [101])
        
        # 验证order_history返回的是副本
        print("\n验证order_history返回的是副本...")
        history = self.taxi.get_order_history()
        history.append(999)
        print(f"修改后的历史副本: {history}")
        print(f"原始订单历史: {self.taxi.get_order_history()}")
        self.assertEqual(self.taxi.get_order_history(), [101])  # 原列表不应被修改

# 自定义TestRunner
class CustomTestRunner(unittest.TextTestRunner):
    def run(self, test):
        print("\n=== 开始测试出租车实体 ===\n")
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
