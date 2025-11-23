#!/usr/bin/env python
"""
cli/moe_cli.py
--------------
Command-line interface for MoE system
"""

import argparse
import asyncio
import json
import sys
from typing import Optional

from services.moe.moe_orchestrator import MoEOrchestrator
from services.moe.monitoring import get_monitor, PerformanceMonitor
from services.moe.feedback_loop import get_feedback_loop
from config.moe_settings import MoESettings
from utils.logging_config import get_logger


class MoECLI:
    """Command-line interface for MoE system"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.orchestrator = None
        self.monitor = get_monitor()
        self.feedback = get_feedback_loop()

    def _init_orchestrator(self):
        """Initialize orchestrator if not already done"""
        if self.orchestrator is None:
            self.orchestrator = MoEOrchestrator()

    def query(self, query_text: str, context: dict = None, output_format: str = 'text'):
        """
        Process a query through MoE system

        Args:
            query_text: Query to process
            context: Optional context
            output_format: Output format (text, json)
        """
        self._init_orchestrator()

        result = self.orchestrator.process_sync(query_text, context)

        if output_format == 'json':
            print(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            self._print_result(result)

    def _print_result(self, result):
        """Print result in human-readable format"""
        print("\n" + "=" * 60)
        print("MoE Query Result")
        print("=" * 60)
        print(f"\nQuery: {result.query}")
        print(f"Primary Expert: {result.primary_expert}")
        print(f"Confidence: {result.combined_confidence:.2%}")
        print(f"Strategy: {result.strategy_used}")
        print(f"Execution Time: {result.execution_time_ms:.2f}ms")

        print("\n--- Expert Contributions ---")
        for contrib in result.expert_contributions:
            print(f"  {contrib['expert_type']}: weight={contrib['weight']:.2f}, "
                  f"confidence={contrib['confidence']:.2%}")

        print("\n--- Combined Data ---")
        for key, value in result.combined_data.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")

        print("\n" + "=" * 60)

    def batch(self, queries_file: str, parallel: bool = True, output_format: str = 'text'):
        """
        Process multiple queries from file

        Args:
            queries_file: Path to JSON file with queries
            parallel: Whether to process in parallel
            output_format: Output format
        """
        self._init_orchestrator()

        with open(queries_file) as f:
            data = json.load(f)

        queries = data if isinstance(data, list) else data.get('queries', [])

        if not queries:
            print("No queries found in file")
            return

        print(f"Processing {len(queries)} queries...")

        results = self.orchestrator.process_batch_sync(queries, parallel)

        if output_format == 'json':
            output = [r.to_dict() for r in results]
            print(json.dumps(output, indent=2, default=str))
        else:
            for i, result in enumerate(results):
                print(f"\n--- Query {i+1} ---")
                self._print_result(result)

    def route(self, query_text: str, output_format: str = 'text'):
        """
        Route query without executing

        Args:
            query_text: Query to route
            output_format: Output format
        """
        self._init_orchestrator()

        decision = self.orchestrator.analyze_query(query_text)

        if output_format == 'json':
            print(json.dumps(decision.to_dict(), indent=2, default=str))
        else:
            print("\n" + "=" * 60)
            print("Routing Decision")
            print("=" * 60)
            print(f"\nQuery: {decision.query}")
            print(f"Query Type: {decision.query_type}")
            print(f"Selected Experts: {', '.join(decision.selected_experts)}")
            print(f"Primary Expert: {decision.primary_expert}")
            print(f"\nConfidence Scores:")
            for expert, score in sorted(decision.confidence_scores.items(),
                                        key=lambda x: x[1], reverse=True):
                bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
                print(f"  {expert}: {bar} {score:.2%}")
            print(f"\nReasoning: {decision.reasoning}")
            print("=" * 60)

    def experts(self, output_format: str = 'text'):
        """
        List available experts

        Args:
            output_format: Output format
        """
        self._init_orchestrator()

        descriptions = self.orchestrator.get_expert_descriptions()

        if output_format == 'json':
            experts_info = []
            for expert_type in MoESettings.EXPERT_TYPES:
                experts_info.append({
                    'type': expert_type,
                    'description': descriptions.get(expert_type, ''),
                    'timeout': MoESettings.get_timeout_for_expert(expert_type),
                    'threshold': MoESettings.get_threshold_for_expert(expert_type),
                    'weight': MoESettings.get_weight_for_expert(expert_type),
                    'keywords': MoESettings.ROUTING_KEYWORDS.get(expert_type, [])[:5]
                })
            print(json.dumps(experts_info, indent=2))
        else:
            print("\n" + "=" * 60)
            print("Available Experts")
            print("=" * 60)
            for expert_type in MoESettings.EXPERT_TYPES:
                print(f"\n{expert_type}")
                print("-" * 40)
                print(f"  Description: {descriptions.get(expert_type, 'N/A')}")
                print(f"  Timeout: {MoESettings.get_timeout_for_expert(expert_type)}s")
                print(f"  Threshold: {MoESettings.get_threshold_for_expert(expert_type)}")
                print(f"  Weight: {MoESettings.get_weight_for_expert(expert_type)}")
                keywords = MoESettings.ROUTING_KEYWORDS.get(expert_type, [])[:5]
                print(f"  Keywords: {', '.join(keywords)}...")
            print("\n" + "=" * 60)

    def metrics(self, output_format: str = 'text'):
        """
        Show performance metrics

        Args:
            output_format: Output format
        """
        data = self.monitor.get_dashboard_data()

        if output_format == 'json':
            print(json.dumps(data, indent=2, default=str))
        else:
            print(self.monitor.format_dashboard())

    def feedback_stats(self, output_format: str = 'text'):
        """
        Show feedback statistics

        Args:
            output_format: Output format
        """
        stats = self.feedback.get_expert_stats()
        recent = self.feedback.get_recent_feedback()
        adjustments = self.feedback.get_weight_adjustments()

        if output_format == 'json':
            print(json.dumps({
                'stats': stats,
                'recent': recent,
                'adjustments': adjustments
            }, indent=2))
        else:
            print("\n" + "=" * 60)
            print("Feedback Statistics")
            print("=" * 60)

            print("\n--- Expert Stats ---")
            for expert, stat in stats.items():
                if stat['total_feedback'] > 0:
                    print(f"\n{expert}:")
                    print(f"  Total feedback: {stat['total_feedback']}")
                    print(f"  Avg rating: {stat['avg_rating']:.2f}")
                    print(f"  Accuracy: {stat['accuracy']:.2%}")

            print("\n--- Weight Adjustments ---")
            for expert, adj in adjustments.items():
                if adj != 0:
                    print(f"  {expert}: {adj:+.3f}")

            print("\n--- Recent Feedback ---")
            for entry in recent[-5:]:
                print(f"  [{entry['rating']}★] {entry['query']} -> {entry['selected_experts']}")

            print("\n" + "=" * 60)

    def settings(self, output_format: str = 'text'):
        """
        Show current settings

        Args:
            output_format: Output format
        """
        settings = MoESettings.to_dict()

        if output_format == 'json':
            print(json.dumps(settings, indent=2))
        else:
            print("\n" + "=" * 60)
            print("MoE Settings")
            print("=" * 60)
            for key, value in settings.items():
                if isinstance(value, dict):
                    print(f"\n{key}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                elif isinstance(value, list):
                    print(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    print(f"{key}: {value}")
            print("\n" + "=" * 60)

    def interactive(self):
        """
        Run interactive mode
        """
        self._init_orchestrator()

        print("\n" + "=" * 60)
        print("MoE Interactive Mode")
        print("=" * 60)
        print("\nCommands:")
        print("  /experts  - List experts")
        print("  /route    - Route without executing")
        print("  /metrics  - Show metrics")
        print("  /feedback - Show feedback stats")
        print("  /settings - Show settings")
        print("  /quit     - Exit")
        print("\nType a query to process it through the MoE system.")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input("MoE> ").strip()

                if not user_input:
                    continue

                if user_input.startswith('/'):
                    cmd = user_input[1:].split()[0]
                    if cmd == 'quit' or cmd == 'exit':
                        print("Goodbye!")
                        break
                    elif cmd == 'experts':
                        self.experts()
                    elif cmd == 'route':
                        query = user_input[len(f'/{cmd}'):].strip()
                        if query:
                            self.route(query)
                        else:
                            print("Usage: /route <query>")
                    elif cmd == 'metrics':
                        self.metrics()
                    elif cmd == 'feedback':
                        self.feedback_stats()
                    elif cmd == 'settings':
                        self.settings()
                    else:
                        print(f"Unknown command: {cmd}")
                else:
                    self.query(user_input)

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MoE System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Query command
    query_parser = subparsers.add_parser('query', help='Process a query')
    query_parser.add_argument('query', help='Query text')
    query_parser.add_argument('--context', type=json.loads, help='Context as JSON')
    query_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process queries from file')
    batch_parser.add_argument('file', help='JSON file with queries')
    batch_parser.add_argument('--sequential', action='store_true', help='Process sequentially')
    batch_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Route command
    route_parser = subparsers.add_parser('route', help='Route query without executing')
    route_parser.add_argument('query', help='Query text')
    route_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Experts command
    experts_parser = subparsers.add_parser('experts', help='List available experts')
    experts_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show performance metrics')
    metrics_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Feedback command
    feedback_parser = subparsers.add_parser('feedback', help='Show feedback statistics')
    feedback_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Settings command
    settings_parser = subparsers.add_parser('settings', help='Show current settings')
    settings_parser.add_argument('--format', choices=['text', 'json'], default='text')

    # Interactive command
    subparsers.add_parser('interactive', help='Run interactive mode')

    args = parser.parse_args()

    cli = MoECLI()

    if args.command == 'query':
        cli.query(args.query, args.context, args.format)
    elif args.command == 'batch':
        cli.batch(args.file, not args.sequential, args.format)
    elif args.command == 'route':
        cli.route(args.query, args.format)
    elif args.command == 'experts':
        cli.experts(args.format)
    elif args.command == 'metrics':
        cli.metrics(args.format)
    elif args.command == 'feedback':
        cli.feedback_stats(args.format)
    elif args.command == 'settings':
        cli.settings(args.format)
    elif args.command == 'interactive':
        cli.interactive()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
