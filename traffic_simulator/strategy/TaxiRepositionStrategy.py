import numpy as np
import random
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
from sklearn.cluster import KMeans
from traffic_simulator.manager.RoadNetworkManager import RoadNetworkManager
from traffic_simulator.entity.TaxiEntity import TaxiEntity


class TaxiRepositionStrategy:
    """
    出租车重定位策略类
    根据指定的策略名称，使用不同的算法进行出租车重定位
    """
    
    def __init__(self, strategy_name: str = "random"):
        """
        初始化重定位策略
        参数:
            strategy_name: 策略名称，可选值为 "random", "cluster", "demand", "balanced"
        """
        self.max_travel_time = 60
        self.strategy_name = strategy_name.lower()
        self.strategy_map = {
            "random": self._random_strategy,
            "llm": self._llm_based_strategy,
            "cluster": self._cluster_based_strategy,
            "demand": self._demand_based_strategy,
            "balanced": self._balanced_distribution_strategy,
        }
        
        if self.strategy_name not in self.strategy_map:
            print(f"警告: 未知的策略名称 '{strategy_name}'，将使用随机重定位策略")
            self.strategy_name = "random"
            
        print(f"已初始化出租车重定位策略: {self.strategy_name}")
    
    def reposition(self, taxis: List[TaxiEntity], road_network: RoadNetworkManager, current_time, **kwargs) -> List[Tuple[int, int, List]]:
        """
        统一的重定位接口，根据初始化时指定的策略调用相应的重定位方法
        参数:
            taxis: 待重定位的出租车列表
            road_network: 道路网络管理器
            current_time: 当前时间
            max_travel_time: 最大旅行时间限制（默认为300时间单位）
            **kwargs: 额外参数，可能被特定策略使用
        返回:
            包含(taxi_id, destination_node, route)元组的列表
        """
        # 将输入转换为原来的格式
        taxi_info = {}
        available_nodes = {}
        
        # 只处理空闲状态的出租车
        idle_taxis = [taxi for taxi in taxis if taxi.status == "idle"]
        
        for taxi in idle_taxis:
            taxi_id = taxi.taxi_id
            current_node = taxi.position_node
            preference = taxi.driver_preference 
            
            taxi_info[taxi_id] = {
                'node_id': current_node,
                'preference': preference
            }
            
            # 获取可用的目标节点 - 使用get_random_node_in_time方法
            all_nodes = []
            for _ in range(10):  # 尝试获取10个候选节点
                # 使用当前节点和最大旅行时间限制获取随机节点
                random_node = road_network.get_random_node_in_time(current_node, self.max_travel_time)
                if random_node is not None:
                    all_nodes.append(random_node)
            
            # 如果没有找到任何节点，可以尝试增加时间限制或使用其他方法
            if not all_nodes:
                print(f"警告: 无法为出租车 {taxi_id} 找到在 {self.max_travel_time} 时间单位内可达的节点")
            
            available_nodes[taxi_id] = list(set(all_nodes))  # 去重
        
        # 添加节点位置信息（如果路网类提供了获取节点位置的方法）
        node_positions = {}
        for node_id in set(sum(available_nodes.values(), [])):
            node_positions[node_id] = road_network.get_coord_by_node(node_id)
        
        kwargs['node_positions'] = node_positions
        kwargs['road_network'] = road_network  # 传递路网对象以供策略方法使用
        kwargs['current_time'] = current_time  # 传递最大旅行时间限制
        
        # 调用对应的策略方法
        reposition_result = self.strategy_map[self.strategy_name](taxi_info, available_nodes, **kwargs)
        
        # 转换结果格式
        result = []
        for taxi_id, target_nodes in reposition_result.items():
            if target_nodes:  # 如果有目标节点
                destination_node = target_nodes[0]
                # 计算从当前节点到目标节点的路径
                current_node = taxi_info[taxi_id]['node_id']
                
                # 使用路网类的方法计算最短路径
                route = road_network.calculate_shortest_path(current_node, destination_node, current_time)
                
                result.append((taxi_id, destination_node, route))
        
        return result
    

    def _random_strategy(self, taxi_info: Dict[int, Dict[str, Any]], 
                        available_nodes: Dict[int, List[int]], **kwargs) -> Dict[int, List[int]]:
        """
        随机重定位策略：为每辆出租车随机选择一个可用节点作为重定位目标
        参数:
            taxi_info: 包含待重定位出租车信息的字典
            available_nodes: 每辆出租车可以重定位的节点列表
            **kwargs: 可选参数，包括:
                    - seed: 随机数种子
                    - road_network: 道路网络管理器
                    - max_travel_time: 最大旅行时间限制
        返回:
            出租车id到重定位节点集的映射
        """
        # 设置随机种子
        seed = kwargs.get("seed")
        if seed is not None:
            random.seed(seed)
        
        road_network = kwargs.get("road_network")
        
        result = {}
        
        for taxi_id, info in taxi_info.items():
            current_node = info['node_id']
            
            # 如果已有可用节点列表，直接从中选择
            if taxi_id in available_nodes and available_nodes[taxi_id]:
                target_node = random.choice(available_nodes[taxi_id])
                result[taxi_id] = [target_node]
            # 如果没有预先计算的可用节点，但有路网对象，则直接使用get_random_node_in_time
            elif road_network is not None:
                target_node = road_network.get_random_node_in_time(current_node, self.max_travel_time)
                if target_node is not None:
                    result[taxi_id] = [target_node]
                else:
                    result[taxi_id] = []
            else:
                # 如果没有可用节点，则返回空列表
                result[taxi_id] = []
        
        # 重置随机种子
        if seed is not None:
            random.seed()
            
        return result

    def _llm_based_strategy(self, taxi_info: Dict[int, Dict[str, Any]], 
                        available_nodes: Dict[int, List[int]], **kwargs) -> Dict[int, List[int]]:
        """
        基于大语言模型的重定位策略：使用LLM API为出租车推荐最佳重定位位置
        参数:
            taxi_info: 包含待重定位出租车信息的字典
            available_nodes: 每辆出租车可以重定位的节点列表
            **kwargs: 可选参数，包括:
                    - api_key: API密钥
                    - road_network: 道路网络管理器
                    - max_travel_time: 最大旅行时间限制
                    - node_positions: 节点id到节点坐标的映射
                    - historical_demand: 历史需求数据
                    - current_time: 当前时间
                    - fallback_strategy: 备用策略，默认为"random"
        返回:
            出租车id到重定位节点集的映射
        """
        import requests
        import json
        
        # 获取参数
        api_key = kwargs.get("api_key", "sk-ideyyrerljenjierbsivqxmymijzzeuhjcphfridnlyrqrwa")
        road_network = kwargs.get("road_network")
        node_positions = kwargs.get("node_positions", {})
        historical_demand = kwargs.get("historical_demand", {})
        current_time = kwargs.get("current_time", "未知")
        fallback_strategy = kwargs.get("fallback_strategy", "random")
        
        # 检查API密钥是否存在
        if not api_key:
            print("警告: 未提供API密钥，将使用备用策略")
            if fallback_strategy == "random":
                return self._random_strategy(taxi_info, available_nodes, **kwargs)
            else:
                return self._cluster_based_strategy(taxi_info, available_nodes, **kwargs)
        
        result = {}
        
        # 为每辆出租车生成重定位建议
        for taxi_id, info in taxi_info.items():
            current_node = info['node_id']
            preference = info['preference']
            
            # 准备可用节点列表及其位置信息
            nodes_info = []
            candidate_nodes = []
            
            # 如果已有可用节点列表，使用它
            if taxi_id in available_nodes and available_nodes[taxi_id]:
                candidate_nodes = available_nodes[taxi_id]
            # 否则，如果有路网对象，获取时间范围内的节点
            elif road_network is not None:
                reachable_nodes = road_network.get_nodes_in_time(current_node, self.max_travel_time)
                if reachable_nodes:
                    candidate_nodes = reachable_nodes
            
            # 为了避免API请求过大，最多选择10个候选节点
            # if len(candidate_nodes) > 10:
            #     candidate_nodes = random.sample(candidate_nodes, 10)
            
            # 为每个候选节点准备信息
            for node in candidate_nodes:
                travel_time = road_network.calculate_shortest_travel_time(current_node, node) if road_network else 0
                
                # 获取该节点的历史需求
                demand = historical_demand.get(node, 0)
                coord = road_network.get_coord_by_node(node)
                
                nodes_info.append({
                    "node_id": node,
                    "经纬度": coord,
                    "行驶时间": travel_time,
                    # "历史需求": demand
                })

            other_taxis = []
            for other_taxi_id, other_info in taxi_info.items():
                if other_taxi_id == taxi_id: continue
                other_taxis.append({"taxi_id": other_taxi_id, "所在路口": other_info['node_id'], "经纬度坐标": road_network.get_coord_by_node(other_info['node_id'])})
        
            # 构建提示词
            instruction = "你是一名出租车司机，正在寻找下一个重定位位置。"+preference
            input_text = f"""
                当前信息:
                - 你是出租车{taxi_id}，现在位于路口{current_node}，该位置的经纬度坐标为{road_network.get_coord_by_node(current_node)},
                - 当前时间: {current_time/3600:.1f}
                - 其他重定位出租车的位置信息如下：{other_taxis}

                可选的重定位目的地:
                {nodes_info}

                请根据重点关注区域的经纬度位置（尽可能前往高订单聚集区域）和行驶时间，选择一个最有可能获得乘客的目的地。
                直接回复你选择的路口编号，只需要一个数字。"""
            try:
                # 调用API获取建议
                recommended_node = self._generate_answer_with_api(instruction, input_text, api_key)
                
                # 尝试将结果解析为整数
                try:
                    recommended_node = int(recommended_node.strip())
                    # 验证推荐的节点是否在候选列表中
                    if recommended_node in candidate_nodes:
                        result[taxi_id] = [recommended_node]
                        # print(instruction+input_text)
                        # print("成功重定位", recommended_node)
                    else:
                        # 如果不在候选列表中，随机选择一个
                        result[taxi_id] = [random.choice(candidate_nodes)]
                        # print("失败重定位1")
                except ValueError:
                    # 如果无法解析为整数，随机选择一个
                    result[taxi_id] = [random.choice(candidate_nodes)]
                    # print("失败重定位2")
            except Exception as e:
                print(f"API请求异常: {str(e)}")
                # 发生异常时，随机选择一个节点
                result[taxi_id] = [random.choice(candidate_nodes)] if candidate_nodes else []
        
        return result

    def _generate_answer_with_api(self, instruction, input_text, api_key):
        """使用API生成回答"""
        import requests
        
        # 构建提示词
        prompt = f"Human: {instruction}\n{input_text}\nAssistant:"
        
        # API请求头和数据
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # API请求数据
        data = {
            "model": "Qwen/Qwen2.5-72B-Instruct-128K",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 100,  # 减少token数，因为我们只需要一个节点ID
            "temperature": 0.3,  # 降低温度以获得更确定的答案
            "top_p": 0.95
        }
        
        try:
            # 发送请求
            response = requests.post(
                "https://api.siliconflow.cn/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            # 解析响应
            if response.status_code == 200:
                response_data = response.json()
                generated_text = response_data["choices"][0]["message"]["content"]
                return generated_text.strip()
            else:
                print(f"API请求失败，状态码: {response.status_code}, 错误信息: {response.text}")
                raise Exception(f"API错误 {response.status_code}")
        except Exception as e:
            print(f"请求异常: {str(e)}")
            raise e

    
    def _cluster_based_strategy(self, taxi_info: Dict[int, Dict[str, Any]], 
                              available_nodes: Dict[int, List[int]], **kwargs) -> Dict[int, List[int]]:
        """
        基于聚类的重定位策略：将出租车分配到不同的区域，以覆盖更广泛的区域
        参数:
            taxi_info: 包含待重定位出租车信息的字典
            available_nodes: 每辆出租车可以重定位的节点列表
            **kwargs: 可选参数，包括:
                      - node_positions: 节点id到节点坐标的映射
                      - n_clusters: 聚类的数量
        返回:
            出租车id到重定位节点集的映射
        """
        node_positions = kwargs.get("node_positions", {})
        n_clusters = kwargs.get("n_clusters", 5)
        
        if not node_positions:
            print("警告: 未提供节点位置信息，将使用随机重定位策略")
            return self._random_strategy(taxi_info, available_nodes)
        
        result = {}
        
        # 如果出租车数量太少，则使用随机策略
        if len(taxi_info) < n_clusters:
            return self._random_strategy(taxi_info, available_nodes)
        
        # 收集所有可用节点的位置
        all_nodes = set()
        for nodes in available_nodes.values():
            all_nodes.update(nodes)
        
        node_positions_list = []
        node_ids = []
        for node_id in all_nodes:
            if node_id in node_positions:
                node_positions_list.append(node_positions[node_id])
                node_ids.append(node_id)
        
        if not node_positions_list:
            # 如果没有可用节点，则返回空结果
            return {taxi_id: [] for taxi_id in taxi_info}
        
        # 使用K-means聚类算法将节点分组
        kmeans = KMeans(n_clusters=min(n_clusters, len(node_positions_list)), 
                        random_state=42)
        node_positions_array = np.array(node_positions_list)
        cluster_labels = kmeans.fit_predict(node_positions_array)
        
        # 将节点按聚类分组
        clusters = defaultdict(list)
        for i, cluster_id in enumerate(cluster_labels):
            clusters[cluster_id].append(node_ids[i])
        
        # 将出租车分配到不同的聚类中
        taxi_ids = list(taxi_info.keys())
        taxi_per_cluster = defaultdict(list)
        
        for i, taxi_id in enumerate(taxi_ids):
            cluster_id = i % len(clusters)
            taxi_per_cluster[cluster_id].append(taxi_id)
        
        # 为每辆出租车选择目标节点
        for cluster_id, cluster_taxis in taxi_per_cluster.items():
            cluster_nodes = clusters[cluster_id]
            
            for taxi_id in cluster_taxis:
                # 找出该出租车可用的且在该聚类中的节点
                available_cluster_nodes = [node for node in available_nodes.get(taxi_id, []) 
                                          if node in cluster_nodes]
                
                if available_cluster_nodes:
                    # 随机选择一个节点作为目标
                    target_node = random.choice(available_cluster_nodes)
                    result[taxi_id] = [target_node]
                else:
                    # 如果没有可用的聚类节点，则随机选择一个可用节点
                    if taxi_id in available_nodes and available_nodes[taxi_id]:
                        result[taxi_id] = [random.choice(available_nodes[taxi_id])]
                    else:
                        result[taxi_id] = []
        
        return result
    
    def _demand_based_strategy(self, taxi_info: Dict[int, Dict[str, Any]], 
                             available_nodes: Dict[int, List[int]], **kwargs) -> Dict[int, List[int]]:
        """
        基于需求的重定位策略：根据历史需求数据将出租车重定位到高需求区域
        
        参数:
            taxi_info: 包含待重定位出租车信息的字典
            available_nodes: 每辆出租车可以重定位的节点列表
            **kwargs: 可选参数，包括:
                      - node_positions: 节点id到节点坐标的映射
                      - historical_demand: 节点id到历史需求量的映射
                      - top_percentage: 选择需求最高的前N%节点作为候选目标
            
        返回:
            出租车id到重定位节点集的映射
        """
        node_positions = kwargs.get("node_positions", {})
        historical_demand = kwargs.get("historical_demand", {})
        top_percentage = kwargs.get("top_percentage", 0.2)
        
        if not historical_demand:
            print("警告: 未提供历史需求数据，将使用随机重定位策略")
            return self._random_strategy(taxi_info, available_nodes)
        
        # 计算高需求节点
        if not historical_demand:
            high_demand_nodes = set()
        else:
            # 按需求量排序
            sorted_nodes = sorted(historical_demand.items(), 
                                 key=lambda x: x[1], reverse=True)
            
            # 选择需求最高的前N%节点
            n_top_nodes = max(1, int(len(sorted_nodes) * top_percentage))
            high_demand_nodes = {node_id for node_id, _ in sorted_nodes[:n_top_nodes]}
        
        result = {}
        
        for taxi_id, info in taxi_info.items():
            if taxi_id not in available_nodes or not available_nodes[taxi_id]:
                result[taxi_id] = []
                continue
            
            # 找出该出租车可用的且在高需求区域的节点
            high_demand_available = [node for node in available_nodes[taxi_id] 
                                    if node in high_demand_nodes]
            
            if high_demand_available:
                # 如果有高需求节点可用，则选择其中一个
                target_node = random.choice(high_demand_available)
                result[taxi_id] = [target_node]
            else:
                # 如果没有高需求节点可用，则使用随机策略
                if available_nodes[taxi_id]:
                    result[taxi_id] = [random.choice(available_nodes[taxi_id])]
                else:
                    result[taxi_id] = []
        
        return result
    
    def _balanced_distribution_strategy(self, taxi_info: Dict[int, Dict[str, Any]], 
                                      available_nodes: Dict[int, List[int]], **kwargs) -> Dict[int, List[int]]:
        """
        平衡分布策略：尝试使出租车在空间上均匀分布
        
        参数:
            taxi_info: 包含待重定位出租车信息的字典
            available_nodes: 每辆出租车可以重定位的节点列表
            **kwargs: 可选参数，包括:
                      - node_positions: 节点id到节点坐标的映射
            
        返回:
            出租车id到重定位节点集的映射
        """
        node_positions = kwargs.get("node_positions", {})
        
        if not node_positions:
            print("警告: 未提供节点位置信息，将使用随机重定位策略")
            return self._random_strategy(taxi_info, available_nodes)
        
        result = {}
        
        # 如果只有一辆出租车，使用随机策略
        if len(taxi_info) <= 1:
            return self._random_strategy(taxi_info, available_nodes)
        
        # 按顺序处理每辆出租车
        taxi_ids = list(taxi_info.keys())
        assigned_positions = []
        
        for taxi_id in taxi_ids:
            if taxi_id not in available_nodes or not available_nodes[taxi_id]:
                result[taxi_id] = []
                continue
            
            # 获取可用节点的位置
            available_positions = []
            for node_id in available_nodes[taxi_id]:
                if node_id in node_positions:
                    available_positions.append((node_id, node_positions[node_id]))
            
            if not available_positions:
                result[taxi_id] = []
                continue
            
            if not assigned_positions:
                # 第一辆出租车随机选择一个节点
                node_id, _ = random.choice(available_positions)
                result[taxi_id] = [node_id]
                assigned_positions.append(node_positions[node_id])
            else:
                # 为后续出租车选择与已分配位置距离最远的节点
                best_node = None
                max_min_distance = -1
                
                for node_id, position in available_positions:
                    # 计算到所有已分配位置的最小距离
                    min_distance = float('inf')
                    for assigned_pos in assigned_positions:
                        dist = ((position[0] - assigned_pos[0]) ** 2 + 
                               (position[1] - assigned_pos[1]) ** 2) ** 0.5
                        min_distance = min(min_distance, dist)
                    
                    # 更新最佳节点
                    if min_distance > max_min_distance:
                        max_min_distance = min_distance
                        best_node = node_id
                
                result[taxi_id] = [best_node]
                assigned_positions.append(node_positions[best_node])
        
        return result
