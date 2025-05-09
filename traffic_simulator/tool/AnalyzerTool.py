import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional


class OrderAnalyzer:
    """订单数据分析类，用于统计和分析仿真结果"""
    
    def __init__(self, orders_data: Dict[str, Dict[str, Any]] = None):
        """
        初始化分析器
        Args:
            orders_data: 订单数据字典
        """
        self.orders_data = orders_data
        self.orders_df = None
        
        if orders_data:
            self.load_data(orders_data)
    
    def load_data(self, orders_data: Dict[str, Dict[str, Any]]) -> None:
        """
        加载订单数据并转换为DataFrame
        Args:
            orders_data: 订单数据字典
        """
        self.orders_data = orders_data
        self.orders_df = pd.DataFrame.from_dict(orders_data, orient='index')
    
    def analyze_key_metrics(self) -> Dict[str, Any]:
        """
        分析订单数据并返回关键指标
        Returns:
            包含关键统计指标的字典
        """
        if self.orders_df is None:
            raise ValueError("请先加载数据")
        
        # 创建结果字典
        results = {}
        
        # 1. 订单总数
        total_orders = len(self.orders_df)
        results['total_orders'] = total_orders
        
        # 2. 响应率（已分配出租车的订单比例）
        responded_orders = self.orders_df[self.orders_df['assigned_taxi'].notna()]
        response_rate = len(responded_orders) / total_orders if total_orders > 0 else 0
        results['response_rate'] = response_rate
        
        # 3. 平均响应等待时间（从请求到分配的时间）
        # 使用 .loc 避免 SettingWithCopyWarning
        self.orders_df.loc[:, 'response_wait_time'] = self.orders_df['assigned_time'] - self.orders_df['request_time']
        avg_response_wait_time = self.orders_df['response_wait_time'].mean()
        results['avg_response_wait_time'] = avg_response_wait_time
        
        # 4. 平均响应后的接客时间（从分配到接客的时间）
        # 创建一个新的 DataFrame，而不是视图
        pickup_mask = self.orders_df['pickup_time'].notna()
        if pickup_mask.any():
            # 计算并直接存储结果，不修改原始 DataFrame
            pickup_after_assignment = self.orders_df.loc[pickup_mask, 'pickup_time'] - self.orders_df.loc[pickup_mask, 'assigned_time']
            avg_pickup_after_assignment = pickup_after_assignment.mean()
            results['avg_pickup_after_assignment'] = avg_pickup_after_assignment
        else:
            results['avg_pickup_after_assignment'] = None
        
        # 5. 平均行程时间（从接客到送达的时间）
        trip_mask = (self.orders_df['pickup_time'].notna()) & (self.orders_df['dropoff_time'].notna())
        if trip_mask.any():
            # 计算并直接存储结果，不修改原始 DataFrame
            trip_time = self.orders_df.loc[trip_mask, 'dropoff_time'] - self.orders_df.loc[trip_mask, 'pickup_time']
            avg_trip_time = trip_time.mean()
            results['avg_trip_time'] = avg_trip_time
            # 检查负的行程时间
            negative_trip_count = (trip_time < 0).sum()
            results['special_case_negative_trip'] = negative_trip_count
        else:
            results['avg_trip_time'] = None
            results['special_case_negative_trip'] = 0
        
        # 6. 特殊情况订单
        # 6.1 无接客时间但有送达时间的订单
        special_case1 = self.orders_df[(self.orders_df['pickup_time'].isna()) & 
                                      (self.orders_df['dropoff_time'].notna())]
        results['special_case_no_pickup'] = len(special_case1)
        
        # 6.2 起点终点相同的订单
        special_case2 = self.orders_df[self.orders_df['pickup_node'] == self.orders_df['dropoff_node']]
        results['special_case_same_location'] = len(special_case2)
        
        # 6.3 分配时间异常的订单（分配时间早于请求时间）
        special_case3 = self.orders_df[self.orders_df['assigned_time'] < self.orders_df['request_time']]
        results['special_case_invalid_assignment'] = len(special_case3)
        
        # 汇总所有特殊情况
        results['total_special_cases'] = (
            results['special_case_no_pickup'] + 
            results['special_case_same_location'] + 
            results['special_case_invalid_assignment'] + 
            results['special_case_negative_trip']
        )

        # 7. 计算平均车辆占用率
        # 首先获取所有有效订单（有分配出租车的订单）
        valid_orders = self.orders_df[self.orders_df['assigned_taxi'].notna()].copy()
        
        if len(valid_orders) > 0:
            # 按出租车ID分组
            taxi_groups = valid_orders.groupby('assigned_taxi')
            
            # 计算每辆出租车的占用率并求平均
            taxi_occupancy_rates = []
            simulation_start_time = valid_orders['request_time'].min()
            simulation_end_time = max(
                valid_orders['request_time'].max(),
                valid_orders['dropoff_time'].dropna().max() if not valid_orders['dropoff_time'].dropna().empty else 0
            )
            simulation_duration = simulation_end_time - simulation_start_time
            
            if simulation_duration > 0:
                for taxi_id, taxi_orders in taxi_groups:
                    # 确保订单按时间排序
                    taxi_orders = taxi_orders.sort_values('assigned_time')
                    
                    # 计算载客时间总和
                    occupied_time = 0
                    for _, order in taxi_orders.iterrows():
                        if pd.notna(order['assigned_time']) and pd.notna(order['dropoff_time']):
                            # 只计算有效的载客时间（接客到送达）
                            occupied_time += max(0, order['dropoff_time'] - order['assigned_time'])
                    
                    # 计算该出租车的占用率
                    taxi_occupancy_rate = occupied_time / simulation_duration
                    taxi_occupancy_rates.append(taxi_occupancy_rate)
                
                # 计算平均占用率
                avg_occupancy_rate = sum(taxi_occupancy_rates) / len(taxi_occupancy_rates) if taxi_occupancy_rates else 0
                results['avg_vehicle_occupancy_rate'] = avg_occupancy_rate
            else:
                results['avg_vehicle_occupancy_rate'] = 0
        else:
            results['avg_vehicle_occupancy_rate'] = 0
        
        return results

        
    def get_special_cases_details(self) -> Dict[str, pd.DataFrame]:
        """
        获取特殊情况订单的详细信息
        
        Returns:
            包含各类特殊情况订单详情的字典
        """
        if self.orders_df is None:
            raise ValueError("请先加载数据")
        
        special_cases = {}
        
        # 无接客时间但有送达时间的订单
        special_cases['no_pickup'] = self.orders_df[(self.orders_df['pickup_time'].isna()) & 
                                                   (self.orders_df['dropoff_time'].notna())].copy()
        
        # 起点终点相同的订单
        special_cases['same_location'] = self.orders_df[self.orders_df['pickup_node'] == self.orders_df['dropoff_node']].copy()
        
        # 分配时间异常的订单
        special_cases['invalid_assignment'] = self.orders_df[self.orders_df['assigned_time'] < self.orders_df['request_time']].copy()
        
        # 行程时间为负的订单
        trip_mask = (self.orders_df['pickup_time'].notna()) & (self.orders_df['dropoff_time'].notna())
        if trip_mask.any():
            # 创建一个新的DataFrame，而不是视图
            trip_df = self.orders_df[trip_mask].copy()
            trip_df['trip_time'] = trip_df['dropoff_time'] - trip_df['pickup_time']
            special_cases['negative_trip'] = trip_df[trip_df['trip_time'] < 0]
        else:
            special_cases['negative_trip'] = pd.DataFrame()
        
        return special_cases
    
    def generate_key_metrics_report(self) -> str:
        """
        生成关键指标报告
        
        Returns:
            关键指标报告字符串
        """
        metrics = self.analyze_key_metrics()
        
        report = "===== 订单关键指标分析报告 =====\n"
        
        # 1. 订单总数
        report += f"1. 订单总数: {metrics['total_orders']}\n"
        
        # 2. 响应率
        report += f"2. 响应率: {metrics['response_rate']:.2%}\n"
        
        # 3. 平均响应等待时间
        report += f"3. 平均响应等待时间: {metrics['avg_response_wait_time']:.2f} 时间单位\n"
        report += f"   (从订单请求到分配出租车的平均时间)\n"
        
        # 4. 平均响应后的接客时间
        if metrics['avg_pickup_after_assignment'] is not None:
            report += f"4. 平均响应后的接客时间: {metrics['avg_pickup_after_assignment']:.2f} 时间单位\n"
            report += f"   (从分配出租车到接客的平均时间)\n"
        else:
            report += "4. 平均响应后的接客时间: 无有效数据\n"
        
        # 5. 平均行程时间
        if metrics['avg_trip_time'] is not None:
            report += f"5. 平均行程时间: {metrics['avg_trip_time']:.2f} 时间单位\n"
            report += f"   (从接客到送达的平均时间)\n"
        else:
            report += "5. 平均行程时间: 无有效数据\n"

        # 6. 平均车辆占用率
        report += f"6. 平均车辆占用率: {metrics['avg_vehicle_occupancy_rate']:.2%}\n"
        report += f"   (车辆载客时间占总运营时间的平均比例)\n"
        
        # 6. 特殊情况订单
        report += "7. 特殊情况订单:\n"
        report += f"   - 无接客时间但有送达时间的订单: {metrics['special_case_no_pickup']}\n"
        report += f"   - 起点终点相同的订单: {metrics['special_case_same_location']}\n"
        report += f"   - 分配时间异常的订单: {metrics['special_case_invalid_assignment']}\n"
        report += f"   - 行程时间为负的订单: {metrics['special_case_negative_trip']}\n"
        report += f"   - 特殊情况订单总数: {metrics['total_special_cases']}\n"
        
        return report


# 使用示例
if __name__ == "__main__":
    # 示例数据
    sample_data = {
        "2": {
            "order_id": 2,
            "pickup_node": 67,
            "dropoff_node": 1123,
            "request_time": 29,
            "assigned_taxi": 7,
            "assigned_time": 300,
            "pickup_time": 826,
            "dropoff_time": 962,
            "status": "completed"
        },
        "21": {
            "order_id": 21,
            "pickup_node": 1453,
            "dropoff_node": 1119,
            "request_time": 37,
            "assigned_taxi": 8,
            "assigned_time": 300,
            "pickup_time": None,
            "dropoff_time": 556,
            "status": "completed"
        },
        "40": {
            "order_id": 40,
            "pickup_node": 519,
            "dropoff_node": 519,
            "request_time": 51,
            "assigned_taxi": 1,
            "assigned_time": 300,
            "pickup_time": None,
            "dropoff_time": 701,
            "status": "completed"
        }
    }
    
    # 创建分析器并加载数据
    analyzer = OrderAnalyzer(sample_data)
    
    # 分析关键指标
    metrics = analyzer.analyze_key_metrics()
    print("关键指标:", metrics)
    
    # 生成关键指标报告
    report = analyzer.generate_key_metrics_report()
    print("\n报告:")
    print(report)
    
    # 获取特殊情况订单详情
    special_cases = analyzer.get_special_cases_details()
    print("特殊情况订单详情:")
    for case_type, case_df in special_cases.items():
        print(f"{case_type}类型特殊订单数量: {len(case_df)}")
        if not case_df.empty:
            print(case_df["order_id"])
