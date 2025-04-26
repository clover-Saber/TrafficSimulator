import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# 根据您的实际项目结构导入OrderEntity
from traffic_simulator.entity.OrderEntity import OrderEntity

class TestOrderEntity(unittest.TestCase):
    """测试OrderEntity类的功能"""
    
    def setUp(self):
        """每个测试方法执行前的准备工作"""
        print(f"\n开始测试: {self._testMethodName}")
        
        # 创建测试订单
        self.order_id = 1001
        self.pickup_node = 10
        self.dropoff_node = 20
        self.pickup_coord = (116.3, 39.9)  # 北京某地坐标示例
        self.dropoff_coord = (116.4, 40.0)
        self.request_time = 100  # 模拟时间戳
        
        self.order = OrderEntity(
            self.order_id,
            self.pickup_node,
            self.dropoff_node,
            self.pickup_coord,
            self.dropoff_coord,
            self.request_time
        )
        
        print(f"创建测试订单: {self.order}")
    
    def tearDown(self):
        """每个测试方法执行后的清理工作"""
        print(f"测试完成: {self._testMethodName}")
    
    def test_initialization(self):
        """测试订单初始化是否正确"""
        print("验证初始化参数...")
        
        self.assertEqual(self.order.order_id, self.order_id)
        self.assertEqual(self.order.pickup_node, self.pickup_node)
        self.assertEqual(self.order.dropoff_node, self.dropoff_node)
        self.assertEqual(self.order.pickup_coord, self.pickup_coord)
        self.assertEqual(self.order.dropoff_coord, self.dropoff_coord)
        self.assertEqual(self.order.request_time, self.request_time)
        
        # 验证默认值
        self.assertIsNone(self.order.assigned_taxi)
        self.assertIsNone(self.order.pickup_time)
        self.assertIsNone(self.order.dropoff_time)
        self.assertEqual(self.order.status, "waiting")
        self.assertIsNone(self.order.fare)
        
        print("初始化参数验证通过!")
    
    def test_assign_taxi(self):
        """测试分配出租车功能"""
        print("测试分配出租车...")
        
        taxi_id = 5001
        result = self.order.assign_taxi(taxi_id)
        
        print(f"分配出租车 {taxi_id} 给订单，结果: {result}")
        print(f"订单状态: {self.order.status}, 分配的出租车: {self.order.assigned_taxi}")
        
        self.assertTrue(result)
        self.assertEqual(self.order.assigned_taxi, taxi_id)
        self.assertEqual(self.order.status, "assigned")
        
        # 测试重复分配
        new_taxi_id = 5002
        result = self.order.assign_taxi(new_taxi_id)
        
        print(f"尝试重新分配出租车 {new_taxi_id} 给已分配的订单，结果: {result}")
        print(f"订单状态: {self.order.status}, 分配的出租车: {self.order.assigned_taxi}")
        
        self.assertFalse(result)
        self.assertEqual(self.order.assigned_taxi, taxi_id)  # 仍然是原来的出租车
    
    def test_pickup_passenger(self):
        """测试接客功能"""
        print("测试接客功能...")
        
        # 先分配出租车
        taxi_id = 5001
        self.order.assign_taxi(taxi_id)
        
        # 接客
        current_time = 150
        result = self.order.pickup_passenger(current_time)
        
        print(f"出租车接客时间: {current_time}, 结果: {result}")
        print(f"订单状态: {self.order.status}, 接客时间: {self.order.pickup_time}")
        
        self.assertTrue(result)
        self.assertEqual(self.order.pickup_time, current_time)
        self.assertEqual(self.order.status, "picked_up")
        
        # 测试重复接客
        new_time = 160
        result = self.order.pickup_passenger(new_time)
        
        print(f"尝试重复接客，时间: {new_time}, 结果: {result}")
        print(f"订单状态: {self.order.status}, 接客时间: {self.order.pickup_time}")
        
        self.assertFalse(result)
        self.assertEqual(self.order.pickup_time, current_time)  # 时间没有改变
    
    def test_complete_order(self):
        """测试完成订单功能"""
        print("测试完成订单功能...")
        
        # 准备订单状态
        taxi_id = 5001
        pickup_time = 150
        self.order.assign_taxi(taxi_id)
        self.order.pickup_passenger(pickup_time)
        
        # 完成订单
        dropoff_time = 200
        fare = 35.5
        result = self.order.complete_order(dropoff_time, fare)
        
        print(f"完成订单，时间: {dropoff_time}, 费用: {fare}, 结果: {result}")
        print(f"订单状态: {self.order.status}, 到达时间: {self.order.dropoff_time}, 费用: {self.order.fare}")
        
        self.assertTrue(result)
        self.assertEqual(self.order.dropoff_time, dropoff_time)
        self.assertEqual(self.order.status, "completed")
        self.assertEqual(self.order.fare, fare)
        
        # 测试重复完成
        new_time = 210
        new_fare = 40.0
        result = self.order.complete_order(new_time, new_fare)
        
        print(f"尝试重复完成订单，时间: {new_time}, 费用: {new_fare}, 结果: {result}")
        print(f"订单状态: {self.order.status}, 到达时间: {self.order.dropoff_time}, 费用: {self.order.fare}")
        
        self.assertFalse(result)
        self.assertEqual(self.order.dropoff_time, dropoff_time)  # 时间没有改变
        self.assertEqual(self.order.fare, fare)  # 费用没有改变
    
    def test_complete_order_auto_fare(self):
        """测试自动计算费用的完成订单功能"""
        print("测试自动计算费用的完成订单功能...")
        
        # 准备订单状态
        taxi_id = 5001
        pickup_time = 150
        self.order.assign_taxi(taxi_id)
        self.order.pickup_passenger(pickup_time)
        
        # 完成订单，不指定费用
        dropoff_time = 200
        result = self.order.complete_order(dropoff_time)
        
        print(f"完成订单，时间: {dropoff_time}, 自动计算费用, 结果: {result}")
        print(f"订单状态: {self.order.status}, 到达时间: {self.order.dropoff_time}, 费用: {self.order.fare}")
        
        self.assertTrue(result)
        self.assertEqual(self.order.dropoff_time, dropoff_time)
        self.assertEqual(self.order.status, "completed")
        self.assertIsNotNone(self.order.fare)
        
        # 验证费用计算逻辑
        # 基础费用 + 时间费用 + 距离费用
        # 10.0 + (200-150)*0.5 + 距离*2.0
        expected_distance = ((self.dropoff_coord[0] - self.pickup_coord[0])**2 + 
                           (self.dropoff_coord[1] - self.pickup_coord[1])**2)**0.5
        expected_fare = 10.0 + (dropoff_time - pickup_time) * 0.5 + expected_distance * 2.0
        
        print(f"预期费用计算: 基础费用(10.0) + 时间费用({(dropoff_time - pickup_time) * 0.5}) + 距离费用({expected_distance * 2.0})")
        print(f"预期费用: {expected_fare}, 实际费用: {self.order.fare}")
        
        self.assertAlmostEqual(self.order.fare, expected_fare, places=2)
    
    def test_get_waiting_time(self):
        """测试获取等待时间功能"""
        print("测试获取等待时间功能...")
        
        # 初始状态，尚未接客
        waiting_time = self.order.get_waiting_time()
        print(f"初始状态，尚未接客，等待时间: {waiting_time}")
        self.assertIsNone(waiting_time)
        
        # 使用当前时间计算等待时间
        current_time = 130
        waiting_time = self.order.get_waiting_time(current_time)
        print(f"使用当前时间({current_time})计算，等待时间: {waiting_time}")
        self.assertEqual(waiting_time, current_time - self.request_time)
        
        # 接客后计算等待时间
        taxi_id = 5001
        pickup_time = 150
        self.order.assign_taxi(taxi_id)
        self.order.pickup_passenger(pickup_time)
        
        waiting_time = self.order.get_waiting_time()
        print(f"接客后(时间:{pickup_time})，等待时间: {waiting_time}")
        self.assertEqual(waiting_time, pickup_time - self.request_time)
    
    def test_get_trip_time(self):
        """测试获取行程时间功能"""
        print("测试获取行程时间功能...")
        
        # 初始状态，尚未完成
        trip_time = self.order.get_trip_time()
        print(f"初始状态，尚未完成，行程时间: {trip_time}")
        self.assertIsNone(trip_time)
        
        # 接客但未完成
        taxi_id = 5001
        pickup_time = 150
        self.order.assign_taxi(taxi_id)
        self.order.pickup_passenger(pickup_time)
        
        trip_time = self.order.get_trip_time()
        print(f"接客后但未完成，行程时间: {trip_time}")
        self.assertIsNone(trip_time)
        
        # 完成订单后
        dropoff_time = 200
        self.order.complete_order(dropoff_time)
        
        trip_time = self.order.get_trip_time()
        print(f"完成订单后，行程时间: {trip_time}")
        self.assertEqual(trip_time, dropoff_time - pickup_time)
    
    def test_get_total_time(self):
        """测试获取总时间功能"""
        print("测试获取总时间功能...")
        
        # 初始状态，尚未完成
        total_time = self.order.get_total_time()
        print(f"初始状态，尚未完成，总时间: {total_time}")
        self.assertIsNone(total_time)
        
        # 完成订单后
        taxi_id = 5001
        pickup_time = 150
        dropoff_time = 200
        self.order.assign_taxi(taxi_id)
        self.order.pickup_passenger(pickup_time)
        self.order.complete_order(dropoff_time)
        
        total_time = self.order.get_total_time()
        print(f"完成订单后，总时间: {total_time}")
        self.assertEqual(total_time, dropoff_time - self.request_time)

# 自定义TestRunner
class CustomTestRunner(unittest.TextTestRunner):
    def run(self, test):
        print("\n=== 开始测试订单实体类 ===\n")
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
