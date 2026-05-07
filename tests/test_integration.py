"""
集成测试：验证各模块协同工作

不依赖真实 PDF 和 API，使用 mock 数据验证流程。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.state import create_initial_state
from src.orchestrator import create_report_graph


def test_graph_structure():
    """测试 1: 验证图结构创建成功"""
    print("=" * 60)
    print("测试 1: 图结构创建")
    print("=" * 60)

    try:
        graph = create_report_graph()
        print("✓ 图创建成功")

        # 检查节点
        nodes = list(graph.nodes.keys())
        print(f"✓ 节点列表: {nodes}")

        expected_nodes = ["plan", "research", "write", "review", "publish", "supplement"]
        missing = set(expected_nodes) - set(nodes)
        if missing:
            print(f"✗ 缺少节点: {missing}")
            return False

        print("✓ 所有预期节点存在")
        return True

    except Exception as e:
        print(f"✗ 图创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_creation():
    """测试 2: 验证状态创建"""
    print("\n" + "=" * 60)
    print("测试 2: 状态创建")
    print("=" * 60)

    try:
        task = {
            "title": "测试报告",
            "description": "集成测试",
        }
        state = create_initial_state(task=task, task_id="test-001")

        # 验证必需字段
        required_fields = [
            "task",
            "task_id",
            "source_docs",
            "research_outline",
            "research_tasks",
            "research_data",
            "draft",
            "review_status",
            "final_report",
            "current_step",
            "logs",
        ]

        for field in required_fields:
            if field not in state:
                print(f"✗ 缺少状态字段: {field}")
                return False

        print("✓ 状态创建成功")
        print(f"✓ 任务 ID: {state['task_id']}")
        print(f"✓ 当前步骤: {state['current_step']}")
        print(f"✓ 初始日志: {state['logs']}")

        return True

    except Exception as e:
        print(f"✗ 状态创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_execution():
    """测试 3: 验证图执行（使用占位节点）"""
    print("\n" + "=" * 60)
    print("测试 3: 工作流执行")
    print("=" * 60)

    try:
        # 创建图
        graph = create_report_graph()

        # 创建初始状态
        task = {
            "title": "测试分析报告",
            "description": "验证工作流执行",
        }
        initial_state = create_initial_state(task=task, task_id="test-002")

        # 添加 mock 源文档
        initial_state["source_docs"] = [
            "# 测试文档\n\n这是一份测试文档内容。\n\n## 第一节\n\n内容..."
        ]
        initial_state["source_images"] = []

        print("✓ 初始状态准备完成")
        print(f"  - 源文档数: {len(initial_state['source_docs'])}")

        # 执行图
        print("\n开始执行工作流...")
        result = graph.invoke(initial_state)

        # 验证结果
        print("\n执行结果:")
        print(f"  - 最终步骤: {result.get('current_step')}")
        print(f"  - 审核状态: {result.get('review_status')}")
        print(f"  - 最终报告长度: {len(result.get('final_report', ''))}")
        print(f"  - 日志条数: {len(result.get('logs', []))}")

        # 打印执行日志
        print("\n执行日志:")
        for log in result.get("logs", []):
            print(f"  {log}")

        # 验证关键节点是否执行
        if result.get("current_step") != "publish":
            print(f"✗ 流程未完成，当前步骤: {result.get('current_step')}")
            return False

        print("\n✓ 工作流执行完成")
        return True

    except Exception as e:
        print(f"✗ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stream_execution():
    """测试 4: 验证流式执行"""
    print("\n" + "=" * 60)
    print("测试 4: 流式执行")
    print("=" * 60)

    try:
        # 创建图
        graph = create_report_graph()

        # 创建初始状态
        task = {
            "title": "流式测试报告",
            "description": "验证流式执行",
        }
        initial_state = create_initial_state(task=task, task_id="test-003")
        initial_state["source_docs"] = ["# 测试文档\n\n测试内容。"]
        initial_state["source_images"] = []

        print("✓ 开始流式执行")

        # 记录执行的节点
        executed_nodes = []

        for event in graph.stream(initial_state):
            for node_name, node_output in event.items():
                executed_nodes.append(node_name)
                current_step = node_output.get("current_step", "")
                print(f"  → 节点: {node_name} (步骤: {current_step})")

        print(f"\n✓ 执行的节点: {' → '.join(executed_nodes)}")

        # 验证关键节点
        expected_nodes = ["plan", "research", "write", "review", "publish"]
        for node in expected_nodes:
            if node not in executed_nodes:
                print(f"✗ 未执行节点: {node}")
                return False

        print("✓ 流式执行完成")
        return True

    except Exception as e:
        print(f"✗ 流式执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_checkpoint_functionality():
    """测试 5: 验证断点续传功能"""
    print("\n" + "=" * 60)
    print("测试 5: 断点续传")
    print("=" * 60)

    try:
        from src.orchestrator import create_graph_with_memory

        # 创建带内存的图
        graph, checkpointer = create_graph_with_memory()
        print("✓ 带内存图创建成功")

        # 创建初始状态
        task = {
            "title": "断点测试报告",
            "description": "验证断点续传",
        }
        initial_state = create_initial_state(task=task, task_id="test-004")
        initial_state["source_docs"] = ["# 测试文档"]
        initial_state["source_images"] = []

        # 配置断点
        config = {"configurable": {"thread_id": "test-checkpoint-001"}}

        # 执行
        result = graph.invoke(initial_state, config=config)
        print(f"✓ 断点续传执行完成")
        print(f"  - 最终步骤: {result.get('current_step')}")

        return True

    except Exception as e:
        print(f"✗ 断点续传失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print(" " * 20 + "DeepFinance 集成测试")
    print("=" * 80)

    tests = [
        test_graph_structure,
        test_state_creation,
        test_graph_execution,
        test_stream_execution,
        test_checkpoint_functionality,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n✗ 测试崩溃: {test_func.__name__}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print("=" * 80)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
