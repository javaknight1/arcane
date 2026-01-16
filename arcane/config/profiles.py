"""Predefined project profiles for common use cases."""

from typing import Dict, Any, List


class ProjectProfiles:
    """Predefined project profiles for common scenarios."""

    PROFILES = {
        'mvp-startup': {
            'name': 'MVP Startup',
            'description': 'Solo founder or small team building an MVP with limited budget',
            'preferences': {
                'timeline': '3-months',
                'focus': 'mvp',
                'team_size': '1',
                'complexity': 'simple',
                'industry': 'b2b-saas',
                'regulatory': ['none'],
                'market_maturity': 'greenfield',
                'target_market': 'national',
                'technical_challenges': ['integrations'],
                'team_expertise': 'intermediate',
                'team_distribution': 'colocated',
                'dev_methodology': 'agile',
                'budget_range': 'bootstrap',
                'infra_budget': 'minimal',
                'services_budget': 'free',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'single-region',
                'scaling_expectations': 'steady',
                'payment_integrations': ['stripe'],
                'communication_integrations': ['email'],
                'business_integrations': ['none'],
                'developer_integrations': ['github-gitlab', 'ci-cd'],
                'data_integrations': ['rest-apis', 'databases'],
                'success_metric': 'adoption',
                'success_timeline': 'short',
                'measurement_approach': 'quantitative',
                'failure_tolerance': 'moderate',
                'roadmap_aspects': ['business-strategy', 'marketing-sales']
            }
        },

        'enterprise-migration': {
            'name': 'Enterprise Migration',
            'description': 'Large team migrating legacy systems to modern architecture',
            'preferences': {
                'timeline': '18-months',
                'focus': 'migration',
                'team_size': '12',
                'complexity': 'complex',
                'industry': 'enterprise',
                'regulatory': ['soc2', 'iso27001'],
                'market_maturity': 'established',
                'target_market': 'global',
                'technical_challenges': ['data-migrations', 'complex-logic', 'integrations', 'multi-tenant'],
                'team_expertise': 'expert',
                'team_distribution': 'hybrid',
                'dev_methodology': 'agile',
                'budget_range': 'enterprise',
                'infra_budget': 'substantial',
                'services_budget': 'enterprise',
                'deployment_environment': 'hybrid',
                'geographic_distribution': 'multi-region',
                'scaling_expectations': 'daily-peaks',
                'payment_integrations': ['none'],
                'communication_integrations': ['email', 'sms'],
                'business_integrations': ['crm', 'accounting', 'analytics'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking'],
                'data_integrations': ['rest-apis', 'databases', 'webhooks'],
                'success_metric': 'performance',
                'success_timeline': 'long',
                'measurement_approach': 'quantitative',
                'failure_tolerance': 'zero',
                'roadmap_aspects': ['operations', 'risk-management']
            }
        },

        'ai-startup': {
            'name': 'AI/ML Startup',
            'description': 'Small team building AI-powered product with modern tech stack',
            'preferences': {
                'timeline': '6-months',
                'focus': 'mvp',
                'team_size': '2-3',
                'complexity': 'complex',
                'industry': 'b2b-saas',
                'regulatory': ['gdpr', 'soc2'],
                'market_maturity': 'emerging',
                'target_market': 'global',
                'technical_challenges': ['ml-ai', 'realtime-data', 'high-concurrency', 'graphql-apis'],
                'team_expertise': 'expert',
                'team_distribution': 'remote-sync',
                'dev_methodology': 'agile',
                'budget_range': 'seed',
                'infra_budget': 'moderate',
                'services_budget': 'professional',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'multi-region',
                'scaling_expectations': 'viral',
                'payment_integrations': ['stripe'],
                'communication_integrations': ['email', 'push-notifications'],
                'business_integrations': ['analytics'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking', 'feature-flags'],
                'data_integrations': ['rest-apis', 'graphql-apis', 'websockets', 'databases'],
                'success_metric': 'adoption',
                'success_timeline': 'medium',
                'measurement_approach': 'mixed',
                'failure_tolerance': 'moderate',
                'roadmap_aspects': ['business-strategy', 'marketing-sales', 'product-management']
            }
        },

        'mobile-app': {
            'name': 'Mobile App',
            'description': 'Team building consumer mobile application',
            'preferences': {
                'timeline': '6-months',
                'focus': 'mvp',
                'team_size': '2-3',
                'complexity': 'moderate',
                'industry': 'b2c-mobile',
                'regulatory': ['gdpr'],
                'market_maturity': 'established',
                'target_market': 'global',
                'technical_challenges': ['offline-first', 'push-notifications', 'integrations'],
                'team_expertise': 'intermediate',
                'team_distribution': 'colocated',
                'dev_methodology': 'agile',
                'budget_range': 'seed',
                'infra_budget': 'moderate',
                'services_budget': 'basic',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'global',
                'scaling_expectations': 'viral',
                'payment_integrations': ['stripe', 'paypal'],
                'communication_integrations': ['push-notifications', 'email'],
                'business_integrations': ['analytics'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking'],
                'data_integrations': ['rest-apis', 'databases'],
                'success_metric': 'adoption',
                'success_timeline': 'short',
                'measurement_approach': 'mixed',
                'failure_tolerance': 'low',
                'roadmap_aspects': ['marketing-sales', 'product-management']
            }
        },

        'ecommerce': {
            'name': 'E-commerce Platform',
            'description': 'Building an online commerce platform',
            'preferences': {
                'timeline': '6-months',
                'focus': 'mvp',
                'team_size': '4-8',
                'complexity': 'moderate',
                'industry': 'ecommerce',
                'regulatory': ['pci-dss', 'gdpr'],
                'market_maturity': 'saturated',
                'target_market': 'national',
                'technical_challenges': ['high-concurrency', 'integrations', 'complex-logic'],
                'team_expertise': 'intermediate',
                'team_distribution': 'colocated',
                'dev_methodology': 'agile',
                'budget_range': 'funded',
                'infra_budget': 'moderate',
                'services_budget': 'professional',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'multi-region',
                'scaling_expectations': 'seasonal',
                'payment_integrations': ['stripe', 'paypal', 'square'],
                'communication_integrations': ['email', 'sms'],
                'business_integrations': ['accounting', 'analytics', 'marketing-automation'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring'],
                'data_integrations': ['rest-apis', 'webhooks', 'databases'],
                'success_metric': 'revenue',
                'success_timeline': 'medium',
                'measurement_approach': 'quantitative',
                'failure_tolerance': 'low',
                'roadmap_aspects': ['business-strategy', 'marketing-sales', 'operations', 'customer-support']
            }
        },

        'healthcare-app': {
            'name': 'Healthcare Application',
            'description': 'HIPAA-compliant healthcare platform',
            'preferences': {
                'timeline': '18-months',
                'focus': 'mvp',
                'team_size': '6',
                'complexity': 'complex',
                'industry': 'healthcare',
                'regulatory': ['hipaa', 'gdpr'],
                'market_maturity': 'established',
                'target_market': 'national',
                'technical_challenges': ['complex-logic', 'integrations', 'multi-tenant'],
                'team_expertise': 'expert',
                'team_distribution': 'hybrid',
                'dev_methodology': 'agile',
                'budget_range': 'funded',
                'infra_budget': 'substantial',
                'services_budget': 'professional',
                'deployment_environment': 'hybrid',
                'geographic_distribution': 'single-region',
                'scaling_expectations': 'steady',
                'payment_integrations': ['stripe'],
                'communication_integrations': ['email', 'sms', 'video-calls'],
                'business_integrations': ['crm', 'support'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking'],
                'data_integrations': ['rest-apis', 'databases', 'file-uploads'],
                'success_metric': 'satisfaction',
                'success_timeline': 'long',
                'measurement_approach': 'mixed',
                'failure_tolerance': 'zero',
                'roadmap_aspects': ['legal-compliance', 'operations', 'risk-management']
            }
        },

        'fintech': {
            'name': 'Fintech Platform',
            'description': 'Financial services platform with strict compliance',
            'preferences': {
                'timeline': '24-months',
                'focus': 'mvp',
                'team_size': '8',
                'complexity': 'complex',
                'industry': 'finance',
                'regulatory': ['pci-dss', 'soc2', 'iso27001'],
                'market_maturity': 'established',
                'target_market': 'national',
                'technical_challenges': ['realtime-data', 'high-concurrency', 'complex-logic', 'integrations'],
                'team_expertise': 'expert',
                'team_distribution': 'hybrid',
                'dev_methodology': 'agile',
                'budget_range': 'funded',
                'infra_budget': 'substantial',
                'services_budget': 'professional',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'multi-region',
                'scaling_expectations': 'daily-peaks',
                'payment_integrations': ['bank-transfers', 'stripe'],
                'communication_integrations': ['email', 'sms', 'push-notifications'],
                'business_integrations': ['accounting', 'analytics'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking'],
                'data_integrations': ['rest-apis', 'webhooks', 'databases'],
                'success_metric': 'revenue',
                'success_timeline': 'medium',
                'measurement_approach': 'quantitative',
                'failure_tolerance': 'zero',
                'roadmap_aspects': ['legal-compliance', 'risk-management', 'operations']
            }
        },

        'microservices': {
            'name': 'Microservices Platform',
            'description': 'Large-scale microservices architecture',
            'preferences': {
                'timeline': '24-months',
                'focus': 'feature',
                'team_size': '20',
                'complexity': 'complex',
                'industry': 'enterprise',
                'regulatory': ['soc2'],
                'market_maturity': 'established',
                'target_market': 'global',
                'technical_challenges': ['microservices', 'high-concurrency', 'realtime-data', 'graphql-apis'],
                'team_expertise': 'expert',
                'team_distribution': 'remote-async',
                'dev_methodology': 'agile',
                'budget_range': 'enterprise',
                'infra_budget': 'unlimited',
                'services_budget': 'enterprise',
                'deployment_environment': 'kubernetes',
                'geographic_distribution': 'global',
                'scaling_expectations': 'viral',
                'payment_integrations': ['none'],
                'communication_integrations': ['none'],
                'business_integrations': ['analytics', 'monitoring'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring', 'error-tracking', 'feature-flags'],
                'data_integrations': ['rest-apis', 'graphql-apis', 'webhooks', 'websockets', 'databases'],
                'success_metric': 'performance',
                'success_timeline': 'long',
                'measurement_approach': 'quantitative',
                'failure_tolerance': 'low',
                'roadmap_aspects': ['operations', 'risk-management']
            }
        },

        'blockchain': {
            'name': 'Blockchain/Web3',
            'description': 'Blockchain or Web3 application',
            'preferences': {
                'timeline': '6-months',
                'focus': 'mvp',
                'team_size': '2-3',
                'complexity': 'complex',
                'industry': 'finance',
                'regulatory': ['none'],
                'market_maturity': 'emerging',
                'target_market': 'global',
                'technical_challenges': ['blockchain', 'complex-logic', 'integrations'],
                'team_expertise': 'expert',
                'team_distribution': 'remote-async',
                'dev_methodology': 'agile',
                'budget_range': 'seed',
                'infra_budget': 'moderate',
                'services_budget': 'professional',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'global',
                'scaling_expectations': 'viral',
                'payment_integrations': ['cryptocurrency'],
                'communication_integrations': ['none'],
                'business_integrations': ['none'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring'],
                'data_integrations': ['rest-apis', 'websockets', 'databases'],
                'success_metric': 'adoption',
                'success_timeline': 'medium',
                'measurement_approach': 'quantitative',
                'failure_tolerance': 'high',
                'roadmap_aspects': ['legal-compliance', 'business-strategy', 'risk-management']
            }
        },

        'education-platform': {
            'name': 'Education Platform',
            'description': 'Online learning management system',
            'preferences': {
                'timeline': '6-months',
                'focus': 'mvp',
                'team_size': '2-3',
                'complexity': 'moderate',
                'industry': 'education',
                'regulatory': ['ferpa', 'gdpr'],
                'market_maturity': 'established',
                'target_market': 'national',
                'technical_challenges': ['integrations', 'video-calls', 'file-uploads'],
                'team_expertise': 'intermediate',
                'team_distribution': 'remote-sync',
                'dev_methodology': 'agile',
                'budget_range': 'seed',
                'infra_budget': 'moderate',
                'services_budget': 'basic',
                'deployment_environment': 'cloud',
                'geographic_distribution': 'single-region',
                'scaling_expectations': 'seasonal',
                'payment_integrations': ['stripe'],
                'communication_integrations': ['email', 'video-calls', 'in-app-chat'],
                'business_integrations': ['analytics'],
                'developer_integrations': ['github-gitlab', 'ci-cd', 'monitoring'],
                'data_integrations': ['rest-apis', 'file-uploads', 'databases'],
                'success_metric': 'satisfaction',
                'success_timeline': 'medium',
                'measurement_approach': 'mixed',
                'failure_tolerance': 'low',
                'roadmap_aspects': ['product-management', 'customer-support']
            }
        }
    }

    @classmethod
    def get_profile(cls, profile_name: str) -> Dict[str, Any]:
        """Get a specific profile by name."""
        profile = cls.PROFILES.get(profile_name)
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found. Available profiles: {', '.join(cls.get_profile_names())}")
        return profile['preferences']

    @classmethod
    def get_profile_names(cls) -> List[str]:
        """Get list of available profile names."""
        return list(cls.PROFILES.keys())

    @classmethod
    def get_profile_descriptions(cls) -> Dict[str, str]:
        """Get profile names with descriptions."""
        return {
            name: profile['description']
            for name, profile in cls.PROFILES.items()
        }

    @classmethod
    def display_profiles(cls) -> str:
        """Get formatted string of all profiles for display."""
        lines = ["Available profiles:"]
        for name, profile in cls.PROFILES.items():
            lines.append(f"  {name}: {profile['description']}")
        return "\n".join(lines)