# 2025.4.24 yh

import json
import os
from datetime import datetime
from traffic_simulator.entity.OrderEntity import OrderEntity

class OrderManager:
    """订单管理类"""
    
    def __init__(self, orders_df, start_time):
        """
        初始化订单管理器
        参数:
            orders_df: 包含订单信息的DataFrame (可选)，
                      应包含列：'id', 'pickup_node', 'dropoff_node', 'ot' (出发时间)
        """
        self.orders = {}  # 存储所有订单，以order_id为键
        # 订单取消时间
        self.waiting_threshold = 300
        
        # 如果提供了DataFrame，则从中初始化订单
        if orders_df is not None:
            self._init_from_dataframe(orders_df, start_time)
    
    def _init_from_dataframe(self, orders_df, start_time):
        """
        从DataFrame初始化订单
        参数:
            orders_df: 包含订单信息的DataFrame，
                      应包含列：'id', 'pickup_node', 'dropoff_node', 'ot' (出发时间)
        """
        # 验证DataFrame是否包含必要的列
        required_columns = ['id', 'pickup_node', 'dropoff_node', 'ot']
        missing_columns = [col for col in required_columns if col not in orders_df.columns]
        
        if missing_columns:
            raise ValueError(f"订单DataFrame缺少必要的列: {', '.join(missing_columns)}")
        
        # 从DataFrame创建订单
        for _, row in orders_df.iterrows():
            if row['ot'] < start_time: continue
            order_id = row['id']
            
            # 创建OrderEntity对象
            order = OrderEntity(
                order_id=order_id,
                pickup_node=row['pickup_node'],
                dropoff_node=row['dropoff_node'],
                request_time=row['ot'],
            )
            # 将订单添加到管理系统
            self.orders[order_id] = order

        print(f"已初始化订单系统，共 {len(orders_df)} 个订单")
    
    def get_order(self, order_id):
        """根据ID获取订单"""
        return self.orders.get(order_id)
    
    def get_waiting_orders(self, current_time):
        """
        获取指定时间范围内等待中的订单，并将超时订单设为取消
        参数:
            current_time: 当前时间（包含）
        返回:
            list: 符合条件的等待订单列表（不包括已取消的超时订单）
        """
        # 先获取所有符合条件的等待订单
        waiting_orders = [
            order for order in self.orders.values() 
            if (order.status == "waiting" and 
                order.request_time <= current_time)
        ]
        
        # 在获取到的等待订单中检查并处理超时订单
        for order in waiting_orders:
            if current_time - order.request_time > self.waiting_threshold:
                order.status = "cancelled"
                order.cancel_time = current_time
        
        # 返回剩余的等待订单（排除已取消的）
        return [order for order in waiting_orders if order.status == "waiting"]
    
    def assign_order(self, order_id, taxi_id, current_time):
        """
        将订单分配给出租车
        
        参数:
            order_id: 订单ID
            taxi_id: 出租车ID
            current_time: 当前时间
        """
        order = self.get_order(order_id)
        if order and order.status == "waiting":
            order.status = "assigned"
            order.assigned_taxi = taxi_id
            order.assigned_time = current_time
            return True
        return False
    
    def pickup_order(self, order_id, current_time):
        """
        标记订单为已接客
        参数:
            order_id: 订单ID
            current_time: 当前时间
        """
        order = self.get_order(order_id)
        if order and order.status == "assigned":
            order.status = "picked_up"
            order.pickup_time = current_time
            return True
        return False
    
    def complete_order(self, order_id, current_time):
        """
        完成订单
        参数:
            order_id: 订单ID
            current_time: 当前时间
            fare: 订单费用 (可选)
        """
        order = self.get_order(order_id)
        if order and order.status == "picked_up":
            order.status = "completed"
            order.dropoff_time = current_time
            return True
        return False
    
    def change_orders_status(self, order_list):
        """
        批量修改订单状态和相关时间
        
        参数:
            order_list: 包含需要修改订单信息的列表，每个元素是一个元组
                    格式为 (order_id, order_status, order_time)
        """
        for order_info in order_list:
            order_id, order_status, order_time = order_info
            
            # 如果订单存在，则更新状态和时间
            if order_id in self.orders:
                order = self.orders[order_id]
                order.status = order_status
                
                # 根据新状态更新相应的时间字段
                if order_status == "picked_up":
                    order.pickup_time = order_time
                elif order_status == "completed":
                    order.dropoff_time = order_time

    
    def export_orders_to_json(self, start_time, end_time, saved):
        """
        将所有订单导出为JSON格式并保存到results文件夹
        文件名自动包含时间戳，精确到分钟
        返回:
            bool: 操作是否成功
        """
        try:
            # 创建要导出的数据结构
            orders_data = {}
            
            for order_id, order in self.orders.items():
                if order.request_time < start_time or order.request_time > end_time:
                    continue
                # 将每个订单对象转换为字典
                order_dict = {
                    "order_id": int(order.order_id),
                    "pickup_node": int(order.pickup_node),
                    "dropoff_node": int(order.dropoff_node),
                    "request_time": int(order.request_time),
                    "assigned_taxi": order.assigned_taxi,
                    "assigned_time": order.assigned_time,
                    "pickup_time": order.pickup_time,
                    "dropoff_time": order.dropoff_time,
                    "status": order.status
                }
                
                # 添加到总数据中
                orders_data[int(order_id)] = order_dict
            
            if saved:
                # 获取当前时间并格式化为时间戳（精确到分钟）
                current_time = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"orders_history_{current_time}.json"
                
                # 获取当前文件所在目录
                current_dir = os.path.dirname(__file__)
                # 获取上上一级目录
                parent_dir = os.path.dirname(os.path.dirname(current_dir))
                # 设置results文件夹路径
                results_dir = os.path.join(parent_dir, "results")
                
                # 确保results目录存在
                os.makedirs(results_dir, exist_ok=True)
                
                # 完整的文件路径
                file_path = os.path.join(results_dir, filename)
                
                # 写入JSON文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(orders_data, f, indent=4, ensure_ascii=False)
                    
                print(f"订单数据已成功导出到: {file_path}")
                return orders_data
            
        except Exception as e:
            print(f"导出订单数据时出错: {str(e)}")
            return None

