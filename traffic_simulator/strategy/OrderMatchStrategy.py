import random
from typing import Dict, List, Tuple, Any, Optional

class TaxiMatchingStrategy:
    """
    出租车匹配策略类
    根据指定的策略名称，使用不同的算法匹配出租车和订单
    """
    
    def __init__(self, strategy_name: str = "random"):
        """
        初始化匹配策略
        
        参数:
            strategy_name: 策略名称，可选值为 "random", "nearest", "batch"
        """
        self.strategy_name = strategy_name.lower()
        self.strategy_map = {
            "random": self._random_matching,
            "nearest": self._nearest_taxi_matching,
            "batch": self._batch_matching
        }
        
        if self.strategy_name not in self.strategy_map:
            print(f"警告: 未知的策略名称 '{strategy_name}'，将使用随机匹配策略")
            self.strategy_name = "random"
            
        print(f"已初始化出租车匹配策略: {self.strategy_name}")
    
    def match(self, cost_matrix: Dict[int, Dict[int, int]], **kwargs) -> List[Tuple[int, int]]:
        """
        统一的匹配接口，根据初始化时指定的策略调用相应的匹配方法
        参数:
            cost_matrix: 出租车到订单的花费时间邻接字典，格式为 {taxi_id: {order_id: cost, ...}, ...}
            **kwargs: 额外参数，可能被特定策略使用
        返回:
            匹配结果列表，每个元素为(taxi_id, order_id)
        """
        # 调用对应的策略方法
        strategy_func = self.strategy_map[self.strategy_name]
        return strategy_func(cost_matrix, **kwargs)
    
    def _random_matching(self, cost_matrix: Dict[int, Dict[int, int]], **kwargs) -> List[Tuple[int, int]]:
        """
        随机匹配策略
        随机将订单分配给出租车，每辆出租车最多分配一个订单
        参数:
            cost_matrix: 出租车到订单的花费时间邻接字典，格式为 {taxi_id: {order_id: cost, ...}, ...}
        返回:
            匹配结果列表，每个元素为(taxi_id, order_id)
        """
        if not cost_matrix:
            return []
        
        # 获取出租车ID列表
        taxi_ids = list(cost_matrix.keys())
        
        # 如果没有出租车，返回空列表
        if not taxi_ids:
            return []
            
        # 获取订单ID列表（从第一个出租车的邻接字典中提取）
        order_ids = list(cost_matrix[taxi_ids[0]].keys())
        
        # 如果没有订单，返回空列表
        if not order_ids:
            return []
        
        # 随机打乱ID列表
        random.shuffle(taxi_ids)
        random.shuffle(order_ids)
        
        # 为了避免重复分配，我们需要跟踪已分配的出租车和订单
        assigned_taxis = set()
        assigned_orders = set()
        matches = []
        
        # 尝试为每辆出租车分配一个订单
        for taxi_id in taxi_ids:
            if taxi_id in assigned_taxis:
                continue
                
            # 查找一个未分配的订单
            for order_id in order_ids:
                if order_id in assigned_orders:
                    continue
                    
                # 确保该出租车可以到达该订单（在邻接字典中有对应的条目）
                if order_id in cost_matrix[taxi_id]:
                    matches.append((taxi_id, order_id))
                    assigned_taxis.add(taxi_id)
                    assigned_orders.add(order_id)
                    break
            
        return matches
    
    def _nearest_taxi_matching(self, cost_matrix: Dict[int, Dict[int, int]], **kwargs) -> List[Tuple[int, int]]:
        """
        最近出租车匹配策略
        为每个订单分配花费时间最少的出租车，且出租车接单的最远时间不超过300秒
        
        参数:
            cost_matrix: 出租车到订单的花费时间邻接字典，格式为 {taxi_id: {order_id: cost, ...}, ...}
            **kwargs: 可选参数
            
        返回:
            匹配结果列表，每个元素为(taxi_id, order_id)
        """
        if not cost_matrix:
            return []
        
        # 获取出租车ID列表
        taxi_ids = list(cost_matrix.keys())
        
        # 如果没有出租车，返回空列表
        if not taxi_ids:
            return []
        
        # 获取订单ID列表（从第一个出租车的邻接字典中提取）
        # 确保至少有一个出租车存在且有订单信息
        if not taxi_ids or not cost_matrix[taxi_ids[0]]:
            return []
        
        order_ids = list(cost_matrix[taxi_ids[0]].keys())
        
        # 如果没有订单，返回空列表
        if not order_ids:
            return []
        
        # 设置最大接单时间限制（300秒）
        MAX_TRAVEL_TIME = 300
        
        # 为了避免重复分配，我们需要跟踪已分配的出租车和订单
        assigned_taxis = set()
        assigned_orders = set()
        matches = []
        
        # 为每个订单找到最近的出租车
        for order_id in order_ids:
            if order_id in assigned_orders:
                continue
            
            best_taxi = None
            min_cost = float('inf')
            
            # 找到距离该订单最近的未分配出租车
            for taxi_id in taxi_ids:
                if taxi_id in assigned_taxis:
                    continue
                
                # 检查该出租车是否可以到达该订单，且旅行时间不超过300秒
                if order_id in cost_matrix[taxi_id]:
                    cost = cost_matrix[taxi_id][order_id]
                    if cost <= MAX_TRAVEL_TIME and cost < min_cost:
                        min_cost = cost
                        best_taxi = taxi_id
            
            # 如果找到了合适的出租车，进行匹配
            if best_taxi:
                matches.append((best_taxi, order_id))
                assigned_taxis.add(best_taxi)
                assigned_orders.add(order_id)
        
        return matches

    
    def _batch_matching(self, cost_matrix: Dict[int, Dict[int, int]], **kwargs) -> List[Tuple[int, int]]:
        """
        批量匹配策略（占位，未完全实现）
        考虑全局最优的批量匹配算法
        
        参数:
            cost_matrix: 出租车到订单的花费时间邻接字典，格式为 {taxi_id: {order_id: cost, ...}, ...}
            
        返回:
            匹配结果列表，每个元素为(taxi_id, order_id)
        """
        # 这里应该实现匈牙利算法或其他全局最优匹配算法
        # 暂时使用最近出租车匹配策略代替
        print("批量匹配策略尚未完全实现，使用最近出租车匹配代替")
        return self._nearest_taxi_matching(cost_matrix)
