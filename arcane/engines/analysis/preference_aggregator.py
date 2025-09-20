"""Comprehensive preference aggregator for advanced analysis and insights."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplexityScore(Enum):
    """Complexity score classifications."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class RiskAssessment:
    """Risk assessment results."""
    level: RiskLevel
    factors: List[str]
    mitigations: List[str]
    score: float  # 0.0 to 1.0


@dataclass
class FeasibilityAnalysis:
    """Feasibility analysis results."""
    is_feasible: bool
    confidence: float  # 0.0 to 1.0
    concerns: List[str]
    recommendations: List[str]


@dataclass
class ResourceAlignment:
    """Resource alignment analysis."""
    budget_alignment: float  # 0.0 to 1.0
    team_alignment: float  # 0.0 to 1.0
    timeline_alignment: float  # 0.0 to 1.0
    gaps: List[str]
    optimizations: List[str]


@dataclass
class TechnicalComplexity:
    """Technical complexity analysis."""
    score: ComplexityScore
    primary_challenges: List[str]
    dependencies: List[str]
    architectural_recommendations: List[str]


@dataclass
class AggregatedInsights:
    """Complete aggregated insights from all preferences."""
    risk_assessment: RiskAssessment
    feasibility: FeasibilityAnalysis
    resource_alignment: ResourceAlignment
    technical_complexity: TechnicalComplexity
    priority_recommendations: List[str]
    success_factors: List[str]
    warning_flags: List[str]

    # Calculated scores
    overall_complexity_score: float  # 0.0 to 1.0
    overall_risk_score: float  # 0.0 to 1.0
    overall_feasibility_score: float  # 0.0 to 1.0

    # Key metrics for prompt enhancement
    estimated_actual_timeline: str
    recommended_team_size: str
    minimum_budget_estimate: str
    critical_skills_needed: List[str]


class PreferenceAggregator:
    """Processes all collected preferences to generate insights and recommendations."""

    def __init__(self):
        self.logger = logger

    def aggregate_preferences(self, preferences: Dict[str, Any]) -> AggregatedInsights:
        """
        Process all preferences and generate comprehensive insights.

        Args:
            preferences: Dictionary containing all 27 question responses

        Returns:
            AggregatedInsights with all calculated values
        """
        # Perform individual analyses
        risk = self._assess_risk(preferences)
        feasibility = self._analyze_feasibility(preferences)
        resources = self._analyze_resource_alignment(preferences)
        complexity = self._analyze_technical_complexity(preferences)

        # Generate recommendations
        priorities = self._generate_priority_recommendations(preferences, risk, feasibility)
        success_factors = self._identify_success_factors(preferences)
        warnings = self._identify_warning_flags(preferences, risk, feasibility, resources)

        # Calculate overall scores
        complexity_score = self._calculate_complexity_score(preferences)
        risk_score = risk.score
        feasibility_score = feasibility.confidence

        # Estimate adjusted values
        actual_timeline = self._estimate_actual_timeline(preferences, complexity_score)
        recommended_team = self._recommend_team_size(preferences, complexity)
        min_budget = self._estimate_minimum_budget(preferences, complexity)
        critical_skills = self._identify_critical_skills(preferences)

        return AggregatedInsights(
            risk_assessment=risk,
            feasibility=feasibility,
            resource_alignment=resources,
            technical_complexity=complexity,
            priority_recommendations=priorities,
            success_factors=success_factors,
            warning_flags=warnings,
            overall_complexity_score=complexity_score,
            overall_risk_score=risk_score,
            overall_feasibility_score=feasibility_score,
            estimated_actual_timeline=actual_timeline,
            recommended_team_size=recommended_team,
            minimum_budget_estimate=min_budget,
            critical_skills_needed=critical_skills
        )

    def _assess_risk(self, preferences: Dict[str, Any]) -> RiskAssessment:
        """Assess project risk based on preferences."""
        risk_factors = []
        mitigations = []
        risk_score = 0.0

        # Team expertise vs complexity
        expertise = preferences.get('team_expertise', 'intermediate')
        complexity = preferences.get('complexity', 'moderate')

        if expertise == 'learning' and complexity in ['complex', 'very_complex']:
            risk_factors.append("Team learning new technology on complex project")
            mitigations.append("Consider hiring consultants or extending timeline")
            risk_score += 0.3

        # Budget constraints
        budget = preferences.get('budget_range', 'undefined')
        if budget in ['bootstrap', 'undefined']:
            risk_factors.append("Limited or undefined budget")
            mitigations.append("Focus on MVP features and phased deployment")
            risk_score += 0.2

        # Technical challenges
        tech_challenges = preferences.get('technical_challenges', [])
        high_risk_challenges = ['ml-ai', 'blockchain', 'iot-hardware', 'realtime-data']
        risky_techs = [tc for tc in tech_challenges if tc in high_risk_challenges]

        if len(risky_techs) > 2:
            risk_factors.append(f"Multiple high-risk technologies: {', '.join(risky_techs)}")
            mitigations.append("Prototype high-risk components early")
            risk_score += 0.25

        # Timeline pressure
        timeline = preferences.get('timeline', '6-months')
        if timeline == '3-months' and complexity != 'simple':
            risk_factors.append("Aggressive timeline for project complexity")
            mitigations.append("Consider reducing scope or extending timeline")
            risk_score += 0.2

        # Regulatory compliance
        regulations = preferences.get('regulatory', [])
        if len(regulations) > 2 and 'none' not in regulations:
            risk_factors.append(f"Multiple regulatory requirements: {', '.join(regulations)}")
            mitigations.append("Budget for compliance audit and legal review")
            risk_score += 0.15

        # Team distribution
        distribution = preferences.get('team_distribution', 'colocated')
        if distribution == 'remote-async' and complexity in ['complex', 'very_complex']:
            risk_factors.append("Async remote team on complex project")
            mitigations.append("Invest in collaboration tools and clear documentation")
            risk_score += 0.1

        # Determine risk level
        if risk_score >= 0.7:
            level = RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskAssessment(
            level=level,
            factors=risk_factors or ["No significant risk factors identified"],
            mitigations=mitigations or ["Maintain current approach"],
            score=min(risk_score, 1.0)
        )

    def _analyze_feasibility(self, preferences: Dict[str, Any]) -> FeasibilityAnalysis:
        """Analyze project feasibility."""
        concerns = []
        recommendations = []
        confidence = 1.0

        # Timeline feasibility
        timeline = preferences.get('timeline', '6-months')
        complexity = preferences.get('complexity', 'moderate')
        team_size = preferences.get('team_size', '2-3')

        timeline_months = {'3-months': 3, '6-months': 6, '12-months': 12}.get(timeline, 6)
        complexity_factor = {'simple': 1, 'moderate': 2, 'complex': 3}.get(complexity, 2)
        team_factor = {'1': 0.5, '2-3': 1, '4-8': 1.5, '8+': 2}.get(team_size, 1)

        estimated_months = complexity_factor * 3 / team_factor

        if estimated_months > timeline_months:
            concerns.append(f"Timeline may be insufficient (need ~{estimated_months:.0f} months)")
            recommendations.append("Consider extending timeline or reducing scope")
            confidence -= 0.3

        # Budget feasibility
        budget = preferences.get('budget_range', 'undefined')
        infra_budget = preferences.get('infra_budget', 'moderate')

        if budget == 'bootstrap' and infra_budget in ['substantial', 'unlimited']:
            concerns.append("Budget mismatch: bootstrap funding with high infrastructure needs")
            recommendations.append("Optimize for serverless or managed services")
            confidence -= 0.2

        # Technical feasibility
        expertise = preferences.get('team_expertise', 'intermediate')
        tech_challenges = preferences.get('technical_challenges', [])

        if expertise == 'learning' and len(tech_challenges) > 3:
            concerns.append("Team learning curve with multiple technical challenges")
            recommendations.append("Plan for training time and proof-of-concepts")
            confidence -= 0.25

        # Integration complexity
        integrations = []
        for key in ['payment_integrations', 'communication_integrations', 'business_integrations',
                   'developer_integrations', 'data_integrations']:
            items = preferences.get(key, [])
            if items and 'none' not in items:
                integrations.extend(items)

        if len(integrations) > 10:
            concerns.append(f"High integration complexity ({len(integrations)} systems)")
            recommendations.append("Phase integrations over multiple releases")
            confidence -= 0.15

        return FeasibilityAnalysis(
            is_feasible=confidence >= 0.5,
            confidence=max(confidence, 0.0),
            concerns=concerns or ["No significant feasibility concerns"],
            recommendations=recommendations or ["Proceed with current plan"]
        )

    def _analyze_resource_alignment(self, preferences: Dict[str, Any]) -> ResourceAlignment:
        """Analyze alignment between resources and requirements."""
        gaps = []
        optimizations = []

        # Budget alignment
        budget = preferences.get('budget_range', 'undefined')
        budget_scores = {'bootstrap': 0.2, 'seed': 0.4, 'funded': 0.7, 'enterprise': 1.0, 'undefined': 0.3}
        budget_score = budget_scores.get(budget, 0.3)

        complexity = preferences.get('complexity', 'moderate')
        complexity_requirement = {'simple': 0.3, 'moderate': 0.5, 'complex': 0.8}.get(complexity, 0.5)

        budget_alignment = min(budget_score / complexity_requirement, 1.0) if complexity_requirement > 0 else 1.0

        if budget_alignment < 0.7:
            gaps.append("Budget may be insufficient for project complexity")
            optimizations.append("Consider phased delivery or seeking additional funding")

        # Team alignment
        team_size = preferences.get('team_size', '2-3')
        team_scores = {'1': 0.25, '2-3': 0.5, '4-8': 0.75, '8+': 1.0}
        team_score = team_scores.get(team_size, 0.5)

        team_alignment = min(team_score / complexity_requirement, 1.0) if complexity_requirement > 0 else 1.0

        if team_alignment < 0.7:
            gaps.append("Team size may be insufficient for project scope")
            optimizations.append("Consider contractor augmentation or scope reduction")

        # Timeline alignment
        timeline = preferences.get('timeline', '6-months')
        timeline_scores = {'3-months': 0.25, '6-months': 0.5, '12-months': 0.75}
        timeline_score = timeline_scores.get(timeline, 0.5)

        timeline_alignment = min(timeline_score / complexity_requirement, 1.0) if complexity_requirement > 0 else 1.0

        if timeline_alignment < 0.7:
            gaps.append("Timeline may be too aggressive")
            optimizations.append("Extend timeline or implement MVP approach")

        return ResourceAlignment(
            budget_alignment=budget_alignment,
            team_alignment=team_alignment,
            timeline_alignment=timeline_alignment,
            gaps=gaps or ["Resources well-aligned with requirements"],
            optimizations=optimizations or ["Current resource allocation is appropriate"]
        )

    def _analyze_technical_complexity(self, preferences: Dict[str, Any]) -> TechnicalComplexity:
        """Analyze technical complexity of the project."""
        challenges = preferences.get('technical_challenges', [])
        primary_challenges = []
        dependencies = []
        recommendations = []

        # Categorize challenges
        if 'realtime-data' in challenges:
            primary_challenges.append("Real-time data processing")
            dependencies.append("Message queue system (Kafka/RabbitMQ)")
            recommendations.append("Design for horizontal scaling from the start")

        if 'ml-ai' in challenges:
            primary_challenges.append("Machine learning implementation")
            dependencies.append("ML framework (TensorFlow/PyTorch)")
            recommendations.append("Separate ML pipeline from main application")

        if 'microservices' in challenges:
            primary_challenges.append("Microservices architecture")
            dependencies.append("Container orchestration (Kubernetes)")
            dependencies.append("Service mesh (Istio/Linkerd)")
            recommendations.append("Start with modular monolith, evolve to microservices")

        if 'blockchain' in challenges:
            primary_challenges.append("Blockchain integration")
            dependencies.append("Web3 libraries and smart contracts")
            recommendations.append("Consider hybrid approach with traditional database")

        # Determine complexity score
        complexity_points = len(challenges)
        regulations = preferences.get('regulatory', [])
        if regulations and 'none' not in regulations:
            complexity_points += len(regulations) * 0.5

        integrations = 0
        for key in ['payment_integrations', 'communication_integrations', 'business_integrations',
                   'developer_integrations', 'data_integrations']:
            items = preferences.get(key, [])
            if items and 'none' not in items:
                integrations += len(items)
        complexity_points += integrations * 0.2

        if complexity_points <= 2:
            score = ComplexityScore.SIMPLE
        elif complexity_points <= 5:
            score = ComplexityScore.MODERATE
        elif complexity_points <= 10:
            score = ComplexityScore.COMPLEX
        else:
            score = ComplexityScore.VERY_COMPLEX

        # Add architectural recommendations
        if score in [ComplexityScore.COMPLEX, ComplexityScore.VERY_COMPLEX]:
            recommendations.append("Invest in robust CI/CD pipeline early")
            recommendations.append("Implement comprehensive monitoring and observability")
            recommendations.append("Plan for dedicated DevOps/SRE resources")

        return TechnicalComplexity(
            score=score,
            primary_challenges=primary_challenges or ["Standard web application challenges"],
            dependencies=dependencies or ["Standard web framework and database"],
            architectural_recommendations=recommendations or ["Follow framework best practices"]
        )

    def _generate_priority_recommendations(
        self,
        preferences: Dict[str, Any],
        risk: RiskAssessment,
        feasibility: FeasibilityAnalysis
    ) -> List[str]:
        """Generate priority recommendations based on analysis."""
        priorities = []

        # High-risk items
        if risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            priorities.append("Address high-risk items first through prototypes")

        # Feasibility concerns
        if not feasibility.is_feasible:
            priorities.append("Revise project scope to improve feasibility")

        # MVP focus
        focus = preferences.get('focus', 'mvp')
        if focus == 'mvp':
            priorities.append("Prioritize core user journey and defer nice-to-haves")

        # Regulatory requirements
        regulations = preferences.get('regulatory', [])
        if regulations and 'none' not in regulations:
            priorities.append("Build compliance requirements into architecture from day 1")

        # Team learning
        expertise = preferences.get('team_expertise', 'intermediate')
        if expertise == 'learning':
            priorities.append("Allocate 20-30% time for learning and experimentation")

        # Quick wins
        timeline = preferences.get('timeline', '6-months')
        if timeline == '3-months':
            priorities.append("Focus on quick wins to build momentum")

        return priorities or ["Execute according to standard development practices"]

    def _identify_success_factors(self, preferences: Dict[str, Any]) -> List[str]:
        """Identify critical success factors."""
        factors = []

        # Team factors
        distribution = preferences.get('team_distribution', 'colocated')
        if distribution in ['remote-sync', 'remote-async']:
            factors.append("Strong async communication and documentation practices")

        methodology = preferences.get('dev_methodology', 'agile')
        if methodology == 'agile':
            factors.append("Regular sprint reviews and stakeholder feedback")

        # Technical factors
        tech_challenges = preferences.get('technical_challenges', [])
        if 'realtime-data' in tech_challenges:
            factors.append("Robust data pipeline monitoring and alerting")

        if 'ml-ai' in tech_challenges:
            factors.append("Clear model performance metrics and validation")

        # Business factors
        success_metric = preferences.get('success_metric', 'adoption')
        metric_factors = {
            'adoption': "User onboarding optimization and activation metrics",
            'revenue': "Clear monetization strategy and pricing validation",
            'cost-saving': "Detailed cost tracking and efficiency metrics",
            'speed': "Performance benchmarking and optimization",
            'performance': "SLA definition and monitoring",
            'satisfaction': "Regular user feedback collection and NPS tracking",
            'innovation': "Market differentiation and unique value proposition"
        }
        if success_metric in metric_factors:
            factors.append(metric_factors[success_metric])

        # Market factors
        industry = preferences.get('industry', 'b2b-saas')
        if industry == 'b2b-saas':
            factors.append("Enterprise-grade security and reliability")
        elif industry == 'b2c-mobile':
            factors.append("Exceptional user experience and app store optimization")

        return factors or ["Clear requirements and consistent execution"]

    def _identify_warning_flags(
        self,
        preferences: Dict[str, Any],
        risk: RiskAssessment,
        feasibility: FeasibilityAnalysis,
        resources: ResourceAlignment
    ) -> List[str]:
        """Identify warning flags that need attention."""
        warnings = []

        # Critical risk
        if risk.level == RiskLevel.CRITICAL:
            warnings.append("⚠️ CRITICAL RISK: Project has multiple high-risk factors")

        # Feasibility issues
        if not feasibility.is_feasible:
            warnings.append("⚠️ FEASIBILITY CONCERN: Project may not be achievable with current constraints")

        # Resource misalignment
        if resources.budget_alignment < 0.5:
            warnings.append("⚠️ BUDGET WARNING: Significant funding gap identified")

        if resources.team_alignment < 0.5:
            warnings.append("⚠️ TEAM WARNING: Team size insufficient for project scope")

        if resources.timeline_alignment < 0.5:
            warnings.append("⚠️ TIMELINE WARNING: Schedule is likely unrealistic")

        # Specific combinations
        budget = preferences.get('budget_range', 'undefined')
        tech_challenges = preferences.get('technical_challenges', [])

        if budget == 'bootstrap' and 'ml-ai' in tech_challenges:
            warnings.append("⚠️ ML on bootstrap budget requires careful cloud cost management")

        team_size = preferences.get('team_size', '2-3')
        if team_size == '1' and 'microservices' in tech_challenges:
            warnings.append("⚠️ Microservices architecture not recommended for solo developers")

        return warnings

    def _calculate_complexity_score(self, preferences: Dict[str, Any]) -> float:
        """Calculate overall complexity score (0.0 to 1.0)."""
        score = 0.0

        # Base complexity
        complexity = preferences.get('complexity', 'moderate')
        base_scores = {'simple': 0.2, 'moderate': 0.5, 'complex': 0.8}
        score += base_scores.get(complexity, 0.5) * 0.3

        # Technical challenges
        challenges = preferences.get('technical_challenges', [])
        score += min(len(challenges) * 0.05, 0.3)

        # Regulations
        regulations = preferences.get('regulatory', [])
        if regulations and 'none' not in regulations:
            score += min(len(regulations) * 0.05, 0.2)

        # Integrations
        integration_count = 0
        for key in ['payment_integrations', 'communication_integrations', 'business_integrations',
                   'developer_integrations', 'data_integrations']:
            items = preferences.get(key, [])
            if items and 'none' not in items:
                integration_count += len(items)
        score += min(integration_count * 0.02, 0.2)

        return min(score, 1.0)

    def _estimate_actual_timeline(self, preferences: Dict[str, Any], complexity_score: float) -> str:
        """Estimate realistic timeline based on all factors."""
        timeline = preferences.get('timeline', '6-months')
        team_size = preferences.get('team_size', '2-3')
        expertise = preferences.get('team_expertise', 'intermediate')

        # Base timeline in months
        base_months = {'3-months': 3, '6-months': 6, '12-months': 12}.get(timeline, 6)

        # Complexity multiplier
        complexity_multiplier = 1.0 + complexity_score

        # Team size factor
        team_factors = {'1': 2.0, '2-3': 1.0, '4-8': 0.8, '8+': 0.7}
        team_factor = team_factors.get(team_size, 1.0)

        # Expertise factor
        expertise_factors = {'learning': 1.5, 'intermediate': 1.0, 'expert': 0.8, 'mixed': 1.1}
        expertise_factor = expertise_factors.get(expertise, 1.0)

        # Calculate
        actual_months = base_months * complexity_multiplier * team_factor * expertise_factor

        if actual_months <= 3:
            return "3 months"
        elif actual_months <= 6:
            return "4-6 months"
        elif actual_months <= 9:
            return "6-9 months"
        elif actual_months <= 12:
            return "9-12 months"
        elif actual_months <= 18:
            return "12-18 months"
        else:
            return "18+ months"

    def _recommend_team_size(self, preferences: Dict[str, Any], complexity: TechnicalComplexity) -> str:
        """Recommend optimal team size based on complexity."""
        current_team = preferences.get('team_size', '2-3')

        if complexity.score == ComplexityScore.SIMPLE:
            return "1-2 developers"
        elif complexity.score == ComplexityScore.MODERATE:
            return "2-4 developers"
        elif complexity.score == ComplexityScore.COMPLEX:
            return "4-8 developers + 1-2 DevOps"
        else:  # VERY_COMPLEX
            return "8-12 developers + 2-3 DevOps + 1-2 architects"

    def _estimate_minimum_budget(self, preferences: Dict[str, Any], complexity: TechnicalComplexity) -> str:
        """Estimate minimum budget based on requirements."""
        # Base costs
        team_size = preferences.get('team_size', '2-3')
        timeline = preferences.get('timeline', '6-months')

        # Average developer costs (rough estimates)
        dev_monthly_cost = 10000  # $10k/month per developer

        # Team size to number
        team_numbers = {'1': 1, '2-3': 2.5, '4-8': 6, '8+': 10}
        team_count = team_numbers.get(team_size, 2.5)

        # Timeline to months
        timeline_months = {'3-months': 3, '6-months': 6, '12-months': 12}.get(timeline, 6)

        # Calculate base cost
        base_cost = dev_monthly_cost * team_count * timeline_months

        # Add infrastructure costs
        infra_budget = preferences.get('infra_budget', 'moderate')
        infra_costs = {
            'minimal': 100 * timeline_months,
            'moderate': 500 * timeline_months,
            'substantial': 5000 * timeline_months,
            'unlimited': 20000 * timeline_months
        }
        infra_cost = infra_costs.get(infra_budget, 500 * timeline_months)

        # Add services costs
        services_budget = preferences.get('services_budget', 'basic')
        service_costs = {
            'free': 0,
            'basic': 200 * timeline_months,
            'professional': 2000 * timeline_months,
            'enterprise': 10000 * timeline_months
        }
        service_cost = service_costs.get(services_budget, 200 * timeline_months)

        # Complexity multiplier
        complexity_multipliers = {
            ComplexityScore.SIMPLE: 1.0,
            ComplexityScore.MODERATE: 1.2,
            ComplexityScore.COMPLEX: 1.5,
            ComplexityScore.VERY_COMPLEX: 2.0
        }
        multiplier = complexity_multipliers.get(complexity.score, 1.2)

        total_cost = (base_cost + infra_cost + service_cost) * multiplier

        if total_cost < 10000:
            return "$5-10k"
        elif total_cost < 50000:
            return f"${int(total_cost/1000)}k"
        elif total_cost < 100000:
            return f"${int(total_cost/5000)*5}k"
        elif total_cost < 1000000:
            return f"${int(total_cost/50000)*50}k"
        else:
            return f"${total_cost/1000000:.1f}M"

    def _identify_critical_skills(self, preferences: Dict[str, Any]) -> List[str]:
        """Identify critical skills needed for the project."""
        skills = []

        # Technical challenge skills
        tech_challenges = preferences.get('technical_challenges', [])
        challenge_skills = {
            'realtime-data': "Real-time data streaming (Kafka, WebSockets)",
            'high-concurrency': "Concurrency and performance optimization",
            'complex-logic': "Domain modeling and business logic design",
            'integrations': "API design and integration patterns",
            'ml-ai': "Machine learning and data science",
            'blockchain': "Blockchain and smart contract development",
            'iot-hardware': "IoT protocols and embedded systems",
            'multi-tenant': "Multi-tenancy architecture and isolation",
            'offline-first': "Offline sync and conflict resolution",
            'data-migrations': "Database migration and ETL processes",
            'microservices': "Microservices and distributed systems",
            'graphql-apis': "GraphQL schema design and optimization"
        }

        for challenge in tech_challenges:
            if challenge in challenge_skills:
                skills.append(challenge_skills[challenge])

        # Deployment skills
        deployment = preferences.get('deployment_environment', 'cloud')
        deployment_skills = {
            'cloud': "Cloud architecture (AWS/GCP/Azure)",
            'serverless': "Serverless architecture and FaaS",
            'kubernetes': "Kubernetes and container orchestration",
            'traditional': "Linux administration and networking",
            'on-premise': "Enterprise deployment and security",
            'hybrid': "Hybrid cloud architecture",
            'edge': "Edge computing and IoT deployment"
        }

        if deployment in deployment_skills:
            skills.append(deployment_skills[deployment])

        # Regulatory skills
        regulations = preferences.get('regulatory', [])
        if regulations and 'none' not in regulations:
            skills.append("Compliance and security best practices")

        # Scale skills
        scaling = preferences.get('scaling_expectations', 'steady')
        if scaling in ['viral', 'daily-peaks']:
            skills.append("Auto-scaling and load balancing")

        return skills or ["Full-stack web development"]

    def generate_enhanced_context(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enhanced context for prompt templates.

        Returns a dictionary with all calculated values ready for template substitution.
        """
        insights = self.aggregate_preferences(preferences)

        return {
            # Original preferences
            **preferences,

            # Risk analysis
            'risk_level': insights.risk_assessment.level.value,
            'risk_factors': insights.risk_assessment.factors,
            'risk_mitigations': insights.risk_assessment.mitigations,
            'risk_score': insights.risk_assessment.score,

            # Feasibility
            'is_feasible': insights.feasibility.is_feasible,
            'feasibility_confidence': insights.feasibility.confidence,
            'feasibility_concerns': insights.feasibility.concerns,
            'feasibility_recommendations': insights.feasibility.recommendations,

            # Resource alignment
            'budget_alignment': insights.resource_alignment.budget_alignment,
            'team_alignment': insights.resource_alignment.team_alignment,
            'timeline_alignment': insights.resource_alignment.timeline_alignment,
            'resource_gaps': insights.resource_alignment.gaps,
            'resource_optimizations': insights.resource_alignment.optimizations,

            # Technical complexity
            'complexity_level': insights.technical_complexity.score.value,
            'primary_challenges': insights.technical_complexity.primary_challenges,
            'technical_dependencies': insights.technical_complexity.dependencies,
            'architectural_recommendations': insights.technical_complexity.architectural_recommendations,

            # Overall metrics
            'overall_complexity_score': insights.overall_complexity_score,
            'overall_risk_score': insights.overall_risk_score,
            'overall_feasibility_score': insights.overall_feasibility_score,

            # Recommendations
            'priority_recommendations': insights.priority_recommendations,
            'success_factors': insights.success_factors,
            'warning_flags': insights.warning_flags,

            # Calculated estimates
            'estimated_actual_timeline': insights.estimated_actual_timeline,
            'recommended_team_size': insights.recommended_team_size,
            'minimum_budget_estimate': insights.minimum_budget_estimate,
            'critical_skills_needed': insights.critical_skills_needed
        }