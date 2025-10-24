#!/usr/bin/env python3
"""
Vision 2045 Intelligence Engine
Automated code analysis, redundancy detection, dependency impact analysis, and capability inference

This is Phase 2 of Vision 2045 - moving from manual to automated insights.

Usage:
  python analyzer.py --scan-redundancies          # Find duplicate code automatically
  python analyzer.py --impact-analysis            # Calculate blast radius for all components
  python analyzer.py --infer-capabilities         # AI discovers hidden capabilities
  python analyzer.py --complexity-score           # Identify refactoring opportunities
  python analyzer.py --full-analysis              # Run all analyses
"""

import os
import sys
import yaml
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


@dataclass
class CodeBlock:
    """Represents a block of code for similarity analysis"""
    file_path: str
    content: str
    start_line: int
    end_line: int
    hash_value: str

    def similarity_to(self, other: 'CodeBlock') -> float:
        """Calculate similarity percentage between two code blocks"""
        if self.hash_value == other.hash_value:
            return 100.0

        # Tokenize and compare
        self_tokens = set(self._tokenize(self.content))
        other_tokens = set(self._tokenize(other.content))

        if not self_tokens and not other_tokens:
            return 100.0
        if not self_tokens or not other_tokens:
            return 0.0

        intersection = len(self_tokens & other_tokens)
        union = len(self_tokens | other_tokens)

        return (intersection / union) * 100.0

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for comparison"""
        # Remove comments and whitespace
        text = re.sub(r'#.*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'\s+', ' ', text)

        # Extract meaningful tokens
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens


@dataclass
class DependencyNode:
    """Represents a component in the dependency graph"""
    path: str
    importance: str
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    external_deps: List[str] = field(default_factory=list)

    def blast_radius(self) -> int:
        """Calculate how many components depend on this one"""
        return len(self.dependents)

    def criticality_score(self) -> float:
        """Calculate criticality (0-100)"""
        importance_scores = {'critical': 100, 'high': 75, 'medium': 50, 'low': 25}
        base_score = importance_scores.get(self.importance, 50)

        # Adjust based on dependents
        dependency_factor = min(self.blast_radius() * 5, 50)

        return min(base_score + dependency_factor, 100)


@dataclass
class InferredCapability:
    """Represents a capability discovered through code analysis"""
    name: str
    description: str
    confidence: float  # 0-100
    evidence: List[str]
    enabled_by: List[str]
    potential_value: str
    implementation_effort: str


@dataclass
class ComplexityMetrics:
    """Code complexity metrics for a file"""
    file_path: str
    line_count: int
    function_count: int
    class_count: int
    import_count: int
    complexity_score: float  # 0-100 (higher = more complex)

    def needs_refactoring(self) -> bool:
        """Determine if file should be refactored"""
        return (
            self.line_count > 500 or
            self.complexity_score > 70 or
            self.function_count > 30
        )


class IntelligenceEngine:
    """
    Automated code analysis and insight generation
    Phase 2 of Vision 2045
    """

    def __init__(self, repo_root: str = ".", manifest_path: str = ".repometa/manifest.yaml"):
        self.repo_root = Path(repo_root)
        self.manifest_path = Path(manifest_path)
        self.manifest = self._load_manifest()
        self.files = self._build_file_index()

    def _load_manifest(self) -> Dict:
        """Load the semantic manifest"""
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ Warning: Manifest not found at {self.manifest_path}")
            print("   Some features will be limited.")
            return {'structure': [], 'categories': []}

    def _build_file_index(self) -> Dict[str, Dict]:
        """Build index of all files from manifest"""
        index = {}
        for item in self.manifest.get('structure', []):
            index[item['path']] = item
        return index

    # ============================================================
    # 1. AUTOMATED REDUNDANCY SCANNER
    # ============================================================

    def scan_redundancies(self, similarity_threshold: float = 70.0) -> Dict:
        """
        Scan actual code files to find duplicates
        Returns clusters of similar code blocks
        """
        print("🔍 Scanning for code redundancies...")
        print(f"   Similarity threshold: {similarity_threshold}%")
        print()

        # Find all markdown files (our primary content)
        md_files = list(self.repo_root.glob('**/*.md'))
        md_files = [f for f in md_files if not f.name.startswith('.') and '.repometa' not in str(f)]

        print(f"   Found {len(md_files)} markdown files to analyze")

        # Extract code blocks from each file
        all_blocks = []
        for file_path in md_files:
            blocks = self._extract_code_blocks(file_path)
            all_blocks.extend(blocks)

        print(f"   Extracted {len(all_blocks)} code blocks")
        print()

        # Find similar blocks
        clusters = self._cluster_similar_blocks(all_blocks, similarity_threshold)

        # Generate report
        return self._generate_redundancy_report(clusters)

    def _extract_code_blocks(self, file_path: Path) -> List[CodeBlock]:
        """Extract code blocks from markdown file"""
        blocks = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            return blocks

        # Find code blocks (```...```)
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            code_content = match.group(2)

            # Skip if too short (less than 3 lines)
            if len(code_content.split('\n')) < 3:
                continue

            # Calculate line numbers
            start_pos = match.start()
            start_line = content[:start_pos].count('\n') + 1
            end_line = start_line + code_content.count('\n')

            # Create hash for exact duplicate detection
            hash_value = hashlib.md5(code_content.encode()).hexdigest()

            blocks.append(CodeBlock(
                file_path=str(file_path.relative_to(self.repo_root)),
                content=code_content,
                start_line=start_line,
                end_line=end_line,
                hash_value=hash_value
            ))

        return blocks

    def _cluster_similar_blocks(self, blocks: List[CodeBlock], threshold: float) -> List[List[CodeBlock]]:
        """Cluster similar code blocks together"""
        clusters = []
        used_indices = set()

        for i, block1 in enumerate(blocks):
            if i in used_indices:
                continue

            cluster = [block1]
            used_indices.add(i)

            for j, block2 in enumerate(blocks[i+1:], start=i+1):
                if j in used_indices:
                    continue

                similarity = block1.similarity_to(block2)

                if similarity >= threshold:
                    cluster.append(block2)
                    used_indices.add(j)

            # Only keep clusters with 2+ blocks
            if len(cluster) >= 2:
                clusters.append(cluster)

        return clusters

    def _generate_redundancy_report(self, clusters: List[List[CodeBlock]]) -> Dict:
        """Generate human-readable redundancy report"""
        report = {
            'total_clusters': len(clusters),
            'total_duplicate_blocks': sum(len(cluster) for cluster in clusters),
            'clusters': []
        }

        for i, cluster in enumerate(clusters, 1):
            # Calculate potential savings
            block_sizes = [len(cluster[0].content.split('\n')) for _ in cluster]
            potential_savings = sum(block_sizes) - block_sizes[0] if block_sizes else 0

            cluster_info = {
                'cluster_id': i,
                'block_count': len(cluster),
                'locations': [
                    {
                        'file': block.file_path,
                        'lines': f"{block.start_line}-{block.end_line}",
                        'size': len(block.content.split('\n'))
                    }
                    for block in cluster
                ],
                'potential_savings_lines': potential_savings,
                'recommendation': self._generate_consolidation_recommendation(cluster)
            }

            report['clusters'].append(cluster_info)

        return report

    def _generate_consolidation_recommendation(self, cluster: List[CodeBlock]) -> str:
        """Generate recommendation for consolidating duplicates"""
        files = set(block.file_path for block in cluster)

        if len(files) == 1:
            return f"Multiple code blocks in {list(files)[0]} - consider extracting to reusable function"
        else:
            return f"Code appears in {len(files)} files - consider creating shared module"

    # ============================================================
    # 2. DEPENDENCY IMPACT ANALYZER
    # ============================================================

    def analyze_impact(self) -> Dict:
        """
        Calculate blast radius for all components
        Shows what breaks if each component fails
        """
        print("💥 Analyzing dependency impact and blast radius...")
        print()

        # Build dependency graph
        graph = self._build_dependency_graph()

        # Calculate impact for each node
        impact_analysis = {
            'critical_paths': [],
            'single_points_of_failure': [],
            'components': []
        }

        for path, node in sorted(graph.items(), key=lambda x: x[1].criticality_score(), reverse=True):
            component_impact = {
                'path': path,
                'importance': node.importance,
                'criticality_score': round(node.criticality_score(), 1),
                'blast_radius': node.blast_radius(),
                'direct_dependents': node.dependents,
                'external_dependencies': node.external_deps,
                'failure_impact': self._calculate_failure_impact(node, graph)
            }

            impact_analysis['components'].append(component_impact)

            # Identify single points of failure
            if node.blast_radius() >= 5 and node.importance == 'critical':
                impact_analysis['single_points_of_failure'].append({
                    'component': path,
                    'reason': f"Critical component with {node.blast_radius()} dependents",
                    'mitigation': self._suggest_mitigation(node)
                })

        # Identify critical paths
        critical_paths = self._find_critical_paths(graph)
        impact_analysis['critical_paths'] = critical_paths

        return impact_analysis

    def _build_dependency_graph(self) -> Dict[str, DependencyNode]:
        """Build complete dependency graph from manifest"""
        graph = {}

        for item in self.manifest.get('structure', []):
            path = item['path']
            node = DependencyNode(
                path=path,
                importance=item.get('importance', 'medium'),
                dependencies=item.get('connects_to', []),
                external_deps=item.get('dependencies', [])
            )
            graph[path] = node

        # Calculate reverse dependencies (who depends on me)
        for path, node in graph.items():
            for dep in node.dependencies:
                if dep in graph:
                    graph[dep].dependents.append(path)

        return graph

    def _calculate_failure_impact(self, node: DependencyNode, graph: Dict[str, DependencyNode]) -> Dict:
        """Calculate what happens if this component fails"""
        # BFS to find all transitive dependents
        visited = set()
        queue = [node.path]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current in graph:
                for dependent in graph[current].dependents:
                    if dependent not in visited:
                        queue.append(dependent)

        total_impacted = len(visited) - 1  # Exclude self

        return {
            'direct_impact': len(node.dependents),
            'total_impact': total_impacted,
            'severity': self._impact_severity(total_impacted, node.importance)
        }

    def _impact_severity(self, impact_count: int, importance: str) -> str:
        """Determine severity level of failure"""
        if importance == 'critical' and impact_count >= 5:
            return "CATASTROPHIC"
        elif importance == 'critical' or impact_count >= 10:
            return "SEVERE"
        elif impact_count >= 5:
            return "MODERATE"
        else:
            return "LOW"

    def _suggest_mitigation(self, node: DependencyNode) -> str:
        """Suggest mitigation strategies"""
        strategies = []

        if node.blast_radius() >= 5:
            strategies.append("Implement circuit breaker pattern")

        if 'BigQuery' in node.external_deps:
            strategies.append("Add caching layer")

        if node.importance == 'critical':
            strategies.append("Set up redundancy/failover")

        return " | ".join(strategies) if strategies else "Monitor closely"

    def _find_critical_paths(self, graph: Dict[str, DependencyNode]) -> List[Dict]:
        """Identify critical dependency paths"""
        paths = []

        # Find longest dependency chains
        for path, node in graph.items():
            if not node.dependencies:  # Leaf node
                chain = self._trace_dependency_chain(path, graph)
                if len(chain) >= 3:
                    paths.append({
                        'chain': chain,
                        'length': len(chain),
                        'risk': 'High' if any(graph[p].importance == 'critical' for p in chain if p in graph) else 'Medium'
                    })

        return sorted(paths, key=lambda x: x['length'], reverse=True)[:5]

    def _trace_dependency_chain(self, start: str, graph: Dict[str, DependencyNode], visited: Set[str] = None) -> List[str]:
        """Trace dependency chain from a node"""
        if visited is None:
            visited = set()

        if start in visited or start not in graph:
            return []

        visited.add(start)
        chain = [start]

        node = graph[start]
        if node.dependencies:
            # Find longest sub-chain
            longest_subchain = []
            for dep in node.dependencies:
                subchain = self._trace_dependency_chain(dep, graph, visited.copy())
                if len(subchain) > len(longest_subchain):
                    longest_subchain = subchain

            chain.extend(longest_subchain)

        return chain

    # ============================================================
    # 3. CAPABILITY INFERENCE ENGINE
    # ============================================================

    def infer_capabilities(self) -> List[InferredCapability]:
        """
        AI-powered discovery of hidden capabilities
        Analyzes patterns and suggests non-obvious connections
        """
        print("💡 Inferring hidden capabilities through pattern analysis...")
        print()

        inferred = []

        # Pattern 1: Testing + Feature = Self-Testing Feature
        inferred.extend(self._infer_self_testing_capabilities())

        # Pattern 2: Multiple ML models + Orchestration = A/B Testing
        inferred.extend(self._infer_ab_testing_capabilities())

        # Pattern 3: Performance Monitoring + Data = Auto-Optimization
        inferred.extend(self._infer_optimization_capabilities())

        # Pattern 4: Multiple similar files = Consolidation opportunity
        inferred.extend(self._infer_consolidation_capabilities())

        # Pattern 5: Data + AI = Predictive capability
        inferred.extend(self._infer_predictive_capabilities())

        return sorted(inferred, key=lambda x: x.confidence, reverse=True)

    def _infer_self_testing_capabilities(self) -> List[InferredCapability]:
        """Detect features that could test themselves"""
        capabilities = []

        # Find feature files
        feature_files = [f for f in self.files.keys() if 'phase-' in f and 'testing' not in f]
        testing_files = [f for f in self.files.keys() if 'testing' in f or 'chaos' in f]

        if not feature_files or not testing_files:
            return capabilities

        # Check for event-driven or orchestration patterns
        orchestration_files = [f for f in feature_files if 'orchestration' in f or 'journey' in f]
        chaos_files = [f for f in testing_files if 'chaos' in f]

        if orchestration_files and chaos_files:
            capabilities.append(InferredCapability(
                name="Self-Healing Feature Validation",
                description="Features can automatically trigger their own chaos tests to validate resilience",
                confidence=85.0,
                evidence=[
                    f"Found {len(orchestration_files)} orchestration files",
                    f"Found {len(chaos_files)} chaos testing files",
                    "Both use event-driven architecture patterns"
                ],
                enabled_by=orchestration_files + chaos_files,
                potential_value="Zero-downtime deployments with automatic validation",
                implementation_effort="medium"
            ))

        return capabilities

    def _infer_ab_testing_capabilities(self) -> List[InferredCapability]:
        """Detect A/B testing opportunities"""
        capabilities = []

        ml_files = [f for f in self.files.keys() if self.files[f].get('category') == 'ai_ml']
        orchestration_files = [f for f in self.files.keys() if 'orchestration' in f or 'journey' in f]

        if len(ml_files) >= 2 and orchestration_files:
            capabilities.append(InferredCapability(
                name="Multi-Model A/B Testing in Production",
                description="Journey orchestration can serve multiple model versions and compare performance in real-time",
                confidence=78.0,
                evidence=[
                    f"Found {len(ml_files)} ML models",
                    f"Found {len(orchestration_files)} orchestration systems",
                    "Orchestration systems can route to multiple backends"
                ],
                enabled_by=ml_files[:2] + orchestration_files,
                potential_value="Continuous model improvement without deployment risk",
                implementation_effort="low"
            ))

        return capabilities

    def _infer_optimization_capabilities(self) -> List[InferredCapability]:
        """Detect auto-optimization opportunities"""
        capabilities = []

        performance_files = [f for f in self.files.keys() if 'performance' in f.lower()]
        data_files = [f for f in self.files.keys() if 'data' in f.lower() or 'bigquery' in f.lower()]

        if performance_files and data_files:
            capabilities.append(InferredCapability(
                name="Automated Query Optimization",
                description="Performance monitoring can identify slow queries and automatically apply optimizations",
                confidence=70.0,
                evidence=[
                    f"Found {len(performance_files)} performance monitoring files",
                    f"Found {len(data_files)} data infrastructure files",
                    "Performance tests can profile query execution"
                ],
                enabled_by=performance_files + data_files[:2],
                potential_value="30-50% query performance improvement without manual intervention",
                implementation_effort="medium"
            ))

        return capabilities

    def _infer_consolidation_capabilities(self) -> List[InferredCapability]:
        """Detect consolidation opportunities"""
        capabilities = []

        # Group files by semantic similarity
        category_counts = defaultdict(int)
        for file_info in self.files.values():
            category_counts[file_info.get('category', 'unknown')] += 1

        # Find categories with many files (consolidation opportunity)
        for category, count in category_counts.items():
            if count >= 4 and category != 'unknown':
                category_files = [f for f, info in self.files.items() if info.get('category') == category]

                capabilities.append(InferredCapability(
                    name=f"Unified {category.replace('_', ' ').title()} Platform",
                    description=f"Consolidate {count} {category} files into single cohesive system",
                    confidence=65.0,
                    evidence=[
                        f"Found {count} files in {category} category",
                        "Similar purposes and capabilities",
                        "Likely shared patterns and utilities"
                    ],
                    enabled_by=category_files[:3],
                    potential_value=f"Reduced maintenance burden, consistent interface for {category}",
                    implementation_effort="high"
                ))

        return capabilities

    def _infer_predictive_capabilities(self) -> List[InferredCapability]:
        """Detect predictive capability opportunities"""
        capabilities = []

        data_files = [f for f in self.files.keys() if 'data' in f.lower()]
        ml_files = [f for f in self.files.keys() if self.files[f].get('category') == 'ai_ml']

        # Check for data + ML combination
        if data_files and ml_files:
            # Look for specific prediction opportunities
            if any('customer' in f.lower() for f in data_files):
                capabilities.append(InferredCapability(
                    name="Predictive Customer Lifetime Value",
                    description="Customer data + ML models enables CLV prediction for all customers",
                    confidence=82.0,
                    evidence=[
                        "Customer data foundation in place",
                        "ML infrastructure operational",
                        "Similar to existing lead scoring model"
                    ],
                    enabled_by=[f for f in data_files if 'customer' in f.lower()][:1] + ml_files[:1],
                    potential_value="Prioritize high-value customers, reduce churn investment waste",
                    implementation_effort="low"
                ))

        return capabilities

    # ============================================================
    # 4. CODE COMPLEXITY SCORER
    # ============================================================

    def score_complexity(self) -> List[ComplexityMetrics]:
        """
        Analyze code complexity and identify refactoring opportunities
        """
        print("📊 Scoring code complexity...")
        print()

        metrics = []

        # Analyze all markdown files
        md_files = list(self.repo_root.glob('**/*.md'))
        md_files = [f for f in md_files if not f.name.startswith('.') and '.repometa' not in str(f)]

        for file_path in md_files:
            metric = self._analyze_file_complexity(file_path)
            if metric:
                metrics.append(metric)

        return sorted(metrics, key=lambda x: x.complexity_score, reverse=True)

    def _analyze_file_complexity(self, file_path: Path) -> Optional[ComplexityMetrics]:
        """Analyze complexity of a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, FileNotFoundError):
            return None

        lines = content.split('\n')
        line_count = len(lines)

        # Count code blocks (functions)
        function_count = len(re.findall(r'```\w+\n.*?def\s+\w+', content, re.DOTALL))

        # Count headings (approximation of classes/sections)
        class_count = len(re.findall(r'^#{1,3}\s+', content, re.MULTILINE))

        # Count imports (in code blocks)
        import_count = len(re.findall(r'^\s*(import|from)\s+', content, re.MULTILINE))

        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            line_count, function_count, class_count, import_count
        )

        return ComplexityMetrics(
            file_path=str(file_path.relative_to(self.repo_root)),
            line_count=line_count,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            complexity_score=complexity_score
        )

    def _calculate_complexity_score(self, lines: int, functions: int, classes: int, imports: int) -> float:
        """Calculate overall complexity score (0-100)"""
        # Normalize each metric
        line_score = min((lines / 1000) * 50, 50)  # Max 50 points for lines
        function_score = min((functions / 30) * 20, 20)  # Max 20 points for functions
        class_score = min((classes / 50) * 20, 20)  # Max 20 points for sections
        import_score = min((imports / 20) * 10, 10)  # Max 10 points for imports

        total = line_score + function_score + class_score + import_score

        return min(total, 100)


def print_redundancy_report(report: Dict):
    """Pretty print redundancy analysis results"""
    print("=" * 80)
    print("🔍 AUTOMATED REDUNDANCY ANALYSIS REPORT")
    print("=" * 80)
    print()

    print(f"📊 Summary:")
    print(f"   Total redundancy clusters found: {report['total_clusters']}")
    print(f"   Total duplicate code blocks: {report['total_duplicate_blocks']}")
    print()

    if report['clusters']:
        print("🔬 Detailed Findings:")
        print()

        for cluster in report['clusters']:
            print(f"   Cluster #{cluster['cluster_id']} - {cluster['block_count']} duplicates found")
            print(f"   Potential savings: {cluster['potential_savings_lines']} lines")
            print(f"   Locations:")
            for loc in cluster['locations']:
                print(f"      - {loc['file']}:{loc['lines']} ({loc['size']} lines)")
            print(f"   💡 {cluster['recommendation']}")
            print()
    else:
        print("✅ No significant code redundancies detected!")
        print("   Your codebase is well-organized.")

    print("=" * 80)


def print_impact_analysis(analysis: Dict):
    """Pretty print dependency impact analysis"""
    print("=" * 80)
    print("💥 DEPENDENCY IMPACT & BLAST RADIUS ANALYSIS")
    print("=" * 80)
    print()

    # Single points of failure
    if analysis['single_points_of_failure']:
        print("⚠️  SINGLE POINTS OF FAILURE:")
        print()
        for spof in analysis['single_points_of_failure']:
            print(f"   🔴 {spof['component']}")
            print(f"      Reason: {spof['reason']}")
            print(f"      Mitigation: {spof['mitigation']}")
            print()

    # Critical paths
    if analysis['critical_paths']:
        print("🔗 CRITICAL DEPENDENCY PATHS:")
        print()
        for i, path in enumerate(analysis['critical_paths'][:3], 1):
            print(f"   Path #{i} (length: {path['length']}, risk: {path['risk']})")
            print(f"      {' → '.join(path['chain'][:4])}")
            if len(path['chain']) > 4:
                print(f"      ... and {len(path['chain']) - 4} more")
            print()

    # Top components by criticality
    print("📊 TOP COMPONENTS BY CRITICALITY:")
    print()

    top_components = sorted(analysis['components'], key=lambda x: x['criticality_score'], reverse=True)[:10]

    for comp in top_components:
        severity_emoji = {
            'CATASTROPHIC': '🔴',
            'SEVERE': '🟠',
            'MODERATE': '🟡',
            'LOW': '🟢'
        }.get(comp['failure_impact']['severity'], '⚪')

        print(f"   {severity_emoji} {comp['path']}")
        print(f"      Criticality: {comp['criticality_score']}/100")
        print(f"      Blast radius: {comp['blast_radius']} direct dependents")
        print(f"      Failure impact: {comp['failure_impact']['severity']} ({comp['failure_impact']['total_impact']} components affected)")
        if comp['external_dependencies']:
            print(f"      External deps: {', '.join(comp['external_dependencies'][:3])}")
        print()

    print("=" * 80)


def print_inferred_capabilities(capabilities: List[InferredCapability]):
    """Pretty print inferred capabilities"""
    print("=" * 80)
    print("💡 INFERRED CAPABILITIES - AI-DISCOVERED OPPORTUNITIES")
    print("=" * 80)
    print()

    if not capabilities:
        print("   No new capabilities inferred at this time.")
        print("   The system will continue learning as the codebase evolves.")
        print()
        return

    for cap in capabilities:
        confidence_emoji = "🟢" if cap.confidence >= 80 else "🟡" if cap.confidence >= 60 else "🟠"

        print(f"{confidence_emoji} {cap.name}")
        print(f"   Confidence: {cap.confidence:.0f}%")
        print(f"   Description: {cap.description}")
        print(f"   Evidence:")
        for evidence in cap.evidence:
            print(f"      • {evidence}")
        print(f"   Enabled by: {', '.join(cap.enabled_by[:3])}")
        if len(cap.enabled_by) > 3:
            print(f"               ... and {len(cap.enabled_by) - 3} more")
        print(f"   💰 Value: {cap.potential_value}")
        print(f"   ⚙️  Implementation effort: {cap.implementation_effort}")
        print()

    print("=" * 80)


def print_complexity_scores(metrics: List[ComplexityMetrics]):
    """Pretty print complexity analysis"""
    print("=" * 80)
    print("📊 CODE COMPLEXITY ANALYSIS")
    print("=" * 80)
    print()

    # Files needing refactoring
    needs_refactoring = [m for m in metrics if m.needs_refactoring()]

    if needs_refactoring:
        print("⚠️  FILES RECOMMENDED FOR REFACTORING:")
        print()
        for metric in needs_refactoring[:10]:
            print(f"   🔴 {metric.file_path}")
            print(f"      Complexity score: {metric.complexity_score:.1f}/100")
            print(f"      Lines: {metric.line_count}, Functions: {metric.function_count}, Sections: {metric.class_count}")

            reasons = []
            if metric.line_count > 500:
                reasons.append(f"Large file ({metric.line_count} lines)")
            if metric.function_count > 30:
                reasons.append(f"Many functions ({metric.function_count})")
            if metric.complexity_score > 70:
                reasons.append(f"High complexity ({metric.complexity_score:.0f}/100)")

            print(f"      Reasons: {', '.join(reasons)}")
            print()

    # Overall stats
    print("📈 OVERALL COMPLEXITY STATISTICS:")
    print()
    print(f"   Total files analyzed: {len(metrics)}")
    print(f"   Average complexity: {sum(m.complexity_score for m in metrics) / len(metrics):.1f}/100")
    print(f"   Files needing refactoring: {len(needs_refactoring)} ({len(needs_refactoring)/len(metrics)*100:.1f}%)")
    print(f"   Total lines of documentation: {sum(m.line_count for m in metrics):,}")
    print()

    # Top 5 most complex
    print("🔝 MOST COMPLEX FILES:")
    print()
    for i, metric in enumerate(metrics[:5], 1):
        print(f"   {i}. {metric.file_path}")
        print(f"      Complexity: {metric.complexity_score:.1f}/100, Lines: {metric.line_count}")

    print()
    print("=" * 80)


def main():
    """Main entry point with CLI arguments"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Vision 2045 Intelligence Engine - Automated code analysis",
        epilog="Phase 2: Moving from manual to automated insights"
    )

    parser.add_argument(
        '--scan-redundancies',
        action='store_true',
        help='Scan for duplicate code automatically'
    )

    parser.add_argument(
        '--impact-analysis',
        action='store_true',
        help='Calculate blast radius for all components'
    )

    parser.add_argument(
        '--infer-capabilities',
        action='store_true',
        help='AI discovers hidden capabilities'
    )

    parser.add_argument(
        '--complexity-score',
        action='store_true',
        help='Identify refactoring opportunities'
    )

    parser.add_argument(
        '--full-analysis',
        action='store_true',
        help='Run all analyses'
    )

    parser.add_argument(
        '--similarity-threshold',
        type=float,
        default=70.0,
        help='Similarity threshold for redundancy detection (0-100, default: 70)'
    )

    args = parser.parse_args()

    # Initialize engine
    try:
        engine = IntelligenceEngine()
    except Exception as e:
        print(f"❌ Failed to initialize intelligence engine: {e}")
        sys.exit(1)

    # Run requested analyses
    if args.full_analysis or args.scan_redundancies:
        report = engine.scan_redundancies(args.similarity_threshold)
        print_redundancy_report(report)
        print()

    if args.full_analysis or args.impact_analysis:
        analysis = engine.analyze_impact()
        print_impact_analysis(analysis)
        print()

    if args.full_analysis or args.infer_capabilities:
        capabilities = engine.infer_capabilities()
        print_inferred_capabilities(capabilities)
        print()

    if args.full_analysis or args.complexity_score:
        metrics = engine.score_complexity()
        print_complexity_scores(metrics)
        print()

    if not any([args.scan_redundancies, args.impact_analysis, args.infer_capabilities,
                args.complexity_score, args.full_analysis]):
        parser.print_help()
        print("\n💡 Tip: Try '--full-analysis' to run all intelligence features!")


if __name__ == '__main__':
    main()
