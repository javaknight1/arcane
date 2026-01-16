# 💡 Idea File Guide: Crafting the Perfect Project Brief

## Overview

The idea file is the foundation of your roadmap generation. The more detailed and structured your idea, the more accurate, actionable, and valuable your roadmap will be. This guide helps you create an idea file that maximizes Arcane's AI capabilities.

## 🎯 Roadmap Scope: Technical vs. Comprehensive

By default, Arcane generates **technical-focused roadmaps** covering implementation, architecture, and development. However, you can expand your roadmap to include **non-technical aspects** for a holistic project plan:

### Available Non-Technical Aspects:
- **Business Strategy & Planning**: Market research, competitive analysis, business model validation
- **Marketing & Sales**: Brand development, customer acquisition, sales funnel optimization
- **Legal & Compliance**: Terms of service, privacy policies, regulatory compliance
- **Operations**: Process design, workflow automation, vendor management
- **Customer Support**: Help desk setup, documentation, support workflows
- **Finance & Accounting**: Financial systems, revenue tracking, budgeting
- **HR & Team Building**: Hiring plans, onboarding, performance management
- **Product Management**: User research, feature prioritization, analytics
- **Quality Assurance**: QA processes, testing frameworks, quality metrics
- **Risk Management**: Risk assessment, business continuity, crisis management

💡 **Pro Tip**: Use `--roadmap-aspects` flag to include these aspects, or let the interactive mode guide you through the selection.

## The Mindset: Think Like a Project Manager

When writing your idea file, adopt the mindset of a project manager presenting a comprehensive brief to a development team. You want to provide enough context and detail that someone with no prior knowledge could understand:

- **What** you're building
- **Why** it's needed
- **Who** will use it
- **How** it should work
- **When** you need it delivered
- **What constraints** exist

## Bare Minimum Requirements

Your idea file **must** include these essential elements:

### 1. Project Overview (Required)
- **Project name** and brief description
- **Primary purpose** - what problem does this solve?
- **Target audience** - who will use this?
- **Core functionality** - what are the main features?

### 2. Technical Context (Required)
- **Platform/technology preferences** (web, mobile, desktop, etc.)
- **Integration requirements** (APIs, databases, third-party services)
- **Performance expectations** (user load, response times, etc.)
- **Security considerations** (data sensitivity, compliance needs)

### 3. Scope Boundaries (Required)
- **What's included** in this project
- **What's explicitly excluded** (future phases)
- **Success criteria** - how do you measure completion?

### 4. Constraints (Required)
- **Timeline expectations** (launch date, milestones) - *Note: Arcane supports timelines from 3 months to multi-year projects (36+ months)*
- **Budget considerations** (if relevant to technical decisions)
- **Resource limitations** (team size, skill sets available) - *Note: Arcane supports teams from solo developers to enterprise teams (100+ members)*
- **Technical constraints** (existing systems, legacy requirements)

## 📋 Roadmap Scope Considerations

### If Including Non-Technical Aspects
When you plan to include non-technical aspects in your roadmap (business, marketing, legal, etc.), provide additional context in your idea file:

**For Business Strategy & Marketing:**
- Target market analysis and customer personas
- Competitive landscape and differentiation
- Business model and revenue strategy
- Go-to-market approach and marketing channels

**For Legal & Compliance:**
- Industry regulations and compliance requirements
- Data privacy and security considerations
- Intellectual property and legal entity needs

**For Operations & Support:**
- Business process requirements
- Customer service approach and SLAs
- Vendor and partner relationships
- Operational scalability needs

**For HR & Finance:**
- Team scaling plans and organizational structure
- Financial projections and funding status
- Compensation and equity considerations

## Optimal Information Structure

### Project Vision Section
```
# Project Name: [Your Project]

## Vision Statement
A clear, compelling 2-3 sentence description of what you're building and why it matters.

## Problem Statement
- What specific problem are you solving?
- Who experiences this problem?
- How are they currently handling it (if at all)?
- What makes this problem worth solving now?
```

### Target Audience Section
```
## Primary Users
- Demographics and characteristics
- Technical skill level
- Usage patterns and context
- Pain points and motivations

## Secondary Users
- Other stakeholders who interact with the system
- Administrative users
- Integration partners
```

### Functional Requirements Section
```
## Core Features (Must-Have)
List the essential features without which the project fails:
- Feature 1: Detailed description and user value
- Feature 2: Detailed description and user value
- Feature 3: Detailed description and user value

## Secondary Features (Should-Have)
Features that significantly enhance value but aren't critical for launch:
- Feature A: Description and rationale
- Feature B: Description and rationale

## Future Features (Could-Have)
Features for potential future phases:
- Future enhancement ideas
- Long-term vision elements
```

### Technical Specifications Section
```
## Technology Stack Preferences
- Frontend: [Specific frameworks, languages, or preferences]
- Backend: [API architecture, databases, server preferences]
- Infrastructure: [Cloud providers, deployment preferences]
- Third-party integrations: [Required external services]

## Performance Requirements
- Expected user load: [concurrent users, transactions per second]
- Response time expectations: [page loads, API responses]
- Availability requirements: [uptime expectations]
- Scalability needs: [growth projections]

## Security & Compliance
- Data sensitivity levels
- Required compliance standards (GDPR, HIPAA, etc.)
- Authentication/authorization needs
- Data encryption requirements
```

### Project Constraints Section
```
## Timeline
- Project start date
- Key milestones and deadlines
- Launch date requirements
- Dependencies on external factors

## Resources
- Team size and composition
- Available skill sets
- Budget constraints affecting technical decisions
- Third-party service budgets

## Technical Constraints
- Existing systems that must be integrated
- Legacy technology that must be supported
- Platform limitations
- Performance/infrastructure constraints
```

## Advanced Tips for Maximum Impact

### 1. Use Specific Examples
Instead of: "User management system"
Write: "User registration with email verification, role-based access control (admin, editor, viewer), and OAuth integration with Google/Microsoft for enterprise users"

### 2. Include User Stories
```
As a [user type], I want to [action] so that [benefit].

Example:
As a project manager, I want to assign tasks with due dates and priority levels so that I can track team workload and ensure deadlines are met.
```

### 3. Define Success Metrics
```
## Success Criteria
- User adoption: 100 active users within 3 months
- Performance: 95% of pages load under 2 seconds
- Reliability: 99.5% uptime
- User satisfaction: 4.5+ star rating in feedback
```

### 4. Address Edge Cases
Think about unusual scenarios:
- What happens when systems are down?
- How do you handle high traffic spikes?
- What if integrations fail?
- How do you manage data corruption/loss?

### 5. Provide Context and Rationale
Don't just list features—explain why they're important:
- Business justification
- User research insights
- Competitive advantages
- Technical reasoning

## Common Mistakes to Avoid

❌ **Being too vague**: "Build a social media app"
✅ **Being specific**: "Build a professional networking platform for remote workers with video chat integration and skill-based matching"

❌ **Technology-first thinking**: "Use React and Node.js to build something"
✅ **Problem-first thinking**: "Solve inventory management pain points, considering React/Node.js if they fit the requirements"

❌ **Missing constraints**: Ignoring timeline, budget, or technical limitations
✅ **Realistic boundaries**: Acknowledging what's possible within your constraints

❌ **Feature laundry list**: 50 features with no prioritization
✅ **Prioritized features**: Clear must-have vs nice-to-have distinctions

## Quality Checklist

Before submitting your idea file, ensure:

- [ ] A technical stranger could understand what you're building
- [ ] You've explained **why** each major feature is needed
- [ ] Technical constraints and preferences are clearly stated
- [ ] Timeline and resource constraints are realistic and explicit (consider: 3 months to 36+ months)
- [ ] Team size and structure are clearly defined (consider: 1 to 100+ members)
- [ ] Success criteria are measurable and specific
- [ ] You've prioritized features into must-have, should-have, could-have
- [ ] Integration requirements are detailed
- [ ] Security and compliance needs are addressed
- [ ] You've included specific examples rather than generic terms
- [ ] The scope is clearly bounded (what's in, what's out)
- [ ] Non-technical aspects are identified if comprehensive roadmap is desired

## Example Idea File Structure

```markdown
# E-Commerce Platform for Local Artisans

## Vision Statement
Create a marketplace platform that connects local artisans with customers, featuring integrated payment processing, inventory management, and social features to build community around handmade goods.

## Problem Statement
Local artisans struggle to reach customers beyond their immediate geographic area. Existing platforms like Etsy charge high fees and don't provide adequate local discovery features. Small crafters need an affordable way to showcase and sell their work while building authentic customer relationships.

## Target Audience
### Primary Users: Local Artisans
- Demographics: 25-55 years old, primarily women, small business owners
- Technical skill: Basic to intermediate computer skills
- Pain points: High platform fees, poor local visibility, complex setup processes

### Secondary Users: Local Customers
- Demographics: 30-65 years old, values handmade/local products
- Behavior: Prefers supporting local businesses, active on social media
- Needs: Easy discovery, secure purchasing, connection with makers

[Continue with detailed functional requirements, technical specs, etc.]
```

## Getting Help

If you're unsure about any aspect of your idea file:

1. **Start with the bare minimum** requirements listed above
2. **Iterate and refine** based on initial roadmap results
3. **Use the interactive mode** in Arcane to get guidance on missing elements
4. **Review successful examples** in the `/examples` directory
5. **Consider consulting** with domain experts for complex technical requirements

Remember: A well-crafted idea file is an investment in your project's success. The time spent creating comprehensive requirements will save countless hours during development and result in a product that truly meets your needs.