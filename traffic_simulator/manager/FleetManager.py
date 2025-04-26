# 2025.4.26 yh

import json
import os
from datetime import datetime
from traffic_simulator.entity.TaxiEntity import TaxiEntity

class FleetManager:
    def __init__(self, taxi_init_positions):
        """初始化车队管理类"""
        self.taxis = {}  # dict[int, TaxiEntity] - 存储所有出租车实体，以 taxi_id 为键
        # 初始出租车车队
        self._initialize_fleet_with_positions(taxi_init_positions)

    def _initialize_fleet_with_positions(self, taxi_init_positions):
        """
        根据提供的位置列表初始化出租车
        参数:
            taxi_positions: 出租车位置列表，每个元素为节点ID，表示一辆出租车的初始位置
        """
        # 创建出租车并分配指定位置
        for position_node in taxi_init_positions:
            taxi_id = len(self.taxis) + 1
            
            # 创建出租车实体
            taxi = TaxiEntity(taxi_id, position_node)
            # 添加到管理器
            self._add_taxi(taxi)
            
        print(f"已初始化车队，共 {len(taxi_init_positions)} 辆出租车")
    
    def _add_taxi(self, taxi):
        """
        添加出租车到管理器
        参数:
            taxi: TaxiEntity对象
        返回:
            添加的出租车ID
        """
        self.taxis[taxi.taxi_id] = taxi
        return taxi.taxi_id

    def get_taxi(self, taxi_id):
        return self.taxis[taxi_id]
    
    def assign_order_to_taxi(self, taxi_id: int, order_id: int, pickup_node: int, route) -> None:
        """
        将订单分配给指定出租车，更新为 enroute_pickup 状态，并设定目标位置
        参数:
            taxi_id: 出租车ID
            order: 订单实体
            current_time: 当前时间
        """
        # 检查出租车是否存在
        if taxi_id not in self.taxis:
            print(f"出租车 {taxi_id} 不存在，无法分配订单")
            return
                
        taxi = self.taxis[taxi_id]
        taxi.assign_order(order_id, pickup_node, route)
        
    
    def update_taxis_position(self, current_time: int):
        """
        更新enroute_pickup、occupied和repositioning状态出租车的位置
        如果车辆到达目的地，则更新车辆状态
        参数:
            current_time: 当前时间
        """
        order_list = []
        for taxi_id, taxi in self.taxis.items():
            # 更新位置
            change_order = taxi.update_position(current_time)
            if change_order: order_list.append(change_order)

        return order_list
    
    def get_idle_taxis(self) -> list[TaxiEntity]:
        """
        获取所有当前空闲出租车的列表
        返回:
            list[TaxiEntity]: 空闲出租车列表
        """
        idle_taxis = []
        for taxi_id, taxi in self.taxis.items():
            if taxi.status == "idle":
                idle_taxis.append(taxi)
        return idle_taxis
    
    def reposition_idle_taxis(self, strategy_list: list[(int, int, list[(int, int)])]):
        """
        根据外部传入的策略，对空闲出租车分配新的目标节点和路线
        
        参数:
            strategy_list: 包含(taxi_id, destination_node, route)元组的列表
        """
        for taxi_id, destination_node, route in strategy_list:
            # 检查出租车是否存在
            if taxi_id not in self.taxis:
                continue
                
            taxi = self.taxis[taxi_id]
            
            # 只有空闲的出租车才能重新定位
            if taxi.status != "idle":
                continue
                
            # 更新出租车状态为重新定位
            taxi.status = "repositioning"
            taxi.current_destination = destination_node
            taxi.current_route = route
    
    def export_history_to_json(self):
        """
        将车队中每辆出租车的订单历史和路线历史保存为JSON格式
        
        参数:
            file_path: 保存JSON文件的路径，默认为'fleet_history.json'
        
        返回:
            bool: 保存成功返回True，否则返回False
        """
        import json
        from datetime import datetime
        
        try:
            fleet_data = {}
            
            # 遍历所有出租车
            for taxi_id, taxi in self.taxis.items():
                # 为每辆出租车创建数据结构
                taxi_data = {
                    "taxi_id": taxi_id,
                    "order_history": [],
                    "route_history": []
                }
                
                # 添加订单历史
                if hasattr(taxi, "order_history"):
                    for order in taxi.order_history:
                        order_data = {
                            "order_id": int(order),
                        }
                        taxi_data["order_history"].append(order_data)
                
                # 添加路线历史
                if hasattr(taxi, "route_history"):
                    for route in taxi.route_history:
                        route_data = {
                            "position": route[0],
                            "timestamp": route[1],
                        }
                        taxi_data["route_history"].append(route_data)
                
                fleet_data[str(taxi_id)] = taxi_data
            
            # 添加元数据
            result = {
                "metadata": {
                    "generated_time": datetime.now().isoformat(),
                    "total_taxis": len(self.taxis)
                },
                "fleet_data": fleet_data
            }
            
            # 获取当前时间并格式化为时间戳（精确到分钟）
            current_time = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"fleet_history_{current_time}.json"
            
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
                json.dump(fleet_data, f, indent=4, ensure_ascii=False)
            
            # 写入JSON文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
            
            print(f"车队历史记录已成功保存至 {file_path}")
            return True
            
        except Exception as e:
            print(f"保存车队历史记录失败: {str(e)}")
            return False
