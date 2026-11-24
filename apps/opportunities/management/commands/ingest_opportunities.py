import csv
import os
import random
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.opportunities.models import Opportunity, OpportunityEmbedding
from apps.search.vector_service import VectorEmbeddingService


class Command(BaseCommand):
    help = "Ingest opportunities from CSV or generate 350+ realistic synthetic opportunities with vector embeddings."

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, help='Path to CSV file with opportunities')
        parser.add_argument('--count', type=int, default=350, help='Number of synthetic opportunities to generate')
        parser.add_argument('--clear', action='store_true', help='Clear existing opportunities before ingesting')

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write("Clearing existing opportunities...")
            Opportunity.objects.all().delete()

        csv_path = options.get('csv')
        if csv_path and os.path.exists(csv_path):
            self.stdout.write(f"Ingesting opportunities from CSV: {csv_path}")
            self.ingest_from_csv(csv_path)
        else:
            count = options.get('count', 350)
            self.stdout.write(f"Generating and ingesting {count} realistic sample opportunities...")
            self.generate_synthetic_opportunities(count)

    def ingest_from_csv(self, file_path: str):
        created_count = 0
        embeddings_to_create = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get('title', '').strip()
                company = row.get('company', '').strip()
                if not title or not company:
                    continue

                # Deduplication check
                if Opportunity.objects.filter(title=title, company=company).exists():
                    continue

                req_skills = [s.strip() for s in row.get('required_skills', '').split(',') if s.strip()]
                pref_skills = [s.strip() for s in row.get('preferred_skills', '').split(',') if s.strip()]

                opp = Opportunity.objects.create(
                    title=title,
                    company=company,
                    description=row.get('description', ''),
                    location=row.get('location', 'Remote'),
                    work_mode=row.get('work_mode', 'Remote'),
                    employment_type=row.get('employment_type', 'Internship'),
                    min_experience_months=int(row.get('min_experience_months', 0)),
                    max_experience_months=int(row.get('max_experience_months', 12)),
                    min_salary_or_stipend=float(row.get('min_salary_or_stipend', 15000)),
                    max_salary_or_stipend=float(row.get('max_salary_or_stipend', 35000)),
                    currency=row.get('currency', 'INR'),
                    is_unpaid=row.get('is_unpaid', 'false').lower() in ('true', '1'),
                    required_skills=req_skills,
                    preferred_skills=pref_skills,
                    apply_url=row.get('apply_url', 'https://matchforge.dev/apply'),
                    posted_date=datetime.now(timezone.utc),
                )
                
                # Generate embedding
                text_to_embed = f"{opp.title} {opp.company} {opp.description} {' '.join(opp.required_skills)}"
                emb_vec = VectorEmbeddingService.generate_embedding(text_to_embed)
                embeddings_to_create.append(
                    OpportunityEmbedding(
                        opportunity=opp,
                        embedding=emb_vec,
                        dimensions=len(emb_vec)
                    )
                )
                created_count += 1

        OpportunityEmbedding.objects.bulk_create(embeddings_to_create)
        self.stdout.write(self.style.SUCCESS(f"Successfully ingested {created_count} opportunities with embeddings."))

    def generate_synthetic_opportunities(self, count: int):
        companies = [
            ("Elip AI", "Pioneering intelligent agent workflows and enterprise search platforms."),
            ("NexusForge Systems", "High-throughput cloud architecture and distributed data processing."),
            ("Krypton Data Labs", "Real-time stream processing, Kafka pipelines and analytics engines."),
            ("Aura Cloud Labs", "Building scalable multi-tenant SaaS backends on AWS and Kubernetes."),
            ("ZetaCore Technologies", "Fintech scale-up processing millions of payment transactions daily."),
            ("Vortex AI Solutions", "Conversational AI, vector databases and LLM orchestration systems."),
            ("QuantSphere Analytics", "Algorithmic decision engines and quantitative modeling platforms."),
            ("Apex Infotech", "Enterprise microservices and API gateways built with Python and Go."),
            ("HyperScale Systems", "Distributed computing infrastructure and database acceleration."),
            ("Novus Logic", "E-commerce infrastructure powering thousands of direct-to-consumer brands."),
            ("PulseHealth Tech", "Healthtech platform delivering secure diagnostic and patient telemetry."),
            ("Beacon Mobility", "Smart logistics routing engines and IoT fleet management systems."),
            ("Starlight Interactive", "Collaborative canvas tools and real-time state synchronization."),
            ("Crestline Robotics", "Edge computing and automation backend services."),
            ("OmniStack Platforms", "Developer tooling, CLI utilities and modern deployment platforms.")
        ]

        roles_templates = [
            # Backend Roles
            {
                'title': 'Backend Developer Intern',
                'employment_type': 'Internship',
                'required': ['Python', 'Django', 'SQL'],
                'preferred': ['PostgreSQL', 'Redis', 'Docker'],
                'desc': 'Join our backend engineering pod to design REST APIs, optimize database queries, and build scalable web services with Django and PostgreSQL.'
            },
            {
                'title': 'Software Engineer Intern (Python / Django)',
                'employment_type': 'Internship',
                'required': ['Python', 'Django', 'REST APIs'],
                'preferred': ['Celery', 'Docker', 'Git'],
                'desc': 'Work alongside senior architects to develop resilient microservices, integrate background task queues with Celery, and build production web applications.'
            },
            {
                'title': 'AI / ML Engineer Intern',
                'employment_type': 'Internship',
                'required': ['Python', 'PyTorch', 'Scikit-Learn'],
                'preferred': ['RAG', 'Vector Search', 'Hugging Face'],
                'desc': 'Design and benchmark Retrieval-Augmented Generation (RAG) pipelines, semantic embeddings, and LLM agent function-calling workflows.'
            },
            {
                'title': 'Full Stack Developer Intern',
                'employment_type': 'Internship',
                'required': ['Python', 'JavaScript', 'Django'],
                'preferred': ['React', 'PostgreSQL', 'Tailwind CSS'],
                'desc': 'Build responsive user interfaces backed by performant Django REST APIs. Collaborate across design and engineering teams.'
            },
            {
                'title': 'Junior Backend Engineer',
                'employment_type': 'Full-time',
                'required': ['Python', 'Django', 'PostgreSQL', 'Redis'],
                'preferred': ['Docker', 'Kubernetes', 'Celery'],
                'desc': 'Full-time backend role responsible for database schema optimization, caching architectures, and continuous deployment workflows.'
            },
            {
                'title': 'Data Engineering Intern',
                'employment_type': 'Internship',
                'required': ['Python', 'SQL', 'PostgreSQL'],
                'preferred': ['Pandas', 'Kafka', 'Airflow'],
                'desc': 'Design automated ETL pipelines, data quality validation checks, and data warehouse ingestion jobs.'
            },
            {
                'title': 'Cloud & DevOps Intern',
                'employment_type': 'Internship',
                'required': ['Linux', 'Git', 'Docker'],
                'preferred': ['AWS', 'Kubernetes', 'CI/CD'],
                'desc': 'Automate deployment pipelines, maintain Docker container images, and monitor infrastructure metrics across production clusters.'
            },
            {
                'title': 'Frontend Developer Intern',
                'employment_type': 'Internship',
                'required': ['JavaScript', 'HTML', 'CSS'],
                'preferred': ['React', 'TypeScript', 'Bootstrap'],
                'desc': 'Craft elegant, accessible UI components and dashboards. Integrate client-side applications with RESTful backend endpoints.'
            },
        ]

        locations = ['Remote', 'Bangalore', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi-NCR', 'Gurgaon']
        work_modes = ['Remote', 'Hybrid', 'Onsite']

        random.seed(42)  # For reproducible generation
        created_opportunities = []
        embeddings_to_create = []

        self.stdout.write("Generating opportunity records in memory...")
        for i in range(count):
            comp_name, comp_mission = random.choice(companies)
            template = random.choice(roles_templates)
            loc = random.choice(locations)
            mode = 'Remote' if loc == 'Remote' else random.choice(work_modes)
            
            # About 7% are intentionally unpaid (for testing hard filter dealbreaker enforcement)
            is_unpaid = (i % 14 == 0)
            
            if is_unpaid:
                min_stipend = 0.0
                max_stipend = 0.0
            else:
                base = random.choice([20000, 25000, 30000, 35000, 45000, 60000])
                min_stipend = float(base)
                max_stipend = float(base + random.choice([5000, 10000, 15000]))

            min_exp = 0 if template['employment_type'] == 'Internship' else random.choice([6, 12, 18])
            max_exp = min_exp + 12

            desc = f"{comp_mission} {template['desc']} You will collaborate with our distributed team in {loc} ({mode} mode)."
            
            # Additional unique identifier in title if duplicates happen
            title = template['title']
            if i > 50:
                qualifier = random.choice(['(Core Team)', '(Platform)', '(Growth)', '(Foundations)', '(Infrastructure)', ''])
                if qualifier:
                    title = f"{title} {qualifier}".strip()

            opp = Opportunity(
                title=title,
                company=comp_name,
                description=desc,
                location=loc,
                work_mode=mode,
                employment_type=template['employment_type'],
                min_experience_months=min_exp,
                max_experience_months=max_exp,
                min_salary_or_stipend=min_stipend,
                max_salary_or_stipend=max_stipend,
                currency='INR',
                is_unpaid=is_unpaid,
                required_skills=template['required'],
                preferred_skills=template['preferred'],
                apply_url=f"https://matchforge.dev/apply/{i+1}",
                posted_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            )
            created_opportunities.append(opp)

        with transaction.atomic():
            Opportunity.objects.bulk_create(created_opportunities)
            
            # Fetch back with IDs to generate embeddings
            all_created = list(Opportunity.objects.all())
            self.stdout.write(f"Generating vector embeddings for {len(all_created)} opportunities...")
            
            for opp in all_created:
                text_to_embed = f"{opp.title} {opp.company} {opp.description} {' '.join(opp.required_skills)}"
                emb_vec = VectorEmbeddingService.generate_embedding(text_to_embed)
                embeddings_to_create.append(
                    OpportunityEmbedding(
                        opportunity=opp,
                        embedding=emb_vec,
                        dimensions=len(emb_vec)
                    )
                )
            
            OpportunityEmbedding.objects.bulk_create(embeddings_to_create)

        self.stdout.write(self.style.SUCCESS(f"Successfully generated and embedded {len(all_created)} opportunities!"))
