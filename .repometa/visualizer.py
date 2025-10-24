#!/usr/bin/env python3
"""
Vision 2045 Repository Visualizer
Interactive diagram generation and navigation for intelligent repository management

Enables conversational exploration:
  "Show me the whole tree"
  "Just the phase-2 branch"
  "Where are the redundancies?"
  "Show me dependencies like a brain"

Usage:
  python visualizer.py --full-tree                    # Show entire repository
  python visualizer.py --branch phase-2-predictive    # Single branch view
  python visualizer.py --dependencies                 # Dependency graph
  python visualizer.py --redundancies                 # Find duplicate code
  python visualizer.py --capabilities                 # Capability matrix
  python visualizer.py --interactive                  # Conversational mode
"""

import yaml
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class ViewMode(Enum):
    """Different visualization modes"""
    FULL_TREE = "full_tree"
    SINGLE_BRANCH = "single_branch"
    DEPENDENCIES = "dependencies"
    REDUNDANCIES = "redundancies"
    CAPABILITIES = "capabilities"
    CATEGORY = "category"
    INTERACTIVE = "interactive"


@dataclass
class RepoFile:
    """Represents a file in the repository with semantic metadata"""
    path: str
    category: str
    purpose: str
    capabilities: List[str]
    connects_to: List[str]
    dependencies: List[str]
    importance: str
    complexity: Optional[str] = None


class RepoVisualizer:
    """
    Intelligent repository visualizer that generates diagrams from semantic metadata
    """

    def __init__(self, manifest_path: str = ".repometa/manifest.yaml"):
        """Load the semantic manifest"""
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load_manifest()
        self.categories = self._build_category_map()
        self.files = self._build_file_map()

    def _load_manifest(self) -> Dict:
        """Load YAML manifest with error handling"""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ Error: Manifest not found at {self.manifest_path}")
            print("Run this from the repository root directory.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ Error parsing manifest: {e}")
            sys.exit(1)

    def _build_category_map(self) -> Dict[str, Dict]:
        """Build quick lookup for categories"""
        return {cat['id']: cat for cat in self.manifest.get('categories', [])}

    def _build_file_map(self) -> Dict[str, RepoFile]:
        """Convert manifest structure to RepoFile objects"""
        files = {}
        for item in self.manifest.get('structure', []):
            files[item['path']] = RepoFile(
                path=item['path'],
                category=item['category'],
                purpose=item['purpose'],
                capabilities=item.get('capabilities', []),
                connects_to=item.get('connects_to', []),
                dependencies=item.get('dependencies', []),
                importance=item['importance'],
                complexity=item.get('complexity')
            )
        return files

    def generate_full_tree_diagram(self) -> str:
        """
        Generate Mermaid diagram of entire repository structure
        Organized by category
        """
        mermaid = ["```mermaid", "graph TB"]

        # Add title
        mermaid.append("    %% NexVigilant Autonomous Marketing Engine - Full Repository")
        mermaid.append("")

        # Group by category
        for cat_id, category in self.categories.items():
            # Category header
            mermaid.append(f"    subgraph {cat_id}[\"{category['name']}\"]")

            # Find all files in this category
            cat_files = [f for f in self.files.values() if f.category == cat_id]

            for file in cat_files:
                # Create node with importance indicator
                importance_emoji = self._get_importance_emoji(file.importance)
                file_id = self._sanitize_id(file.path)
                file_label = self._get_file_label(file.path)

                mermaid.append(f"        {file_id}[{importance_emoji} {file_label}]")

            mermaid.append("    end")
            mermaid.append("")

        # Add connections
        mermaid.append("    %% Connections")
        for file in self.files.values():
            file_id = self._sanitize_id(file.path)
            for connection in file.connects_to:
                if connection in self.files:
                    conn_id = self._sanitize_id(connection)
                    mermaid.append(f"    {file_id} --> {conn_id}")

        # Add styling
        mermaid.extend([
            "",
            "    %% Styling by importance",
            "    classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff",
            "    classDef high fill:#ffa94d,stroke:#fd7e14,color:#000",
            "    classDef medium fill:#74c0fc,stroke:#339af0,color:#000"
        ])

        mermaid.append("```")
        return "\n".join(mermaid)

    def generate_branch_diagram(self, branch_path: str) -> str:
        """
        Generate diagram for a single branch/directory
        Shows files in that path and their immediate connections
        """
        mermaid = ["```mermaid", "graph LR"]
        mermaid.append(f"    %% Branch: {branch_path}")
        mermaid.append("")

        # Find files in this branch
        branch_files = [f for f in self.files.values() if f.path.startswith(branch_path)]

        if not branch_files:
            return f"❌ No files found in branch: {branch_path}"

        # Show files in this branch
        mermaid.append(f"    subgraph branch[\"{branch_path}\"]")
        for file in branch_files:
            file_id = self._sanitize_id(file.path)
            file_label = self._get_file_label(file.path)
            importance = self._get_importance_emoji(file.importance)

            mermaid.append(f"        {file_id}[{importance} {file_label}]")
        mermaid.append("    end")
        mermaid.append("")

        # Show connections to files outside this branch
        mermaid.append("    %% External connections")
        external_connections = set()
        for file in branch_files:
            file_id = self._sanitize_id(file.path)
            for connection in file.connects_to:
                if connection not in [f.path for f in branch_files]:
                    external_connections.add(connection)
                    conn_id = self._sanitize_id(connection)
                    conn_label = self._get_file_label(connection)
                    mermaid.append(f"    {conn_id}[{conn_label}]")
                    mermaid.append(f"    {file_id} -.-> {conn_id}")

        mermaid.append("```")
        return "\n".join(mermaid)

    def generate_dependency_graph(self) -> str:
        """
        Generate "brain-like" dependency visualization
        Shows how all components connect like neural pathways
        """
        mermaid = ["```mermaid", "graph TB"]
        mermaid.append("    %% Dependency Graph - Neural Network View")
        mermaid.append("")

        # Analyze connection density to find "hub" nodes
        connection_count = {}
        for file in self.files.values():
            connection_count[file.path] = len(file.connects_to)

        # Sort by importance as hubs
        hubs = sorted(connection_count.items(), key=lambda x: x[1], reverse=True)[:10]

        mermaid.append("    %% Critical Hubs (most connections)")
        for hub_path, count in hubs:
            if count > 0:
                hub_id = self._sanitize_id(hub_path)
                hub_label = self._get_file_label(hub_path)
                mermaid.append(f"    {hub_id}(({hub_label}<br/>↔️ {count} connections))")

        mermaid.append("")
        mermaid.append("    %% Neural Pathways")

        # Show connections from hubs
        for hub_path, _ in hubs:
            if hub_path in self.files:
                hub_file = self.files[hub_path]
                hub_id = self._sanitize_id(hub_path)

                for connection in hub_file.connects_to:
                    if connection in self.files:
                        conn_id = self._sanitize_id(connection)
                        mermaid.append(f"    {hub_id} ==> {conn_id}")

        # Add external dependencies (GCP services, etc.)
        mermaid.append("")
        mermaid.append("    %% External Dependencies")
        all_dependencies = set()
        for file in self.files.values():
            all_dependencies.update(file.dependencies)

        for dep in sorted(all_dependencies):
            if dep:
                dep_id = self._sanitize_id(dep)
                mermaid.append(f"    {dep_id}[/💎 {dep}/]")

        # Connect files to their dependencies
        for file in self.files.values():
            if file.dependencies and file.path in [h[0] for h in hubs[:5]]:
                file_id = self._sanitize_id(file.path)
                for dep in file.dependencies:
                    dep_id = self._sanitize_id(dep)
                    mermaid.append(f"    {file_id} -.-> {dep_id}")

        # Styling
        mermaid.extend([
            "",
            "    %% Styling",
            "    classDef hub fill:#9775fa,stroke:#7950f2,color:#fff,stroke-width:3px",
            "    classDef external fill:#20c997,stroke:#12b886,color:#fff"
        ])

        mermaid.append("```")
        return "\n".join(mermaid)

    def generate_redundancy_report(self) -> str:
        """
        Identify redundancies and code compression opportunities
        """
        report = ["# 🔍 Redundancy Analysis Report\n"]

        redundancy_rules = self.manifest.get('redundancy_patterns', {})

        if not redundancy_rules:
            report.append("✅ No redundancy patterns defined in manifest.\n")
            return "\n".join(report)

        report.append("## Detected Redundancy Clusters\n")

        for pattern_name, pattern_data in redundancy_rules.items():
            report.append(f"### {pattern_name.replace('_', ' ').title()}\n")
            report.append(f"**Locations ({len(pattern_data['locations'])}):**")

            for location in pattern_data['locations']:
                file_obj = self.files.get(location)
                if file_obj:
                    report.append(f"- `{location}` - {file_obj.purpose}")
                else:
                    report.append(f"- `{location}`")

            report.append(f"\n**💡 Recommendation:** {pattern_data['recommendation']}")

            if 'estimated_cleanup' in pattern_data:
                report.append(f"**📊 Potential Savings:** {pattern_data['estimated_cleanup']}")

            report.append("")

        # Analyze file purposes for similarity
        report.append("## 🔬 Semantic Similarity Analysis\n")
        report.append("Files with similar purposes that might benefit from consolidation:\n")

        # Group by similar keywords in purpose
        purpose_keywords = {}
        for file in self.files.values():
            # Extract keywords from purpose
            words = set(file.purpose.lower().split())
            keywords = words & {'testing', 'monitoring', 'data', 'quality', 'performance', 'ml', 'model'}

            for keyword in keywords:
                if keyword not in purpose_keywords:
                    purpose_keywords[keyword] = []
                purpose_keywords[keyword].append(file.path)

        for keyword, paths in purpose_keywords.items():
            if len(paths) > 2:  # More than 2 files mention this
                report.append(f"\n**{keyword.upper()}** mentioned in {len(paths)} files:")
                for path in paths[:5]:  # Top 5
                    report.append(f"  - `{path}`")

        return "\n".join(report)

    def generate_capability_matrix(self) -> str:
        """
        Show what capabilities exist and what enables them
        Reveals hidden connections and opportunities
        """
        report = ["# 🎯 Capability Discovery Matrix\n"]

        capabilities_map = self.manifest.get('capabilities_map', {})

        report.append("## Core Capabilities\n")
        for capability_name, capability_data in capabilities_map.items():
            report.append(f"### {capability_name.replace('_', ' ').title()}\n")

            report.append("**✅ Enabled by:**")
            for enabler in capability_data.get('enabled_by', []):
                report.append(f"- `{enabler}`")

            report.append("\n**🚀 Enables:**")
            for enabled in capability_data.get('enables', []):
                report.append(f"- {enabled}")

            report.append("\n**⚠️ Required for:**")
            for required in capability_data.get('required_for', []):
                report.append(f"- {required}")

            report.append("")

        # Hidden capabilities
        report.append("## 💎 Hidden Capabilities (Discovered Connections)\n")
        report.append("*Capabilities that exist but may not be obvious from file names alone*\n")

        hidden_caps = self.manifest.get('hidden_capabilities', [])
        for cap in hidden_caps:
            report.append(f"### {cap['capability']}\n")
            report.append(f"**Description:** {cap['description']}\n")
            report.append("**✨ Enabled by:**")
            for enabler in cap['enabled_by']:
                report.append(f"- `{enabler}`")
            report.append(f"\n**🔍 Discovery Path:** {cap['discovery_path']}")
            report.append(f"**💰 Value:** {cap['value']}")
            report.append(f"**⚙️ Implementation Effort:** {cap['implementation_effort']}\n")

        return "\n".join(report)

    def interactive_mode(self):
        """
        Conversational exploration mode
        "show me full tree" -> "next branch" -> "show redundancies"
        """
        print("🎯 Vision 2045 Interactive Repository Explorer")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  'tree' or 'full'      - Show full repository tree")
        print("  'branch <path>'       - Show specific branch")
        print("  'deps' or 'brain'     - Show dependency graph (brain view)")
        print("  'redundant' or 'dups' - Find redundancies")
        print("  'capabilities'        - Show capability matrix")
        print("  'list'                - List all files")
        print("  'category <name>'     - Show files by category")
        print("  'help'                - Show this help")
        print("  'quit' or 'exit'      - Exit interactive mode")
        print("\n" + "=" * 60 + "\n")

        while True:
            try:
                command = input("🤖 What would you like to explore? > ").strip().lower()

                if command in ['quit', 'exit', 'q']:
                    print("\n👋 Thank you for exploring! Building the future together.\n")
                    break

                elif command in ['tree', 'full', 'all']:
                    print("\n📊 Generating full repository tree...\n")
                    print(self.generate_full_tree_diagram())

                elif command.startswith('branch '):
                    branch = command.replace('branch ', '').strip()
                    print(f"\n🌿 Generating branch view: {branch}\n")
                    print(self.generate_branch_diagram(branch))

                elif command in ['deps', 'dependencies', 'brain', 'neural']:
                    print("\n🧠 Generating neural dependency graph...\n")
                    print(self.generate_dependency_graph())

                elif command in ['redundant', 'redundancies', 'dups', 'duplicates']:
                    print("\n🔍 Analyzing redundancies...\n")
                    print(self.generate_redundancy_report())

                elif command in ['capabilities', 'caps', 'hidden']:
                    print("\n💎 Discovering capabilities...\n")
                    print(self.generate_capability_matrix())

                elif command == 'list':
                    print("\n📁 All files in repository:\n")
                    for i, file_path in enumerate(sorted(self.files.keys()), 1):
                        file_obj = self.files[file_path]
                        importance = self._get_importance_emoji(file_obj.importance)
                        print(f"{i:2}. {importance} {file_path}")
                        print(f"    📝 {file_obj.purpose}")

                elif command.startswith('category '):
                    cat = command.replace('category ', '').strip()
                    print(f"\n📂 Files in category: {cat}\n")
                    cat_files = [f for f in self.files.values() if f.category == cat]
                    if cat_files:
                        for file in cat_files:
                            print(f"- {file.path}")
                            print(f"  {file.purpose}")
                    else:
                        print(f"❌ No files found in category: {cat}")
                        print(f"Available categories: {', '.join(self.categories.keys())}")

                elif command in ['help', '?']:
                    print("\n📖 Command Reference:")
                    print("  tree, full, all       → Full repository visualization")
                    print("  branch <path>         → Single branch (e.g., 'branch phase-2-predictive')")
                    print("  deps, brain           → Dependency graph (neural view)")
                    print("  redundant, dups       → Find code redundancies")
                    print("  capabilities, hidden  → Discover hidden capabilities")
                    print("  list                  → List all files")
                    print("  category <name>       → Filter by category")
                    print("  quit, exit            → Exit explorer\n")

                else:
                    print(f"\n❓ Unknown command: '{command}'")
                    print("Type 'help' to see available commands.\n")

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Exiting...\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    # Helper methods

    def _sanitize_id(self, path: str) -> str:
        """Convert file path to valid Mermaid ID"""
        return path.replace('/', '_').replace('.', '_').replace('-', '_')

    def _get_file_label(self, path: str) -> str:
        """Get human-readable label from path"""
        return path.split('/')[-1]

    def _get_importance_emoji(self, importance: str) -> str:
        """Visual indicator for importance"""
        emoji_map = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        return emoji_map.get(importance, '⚪')


def main():
    """Main entry point with CLI argument parsing"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Vision 2045 Repository Visualizer - Intelligent diagram generation",
        epilog="Building the future, one visualization at a time."
    )

    parser.add_argument(
        '--full-tree',
        action='store_true',
        help='Generate full repository tree diagram'
    )

    parser.add_argument(
        '--branch',
        type=str,
        metavar='PATH',
        help='Generate diagram for specific branch (e.g., phase-2-predictive)'
    )

    parser.add_argument(
        '--dependencies',
        action='store_true',
        help='Generate dependency graph (brain view)'
    )

    parser.add_argument(
        '--redundancies',
        action='store_true',
        help='Analyze redundancies and code compression opportunities'
    )

    parser.add_argument(
        '--capabilities',
        action='store_true',
        help='Show capability matrix and hidden capabilities'
    )

    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Launch interactive exploration mode'
    )

    parser.add_argument(
        '--manifest',
        type=str,
        default='.repometa/manifest.yaml',
        help='Path to manifest file (default: .repometa/manifest.yaml)'
    )

    args = parser.parse_args()

    # Initialize visualizer
    try:
        viz = RepoVisualizer(manifest_path=args.manifest)
    except Exception as e:
        print(f"❌ Failed to initialize visualizer: {e}")
        sys.exit(1)

    # Execute requested visualization
    if args.interactive:
        viz.interactive_mode()

    elif args.full_tree:
        print(viz.generate_full_tree_diagram())

    elif args.branch:
        print(viz.generate_branch_diagram(args.branch))

    elif args.dependencies:
        print(viz.generate_dependency_graph())

    elif args.redundancies:
        print(viz.generate_redundancy_report())

    elif args.capabilities:
        print(viz.generate_capability_matrix())

    else:
        # No arguments - show help and suggest interactive mode
        parser.print_help()
        print("\n💡 Tip: Try '--interactive' for conversational exploration!")


if __name__ == '__main__':
    main()
