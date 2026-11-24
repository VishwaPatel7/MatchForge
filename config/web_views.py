from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.profiles.models import UserProfile
from apps.opportunities.models import Opportunity, SavedOpportunity
from apps.recommendations.models import Recommendation
from apps.preferences.models import UserPreference, PreferenceHistory
from apps.ai_agent.models import Conversation
from apps.resumes.models import CandidateResume
from apps.recommendations.services import HybridRecommendationEngine, SkillGapAnalyzer


def landing_page(request):
    """Public landing page showcasing MatchForge value proposition."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    total_jobs = Opportunity.objects.filter(is_active=True).count()
    return render(request, 'landing.html', {'total_jobs': total_jobs})


def register_page(request):
    """Candidate user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        u = request.POST.get('username')
        e = request.POST.get('email')
        p = request.POST.get('password')
        fn = request.POST.get('full_name', '')
        loc = request.POST.get('location', '')

        if not u or not p:
            messages.error(request, "Username and password are required.")
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=u).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=u, email=e, password=p)
        if fn:
            parts = fn.split(' ', 1)
            user.first_name = parts[0]
            if len(parts) > 1:
                user.last_name = parts[1]
            user.save()

        UserProfile.objects.create(user=user, current_location=loc)
        login(request, user)
        messages.success(request, f"Welcome to MatchForge, {user.username}!")
        return redirect('dashboard')

    return render(request, 'accounts/register.html')


def login_page(request):
    """User authentication."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html')


def logout_action(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    """Main candidate dashboard with key metrics and match summaries."""
    profile = request.user.profile
    total_indexed = Opportunity.objects.filter(is_active=True).count()
    saved_count = SavedOpportunity.objects.filter(profile=profile).count()

    recs = Recommendation.objects.filter(profile=profile, passed_hard_filters=True).select_related('opportunity')
    if not recs.exists() and total_indexed > 0:
        recs = HybridRecommendationEngine.generate_recommendations_for_user(profile, limit=15)

    matching_count = len(recs)
    avg_score = round(sum(float(r.overall_score) for r in recs) / max(1, matching_count), 1) if matching_count else 0.0

    recent_prefs = UserPreference.objects.filter(profile=profile).order_by('-updated_at')[:5]
    top_recs = recs[:6]
    skill_gaps = SkillGapAnalyzer.analyze_candidate_gaps(profile)

    context = {
        'profile': profile,
        'total_indexed': total_indexed,
        'matching_count': matching_count,
        'avg_score': avg_score,
        'saved_count': saved_count,
        'recent_preferences': recent_prefs,
        'top_recommendations': top_recs,
        'skill_gaps': skill_gaps,
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_view(request):
    """Profile editing and career goal configuration."""
    profile = request.user.profile
    if request.method == 'POST':
        profile.headline = request.POST.get('headline', '')
        profile.bio = request.POST.get('bio', '')
        profile.current_location = request.POST.get('current_location', '')
        profile.willing_to_relocate = request.POST.get('willing_to_relocate') == 'on'
        try:
            profile.experience_months = int(request.POST.get('experience_months', 0))
        except ValueError:
            pass
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    return render(request, 'dashboard/profile.html', {'profile': profile})


@login_required
def resume_upload_view(request):
    """Resume management and PDF parsing interface."""
    profile = request.user.profile
    resumes = CandidateResume.objects.filter(profile=profile).order_by('-created_at')
    active_resume = resumes.filter(is_active=True).first()
    return render(request, 'dashboard/resume.html', {
        'profile': profile,
        'resumes': resumes,
        'active_resume': active_resume
    })


@login_required
def chat_agent_view(request):
    """Conversational AI Agent interface."""
    profile = request.user.profile
    conversations = Conversation.objects.filter(profile=profile).order_by('-last_activity')
    active_conv = conversations.first()
    if not active_conv:
        active_conv = Conversation.objects.create(profile=profile, title="Opportunity Discovery")

    return render(request, 'dashboard/chat.html', {
        'profile': profile,
        'conversations': conversations,
        'active_conversation': active_conv
    })


@login_required
def opportunities_discovery_view(request):
    """Browse and filter all opportunities."""
    return render(request, 'dashboard/opportunities.html', {'profile': request.user.profile})


@login_required
def recommendations_view(request):
    """Ranked recommendations with match percentage and dealbreaker status."""
    profile = request.user.profile
    recs = Recommendation.objects.filter(profile=profile).select_related('opportunity', 'explanation')
    if not recs.exists():
        recs = HybridRecommendationEngine.generate_recommendations_for_user(profile, limit=20)

    return render(request, 'dashboard/recommendations.html', {
        'profile': profile,
        'recommendations': recs
    })


@login_required
def opportunity_detail_view(request, id):
    """Detailed view of a single opportunity with match explanation."""
    profile = request.user.profile
    opportunity = get_object_or_404(Opportunity, id=id)
    rec = Recommendation.objects.filter(profile=profile, opportunity=opportunity).first()
    is_saved = SavedOpportunity.objects.filter(profile=profile, opportunity=opportunity).exists()

    return render(request, 'dashboard/opportunity_detail.html', {
        'profile': profile,
        'opportunity': opportunity,
        'recommendation': rec,
        'is_saved': is_saved
    })


@login_required
def compare_view(request):
    """Side-by-side comparison of opportunities."""
    return render(request, 'dashboard/compare.html', {'profile': request.user.profile})


@login_required
def skill_gaps_view(request):
    """Market skill gap analysis dashboard."""
    profile = request.user.profile
    gaps = SkillGapAnalyzer.analyze_candidate_gaps(profile)
    return render(request, 'dashboard/skill_gaps.html', {
        'profile': profile,
        'gaps': gaps
    })


@login_required
def saved_opportunities_view(request):
    """Saved / bookmarked opportunities."""
    profile = request.user.profile
    saved = SavedOpportunity.objects.filter(profile=profile).select_related('opportunity')
    return render(request, 'dashboard/saved.html', {
        'profile': profile,
        'saved_list': saved
    })


@login_required
def preferences_management_view(request):
    """Explicit preference management and version history view."""
    profile = request.user.profile
    prefs = UserPreference.objects.filter(profile=profile).order_by('-priority_level')
    history = PreferenceHistory.objects.filter(preference__profile=profile).order_by('-changed_at')[:20]

    return render(request, 'dashboard/preferences.html', {
        'profile': profile,
        'preferences': prefs,
        'history': history
    })


@login_required
def evaluations_dashboard_view(request):
    """AI Evaluation benchmark report dashboard."""
    return render(request, 'dashboard/evaluations.html', {'profile': request.user.profile})
