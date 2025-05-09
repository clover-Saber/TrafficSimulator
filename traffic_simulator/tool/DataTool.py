import networkx as nx
import math
from scipy import spatial
from tqdm import tqdm
import pandas as pd

class DataTool:
    """
    图处理工具类，提供图的读取、重构和分析功能
    """
    
    @staticmethod
    def reconstruct_graph(input_path, output_path=None, speed=10, preserve_ids=True):
        """
        重构GraphML图，使节点ID从0开始的整数，
        只保留节点的经纬度和ID，以及边的距离和时间属性，
        并确保所有节点互相可达
        
        参数:
            input_path: 输入的graphml文件路径
            output_path: 输出的graphml文件路径，默认为None（不保存）
            speed: 通行速度，默认为10m/s
            preserve_ids: 是否保留原始ID的顺序，默认为True
            
        返回:
            重构后的networkx图对象
        """
        try:
            # 读取原始graphml文件
            original_graph = nx.read_graphml(input_path)
            
            print(f"成功读取原始图文件，包含 {original_graph.number_of_nodes()} 个节点和 {original_graph.number_of_edges()} 条边")
            
            # 找出最大连通分量
            if not nx.is_connected(original_graph):
                print("原始图不是连通的，寻找最大连通分量...")
                largest_cc = max(nx.connected_components(original_graph), key=len)
                print(f"最大连通分量包含 {len(largest_cc)} 个节点，占总节点数的 {len(largest_cc)/original_graph.number_of_nodes()*100:.2f}%")
            else:
                print("原始图是连通的")
                largest_cc = set(original_graph.nodes())
            
            # 只保留最大连通分量中的节点
            nodes_to_keep = largest_cc
            
            # 创建新的无向图
            G = nx.Graph()
            
            # 创建旧ID到新ID的映射
            old_to_new_id = {}
            
            # 如果要保持ID的一致性，先对原始ID进行排序
            if preserve_ids:
                # 将节点ID转换为整数（如果可能）以便进行一致的排序
                sorted_nodes = []
                for node_id in nodes_to_keep:
                    try:
                        # 尝试将节点ID转换为整数
                        node_id_int = int(node_id)
                        sorted_nodes.append((node_id_int, node_id))
                    except (ValueError, TypeError):
                        # 如果无法转换为整数，则使用原始ID
                        sorted_nodes.append((float('inf'), node_id))  # 非数字ID放在最后
                
                # 按转换后的整数ID排序
                sorted_nodes.sort()
                # 提取排序后的原始ID
                sorted_node_ids = [original_id for _, original_id in sorted_nodes]
            else:
                # 不需要保持ID一致性，直接使用集合
                sorted_node_ids = list(nodes_to_keep)
            
            # 添加节点，只保留经纬度和ID
            for new_id, node_id in enumerate(sorted_node_ids):
                node_data = original_graph.nodes[node_id]
                
                # 检查节点是否有经纬度信息
                if 'x' in node_data and 'y' in node_data:
                    # 将经纬度转换为double类型
                    x = float(node_data['x'])
                    y = float(node_data['y'])
                    
                    # 添加节点，使用新的整数ID
                    G.add_node(new_id, x=x, y=y)
                    
                    # 记录ID映射
                    old_to_new_id[node_id] = new_id
            
            # 添加边，直接使用源文件中的length和time属性
            edges_processed = 0
            edges_skipped = 0
            
            for u, v, edge_data in original_graph.edges(data=True):
                # 只处理在最大连通分量中的节点之间的边
                if u in nodes_to_keep and v in nodes_to_keep:
                    if 'length' in edge_data and 'time' in edge_data:
                        try:
                            # 直接使用源文件中的length和time属性
                            length = float(edge_data['length'])
                            time = float(edge_data['time'])
                        
                            # 添加边，保留距离和时间属性，使用新的节点ID
                            G.add_edge(old_to_new_id[u], old_to_new_id[v], length=length, time=time)
                            edges_processed += 1
                        except Exception as e:
                            print(f"警告: 边 ({u}, {v}) 的属性处理出错: {str(e)}，已跳过")
                            edges_skipped += 1
                    else:
                        # 如果缺少length或time属性，但有length属性，则计算time
                        if 'length' in edge_data and 'time' not in edge_data:
                            try:
                                length = float(edge_data['length'])
                                time = int(math.ceil(length / speed))
                                G.add_edge(old_to_new_id[u], old_to_new_id[v], length=length, time=time)
                                edges_processed += 1
                            except Exception as e:
                                print(f"警告: 边 ({u}, {v}) 的length属性处理出错: {str(e)}，已跳过")
                                edges_skipped += 1
                        else:
                            print(f"警告: 边 ({u}, {v}) 缺少必要的'length'或'time'属性，已跳过")
                            edges_skipped += 1
            
            # 检查重构后的图是否是连通的
            if not nx.is_connected(G):
                print("警告: 重构后的图不是连通的，某些节点可能无法互相到达")
                
                # 找出最大连通分量
                largest_cc = max(nx.connected_components(G), key=len)
                
                # 如果最大连通分量小于总节点数，可以选择只保留最大连通分量
                if len(largest_cc) < G.number_of_nodes():
                    print(f"最大连通分量包含 {len(largest_cc)} 个节点，总节点数为 {G.number_of_nodes()}")
                    
                    # 创建一个只包含最大连通分量的新图
                    H = G.subgraph(largest_cc).copy()
                    
                    # 如果需要保持ID一致性，需要重新映射节点ID
                    if preserve_ids:
                        # 创建一个从当前ID到新ID的映射
                        old_ids_in_cc = sorted(list(largest_cc))
                        mapping = {old_id: new_id for new_id, old_id in enumerate(old_ids_in_cc)}
                        H = nx.relabel_nodes(H, mapping)
                    
                    print(f"已只保留最大连通分量，图节点数从 {G.number_of_nodes()} 减少到 {H.number_of_nodes()}")
                    G = H
            else:
                print("重构后的图是连通的，所有节点可以互相到达")
            
            # 如果需要保存
            if output_path:
                nx.write_graphml(G, output_path)
                print(f"重构后的图已保存至: {output_path}")
            
            print(f"处理完成! 重构后的图包含 {G.number_of_nodes()} 个节点和 {G.number_of_edges()} 条边")
            
            return G
            
        except Exception as e:
            print(f"处理过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


    @staticmethod
    def match_orders_to_network(order_path, G, output_path=None):
        """
        将订单数据（包含起点和终点）匹配到路网节点上
        
        参数:
            order_path: 输入订单文件路径，CSV格式，应包含id,stime,slon,slat,elon,elat列
            G: 路网图
            output_path: 输出文件路径，CSV格式
            
        返回:
            匹配后的DataFrame，只包含id,ot,pickup_node,dropoff_node
        """
        try:
            # 提取路网节点的经纬度信息，构建KD树
            midpoints = []
            nodes = []
            for i in G.nodes():
                midpoints.append([float(G.nodes[i]['x']), float(G.nodes[i]['y'])])
                nodes.append(i)
            
            # 构建KD树用于快速查找最近节点
            tree = spatial.KDTree(midpoints)
            print("已构建KD树用于空间匹配")
            
            # 读取输入数据
            orders = pd.read_csv(order_path, header=0)
            print(f"成功读取订单数据，包含 {len(orders)} 条记录")
            
            # 检查必要的列是否存在
            required_columns = ['id', 'stime', 'slon', 'slat', 'elon', 'elat']
            missing_columns = [col for col in required_columns if col not in orders.columns]
            if missing_columns:
                print(f"错误: 输入数据缺少必要的列: {missing_columns}")
                return None
            
            # 准备匹配结果
            matched_orders = []
            
            # 遍历输入数据，进行匹配
            for index, row in tqdm(orders.iterrows(), total=len(orders), desc="匹配订单到路网"):
                # 获取时间
                s = row['stime'].split(':')
                ot = int(s[0]) * 3600 + int(s[1]) * 60 + int(s[2])
                
                # 匹配起点
                _, s_node_idx = tree.query([row['slon'], row['slat']], k=1)
                pickup_node = nodes[s_node_idx]
                
                # 匹配终点
                _, e_node_idx = tree.query([row['elon'], row['elat']], k=1)
                dropoff_node = nodes[e_node_idx]
                
                # 构建匹配结果（只包含必要字段）
                matched_order = {
                    'id': row['id'],
                    'ot': ot,
                    'pickup_node': pickup_node,
                    'dropoff_node': dropoff_node
                }
                
                matched_orders.append(matched_order)

            # 转换为DataFrame并保存
            result_df = pd.DataFrame(matched_orders)
            # 按ot排序
            result_df = result_df.sort_values(by='ot')
            # 重置索引
            result_df = result_df.reset_index(drop=True)
            
            # 保存结果
            if output_path:
                result_df.to_csv(output_path, index=False)
                print(f"匹配完成! 结果已保存至: {output_path}")
            
            return result_df
        
        except Exception as e:
            print(f"处理过程中发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return None



# 使用示例
if __name__ == "__main__":
    input_graphml = "/home/yuhao/project/data/input_network.graphml"  # 替换为您的输入文件路径
    output_graphml = "/home/yuhao/project/data/network.graphml" 
    order_path = "/home/yuhao/project/data/input_orders.csv"
    output_order_path = "/home/yuhao/project/data/input_orders_1.csv"
    
    # 重构图
    G = DataTool.reconstruct_graph(input_graphml, output_graphml)
    DataTool.match_orders_to_network(order_path, G)

