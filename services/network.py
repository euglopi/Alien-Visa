import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from models.network import (
    MentorProfile, ExpertReviewer, SuccessStory,
    ForumPost, ForumReply, MentorshipRequest, NetworkMatch
)
from models.resume import ParsedResume


class NetworkService:
    """Service for managing expert network, mentorship, and community features."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize data files if they don't exist
        self._init_data_files()

    def _init_data_files(self):
        """Initialize JSON data files for network data."""
        data_files = {
            "mentors.json": [],
            "experts.json": [],
            "stories.json": [],
            "forum_posts.json": [],
            "forum_replies.json": [],
            "mentorship_requests.json": []
        }

        for filename, default_data in data_files.items():
            file_path = self.data_dir / filename
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump(default_data, f, indent=2, default=str)

    def _load_data(self, filename: str) -> List[Dict]:
        """Load data from JSON file."""
        file_path = self.data_dir / filename
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_data(self, filename: str, data: List[Dict]):
        """Save data to JSON file."""
        file_path = self.data_dir / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def find_mentors(self, field: str, subfield: Optional[str] = None,
                    max_results: int = 5) -> List[NetworkMatch]:
        """Find relevant mentors for a given field."""
        mentors_data = self._load_data("mentors.json")
        mentors = [MentorProfile(**m) for m in mentors_data if m.get("is_active", True)]

        matches = []
        for mentor in mentors:
            score = self._calculate_mentor_match_score(mentor, field, subfield)
            if score > 0:
                matches.append(NetworkMatch(
                    type="mentor",
                    id=mentor.id,
                    name=mentor.name,
                    field=mentor.field,
                    relevance_score=score,
                    key_qualifications=[
                        f"{mentor.years_experience} years experience",
                        f"O-1 approved in {mentor.o1_approval_year}",
                        f"Specializes in: {', '.join(mentor.mentoring_topics[:2])}"
                    ],
                    availability=mentor.availability
                ))

        # Sort by relevance score and return top matches
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:max_results]

    def find_experts(self, field: str, subfield: Optional[str] = None,
                    max_results: int = 5) -> List[NetworkMatch]:
        """Find relevant expert reviewers for consultation letters."""
        experts_data = self._load_data("experts.json")
        experts = [ExpertReviewer(**e) for e in experts_data if e.get("is_active", True)]

        matches = []
        for expert in experts:
            score = self._calculate_expert_match_score(expert, field, subfield)
            if score > 0:
                matches.append(NetworkMatch(
                    type="expert",
                    id=expert.id,
                    name=expert.name,
                    field=expert.field,
                    relevance_score=score,
                    key_qualifications=[
                        expert.credentials,
                        f"{expert.years_experience} years experience",
                        f"Fee range: {expert.consultation_fee_range}",
                        f"Response time: {expert.response_time}"
                    ] + ([f"Rating: {expert.rating}/5 ({expert.review_count} reviews)"]
                         if expert.rating else []),
                    contact_info=expert.contact_info
                ))

        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:max_results]

    def _calculate_mentor_match_score(self, mentor: MentorProfile,
                                    field: str, subfield: Optional[str]) -> float:
        """Calculate how well a mentor matches the requested field."""
        score = 0.0

        # Field match
        if mentor.field.lower() == field.lower():
            score += 0.6
        elif field.lower() in mentor.field.lower() or mentor.field.lower() in field.lower():
            score += 0.3

        # Subfield match
        if subfield and mentor.subfield:
            if mentor.subfield.lower() == subfield.lower():
                score += 0.3
            elif subfield.lower() in mentor.subfield.lower():
                score += 0.2

        # Availability bonus
        if mentor.availability == "high":
            score += 0.1
        elif mentor.availability == "medium":
            score += 0.05

        return min(score, 1.0)

    def _calculate_expert_match_score(self, expert: ExpertReviewer,
                                    field: str, subfield: Optional[str]) -> float:
        """Calculate how well an expert matches the requested field."""
        score = 0.0

        # Field match
        if expert.field.lower() == field.lower():
            score += 0.5
        elif field.lower() in expert.field.lower() or expert.field.lower() in field.lower():
            score += 0.25

        # Subfield match
        if subfield and expert.subfield:
            if expert.subfield.lower() == subfield.lower():
                score += 0.3
            elif subfield.lower() in expert.subfield.lower():
                score += 0.15

        # Experience bonus
        if expert.years_experience > 20:
            score += 0.1
        elif expert.years_experience > 10:
            score += 0.05

        # Rating bonus
        if expert.rating and expert.rating >= 4.5:
            score += 0.1
        elif expert.rating and expert.rating >= 4.0:
            score += 0.05

        return min(score, 1.0)

    def get_success_stories(self, field: Optional[str] = None,
                           min_score: int = 0, limit: int = 10) -> List[SuccessStory]:
        """Get relevant success stories."""
        stories_data = self._load_data("stories.json")
        stories = [SuccessStory(**s) for s in stories_data]

        # Filter by field and minimum score
        filtered = [
            s for s in stories
            if (not field or s.field.lower() == field.lower()) and s.assessment_score >= min_score
        ]

        # Sort by helpful votes and recency
        filtered.sort(key=lambda x: (x.helpful_votes, x.created_at), reverse=True)
        return filtered[:limit]

    def get_forum_posts(self, field: Optional[str] = None,
                       tag: Optional[str] = None, limit: int = 20) -> List[ForumPost]:
        """Get forum posts, optionally filtered by field or tag."""
        posts_data = self._load_data("forum_posts.json")
        posts = [ForumPost(**p) for p in posts_data]

        filtered = posts
        if field:
            filtered = [p for p in filtered if p.field.lower() == field.lower()]
        if tag:
            filtered = [p for p in filtered if tag in p.tags]

        filtered.sort(key=lambda x: x.created_at, reverse=True)
        return filtered[:limit]

    def add_success_story(self, story: SuccessStory):
        """Add a new success story."""
        stories_data = self._load_data("stories.json")
        stories_data.append(story.model_dump())
        self._save_data("stories.json", stories_data)

    def add_forum_post(self, post: ForumPost):
        """Add a new forum post."""
        posts_data = self._load_data("forum_posts.json")
        posts_data.append(post.model_dump())
        self._save_data("forum_posts.json", posts_data)

    def add_forum_reply(self, reply: ForumReply):
        """Add a reply to a forum post."""
        replies_data = self._load_data("forum_replies.json")
        replies_data.append(reply.model_dump())
        self._save_data("forum_replies.json", replies_data)

    def request_mentorship(self, request: MentorshipRequest):
        """Submit a mentorship request."""
        requests_data = self._load_data("mentorship_requests.json")
        requests_data.append(request.model_dump())
        self._save_data("mentorship_requests.json", requests_data)

    # Sample data seeding methods (for development)
    def seed_sample_data(self):
        """Add sample mentors, experts, and stories for testing."""
        # Sample mentors
        mentors = [
            MentorProfile(
                id="mentor_001",
                name="Dr. Sarah Chen",
                field="Computer Science",
                subfield="AI/ML",
                years_experience=15,
                o1_approval_year=2020,
                location="San Francisco, CA",
                languages=["English", "Mandarin"],
                availability="high",
                mentoring_topics=["O-1 application process", "Building extraordinary ability evidence", "Consultation letters"],
                created_at=datetime.now()
            ),
            MentorProfile(
                id="mentor_002",
                name="Prof. Michael Rodriguez",
                field="Medicine",
                subfield="Neurosurgery",
                years_experience=20,
                o1_approval_year=2019,
                location="Boston, MA",
                languages=["English", "Spanish"],
                availability="medium",
                mentoring_topics=["Medical research", "Surgical innovation", "Academic publishing"],
                created_at=datetime.now()
            )
        ]

        # Sample experts
        experts = [
            ExpertReviewer(
                id="expert_001",
                name="Dr. Emily Watson",
                credentials="Professor of Artificial Intelligence, MIT",
                field="Computer Science",
                subfield="AI/ML",
                institution="MIT",
                position="Full Professor",
                publications=150,
                years_experience=18,
                consultation_fee_range="$800-1500",
                response_time="1-2 weeks",
                contact_info="Available through platform messaging",
                verified=True,
                rating=4.8,
                review_count=24,
                created_at=datetime.now()
            )
        ]

        # Sample success stories
        stories = [
            SuccessStory(
                id="story_001",
                field="Computer Science",
                subfield="AI/ML",
                approval_timeline="10 months",
                key_success_factors=["Published 12 papers in top conferences", "Received 2 prestigious awards", "Consultation letter from Turing Award winner"],
                challenges_overcome=["Initial rejection due to insufficient evidence", "Difficulty finding qualified expert reviewers"],
                advice_for_others="Start building your publication record early. Focus on high-impact conferences and journals. Network extensively to get strong consultation letters.",
                criteria_met=["Awards", "Published Material", "Original Contributions", "Scholarly Articles", "High Salary"],
                assessment_score=7,
                approval_year=2023,
                created_at=datetime.now(),
                helpful_votes=45
            )
        ]

        # Save sample data
        self._save_data("mentors.json", [m.model_dump() for m in mentors])
        self._save_data("experts.json", [e.model_dump() for e in experts])
        self._save_data("stories.json", [s.model_dump() for s in stories])

        print("Sample network data seeded successfully!")
