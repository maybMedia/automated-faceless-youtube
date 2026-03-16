import os

import praw
import requests
from prawcore.exceptions import PrawcoreException
from random import choice

reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID", "CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET", "CLIENT_SECRET"),
    user_agent="scrollstoriesbot"
)

SUBREDDITS = [
    "AmItheAsshole",
    "confession",
    "relationship_advice",
    "tifu"
]

MIN_STORY_LENGTH = 500
MAX_STORY_LENGTH = 12000
POST_LIMIT = 30
EXCLUDED_TITLE_PHRASES = (
    "monthly open forum",
    "open forum",
    "monthly forum",
    "meta",
    "announcement",
    "rule",
    "rules",
    "mod post",
    "megathread",
    "weekly discussion",
    "daily discussion",
    "updates, rules",
)


def _has_reddit_api_credentials():
    return (
        reddit.config.client_id
        and reddit.config.client_id != "CLIENT_ID"
        and reddit.config.client_secret
        and reddit.config.client_secret != "CLIENT_SECRET"
    )


def _is_story_candidate(title, story, *, pinned=False, stickied=False, is_self=True):
    normalized_title = title.strip().lower()
    normalized_story = story.strip()

    if pinned or stickied or not is_self:
        return False

    if len(normalized_story) < MIN_STORY_LENGTH or len(normalized_story) > MAX_STORY_LENGTH:
        return False

    if any(phrase in normalized_title for phrase in EXCLUDED_TITLE_PHRASES):
        return False

    if normalized_title.startswith(("[meta]", "meta:", "announcement:", "mod:")):
        return False

    return True


def _story_score(title, story, ups=0, comments=0):
    title_bonus = 100 if any(
        keyword in title.lower()
        for keyword in ("aita", "tifu", "confession", "relationship", "boyfriend", "girlfriend", "husband", "wife")
    ) else 0
    length_score = min(len(story), 1800)
    engagement_score = min(ups, 500) + min(comments * 3, 300)
    return title_bonus + length_score + engagement_score


def _select_best_story(candidates):
    if not candidates:
        return None

    best_score = max(candidate["score"] for candidate in candidates)
    best_candidates = [candidate for candidate in candidates if candidate["score"] == best_score]
    selected = choice(best_candidates)
    return {
        "title": selected["title"],
        "story": selected["story"],
        "subreddit": selected["subreddit"],
    }


def _get_story_from_public_json():
    headers = {"User-Agent": "scrollstoriesbot/0.1"}
    candidates = []

    for sub in SUBREDDITS:
        response = requests.get(
            f"https://www.reddit.com/r/{sub}/hot.json",
            params={"limit": POST_LIMIT, "raw_json": 1},
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        posts = response.json().get("data", {}).get("children", [])
        for post in posts:
            post_data = post.get("data", {})
            story = post_data.get("selftext", "").strip()
            title = post_data.get("title", "").strip()

            if _is_story_candidate(
                title,
                story,
                pinned=post_data.get("pinned", False),
                stickied=post_data.get("stickied", False),
                is_self=post_data.get("is_self", True),
            ):
                candidates.append(
                    {
                        "title": title,
                        "story": story,
                        "subreddit": sub,
                        "score": _story_score(
                            title,
                            story,
                            ups=post_data.get("ups", 0),
                            comments=post_data.get("num_comments", 0),
                        ),
                    }
                )

    return _select_best_story(candidates)


def get_story():
    if not _has_reddit_api_credentials():
        return _get_story_from_public_json()

    try:
        candidates = []
        for sub in SUBREDDITS:
            subreddit = reddit.subreddit(sub)

            for post in subreddit.hot(limit=POST_LIMIT):
                if _is_story_candidate(
                    post.title,
                    post.selftext,
                    pinned=getattr(post, "pinned", False),
                    stickied=getattr(post, "stickied", False),
                    is_self=getattr(post, "is_self", True),
                ):
                    candidates.append(
                        {
                            "title": post.title.strip(),
                            "story": post.selftext.strip(),
                            "subreddit": sub,
                            "score": _story_score(
                                post.title,
                                post.selftext,
                                ups=getattr(post, "ups", 0),
                                comments=getattr(post, "num_comments", 0),
                            ),
                        }
                    )
        return _select_best_story(candidates)
    except PrawcoreException:
        return _get_story_from_public_json()

if __name__ == "__main__":
    print(get_story())
