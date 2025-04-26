# 2025.4.26 yh

class OrderEntity:
    """
    订单实体类，表示出租车仿真环境中的一个乘客订单请求，
    记录乘客的起点、终点、请求时间，以及订单的分配和完成状态。
    """
    
    def __init__(self, order_id, pickup_node, dropoff_node, request_time):
        """
        初始化订单实体
        参数:
            order_id (int): 订单的唯一标识符
            pickup_node (int): 乘客起点的节点编号
            dropoff_node (int): 乘客终点的节点编号
            request_time (int): 订单发出的时间(仿真时间戳)
        """
        self.order_id = order_id
        self.pickup_node = pickup_node
        self.dropoff_node = dropoff_node
        self.request_time = request_time
        
        # 初始化其他属性
        self.assigned_taxi = None  # 被分配执行该订单的出租车ID
        self.assigned_time = None  # 被分配出租车的时间
        self.pickup_time = None    # 出租车实际接到乘客的时间
        self.dropoff_time = None   # 乘客实际到达目的地的时间
        self.status = "waiting"    # 初始状态为等待分配
    
    def assign_taxi(self, taxi_id, current_time):
        """
        将订单分配给指定的出租车
        参数:
            taxi_id (int): 出租车ID
        返回:
            bool: 分配是否成功
        """
        if self.status != "waiting":
            return False
            
        self.assigned_taxi = taxi_id
        self.assigned_time = current_time
        self.status = "assigned"
        return True
    
    def pickup_passenger(self, current_time):
        """
        记录出租车接到乘客
        参数:
            current_time (int): 当前仿真时间
        返回:
            bool: 操作是否成功
        """
        if self.status != "assigned":
            return False
            
        self.pickup_time = current_time
        self.status = "picked_up"
        return True
    
    def complete_order(self, current_time):
        """
        完成订单，记录到达目的地的时间和费用
        参数:
            current_time (int): 当前仿真时间
        返回:
            bool: 操作是否成功
        """
        if self.status != "picked_up":
            return False
            
        self.dropoff_time = current_time
        self.status = "completed"
        
        return True
    