#!/usr/bin/env python3
"""
Condensed Immigration Copilot - All functionality in one Python file
Supports CLI, Web, and O-1 specific modes
"""

import sys
import json
import os
import time
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

# Web framework imports (optional)
try:
    from flask import Flask, render_template, request, jsonify, session
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Rich CLI imports (optional)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# OpenAI imports (optional)
try:
    import openai
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

@dataclass
class UserProfile:
    name: Optional[str] = None
    country: Optional[str] = None
    status: str = "unknown"
    education: Optional[str] = None
    profession: Optional[str] = None
    goal: Optional[str] = None
    o1_field: Optional[str] = None
    recognition: List[str] = None
    has_experience: bool = False
    us_work_plans: bool = False

    def __post_init__(self):
        if self.recognition is None:
            self.recognition = []

@dataclass
class PathwayStep:
    id: int
    title: str
    description: str
    duration: str
    risks: List[str]
    decision_point: Optional[str] = None

class ImmigrationEngine:
    def __init__(self):
        self.sources = {"uscis": "https://www.uscis.gov", "state_dept": "https://travel.state.gov"}

    def assess_eligibility(self, profile: UserProfile) -> Dict[str, Dict]:
        pathways = {}
        if profile.profession and profile.education:
            pathways['h1b'] = self._assess_h1b(profile)
        if profile.recognition:
            pathways['o1'] = self._assess_o1(profile)
        pathways['employment_pr'] = self._assess_employment_pr(profile)
        return pathways

    def _assess_h1b(self, profile: UserProfile) -> Dict:
        return {
            'eligible': True,
            'confidence': 0.7,
            'requirements_met': ["Professional experience", "Education qualification"],
            'next_steps': ["Find employer sponsor", "Apply during April lottery"],
            'risks': ["Lottery system", "Employer dependency"],
            'sources': [self.sources['uscis']]
        }

    def _assess_o1(self, profile: UserProfile) -> Dict:
        score = calculate_o1_eligibility(profile)
        return {
            'eligible': score >= 60,
            'confidence': 0.8,
            'score': score,
            'level': get_eligibility_level(score),
            'requirements_met': get_met_criteria(profile),
            'next_steps': ["Gather extraordinary ability evidence", "Obtain consultation letters"],
            'risks': ["Subjective determination", "High evidentiary burden"],
            'sources': [self.sources['uscis']]
        }

    def _assess_employment_pr(self, profile: UserProfile) -> Dict:
        return {
            'eligible': True,
            'confidence': 0.6,
            'requirements_met': ["Work authorization"],
            'next_steps': ["PERM labor certification", "File I-485 adjustment"],
            'risks': ["Long processing times", "Visa backlogs"],
            'sources': [self.sources['uscis']]
        }

class QuestionEngine:
    def __init__(self):
        self.questions = {
            "country": "What country are you a citizen of?",
            "o1_field": "What field demonstrates your extraordinary ability? (science/arts/education/business/athletics/film_tv)",
            "education": "What's your educational background?",
            "recognition": "What evidence do you have of recognition? (awards/publications/media)",
            "profession": "What's your profession?",
            "goal": "What's your primary goal in the U.S.?"
        }

    def get_next_question(self, profile: UserProfile) -> Optional[str]:
        if not profile.country:
            return "country"
        if not profile.o1_field:
            return "o1_field"
        if not profile.education:
            return "education"
        if not profile.recognition:
            return "recognition"
        if not profile.profession:
            return "profession"
        if not profile.goal:
            return "goal"
        return None

def calculate_o1_eligibility(profile: UserProfile) -> int:
    score = 0
    if profile.o1_field: score += 20
    if profile.education in ['masters', 'phd']: score += 15
    score += len(profile.recognition) * 10
    if profile.has_experience: score += 15
    if profile.us_work_plans: score += 10
    return min(score, 100)

def get_eligibility_level(score: int) -> str:
    if score >= 80: return "Strong Candidate"
    elif score >= 60: return "Potential Candidate"
    elif score >= 40: return "Weak Candidate"
    else: return "Not Eligible"

def get_met_criteria(profile: UserProfile) -> List[str]:
    met = []
    if profile.o1_field: met.append(f"Extraordinary ability in {profile.o1_field}")
    if profile.education: met.append(f"Education: {profile.education}")
    met.extend([f"Recognition: {r}" for r in profile.recognition])
    if profile.has_experience: met.append("Professional experience")
    if profile.us_work_plans: met.append("U.S. work plans")
    return met

def create_immigration_index(profile: UserProfile) -> Dict:
    score = calculate_o1_eligibility(profile)
    return {
        "user_profile": {
            "title": "Your O-1 Profile",
            "items": [
                f"Country: {profile.country or 'Not specified'}",
                f"O-1 Field: {profile.o1_field or 'Not specified'}",
                f"Education: {profile.education or 'Not specified'}",
                f"Recognition: {', '.join(profile.recognition) or 'None'}"
            ]
        },
        "eligibility_assessment": {
            "title": "O-1 Eligibility Assessment",
            "score": score,
            "level": get_eligibility_level(score),
            "criteria_met": get_met_criteria(profile),
            "missing_criteria": []
        },
        "application_process": {
            "title": "O-1 Application Process",
            "steps": [
                "File Form I-129 with USCIS",
                "Submit evidence of extraordinary ability",
                "Include 2+ consultation letters",
                "Wait for approval (3-6 months)"
            ]
        },
        "next_steps": {
            "title": "Next Steps",
            "items": [
                "Consult immigration attorney",
                "Gather evidence documentation",
                "Obtain consultation letters",
                "Prepare work plan"
            ]
        }
    }

# CLI Interface
class CLIInterface:
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.profile = UserProfile()
        self.engine = ImmigrationEngine()
        self.questions = QuestionEngine()

    def run(self):
        if not self.console:
            print("Rich library not available. Install with: pip install rich")
            return

        self.console.print(Panel("Immigration Copilot - CLI Version\n\nAnswer questions to get personalized guidance.", title="Welcome"))
        self.conversation_loop()

    def conversation_loop(self):
        while True:
            next_q = self.questions.get_next_question(self.profile)
            if not next_q:
                self.show_results()
                break

            question = self.questions.questions[next_q]
            self.console.print(f"\n[bold cyan]Q:[/bold cyan] {question}")

            answer = input("Your answer: ").strip()
            if not answer:
                continue

            self.process_answer(next_q, answer)

    def process_answer(self, question_key: str, answer: str):
        if question_key == "country":
            self.profile.country = answer
        elif question_key == "o1_field":
            self.profile.o1_field = answer.lower().replace(' ', '_')
        elif question_key == "education":
            if 'phd' in answer.lower() or 'doctorate' in answer.lower():
                self.profile.education = 'phd'
            elif 'master' in answer.lower():
                self.profile.education = 'masters'
            elif 'bachelor' in answer.lower():
                self.profile.education = 'bachelors'
        elif question_key == "recognition":
            self.profile.recognition = [r.strip() for r in answer.split(',') if r.strip()]
        elif question_key == "profession":
            self.profile.profession = answer
            self.profile.has_experience = True
        elif question_key == "goal":
            self.profile.goal = answer
            self.profile.us_work_plans = 'work' in answer.lower() or 'us' in answer.lower()

    def show_results(self):
        pathways = self.engine.assess_eligibility(self.profile)
        index = create_immigration_index(self.profile)

        self.console.print("\n[bold green]Your Immigration Assessment:[/bold green]")

        # Show user profile
        table = Table(title="Your Profile")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        for item in index["user_profile"]["items"]:
            field, value = item.split(": ", 1)
            table.add_row(field, value)
        self.console.print(table)

        # Show eligibility
        assessment = index["eligibility_assessment"]
        self.console.print(f"\n[bold]O-1 Eligibility: {assessment['level']} (Score: {assessment['score']}/100)[/bold]")

        if assessment["criteria_met"]:
            self.console.print("\n[green]Criteria Met:[/green]")
            for criterion in assessment["criteria_met"]:
                self.console.print(f"  • {criterion}")

        # Show next steps
        self.console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        for step in index["next_steps"]["items"]:
            self.console.print(f"  • {step}")

        self.console.print("\n[red]Disclaimer: This is not legal advice. Consult an immigration attorney.[/red]")

# Web Application
class WebApp:
    def __init__(self):
        if not FLASK_AVAILABLE:
            print("Flask not available. Install with: pip install flask flask-cors")
            return

        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        CORS(self.app)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('condensed_index.html')

        @self.app.route('/api/start', methods=['POST'])
        def start_chat():
            session.clear()
            session['profile'] = asdict(UserProfile())
            session['conversation'] = []
            return jsonify({
                "question": "What country are you a citizen of?",
                "has_info": False
            })

        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            data = request.json
            user_message = data.get('message', '').strip()

            if not user_message:
                return jsonify({"error": "Message cannot be empty"}), 400

            profile_dict = session.get('profile', asdict(UserProfile()))
            profile = UserProfile(**profile_dict)

            # Process answer
            self.process_web_answer(profile, user_message)

            # Check if we should create index
            engine = ImmigrationEngine()
            pathways = engine.assess_eligibility(profile)

            response_data = {
                "response": "Thank you for that information.",
                "has_info": True,
                "user_info": asdict(profile),
                "should_create_index": len([p for p in pathways.values() if p.get('eligible')]) > 0
            }

            if response_data["should_create_index"]:
                response_data["index"] = create_immigration_index(profile)

            session['profile'] = asdict(profile)
            return jsonify(response_data)

        @self.app.route('/api/reset', methods=['POST'])
        def reset():
            session.clear()
            return jsonify({"success": True})

    def process_web_answer(self, profile: UserProfile, message: str):
        message_lower = message.lower()

        # Extract information using simple keyword matching
        if 'citizen' in message_lower or 'from' in message_lower:
            # Simple country extraction
            for country in ['india', 'china', 'mexico', 'canada', 'uk', 'germany', 'france']:
                if country in message_lower:
                    profile.country = country.title()
                    break

        if 'science' in message_lower or 'art' in message_lower or 'education' in message_lower:
            if 'science' in message_lower: profile.o1_field = 'science'
            elif 'art' in message_lower: profile.o1_field = 'arts'
            elif 'education' in message_lower: profile.o1_field = 'education'
            elif 'business' in message_lower: profile.o1_field = 'business'
            elif 'athlet' in message_lower: profile.o1_field = 'athletics'
            elif 'film' in message_lower or 'tv' in message_lower: profile.o1_field = 'film_tv'

        if 'phd' in message_lower or 'doctorate' in message_lower: profile.education = 'phd'
        elif 'master' in message_lower: profile.education = 'masters'
        elif 'bachelor' in message_lower: profile.education = 'bachelors'

        # Recognition keywords
        recognition_keywords = ['award', 'prize', 'publication', 'paper', 'media', 'recognition']
        if any(kw in message_lower for kw in recognition_keywords):
            profile.recognition.extend([kw for kw in recognition_keywords if kw in message_lower])

        if 'engineer' in message_lower or 'scientist' in message_lower:
            profile.profession = 'engineer' if 'engineer' in message_lower else 'scientist'
            profile.has_experience = True

        if 'work' in message_lower or 'job' in message_lower:
            profile.goal = 'work'
            profile.us_work_plans = True

    def run(self, port=3000):
        self.app.run(debug=True, port=port)

# Main execution
def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == 'web':
            if not FLASK_AVAILABLE:
                print("Flask required for web mode. Install: pip install flask flask-cors")
                return
            web_app = WebApp()
            web_app.run()
            return

        elif mode == 'o1':
            # O-1 specific mode
            if not FLASK_AVAILABLE:
                print("Flask required for O-1 mode. Install: pip install flask flask-cors")
                return
            web_app = WebApp()
            web_app.run()
            return

    # Default to CLI mode
    cli = CLIInterface()
    cli.run()

if __name__ == '__main__':
    main()
