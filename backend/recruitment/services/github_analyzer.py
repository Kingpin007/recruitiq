import re
import time
from collections import Counter

from decouple import config
from github import Github, GithubException, RateLimitExceededException


class GitHubAnalyzer:
    """Service for analyzing GitHub profiles."""

    def __init__(self):
        self.api_token = config("GITHUB_TOKEN", default="")
        if self.api_token:
            self.client = Github(self.api_token)
        else:
            # Anonymous access (lower rate limits)
            self.client = Github()
        self.max_repos = 100  # Limit to prevent excessive API calls

    def extract_github_username(self, text):
        """
        Extract GitHub username from text (resume).

        Looks for patterns like:
        - github.com/username
        - github.com/username/
        - @username (if GitHub is mentioned nearby)
        """
        # Pattern for full GitHub URLs
        url_pattern = r"github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})"
        matches = re.findall(url_pattern, text, re.IGNORECASE)

        if matches:
            return matches[0]

        # Pattern for @username mentions near "github"
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "github" in line.lower():
                # Look in this line and next few lines for @username
                search_text = "\n".join(lines[i : i + 3])
                username_pattern = r"@([a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38})"
                username_matches = re.findall(username_pattern, search_text)
                if username_matches:
                    return username_matches[0]

        return None

    def fetch_user_profile(self, username):
        """Fetch GitHub user profile data."""
        try:
            user = self.client.get_user(username)
            return {
                "login": user.login,
                "name": user.name,
                "bio": user.bio,
                "company": user.company,
                "location": user.location,
                "email": user.email,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        except GithubException as e:
            if e.status == 404:
                raise Exception(f"GitHub user '{username}' not found")
            elif e.status == 403:
                raise Exception("GitHub API rate limit exceeded")
            else:
                raise Exception(f"GitHub API error: {e}")

    def fetch_repositories(self, username, max_repos=None):
        """Fetch user's repositories and analyze them."""
        max_repos = max_repos or self.max_repos

        try:
            user = self.client.get_user(username)
            repos = list(user.get_repos(type="owner", sort="updated")[:max_repos])

            repos_data = []
            for repo in repos:
                try:
                    repos_data.append(
                        {
                            "name": repo.name,
                            "description": repo.description,
                            "language": repo.language,
                            "stars": repo.stargazers_count,
                            "forks": repo.forks_count,
                            "is_fork": repo.fork,
                            "created_at": repo.created_at.isoformat() if repo.created_at else None,
                            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                            "size": repo.size,
                            "topics": repo.get_topics(),
                        }
                    )
                except Exception as e:
                    # Skip repos that can't be accessed
                    continue

            return repos_data

        except RateLimitExceededException:
            raise Exception("GitHub API rate limit exceeded")
        except GithubException as e:
            if e.status == 404:
                raise Exception(f"GitHub user '{username}' not found")
            else:
                raise Exception(f"GitHub API error: {e}")

    def analyze_profile(self, repos_data):
        """Analyze GitHub profile data and compute metrics."""
        if not repos_data:
            return {
                "total_repos": 0,
                "active_repos": 0,
                "languages": [],
                "total_stars": 0,
                "total_forks": 0,
                "total_contributions": 0,
                "original_repos": 0,
                "forked_repos": 0,
                "topics": [],
            }

        # Filter out forks for some metrics
        original_repos = [r for r in repos_data if not r["is_fork"]]

        # Count languages
        language_counter = Counter()
        for repo in repos_data:
            if repo["language"]:
                language_counter[repo["language"]] += 1

        # Get most common languages
        top_languages = [lang for lang, count in language_counter.most_common(10)]

        # Count topics
        topic_counter = Counter()
        for repo in repos_data:
            for topic in repo.get("topics", []):
                topic_counter[topic] += 1

        top_topics = [topic for topic, count in topic_counter.most_common(10)]

        # Calculate total stars and forks
        total_stars = sum(r["stars"] for r in original_repos)
        total_forks = sum(r["forks"] for r in original_repos)

        # Determine active repos (updated in last year)
        from datetime import datetime, timedelta

        one_year_ago = datetime.now() - timedelta(days=365)
        active_repos = [
            r
            for r in repos_data
            if r["updated_at"]
            and datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00")) > one_year_ago
        ]

        return {
            "total_repos": len(repos_data),
            "active_repos": len(active_repos),
            "languages": top_languages,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_contributions": len(repos_data),  # Simplified metric
            "original_repos": len(original_repos),
            "forked_repos": len(repos_data) - len(original_repos),
            "topics": top_topics,
            "language_diversity": len(language_counter),
            "average_repo_stars": total_stars / len(original_repos) if original_repos else 0,
        }

