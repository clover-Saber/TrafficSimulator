# 2025.4.24 yh
from tqdm import tqdm
from traffic_simulator.manager.FleetManager import FleetManager
from traffic_simulator.manager.OrderManager import OrderManager
from traffic_simulator.manager.RoadNetworkManager import RoadNetworkManager
from traffic_simulator.strategy.OrderMatchStrategy import TaxiMatchingStrategy
from traffic_simulator.strategy.TaxiRepositionStrategy import TaxiRepositionStrategy
from traffic_simulator.tool.AnalyzerTool import OrderAnalyzer

class TrafficSimulator:
    """交通模拟器类"""
    
    def __init__(self, taxi_number, start_time, time_window, road_network, orders_df, order_match_strategy="nearest", taxi_reposition_strategy="random", order_saved=False, fleet_saved=False):
        """
        初始化交通模拟器
        """
        self.order_saved = order_saved
        self.fleet_saved = fleet_saved
        # 初始化管理器
        self.road_network_manager = RoadNetworkManager(road_network)
        taxi_init_positions = self.generate_taxi_positions(taxi_number)
        self.fleet_manager = FleetManager(taxi_init_positions)
        self.order_manager = OrderManager(orders_df, start_time)
        
        # 初始化策略
        self.matching_strategy = TaxiMatchingStrategy(strategy_name=order_match_strategy)
        self.repositioning_strategy = TaxiRepositionStrategy(strategy_name="random")
        
        # 初始化仿真时间
        self.start_time = start_time
        self.end_time = None
        self.current_time = start_time
        self.time_window = time_window


    def generate_taxi_positions(self, taxi_number):
        """
        根据指定的出租车数量生成随机初始位置列表
        参数:
            taxi_number: 出租车数量
        返回:
            节点ID列表，表示每辆出租车的初始位置
        """
        if taxi_number <= 0:
            raise ValueError("出租车数量必须大于0")
            
        # 随机选择节点作为初始位置
        positions = []
        for _ in range(taxi_number):
            # 随机选择一个节点作为初始位置
            position_node = self.road_network_manager.get_random_node()
            positions.append(position_node)
        return positions

    
    def step(self):
        """执行一次仿真步骤"""
        # 1. 更新时间
        self.current_time += self.time_window
        
        # 2. 更新出租车状态
        order_list = self.fleet_manager.update_taxis_position(self.current_time)
        self.order_manager.change_orders_status(order_list)
        
        # 3. 匹配订单
        self._match_and_assign_orders()
        
        # 4. 重定位空闲出租车
        self._reposition_idle_taxis()
        
        # 返回当前时间
        return self.current_time
    
    def _match_and_assign_orders(self):
        """匹配并分配订单"""
        # 获取空闲出租车和等待订单
        idle_taxis = self.fleet_manager.get_idle_taxis()
        waiting_orders = self.order_manager.get_waiting_orders(self.current_time)
        
        if not idle_taxis or not waiting_orders:
            return
        
        # 构建成本矩阵
        cost_matrix = {}
        
        for taxi in idle_taxis:
            taxi_id = taxi.taxi_id
            cost_matrix[taxi_id] = {}
            
            for order in waiting_orders:
                order_id = order.order_id
                
                # 计算从出租车当前位置到接客点的成本（例如距离或时间）
                cost = self.road_network_manager.calculate_shortest_travel_time(taxi.position_node, order.pickup_node)
                
                cost_matrix[taxi_id][order_id] = cost
        
        # 执行匹配策略
        matches = self.matching_strategy.match(cost_matrix)
        
        # 分配订单
        for taxi_id, order_id in matches:
            # 更新订单状态
            self.order_manager.assign_order(order_id, taxi_id, self.current_time)
            
            # 获取订单和出租车对象
            order = self.order_manager.get_order(order_id)
            taxi = self.fleet_manager.get_taxi(taxi_id)
            
            if order and taxi:
                route_1 = self.road_network_manager.calculate_shortest_path(taxi.position_node, order.pickup_node, self.current_time)
                route_2 = self.road_network_manager.calculate_shortest_path(order.pickup_node, order.dropoff_node, route_1[-1][1])
                # 合并两条路径
                complete_route = route_1 + route_2
                self.fleet_manager.assign_order_to_taxi(taxi_id, order.order_id, order.pickup_node, complete_route)
                

    
    def _reposition_idle_taxis(self):
        """重定位空闲出租车"""
        # 获取仍然空闲的出租车
        idle_taxis = self.fleet_manager.get_idle_taxis()
        
        if not idle_taxis:
            return
        
        # 执行重定位策略
        reposition_plan = self.repositioning_strategy.reposition(
            idle_taxis,
            self.road_network_manager,
            self.current_time
        )

        # 执行重定位计划
        self.fleet_manager.reposition_idle_taxis(reposition_plan)
        
    
    def run_simulation(self, until_step):
        """
        运行仿真直到指定时间
        参数:
            until_time: 结束时间
        """
        print(f"开始仿真，当前时间: {self.current_time}, 目标时间步: {until_step}")
        self.end_time = self.start_time + until_step * self.time_window
        
        for _ in tqdm(range(until_step), desc="Simulation Progress", unit="step"):
            self.step()

        print(f"仿真结束，当前时间: {self.current_time}")

        order_result = self.order_manager.export_orders_to_json(self.start_time, self.end_time, saved=self.order_saved)
        fleet_result = self.fleet_manager.export_history_to_json(saved=self.fleet_saved)

        analyzer = OrderAnalyzer(order_result)
        # 生成关键指标报告
        report = analyzer.generate_key_metrics_report()
        print(report)


