# 2025.4.24 yh

class TaxiEntity:
    """
    出租车实体类，表示仿真环境中的出租车实体
    每辆出租车有独立的ID、当前位置、状态以及订单信息
    """
    
    def __init__(self, taxi_id: int, position_node: int, driver_preference: str = ""):
        """
        初始化出租车实体
        
        参数:
            taxi_id: 出租车的唯一标识符
            position_node: 出租车初始位置(节点编号)
            driver_preference: 驾驶员偏好，默认为空字符串
        """
        self.taxi_id = taxi_id                  # 出租车的唯一标识符
        self.driver_preference = driver_preference  # 驾驶员偏好
        self.status = "idle"                    # 出租车当前状态，初始为空闲
        self.position_node = position_node      # 出租车当前位置(节点编号)
        self.current_order = None               # 当前出租车正在处理的订单ID，无订单时为None
        self.current_destination = None         # 当前出租车的目的地节点，无则为None
        self.current_route = None               # 到达目的地的路线及每一个路段的时间，无则为None
        self.order_history = []                 # 出租车接取的订单列表
        self.route_history = []                 # 出租车历史路线(路口id, 时间)
    
    def assign_order(self, order_id: int, pickup_node: int, route: list[(int, int)]):
        """
        分配订单给出租车
        参数:
            order_id: 订单ID
            pickup_node: 乘客上车位置(节点编号)
            route: 到达接客点的路线及时间
        """
        # 只有空闲状态的出租车才能接单
        if self.status != "idle":
            return False
        
        self.status = "enroute_pickup"
        self.current_order = order_id
        # 设置目的地为乘客位置
        self.current_destination = pickup_node
        # route 格式为 [(node1, time1), (node2, time2), ...]
        self.current_route = route
        self.order_history.append(order_id)
        self.route_history.extend(route)
        return True
    
    def _arrive_at_pickup(self):
        """
        到达接客点，更新为载客状态
        参数:
            destination_node: 乘客目的地(节点编号)
            route: 到达目的地的路线及时间
        """
        if self.status != "enroute_pickup":
            return False
        
        self.status = "occupied"
        self.position_node = self.current_destination  # 更新位置为接客点
        self.current_destination = self.current_route[-1][0]
        return True
    
    def _complete_order(self):
        """
        完成订单，更新为空闲状态
        """
        if self.status != "occupied":
            return False
        
        self.status = "idle"
        self.position_node = self.current_destination  # 更新位置为乘客目的地
        self.current_order = None
        self.current_destination = None
        self.current_route = None
        return True
    
    def start_repositioning(self, destination_node: int, route: list[(int, int)]):
        """
        开始重新定位，更新为重新定位状态
        参数:
            destination_node: 重新定位的目标位置(节点编号)
            route: 到达目标位置的路线及时间
        """
        if self.status != "idle":
            return False
        
        self.status = "repositioning"
        self.current_destination = destination_node
        self.current_route = route
        self.route_history.extend(route)
        return True
    
    def _complete_repositioning(self):
        """
        完成重新定位，更新为空闲状态
        """
        if self.status != "repositioning":
            return False
        
        self.status = "idle"
        self.position_node = self.current_destination  # 更新位置为重新定位的目标位置
        self.current_destination = None
        self.current_route = None
        return True
    
    def update_position(self, current_time: int):
        """
        根据当前时间更新出租车位置
        参数:
            current_time: 当前时间
        返回:
            bool: 如果到达目的地返回True，否则返回False
        """
        # 如果没有路线或不在移动状态，不需要更新
        if not self.current_route or self.status not in ["enroute_pickup", "occupied", "repositioning"]:
            return False
        
        order_id = self.current_order
        order_status = None
        order_time = None
        # 找到当前时间应该在的位置
        new_position = None
        if self.status == "enroute_pickup":
            for node, arrival_time in self.current_route:
                if arrival_time > current_time:
                    break
                new_position = node
                # 成功接到人，特殊处理
                if new_position == self.current_destination:
                    order_status = "picked_up"
                    order_time = arrival_time
                    self._arrive_at_pickup()
        else:
            for node, arrival_time in self.current_route:
                if arrival_time > current_time:
                    break
                new_position = node
        
        # 如果找到了新位置，更新出租车位置
        if new_position is not None:
            self.position_node = new_position
        
        # 检查是否到达目的地（路线的最后一个节点）
        last_node, last_time = self.current_route[-1]
        if current_time >= last_time:
            self.position_node = last_node
            # 已到达目的地
            if self.status == "occupied":
                self._complete_order()
                order_status = "completed"    
                order_time = last_time
            elif self.status == "repositioning":
                self._complete_repositioning()

        # 变化后的订单及其状态
        if order_status: return (order_id, order_status, order_time)
        return None  # 订单状态未变化